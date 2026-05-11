import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import re
import unicodedata
from supabase import create_client, Client
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(
    page_title="IA Competitive Intelligence",
    layout="wide"
)

# ---------------------------------------------------
# CONFIGURAÇÃO SUPABASE
# ---------------------------------------------------
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase = get_supabase()

# ---------------------------------------------------
# CONFIGURAÇÃO GEMINI (ATUALIZADA)
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-1.5-pro")
else:
    gemini_model = None

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------
def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def formatar_url(url):
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ---------------------------------------------------
# EXTRAÇÃO REAL DE CONTEÚDO (JS RENDERIZADO)
# ---------------------------------------------------
def extrair_conteudo_site(url: str) -> str:
    url_fmt = formatar_url(url)
    if not url_fmt:
        return ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )

            page.goto(url_fmt, timeout=30000)
            page.wait_for_timeout(5000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # Remove elementos irrelevantes
        for tag in soup(["script", "style", "noscript", "svg", "footer", "header"]):
            tag.decompose()

        texto = soup.get_text(separator="\n")

        # Limpeza semântica
        texto = re.sub(
            r"(Política de Privacidade.*|Cookies.*|©.*|Todos os direitos reservados.*)",
            "",
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        texto = re.sub(r"\n{3,}", "\n\n", texto).strip()

        if len(texto) < 300:
            return "Conteúdo institucional limitado ou carregado dinamicamente."

        return texto

    except Exception as e:
        return f"[Erro ao processar {url_fmt}: {e}]"

# ---------------------------------------------------
# INTERFACE DO APP
# ---------------------------------------------------
st.title("Análise Competitiva com IA")

st.markdown(
    "Informe os **sites da sua empresa e dos concorrentes** para gerar "
    "um relatório comparativo de posicionamento, mensagens-chave e oportunidades."
)

urls = st.text_area(
    "Sites (um por linha):",
    placeholder="https://suaempresa.com\nhttps://concorrente.com"
)

if st.button("Gerar Relatório"):
    if not gemini_model:
        st.error("API do Gemini não configurada.")
    elif not urls.strip():
        st.warning("Informe ao menos um site.")
    else:
        sites = [u.strip() for u in urls.split("\n") if u.strip()]
        conteudos = []

        for site in sites:
            with st.spinner(f"Extraindo conteúdo de {site}..."):
                texto = extrair_conteudo_site(site)
                conteudos.append(f"SITE: {site}\n\n{texto}")

        prompt = f"""
Você é um estrategista sênior de marketing e branding.

Analise os conteúdos institucionais abaixo e gere um relatório contendo:

1. Posicionamento estratégico de cada empresa
2. Mensagens-chave principais
3. Diferenciais competitivos percebidos
4. Pontos fracos de comunicação
5. Oportunidades estratégicas NÃO exploradas pelos concorrentes
6. Recomendações práticas de diferenciação

Ignore rodapés, endereços e informações legais.

CONTEÚDOS:
{"\n\n---\n\n".join(conteudos)}
"""

        try:
            resposta = gemini_model.generate_content(prompt)
            st.subheader("Relatório de Competitividade")
            st.write(resposta.text)
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
