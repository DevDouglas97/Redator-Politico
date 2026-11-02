import os
import requests
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    """Faz uma requisição curta para verificar a conexão configurada com Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY não encontrada no .env")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
    payload = {"contents": [{"parts": [{"text": "Oi"}]}]}
    try:
        response = requests.post(url, headers={"x-goog-api-key": api_key}, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as erro:
        raise SystemExit(f"Falha ao conectar com o Gemini: {erro}") from erro
    print("Status:", response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
