import streamlit as st
import pandas as pd
import re
import requests
import trafilatura
from supabase import create_client, Client
import google.generativeai as genai

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
# CONFIGURAÇÃO GEMINI (SDK ESTÁVEL)
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("models/gemini-pro")
else:
    gemini_model = None

# ---------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------
def formatar_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url

def extrair_conteudo_site(url: str) -> str:
    try:
        url = formatar_url(url)
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0"
        })

        if r.status_code != 200:
            return "Conteúdo indisponível."

        texto = trafilatura.extract(
            r.text,
            favor_precision=True,
            include_links=False,
            include_images=False
        )

        if not texto or len(texto) < 200:
            return "Site com pouco conteúdo institucional ou carregado via JS."

        texto = re.sub(
            r"(Política de Privacidade.*|Cookies.*)",
            "",
            texto,
            flags=re.I | re.S
        )

        return texto.strip()

    except Exception as e:
        return f"Erro ao acessar site: {e}"

# ---------------------------------------------------
# INTERFACE
# ---------------------------------------------------
st.title("Análise Competitiva com IA")

urls = st.text_area(
    "Sites (um por linha):",
    placeholder="https://suaempresa.com\nhttps://concorrente.com"
)

if st.button("Gerar Relatório"):
    if not gemini_model:
        st.error("API Gemini não configurada.")
    elif not urls.strip():
        st.warning("Informe ao menos um site.")
    else:
        sites = [u.strip() for u in urls.split("\n") if u.strip()]
        conteudos = []

        for site in sites:
            with st.spinner(f"Extraindo {site}..."):
                conteudos.append(
                    f"SITE: {site}\n{extrair_conteudo_site(site)}"
                )

        prompt = f"""
Você é um estrategista sênior de marketing.

Analise os sites abaixo e gere um relatório com:
1. Posicionamento
2. Mensagens-chave
3. Diferenciais
4. Fragilidades
5. Oportunidades
6. Recomendações práticas

CONTEÚDOS:
{"\n\n---\n\n".join(conteudos)}
"""

        try:
            resposta = gemini_model.generate_content(prompt)
            st.subheader("Relatório de Competitividade")
            st.write(resposta.text)
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
