import subprocess
import sys

# ---------------------------------------------------
# GARANTE DEPENDÊNCIA (evita erro no Streamlit Cloud)
# ---------------------------------------------------
def ensure_package(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

ensure_package("google-generativeai")

# ---------------------------------------------------
# IMPORTS
# ---------------------------------------------------
import streamlit as st
import requests
import trafilatura
import re
import google.generativeai as genai

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(
    page_title="Marketylics - Análise de Concorrentes",
    layout="wide"
)

# ---------------------------------------------------
# GEMINI CONFIG
# ---------------------------------------------------
if "GEMINI_API_KEY" not in st.secrets:
    st.error("GEMINI_API_KEY não configurada nos Secrets")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

MODEL_NAME = "models/gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# ---------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------
def format_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def extract_site_content(url: str) -> str:
    try:
        url = format_url(url)

        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "Conteúdo não acessível."

        text = trafilatura.extract(
            downloaded,
            include_links=False,
            include_images=False,
            include_tables=False
        )

        if not text or len(text) < 200:
            return "Site com pouco conteúdo ou carregamento via JavaScript."

        text = re.sub(
            r"(Política de Privacidade.*|Cookies.*|©.*)",
            "",
            text,
            flags=re.I | re.S
        )

        return text.strip()

    except Exception as e:
        return f"Erro ao acessar site: {e}"


def generate_report(all_data: str) -> str:
    prompt = f"""
Você é um estrategista sênior de marketing e análise competitiva.

Com base nos sites abaixo, gere um relatório detalhado com:

1. Posicionamento de cada empresa
2. Mensagem principal
3. Diferenciais competitivos
4. Tom de comunicação
5. Fraquezas estratégicas
6. Oportunidades de mercado
7. Recomendações práticas

SITES ANALISADOS:
{all_data}
"""

    response = model.generate_content(prompt)
    return response.text

# ---------------------------------------------------
# INTERFACE
# ---------------------------------------------------
st.title("🔎 Análise Competitiva com IA")

st.markdown(
    "Cole os sites da sua empresa e dos concorrentes para análise estratégica."
)

urls_input = st.text_area(
    "Sites (um por linha):",
    placeholder="https://suaempresa.com\nhttps://concorrente1.com\nhttps://concorrente2.com"
)

if st.button("Gerar Relatório"):
    if not urls_input.strip():
        st.warning("Insira pelo menos um site.")
    else:
        urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

        collected_data = []

        for url in urls:
            with st.spinner(f"Analisando {url}..."):
                content = extract_site_content(url)
                collected_data.append(f"SITE: {url}\n\n{content}")

        final_input = "\n\n---------------------\n\n".join(collected_data)

        try:
            report = generate_report(final_input)

            st.success("Relatório gerado com sucesso!")
            st.subheader("📊 Relatório de Competitividade")
            st.markdown(report)

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
