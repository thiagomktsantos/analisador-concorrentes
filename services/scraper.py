import requests
from bs4 import BeautifulSoup


def extrair_conteudo_site(url):

    try:
        html = requests.get(url, timeout=10).text

        soup = BeautifulSoup(html, "html.parser")

        return soup.get_text(separator=" ")[:10000]

    except Exception as e:
        return f"[Erro] {e}"
