import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import re
import unicodedata
import trafilatura
import requests
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
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ---------------------------------------------------
# CONFIGURAÇÃO GEMINI
# ---------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-pro")
else:
    gemini_model = None

# ---------------------------------------------------
# LISTA ESTADOS E CIDADES
# ---------------------------------------------------
ESTADOS_CIDADES = {
    "Acre": ["Rio Branco", "Cruzeiro do Sul"],
    "Alagoas": ["Maceió", "Arapiraca"],
    "Amapá": ["Macapá", "Santana"],
    "Amazonas": ["Manaus", "Parintins"],
    "Bahia": ["Salvador", "Feira de Santana"],
    "Ceará": ["Fortaleza", "Juazeiro do Norte", "Sobral"],
    "Distrito Federal": ["Brasília"],
    "Espírito Santo": ["Vitória", "Vila Velha"],
    "Goiás": ["Goiânia", "Anápolis"],
    "Maranhão": ["São Luís", "Imperatriz"],
    "Mato Grosso": ["Cuiabá", "Rondonópolis"],
    "Mato Grosso do Sul": ["Campo Grande", "Dourados"],
    "Minas Gerais": ["Belo Horizonte", "Uberlândia"],
    "Pará": ["Belém", "Santarém"],
    "Paraíba": ["João Pessoa", "Campina Grande"],
    "Paraná": ["Curitiba", "Londrina"],
    "Pernambuco": ["Recife", "Caruaru"],
    "Piauí": ["Teresina", "Parnaíba"],
    "Rio de Janeiro": ["Rio de Janeiro", "Niterói"],
    "Rio Grande do Norte": ["Natal", "Mossoró"],
    "Rio Grande do Sul": ["Porto Alegre", "Caxias do Sul"],
    "Rondônia": ["Porto Velho", "Ji-Paraná"],
    "Roraima": ["Boa Vista"],
    "Santa Catarina": ["Florianópolis", "Joinville"],
    "São Paulo": ["São Paulo", "Campinas", "Santos"],
    "Sergipe": ["Aracaju"],
    "Tocantins": ["Palmas"]
}

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------
def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def limpar_site(url):
    if not url:
        return ""
    url = url.strip().lower()
    url = re.sub(r"^https?:\/\/", "", url, flags=re.IGNORECASE)
    url = re.sub(r"^www\.", "", url, flags=re.IGNORECASE)
    url = remover_acentos(url)
    url = re.sub(r"[^a-z0-9\.\-\/]", "", url)
    return url

def gerar_avatar(nome):
    nome = nome.strip().upper()
    if not nome:
        return "?"
    partes = nome.split()
    if len(partes) == 1:
        return partes[0][0]
    return partes[0][0] + partes[1][0]

def obter_instagram_handle(valor):
    if not valor:
        return ""
    valor = valor.strip()
    valor = re.sub(r"^https?:\/\/(www\.)?instagram\.com\/", "", valor, flags=re.IGNORECASE)
    valor = valor.strip("/")
    valor = valor.lstrip("@")
    if valor:
        valor = "@" + valor
    return valor

def obter_facebook_handle(valor):
    if not valor:
        return ""
    valor = valor.strip()
    valor = re.sub(r"^https?:\/\/(www\.)?facebook\.com\/", "", valor, flags=re.IGNORECASE)
    valor = valor.strip("/")
    return valor

def empresa_tem_dados(emp):
    return bool(emp.get("nome", "").strip())

def formatar_url(url):
    """Garante que a URL tenha schema HTTP para Trafilatura."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ---------------------------------------------------
# NOVA FUNÇÃO DE EXTRAÇÃO DE CONTEÚDO
# ---------------------------------------------------
def extrair_conteudo_site(url: str) -> str:
    """Extrai texto principal do site com fallback inteligente."""
    url_fmt = formatar_url(url)
    if not url_fmt:
        return ""

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }

        # 1) Tenta baixar com Trafilatura
        downloaded = trafilatura.fetch_url(url_fmt)

        # 2) Fallback com Requests se Trafilatura não trouxe HTML
        if not downloaded:
            resp = requests.get(url_fmt, headers=headers, timeout=15)
            if resp.status_code == 200:
                downloaded = resp.text

        if not downloaded:
            return ""

        # 3) Extração otimizada
        texto = trafilatura.extract(
            downloaded,
            include_tables=False,
            include_links=False,
            include_images=False,
            favor_precision=True,
            no_fallback=False,
            deduplicate=True
        )

        if not texto:
            return ""

        # 4) Limpeza semântica (remove rodapés, políticas etc.)
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
# CONTINUAÇÃO DO APP (SEM ALTERAÇÕES)
# ---------------------------------------------------

# — daqui em diante todo o restante do seu `app.py`
# permanece exatamente como está no GitHub.

# As funcionalidades de autenticação, navegação,
# dashboard, relatórios, integração com Gemini,
# comentários, páginas e UI não foram alteradas.

# (O trecho que foi substituído foi apenas a função `extrair_conteudo_site`)
