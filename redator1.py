import time
from typing import Any

import requests
import pandas as pd

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
REQUEST_INTERVAL_SECONDS = 0.25
MAX_RETRIES = 4
_ultima_requisicao = 0.0


def buscar_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Consulta a API da Câmara com limite de ritmo e retry progressivo."""
    global _ultima_requisicao
    for tentativa in range(MAX_RETRIES):
        tempo_ate_proxima = REQUEST_INTERVAL_SECONDS - (time.monotonic() - _ultima_requisicao)
        if tempo_ate_proxima > 0:
            time.sleep(tempo_ate_proxima)
        try:
            resposta = requests.get(url, params=params, timeout=30)
        except requests.RequestException:
            if tentativa == MAX_RETRIES - 1:
                raise
            time.sleep(min(2**tentativa, 8))
            continue
        _ultima_requisicao = time.monotonic()
        if resposta.status_code == 429 or resposta.status_code >= 500:
            if tentativa == MAX_RETRIES - 1:
                resposta.raise_for_status()
            time.sleep(min(2**tentativa, 8))
            continue
        resposta.raise_for_status()
        return resposta.json()
    raise RuntimeError("A consulta à API terminou sem resposta.")


def buscar_todos(url: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Percorre as páginas indicadas pela API e reúne todos os registros."""
    resultados = []
    proxima_url = url
    parametros = params
    while proxima_url:
        resposta = buscar_json(proxima_url, params=parametros)
        resultados.extend(resposta.get("dados", []))
        proxima_url = next(
            (link["href"] for link in resposta.get("links", []) if link.get("rel") == "next"),
            None,
        )
        parametros = None  # O link seguinte já contém os parâmetros da página.
    return resultados


def coletar_proposicoes() -> list[dict[str, Any]]:
    """Busca até cinco proposições recentes para cada deputado do RS."""
    url_deputados = f"{API_BASE}/deputados"
    params_deputados = {"siglaUf": "RS", "ordem": "ASC", "ordenarPor": "nome", "itens": 100}
    print("Buscando deputados do RS...")
    deputados_rs = buscar_todos(url_deputados, params_deputados)
    lista_proposicoes_rs = []

    print("Buscando projetos assinados (isso pode levar alguns segundos)...")
    for dep in deputados_rs:
        id_deputado = dep.get("id")
        nome_deputado = dep.get("nome", "Nome não informado")
        partido = dep.get("siglaPartido", "Partido não informado")

        if id_deputado is None:
            continue

        url_proposicoes = f"{API_BASE}/proposicoes"
        params_proposicoes = {
            "idDeputadoAutor": id_deputado,
            "ordem": "DESC",
            "ordenarPor": "id",
            "itens": 5,
        }
        resposta_prop = buscar_json(url_proposicoes, params=params_proposicoes)

        for prop in resposta_prop.get("dados", []):
            prop_id = prop.get("id")
            ultimo_status = "N/A"

            if prop_id is not None:
                url_detalhe_prop = f"{API_BASE}/proposicoes/{prop_id}"
                try:
                    detalhe_prop = buscar_json(url_detalhe_prop)
                    dados_prop = detalhe_prop.get("dados", {})
                    status_obj = dados_prop.get("statusProposicao") or dados_prop.get("ultimoStatus")

                    if isinstance(status_obj, dict):
                        ultimo_status = (
                            status_obj.get("descricaoSituacao")
                            or status_obj.get("descricaoTramitacao")
                            or status_obj.get("despacho")
                            or "N/A"
                        )
                    elif isinstance(status_obj, str):
                        ultimo_status = status_obj
                except requests.RequestException as erro:
                    print(f"Aviso: não foi possível obter o status da proposição {prop_id}: {erro}")

            lista_proposicoes_rs.append(
                {
                    "Deputado(a)": nome_deputado,
                    "Partido": partido,
                    "Tipo": prop.get("siglaTipo", "N/A"),
                    "Número": prop.get("numero", "N/A"),
                    "Ano": prop.get("ano", "N/A"),
                    "Último Status": ultimo_status,
                    "Ementa/Resumo": prop.get("ementa", "N/A"),
                }
            )
    return lista_proposicoes_rs


def main() -> None:
    """Executa coleta, análise e geração do boletim em sequência."""
    try:
        df = pd.DataFrame(coletar_proposicoes())
    except requests.RequestException as erro:
        raise SystemExit(f"Falha ao consultar a API da Câmara: {erro}") from erro
    if df.empty:
        print("\nNenhuma proposição foi encontrada para os deputados do RS.")
        return
    df.to_csv("projetos_assinados_parlamentares_rs.csv", index=False, encoding="utf-8-sig")
    print("\nSucesso! Arquivo 'projetos_assinados_parlamentares_rs.csv' gerado.")
    print(df.head())

    # Importações locais evitam carregar etapas posteriores quando o módulo é importado.
    from analisador_dados import main as executar_analise
    from gerador_boletim import main as executar_gerador

    print("\n=== Etapa 2/3: análise dos dados ===")
    executar_analise()

    print("\n=== Etapa 3/3: geração do boletim ===")
    executar_gerador()

    print("\nPipeline concluído: CSV, análise e boletim foram gerados.")


if __name__ == "__main__":
    main()
