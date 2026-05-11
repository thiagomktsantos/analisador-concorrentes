import streamlit as st
import pandas as pd
import re
import unicodedata
import requests
import trafilatura
from supabase import create_client, Client
from google import genai

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
# CONFIGURAÇÃO GEMINI (SDK NOVO - FUNCIONAL)
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    gemini_client = None

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------
def formatar_url(url):
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ---------------------------------------------------
# EXTRAÇÃO DE CONTEÚDO (ROBUSTA)
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

        texto = trafilatura.extract(
            resp.text,
            favor_precision=True,
            include_links=False,
            include_images=False,
            include_tables=False,
            deduplicate=True,
            no_fallback=False
        )

        if not texto or len(texto) < 200:
            return "Site com conteúdo carregado via JavaScript ou com baixo conteúdo institucional."

        texto = re.sub(
            r"(Política de Privacidade.*|Cookies.*|©.*|Todos os direitos reservados.*)",
            "",
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        return texto.strip()

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
    if not gemini_client:
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
Você é um estrategista sênior de marketing e posicionamento competitivo.

Analise os conteúdos abaixo e gere um relatório com:
1. Posicionamento de cada empresa
2. Mensagens-chave
3. Diferenciais competitivos
4. Fragilidades
5. Oportunidades
6. Recomendações práticas

CONTEÚDOS:
{"\n\n---\n\n".join(conteudos)}
"""

        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            st.subheader("Relatório de Competitividade")
            st.write(response.text)

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
