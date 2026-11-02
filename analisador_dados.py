import pandas as pd
from relatorios import salvar_pdf_analise


CAMINHO_CSV = "projetos_assinados_parlamentares_rs.csv"


def main() -> None:
    """Valida o CSV, exibe indicadores e exporta a análise para PDF."""
    try:
        df = pd.read_csv(CAMINHO_CSV, encoding="utf-8-sig")
    except FileNotFoundError as erro:
        raise SystemExit(f"Arquivo '{CAMINHO_CSV}' não encontrado. Execute redator1.py primeiro.") from erro
    except pd.errors.EmptyDataError as erro:
        raise SystemExit(f"O arquivo '{CAMINHO_CSV}' está vazio.") from erro

    colunas = {"Deputado(a)", "Partido", "Tipo", "Número", "Ano", "Ementa/Resumo"}
    faltantes = colunas - set(df.columns)
    if faltantes:
        raise SystemExit(f"CSV inválido: faltam as colunas {', '.join(sorted(faltantes))}.")
    if df.empty:
        raise SystemExit("O CSV não contém registros para analisar.")
    if "Último Status" not in df.columns:
        df["Último Status"] = "N/A"

    print("--- ANÁLISE COMPLETA DOS DADOS --- \n")

    # Total de proposições mapeadas
    total_registros = len(df)
    print(f"📊 Total de proposições registradas: {total_registros}\n")

    # Ranking de deputados mais ativos na base
    print("🔥 Top 5 Deputados com mais registros:")
    print(df["Deputado(a)"].value_counts().head(5))
    print("\n" + "-"*40 + "\n")

    # Distribuição por Partido político
    print("🏢 Proposições por Partido:")
    print(df["Partido"].value_counts())
    print("\n" + "-"*40 + "\n")

    # Status mais frequentes
    print("📌 Status mais frequentes:")
    status_counts = df["Último Status"].fillna("N/A").value_counts()
    print(status_counts.head(10))
    print("\n" + "-"*40 + "\n")

    # Filtrar apenas Projetos de Lei e PECs
    projetos_importantes = df[df["Tipo"].isin(["PL", "PEC"])].copy()
    print(f"💡 Foram encontrados {len(projetos_importantes)} Projetos de Lei (PL) ou PECs.")

    # Exibe os principais destaques com status atual
    for _, linha in projetos_importantes.head(5).iterrows():
        nome = linha["Deputado(a)"]
        partido = linha["Partido"]
        tipo = linha["Tipo"]
        numero = linha["Número"]
        ano = linha["Ano"]
        status = linha["Último Status"]
        ementa = linha["Ementa/Resumo"]

        print(f"\nNome: {nome} ({partido})")
        print(f"Tipo: {tipo} nº {numero}/{ano}")
        print(f"Status atual: {status}")
        print(f"Resumo: {ementa}")
        print("-" * 60)

    # Salvar resumo em PDF
    caminho_pdf = "analise_dados.pdf"
    salvar_pdf_analise(df, caminho_pdf)
    print(f"\n📄 PDF da análise salvo em: '{caminho_pdf}'")


if __name__ == "__main__":
    main()

