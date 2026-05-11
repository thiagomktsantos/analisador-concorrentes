import streamlit as st
import pandas as pd
import re
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
# CONFIGURAÇÃO GEMINI (SDK NOVO — ÚNICO FUNCIONAL)
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    gemini_client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )
else:
    gemini_client = None

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------
def formatar_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ---------------------------------------------------
# EXTRAÇÃO DE CONTEÚDO
# ---------------------------------------------------
def extrair_conteudo_site(url: str) -> str:
    try:
        url = formatar_url(url)
        resp = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if resp.status_code != 200:
            return "Conteúdo indisponível."

        texto = trafilatura.extract(
            resp.text,
            favor_precision=True,
            include_links=False,
            include_images=False,
            deduplicate=True,
            no_fallback=False
        )

        if not texto or len(texto) < 200:
            return "Site com conteúdo institucional limitado ou carregado via JavaScript."

        texto = re.sub(
            r"(Política de Privacidade.*|Cookies.*|©.*)",
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

st.markdown(
    "Insira os **sites da sua empresa e concorrentes** "
    "para gerar um relatório comparativo."
)

urls = st.text_area(
    "Sites (um por linha):",
    placeholder="https://suaempresa.com\nhttps://concorrente.com"
)

if st.button("Gerar Relatório"):
    if not gemini_client:
        st.error("API Gemini não configurada.")
    elif not urls.strip():
        st.warning("Informe pelo menos um site.")
    else:
        sites = [u.strip() for u in urls.split("\n") if u.strip()]
        conteudos = []

        for site in sites:
            with st.spinner(f"Extraindo conteúdo de {site}..."):
                conteudos.append(
                    f"SITE: {site}\n{extrair_conteudo_site(site)}"
                )

        prompt = f"""
Você é um estrategista sênior de marketing e posicionamento competitivo.

Analise os conteúdos abaixo e gere um relatório com:
1. Posicionamento de cada empresa
2. Mensagens-chave
3. Diferenciais competitivos
4. Fragilidades de comunicação
5. Oportunidades estratégicas
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
