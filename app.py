import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import unicodedata
import requests
import trafilatura
from supabase import create_client, Client

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
def get_supabase() -> Client | None:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

supabase = get_supabase()

# ---------------------------------------------------
# CONFIGURAÇÃO GEMINI (VERSÃO ATUAL DA API)
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
else:
    gemini_model = None

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------
def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def formatar_url(url):
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ---------------------------------------------------
# EXTRAÇÃO DE CONTEÚDO (ROBUSTA / CLOUD SAFE)
# ---------------------------------------------------
def extrair_conteudo_site(url: str) -> str:
    url_fmt = formatar_url(url)
    if not url_fmt:
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }

    try:
        resp = requests.get(url_fmt, headers=headers, timeout=20)
        if resp.status_code != 200:
            return "Conteúdo indisponível ou bloqueado."

        html = resp.text

        texto = trafilatura.extract(
            html,
            favor_precision=True,
            include_links=False,
            include_images=False,
            include_tables=False,
            deduplicate=True,
            no_fallback=False
        )

        if not texto or len(texto) < 200:
            return (
                "Site com conteúdo carregado via JavaScript ou com baixo conteúdo institucional."
            )

        texto = re.sub(
            r"(Política de Privacidade.*|Cookies.*|©.*|Todos os direitos reservados.*)",
            "",
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )
        texto = re.sub(r"\n{3,}", "\n\n", texto).strip()

        return texto

    except Exception as e:
        return f"[Erro ao acessar {url_fmt}: {e}]"

# ---------------------------------------------------
# INTERFACE
# ---------------------------------------------------
st.title("Análise Competitiva com IA")

st.markdown(
    "Insira os **sites da sua empresa e concorrentes** "
    "para gerar um relatório estratégico comparativo."
)

urls = st.text_area(
    "Sites (um por linha):",
    placeholder="https://suaempresa.com\nhttps://concorrente.com"
)

if st.button("Gerar Relatório"):
    if not gemini_model:
        st.error("API do Gemini não configurada.")
    elif not urls.strip():
        st.warning("Informe pelo menos um site.")
    else:
        sites = [u.strip() for u in urls.split("\n") if u.strip()]
        conteudos = []

        for site in sites:
            with st.spinner(f"Extraindo conteúdo de {site}..."):
                texto = extrair_conteudo_site(site)
                conteudos.append(f"SITE: {site}\n\n{texto}")

        prompt = f"""
Você é um estrategista sênior de marketing, branding e posicionamento competitivo.

Analise os conteúdos abaixo e gere um relatório com:

1. Posicionamento percebido de cada empresa
2. Mensagens-chave predominantes
3. Diferenciais competitivos
4. Fragilidades de comunicação
5. Oportunidades estratégicas
6. Recomendações práticas e acionáveis

Considere ausência ou baixo conteúdo como insight estratégico.

CONTEÚDOS:
{"\n\n---\n\n".join(conteudos)}
"""

        try:
            resposta = gemini_model.generate_content(prompt)
            st.subheader("Relatório de Competitividade")
            st.write(resposta.text)
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
