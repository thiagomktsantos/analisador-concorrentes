import streamlit as st
import requests
import trafilatura
import re
import google.generativeai as genai

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(
    page_title="Marketylics — Análise de Concorrentes",
    layout="wide"
)

# ---------------------------------------------------
# CONFIGURAÇÃO GEMINI
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("GEMINI_API_KEY não configurada no Streamlit Secrets.")
    st.stop()


@st.cache_resource
def get_gemini_model():
    """
    Descobre automaticamente um modelo Gemini
    compatível com generateContent
    """
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except Exception:
        return None
    return None


gemini_model = get_gemini_model()

if not gemini_model:
    st.error("Nenhum modelo Gemini disponível para generateContent.")
    st.stop()

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------
def formatar_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def limpar_texto(texto: str) -> str:
    texto = re.sub(
        r"(Política de Privacidade.*|Cookies.*|©.*|Todos os direitos reservados.*)",
        "",
        texto,
        flags=re.I | re.S
    )
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extrair_conteudo_site(url: str) -> str:
    try:
        url = formatar_url(url)

        resp = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketylicsBot/1.0)"
            }
        )

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
            return "Site com conteúdo institucional limitado ou carregado via JavaScript."

        return limpar_texto(texto)

    except Exception as e:
        return f"Erro ao acessar site: {e}"


# ---------------------------------------------------
# INTERFACE
# ---------------------------------------------------
st.title("Análise Competitiva com IA")

st.markdown(
    "Insira o site da **sua empresa** e dos **concorrentes** "
    "para gerar um relatório estratégico comparativo."
)

urls = st.text_area(
    "Sites (um por linha):",
    placeholder="https://suaempresa.com\nhttps://concorrente1.com\nhttps://concorrente2.com"
)

if st.button("Gerar Relatório"):
    if not urls.strip():
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

Analise os conteúdos abaixo e gere um relatório contendo:

1. Posicionamento de cada empresa
2. Mensagens-chave predominantes
3. Diferenciais competitivos
4. Fragilidades de comunicação
5. Oportunidades estratégicas
6. Recomendações práticas e acionáveis

Se algum site tiver pouco conteúdo ou depender de JavaScript,
considere isso como um insight estratégico.

CONTEÚDOS:
{"\n\n---\n\n".join(conteudos)}
"""

        try:
            resposta = gemini_model.generate_content(prompt)
            st.subheader("Relatório de Competitividade")
            st.write(resposta.text)

        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                st.error(
                    "Limite da API Gemini excedido.\n\n"
                    "➡ Verifique billing e quota do projeto Google Cloud."
                )
            else:
                st.error(f"Erro ao gerar relatório: {e}")
