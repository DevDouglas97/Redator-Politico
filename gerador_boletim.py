import os
import time
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from relatorios import salvar_pdf_boletim

# 1. Carrega as variáveis salvas no arquivo .env
load_dotenv()

# 2. Resgata a chave de API de forma protegida
API_KEY = os.getenv("GEMINI_API_KEY")


def traduzir_ementa_com_requests(texto_tecnico: str, status_atual: str = "N/A") -> str:
    """Simplifica uma ementa com Gemini, repetindo falhas temporárias com backoff."""
    if not API_KEY:
        print("❌ Erro: Chave GEMINI_API_KEY não encontrada no arquivo .env!")
        return texto_tecnico

    url_gemini = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.5-flash-lite:generateContent"
    )

    prompt = (
        "Você é um redator parlamentar especializado em transformar textos técnicos em linguagem clara para o cidadão comum. "
        "Resuma a ementa abaixo em uma frase curta, objetiva e informativa, em português do Brasil. "
        "Explique o objetivo da proposta e, se houver, indique seu impacto prático para a população. "
        "Não use termos jurídicos excessivos. Mantenha um tom jornalístico, natural e acessível. "
        "Se o status atual da proposição for relevante, leve isso em conta no texto, mas não o transforme em jargão. \n\n"
        f"Status atual da proposição: {status_atual}\n\n"
        f"Texto original: {texto_tecnico}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    for tentativa in range(4):
        if tentativa:
            time.sleep(min(2**tentativa, 8))
        try:
            resposta = requests.post(
                url_gemini,
                headers={"x-goog-api-key": API_KEY},
                json=payload,
                timeout=30,
            )
            resposta.raise_for_status()
            partes = resposta.json()["candidates"][0]["content"]["parts"]
            texto = " ".join(parte["text"] for parte in partes if "text" in parte).strip()
            return texto or texto_tecnico
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as erro:
            if tentativa == 3:
                print(f"⚠️ Falha na comunicação com a IA: {erro}. Usando texto original.")
                return texto_tecnico
    return texto_tecnico

def main() -> None:
    """Gera o boletim Markdown e PDF a partir da base CSV."""
    caminho_csv = "projetos_assinados_parlamentares_rs.csv"
    if not os.path.exists(caminho_csv):
        raise SystemExit(f"Arquivo '{caminho_csv}' não encontrado. Execute redator1.py primeiro.")

    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except pd.errors.EmptyDataError as erro:
        raise SystemExit(f"O arquivo '{caminho_csv}' está vazio.") from erro

    colunas = {"Tipo", "Ano", "Número", "Deputado(a)", "Partido", "Ementa/Resumo"}
    faltantes = colunas - set(df.columns)
    if faltantes:
        raise SystemExit(f"CSV inválido: faltam as colunas {', '.join(sorted(faltantes))}.")
    if "Último Status" not in df.columns:
        df["Último Status"] = "N/A"

    pls_e_pecs = df[df["Tipo"].isin(["PL", "PEC"])].copy()
    pls_e_pecs = pls_e_pecs.sort_values(by=["Ano", "Número"], ascending=[False, False]).head(20)
    data_atual = datetime.now().strftime("%d/%m/%Y")
    boletim_markdown = (
        f"# 📝 Boletim de Atividade Parlamentar Gaúcha\n"
        f"**Data de Geração:** {data_atual}\n\n"
        "A seguir, os destaques mais relevantes em Projetos de Lei (PL) e Propostas de Emenda à Constituição (PEC) "
        "apresentados por deputados gaúchos, com explicação em linguagem acessível para o leitor.\n\n"
    )

    print("🤖 Iniciando processamento do texto com a Inteligência Artificial...")
    for _, linha in pls_e_pecs.iterrows():
        deputado = linha["Deputado(a)"]
        status_atual = linha["Último Status"]
        print(f"-> Traduzindo projeto de {deputado}...")
        resumo_simples = traduzir_ementa_com_requests(linha["Ementa/Resumo"], status_atual)
        boletim_markdown += (
            f"* **{deputado} ({linha['Partido']})** - {linha['Tipo']} {linha['Número']}/{linha['Ano']}\n"
            f"  * **Status:** {status_atual}\n"
            f"  * **Resumo:** {resumo_simples}\n\n"
        )
        time.sleep(0.5)

    caminho_saida = "boletim_parlamentar.md"
    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(boletim_markdown)
    caminho_pdf = "boletim_parlamentar.pdf"
    salvar_pdf_boletim(boletim_markdown, caminho_pdf)
    print(f"\n✨ Arquivo final gerado com sucesso em: '{caminho_saida}'")
    print(f"📄 PDF do boletim salvo em: '{caminho_pdf}'")


if __name__ == "__main__":
    main()
