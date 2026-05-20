import instaloader
import plotly.graph_objects as go
import plotly.express as px
from playwright.sync_api import sync_playwright
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
    page_title="Marketylics · Competitive Intelligence",
    page_icon="https://raw.githubusercontent.com/thiagomktsantos/marketylics/231a39c102b672fbb803b0ecf335febdd119d3b1/images/favicon.jpg",
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

SUBNICHOS = {
    "Alimentação": ["Restaurante", "Delivery", "Confeitaria", "Padaria", "Lanchonete", "Food Truck", "Catering", "Franquia de Alimentação"],
    "Marketing": ["Agência Digital", "Marketing de Conteúdo", "SEO", "Tráfego Pago", "Social Media", "Branding", "Email Marketing", "Inbound Marketing"],
    "Tecnologia": ["Software House", "SaaS", "Consultoria TI", "Segurança", "Dados & BI", "Mobile", "Cloud", "Inteligência Artificial"],
    "Varejo": ["E-commerce", "Moda", "Eletrônicos", "Alimentos", "Farmácia", "Pet Shop", "Decoração", "Esportes"],
    "Saúde": ["Clínica Médica", "Odontologia", "Psicologia", "Nutrição", "Fisioterapia", "Academia", "Farmácia", "Estética"],
    "Educação": ["Escola", "Curso Online", "Coaching", "Consultoria", "Idiomas", "Pré-vestibular", "Creche", "Faculdade"],
    "Indústria": ["Manufatura", "Construção", "Agronegócio", "Química", "Têxtil", "Metalurgia", "Energia", "Logística"],
}

# ---------------------------------------------------
# PALETA DE CORES GLOBAL PARA AVATARES
# ---------------------------------------------------

AVATAR_COLORS = ["#27ae60", "#3a9fd6", "#2ecc71", "#5bc4f5", "#1a7abf", "#1a2e4a"]

def get_avatar_color(index: int) -> str:
    return AVATAR_COLORS[index % len(AVATAR_COLORS)]

def get_minha_empresa_color() -> str:
    return AVATAR_COLORS[0]

def get_concorrente_color(concorrente_index: int) -> str:
    return AVATAR_COLORS[(concorrente_index + 1) % len(AVATAR_COLORS)]

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
    url = url.rstrip("/")
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
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ---------------------------------------------------
# SUPABASE — USUÁRIOS / AUTH
# ---------------------------------------------------

def login_supabase(email: str, senha: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return res.user, None
    except Exception as e:
        return None, str(e)

def cadastro_supabase(email: str, senha: str):
    try:
        res = supabase.auth.sign_up({"email": email, "password": senha})
        return res.user, None
    except Exception as e:
        return None, str(e)

def logout_supabase():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

# ---------------------------------------------------
# SUPABASE — DADOS DO USUÁRIO
# ---------------------------------------------------

def carregar_dados_usuario(user_id: str) -> dict:
    try:
        res = supabase.table("ci_dados").select("*").eq("user_id", user_id).execute()
        if res.data:
            row = res.data[0]
            return {
                "minha_empresa": row.get("minha_empresa", {}),
                "concorrentes": row.get("concorrentes", []),
                "metricas_redes": row.get("metricas_redes", {}),
            }
    except Exception:
        pass
    return {
        "minha_empresa": {
            "nome": "", "setor": "Marketing", "tipo": "",
            "estado": "", "cidade": "",
            "instagram": "@", "fb_page": "", "site": "",
            "servicos": [], "ads_id": "", "ads_page_pic": ""
        },
        "concorrentes": [],
        "metricas_redes": {},
    }

def salvar_dados_usuario(user_id: str):
    try:
        payload = {
            "user_id": user_id,
            "minha_empresa": st.session_state.dados["minha_empresa"],
            "concorrentes": st.session_state.dados["concorrentes"],
            "metricas_redes": st.session_state.metricas_redes,
        }
        supabase.table("ci_dados").upsert(payload, on_conflict="user_id").execute()
    except Exception as e:
        st.toast(f"⚠️ Erro ao salvar: {e}", icon="⚠️")

# ---------------------------------------------------
# ESTADO DA SESSÃO
# ---------------------------------------------------

if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_tab" not in st.session_state:
    st.session_state.auth_tab = "login"
if "dados" not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "", "setor": "Marketing", "tipo": "",
            "estado": "", "cidade": "",
            "instagram": "@", "fb_page": "", "site": "",
            "servicos": [], "ads_id": "", "ads_page_pic": ""
        },
        "concorrentes": []
    }
if "metricas_redes" not in st.session_state:
    st.session_state.metricas_redes = {}
if "pagina" not in st.session_state:
    st.session_state.pagina = "home"
if "mostrar_form_concorrente" not in st.session_state:
    st.session_state.mostrar_form_concorrente = False
if "editando_concorrente" not in st.session_state:
    st.session_state.editando_concorrente = None
if "editar_empresa" not in st.session_state:
    st.session_state.editar_empresa = False
if "relatorio_sites" not in st.session_state:
    st.session_state.relatorio_sites = {}
if "relatorio_gemini" not in st.session_state:
    st.session_state.relatorio_gemini = ""
if "analises_salvas" not in st.session_state:
    st.session_state.analises_salvas = []

empresa = st.session_state.dados["minha_empresa"]
campos_padrao = {
    "estado": "", "cidade": "", "instagram": "@",
    "fb_page": "", "site": "", "servicos": [], "ads_id": "", "ads_page_pic": ""
}
for campo, valor in campos_padrao.items():
    if campo not in empresa:
        empresa[campo] = valor

# ---------------------------------------------------
# CONTROLE NAVEGAÇÃO
# ---------------------------------------------------

def trocar_pagina(destino):
    st.session_state.pagina = destino
    st.session_state.mostrar_form_concorrente = False
    st.session_state.editando_concorrente = None
    st.session_state.editar_empresa = False

# ---------------------------------------------------
# FUNÇÃO IA — BATTLE CARD
# ---------------------------------------------------

def consultar_ia(prompt):
    if gemini_model is None:
        return "Erro: Chave API Gemini não configurada."
    try:
        emp = st.session_state.dados["minha_empresa"]
        contexto = f"""
Empresa: {emp['nome']}
Setor: {emp['setor']}
Instagram: {emp['instagram']}
"""
        resposta = gemini_model.generate_content(contexto + "\n" + prompt)
        return resposta.text
    except Exception as e:
        return f"Erro: {str(e)}"

# ---------------------------------------------------
# TRAFILATURA — EXTRAÇÃO DE CONTEÚDO
# ---------------------------------------------------

def extrair_conteudo_site(url: str) -> str:
    url_fmt = formatar_url(url)
    if not url_fmt:
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        resp = requests.get(url_fmt, headers=headers, timeout=15, allow_redirects=True)
        resp.encoding = resp.apparent_encoding
        html = resp.text

        texto = trafilatura.extract(
            html,
            include_tables=True,
            include_links=False,
            include_images=False,
            no_fallback=False,
            favor_recall=True,
        )
        if texto and len(texto) > 100:
            return texto

        import re as _re
        texto_bruto = _re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=_re.DOTALL)
        texto_bruto = _re.sub(r"<style[^>]*>.*?</style>", " ", texto_bruto, flags=_re.DOTALL)
        texto_bruto = _re.sub(r"<[^>]+>", " ", texto_bruto)
        texto_bruto = _re.sub(r"\s+", " ", texto_bruto).strip()
        return texto_bruto[:5000] if texto_bruto else ""
    except Exception as e:
        return f"[Erro ao acessar {url}: {e}]"

# ---------------------------------------------------
# GEMINI — RELATÓRIO DE POSICIONAMENTO
# ---------------------------------------------------

def gerar_relatorio_posicionamento(empresa_principal: dict, concorrentes_data: list) -> str:
    if gemini_model is None:
        return "Erro: Chave API Gemini não configurada."

    secoes = []
    if empresa_principal.get("conteudo"):
        secoes.append(f"""
## MINHA EMPRESA — {empresa_principal['nome']} ({empresa_principal['url']})
{empresa_principal['conteudo'][:3000]}
""")

    for c in concorrentes_data:
        if c.get("conteudo"):
            secoes.append(f"""
## CONCORRENTE — {c['nome']} ({c['url']})
{c['conteudo'][:3000]}
""")

    if not secoes:
        return "Nenhum conteúdo extraído dos sites para análise."

    prompt = f"""
Você é um especialista em marketing digital e inteligência competitiva.
Analise o conteúdo extraído dos sites abaixo e gere um **Relatório de Posicionamento Competitivo** completo em português.

{''.join(secoes)}

---

O relatório deve conter:

### 1. 📌 Proposta de Valor
Para cada empresa, identifique a proposta de valor central comunicada no site.

### 2. 🎯 Posicionamento de Mercado
Como cada empresa se posiciona? (premium, popular, nicho, generalista etc.)

### 3. 🔑 Palavras-chave e Mensagens Principais
Quais termos, promessas e mensagens cada empresa repete com mais frequência?

### 4. 🛠️ Serviços e Diferenciais
Liste os principais serviços/produtos destacados por cada empresa.

### 5. ⚔️ Análise Competitiva
Compare minha empresa com os concorrentes. Onde estamos mais fortes? Onde estamos vulneráveis?

### 6. 💡 Recomendações Estratégicas
Com base na análise, sugira 3 a 5 ações concretas para melhorar o posicionamento da minha empresa.

Seja direto, objetivo e use dados do conteúdo real dos sites.
"""

    try:
        resposta = gemini_model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Erro ao gerar relatório: {e}"

# ---------------------------------------------------
# CSS GLOBAL
# ---------------------------------------------------

st.markdown("""
<style>
@font-face {
    font-family: 'Animo';
    src: url('https://raw.githubusercontent.com/thiagomktsantos/marketylics/63946b2d891db6b45cc75a45550b7aa5fe67244a/utils/Animo-font.otf') format('opentype');
    font-weight: normal;
    font-style: normal;
}

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

[data-testid="stSidebar"] {
    background-color: #0f1117 !important;
    border-right: 1px solid #1e2530 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

section.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1100px !important;
    background: #f0f4f8 !important;
}

[data-testid="stAppViewContainer"] { background: #f0f4f8 !important; }
section.main { background: #f0f4f8 !important; }

.page-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;
}
.page-title { font-size: 28px; font-weight: 600; color: #111827; letter-spacing: -0.5px; margin: 0; font-family: 'Animo', 'DM Sans', sans-serif; }
.page-subtitle { font-size: 16px; color: #6b7280; margin-top: 3px; }

section.main div.stButton > button {
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    border: 1px solid #d1d5db !important;
    background: #ffffff !important;
    color: #374151 !important;
    box-shadow: none !important;
    padding: 8px 16px !important;
    min-height: 40px !important;
    transition: all 0.12s ease !important;
    font-family: 'DM Sans', sans-serif !important;
}
section.main div.stButton > button:hover {
    background: #f9fafb !important;
    border-color: #9ca3af !important;
    color: #111827 !important;
}

section.main div.stButton > button[kind="primary"],
[data-testid="stMainBlockContainer"] button[kind="primary"],
button[data-testid="baseButton-primary"],
div.stButton > button[kind="primary"] {
    background: #0780c0 !important;
    color: #ffffff !important;
    border: none !important;
    opacity: 1 !important;
}
section.main div.stButton > button[kind="primary"]:hover,
[data-testid="stMainBlockContainer"] button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover,
div.stButton > button[kind="primary"]:hover {
    background: #065f9e !important;
    color: #ffffff !important;
    opacity: 1 !important;
}

section.main div.stFormSubmitButton > button {
    background: #111827 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    min-height: 40px !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.12s ease !important;
}
section.main div.stFormSubmitButton > button:hover {
    background: #1f2937 !important;
}

.form-section-header {
    font-size: 13px; font-weight: 600; color: #6b7280;
    text-transform: uppercase; letter-spacing: 0.8px;
    padding: 20px 0 12px 0; border-bottom: 1px solid #f3f4f6;
    margin-bottom: 16px; font-family: 'DM Sans', sans-serif;
}

section.main div[data-testid="stTextInput"] input,
section.main div[data-testid="stSelectbox"] select,
section.main div[data-baseweb="select"] {
    font-size: 15px !important; border-radius: 7px !important;
    border: 1px solid #e5e7eb !important;
    font-family: 'DM Sans', sans-serif !important; color: #111827 !important;
}
section.main label {
    font-size: 14px !important; font-weight: 500 !important;
    color: #374151 !important; font-family: 'DM Sans', sans-serif !important;
    margin-bottom: 4px !important;
}
section.main h1, section.main h2, section.main h3 {
    font-family: 'Animo', 'DM Sans', sans-serif !important;
}
section.main h1 { font-size: 28px !important; font-weight: 600 !important; color: #111827 !important; }
section.main h2 { font-size: 20px !important; font-weight: 600 !important; color: #111827 !important; margin-top: 28px !important; }
section.main h3 { font-size: 16px !important; font-weight: 600 !important; color: #374151 !important; }
section.main hr { border: none !important; border-top: 1px solid #f3f4f6 !important; margin: 20px 0 !important; }

div[data-testid="stInfo"] {
    background: #f0f9ff !important; border: 1px solid #bae6fd !important;
    border-radius: 8px !important; font-size: 15px !important;
    color: #0c4a6e !important; padding: 14px 18px !important;
}
div[data-testid="stWarning"] {
    background: #fffbeb !important; border: 1px solid #fcd34d !important;
    border-radius: 8px !important; font-size: 15px !important; padding: 14px 18px !important;
}
div[data-testid="stSuccess"] {
    background: #f0fdf4 !important; border: 1px solid #86efac !important;
    border-radius: 8px !important; font-size: 15px !important; padding: 14px 18px !important;
}
div[data-testid="stError"] {
    background: #fef2f2 !important; border: 1px solid #fca5a5 !important;
    border-radius: 8px !important; font-size: 15px !important; padding: 14px 18px !important;
}

details summary { font-size: 16px !important; font-weight: 500 !important; padding: 14px 0 !important; }

.popup-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.5);
    z-index: 999999; backdrop-filter: blur(2px);
}
.popup-box {
    position: fixed; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    background: #ffffff; width: 480px; border-radius: 14px;
    padding: 32px; z-index: 9999999; border: 1px solid #e5e7eb;
    color: #111827; box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.popup-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; color: #111827; }
.popup-text { color: #6b7280; margin-bottom: 24px; font-size: 15px; line-height: 1.6; }

div[data-baseweb="select"] > div {
    border-radius: 7px !important; min-height: 42px !important;
    font-size: 15px !important; font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stDataFrame"] {
    border-radius: 10px !important; overflow: hidden !important; border: 1px solid #e5e7eb !important;
}
section.main div[data-testid="stTextArea"] textarea {
    font-size: 15px !important; border-radius: 7px !important;
    border: 1px solid #e5e7eb !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #111827 !important; resize: vertical !important;
}

div[data-testid="stTabs"] > div:first-child {
    justify-content: center !important; border-bottom: 2px solid #e5e7eb !important; gap: 0 !important;
}
div[data-testid="stTabs"] button[role="tab"] {
    font-size: 15px !important; font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important; padding: 10px 32px !important;
    color: #9ca3af !important; border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #111827 !important; border-bottom: 2px solid #111827 !important;
}
div[data-testid="stTabs"] button[role="tab"]:hover { color: #374151 !important; background: transparent !important; }

.sb-logo { padding:22px 18px 16px; border-bottom:1px solid #1e2530; margin-bottom:8px; }
.sb-logo-sub { font-size:8.4px; color:#3a9fd6; font-weight:600; letter-spacing:2px; text-transform:uppercase; text-align:center; font-family:'DM Sans',sans-serif; }

[data-testid="stSidebar"] div.stButton > button {
    position: fixed !important;
    top: -9999px !important;
    left: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
}
[data-testid="stSidebar"] .stElementContainer:has(div.stButton) {
    margin: 0 !important;
    padding: 0 !important;
    height: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    line-height: 0 !important;
    display: none !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div > div,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] > div,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] > div > div,
[data-testid="stVerticalBlockBorderWrapper"] .stElementContainer,
[data-testid="stVerticalBlockBorderWrapper"] .stElementContainer > div {
    background-color: #ffffff !important;
}
[data-testid="stVerticalBlockBorderWrapper"] iframe,
[data-testid="stVerticalBlockBorderWrapper"] canvas,
[data-testid="stVerticalBlockBorderWrapper"] img {
    background: transparent !important;
}

[data-testid="stVerticalBlockBorderWrapper"] *:not(iframe):not(canvas):not(img):not(svg):not(path):not(circle):not(rect) {
    background-color: #ffffff !important;
}

button[data-testid="baseButton-secondary"][kind="secondary"]:has(~ *) {
    display: none !important;
}

/* ── OCULTAR campo ads_id no formulário de concorrentes ── */
.st-key-ads_id_hidden {
    display: none !important;
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CARD HELPERS
# ---------------------------------------------------

CARD_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html, body {
    background: transparent;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    -webkit-font-smoothing: antialiased;
    overflow: visible;
}
body { padding-bottom: 8px; }
"""
CARD_FONT_IMPORT = """<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">"""

# ---------------------------------------------------
# LOGIN / CADASTRO (Supabase Auth)
# ---------------------------------------------------

import base64
from pathlib import Path

def get_logo_base64():
    logo_path = Path("images/logo-marketylics.jpg")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def get_logo_white_base64():
    logo_path = Path("images/logo-marketylics-white.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

if not st.session_state.logado:
    logo_b64 = get_logo_base64()
    logo_src = f"data:image/jpeg;base64,{logo_b64}" if logo_b64 else ""

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

    header, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

    [data-testid="stAppViewContainer"] { background: #f0f2f5 !important; }

    section.main .block-container {
        max-width: 440px !important;
        padding: 48px 24px !important;
        margin: 0 auto !important;
        background: transparent !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        background: #ffffff !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 20px rgba(0,0,0,0.08) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-testid="stVerticalBlockBorderWrapper"] > div > div,
    [data-testid="stVerticalBlock"],
    div[data-testid="stForm"],
    div[data-testid="stForm"] > div,
    div[data-baseweb="tab-panel"] {
        background: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
    }
    [data-testid="stVerticalBlock"] {
        width: 100% !important;
        max-width: 440px !important;
        margin: 0 auto !important;
    }
    div[class*="st-emotion-cache"] {
        border-color: transparent !important;
    }

    div[data-testid="stTextInput"] input {
        border: 1.5px solid #e5e7eb !important;
        border-radius: 8px !important;
        background: #fafafa !important;
        font-size: 15px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3a9fd6 !important;
        background: #fff !important;
        box-shadow: none !important;
    }

    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #3a9fd6 0%, #2ecc71 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        padding: 12px !important;
        width: 100% !important;
    }
    div.stFormSubmitButton > button:hover { opacity: 0.9 !important; }

    div[data-testid="stTabs"] > div:first-child {
        justify-content: center !important;
        border-bottom: 2px solid #e5e7eb !important;
        gap: 0 !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 8px 0 !important;
        color: #9ca3af !important;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -2px !important;
        background: transparent !important;
        box-shadow: none !important;
        flex: 1 !important;
        text-align: center !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #3a9fd6 !important;
        border-bottom: 2px solid #3a9fd6 !important;
        background: transparent !important;
    }
    div[data-testid="stTabs"] button[role="tab"]:focus,
    div[data-testid="stTabs"] button[role="tab"]:focus-visible {
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #3a9fd6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:24px">
            {'<img src="' + logo_src + '" style="width:200px;" />' if logo_src else '<div style="font-size:24px;font-weight:700;color:#1a2234">Marketylics</div>'}
            <div style="font-size:10.9px;color:#3a9fd6;font-weight:600;letter-spacing:2px;text-transform:uppercase">Competitive Intelligence</div>
        </div>
        <hr style="border:none;border-top:1px solid #f3f4f6;margin:0 0 10px 0" />
        """, unsafe_allow_html=True)

        aba = st.tabs(["Já tenho conta", "Criar conta"])

        with aba[0]:
            with st.form("form_login"):
                email_login = st.text_input("E-mail", placeholder="seu@email.com")
                senha_login = st.text_input("Senha", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Entrar na plataforma →", use_container_width=True)

            if submit_login:
                if email_login and senha_login:
                    with st.spinner("Autenticando..."):
                        user, err = login_supabase(email_login, senha_login)
                    if user:
                        st.session_state.logado = True
                        st.session_state.user = user
                        dados_db = carregar_dados_usuario(user.id)
                        minha_emp = dados_db["minha_empresa"] or {
                            "nome": "", "setor": "Marketing", "tipo": "",
                            "estado": "", "cidade": "",
                            "instagram": "@", "fb_page": "", "site": "",
                            "servicos": [], "ads_id": "", "ads_page_pic": ""
                        }
                        if "ads_id" not in minha_emp:
                            minha_emp["ads_id"] = ""
                        if "ads_page_pic" not in minha_emp:
                            minha_emp["ads_page_pic"] = ""
                        st.session_state.dados = {
                            "minha_empresa": minha_emp,
                            "concorrentes": dados_db.get("concorrentes", []),
                        }
                        st.session_state.metricas_redes = dados_db.get("metricas_redes", {})
                        st.rerun()
                    else:
                        st.error(f"Erro ao entrar: {err}")
                else:
                    st.warning("Preencha e-mail e senha.")

        with aba[1]:
            with st.form("form_cadastro"):
                email_cad  = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
                senha_cad  = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="cad_senha")
                senha_cad2 = st.text_input("Confirmar senha", type="password", placeholder="Repita a senha", key="cad_senha2")
                submit_cad = st.form_submit_button("Criar conta", use_container_width=True)

            if submit_cad:
                if not email_cad or not senha_cad:
                    st.warning("Preencha todos os campos.")
                elif senha_cad != senha_cad2:
                    st.error("As senhas não coincidem.")
                elif len(senha_cad) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    with st.spinner("Criando conta..."):
                        user, err = cadastro_supabase(email_cad, senha_cad)
                    if user:
                        st.success("Conta criada! Verifique seu e-mail para confirmar, depois faça login.")
                    else:
                        st.error(f"Erro: {err}")

        st.markdown("""
        <div style="text-align:center;font-size:11px;color:#696969;margin-bottom:16px">
            🔒 Conexão segura com criptografia SSL &nbsp;·&nbsp;
            <a href="#" style="color:#3a9fd6;text-decoration:none">Termos de Uso</a> &nbsp;·&nbsp;
            <a href="#" style="color:#3a9fd6;text-decoration:none">Privacidade</a>
        </div>
        """, unsafe_allow_html=True)

    st.stop()

# ---------------------------------------------------
# SIDEBAR (apenas quando logado)
# ---------------------------------------------------

with st.sidebar:

    logo_white_b64 = get_logo_white_base64()
    logo_white_src = f"data:image/png;base64,{logo_white_b64}" if logo_white_b64 else ""

    paginas = ["home", "cad", "geral", "redes", "sites", "ads", "insights", "sair"]
    for p in paginas:
        if st.button(p, key=f"_hidden_{p}"):
            if p == "sair":
                logout_supabase()
                for k in ["logado","user","dados","metricas_redes","pagina",
                          "mostrar_form_concorrente","editando_concorrente",
                          "editar_empresa","relatorio_sites","relatorio_gemini"]:
                    if k in st.session_state:
                        del st.session_state[k]
            else:
                trocar_pagina(p)
            st.rerun()

    pagina_atual = st.session_state.pagina
    user_email = st.session_state.user.email if st.session_state.user else ""

    menu_html = f"""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
 
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    background: #0d1117;
    font-family: 'DM Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}}
.logo-wrap {{
    text-align: center;
    padding: 28px 20px 20px;
}}
.logo-wrap img {{ width: 180px; display: block; margin: 0 auto 6px; }}
.logo-sub {{
    font-size: 8.3px; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; color: #3a9fd6;
    font-family: 'DM Sans', sans-serif;
}}
.sec {{
    display: flex; align-items: center; gap: 10px;
    padding: 15px 14px 8px;
}}
.sec-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: #3a9fd6; flex-shrink: 0;
}}
.sec-line {{ flex: 1; height: 1px; background: #1e2a3a; }}
.sec-label {{
    font-size: 10px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #3a9fd6;
    white-space: nowrap;
}}
.nav-list {{ padding: 4px 10px; flex: 1; }}
.nav-item {{
    display: flex; align-items: center; gap: 14px;
    padding: 6px 16px;
    border-radius: 10px;
    margin-bottom: 3px;
    cursor: pointer;
    text-decoration: none;
    background: #131c2b;
    border: 1px solid #1e2a3a;
    transition: background 0.15s, border-color 0.15s;
    position: relative;
}}
.nav-item:hover {{
    background: #1a2535;
    border-color: #1e2a3a;
}}
.nav-item.active {{
    background: #0e2a47;
    border-color: #1e5a8a;
    border-left: 4px solid #00a7e3;
}}
.nav-icon {{
    width: 26px; text-align: center; flex-shrink: 0;
    font-size: 18px; color: #8a9bb0;
}}
.nav-item.active .nav-icon {{ color: #e2eaf5; }}
.nav-label {{
    font-size: 14px; font-weight: 600;
    color: #8a9bb0; flex: 1;
    letter-spacing: 0.1px;
}}
.nav-item.active .nav-label {{ color: #e2eaf5; }}
.nav-arrow {{
    font-size: 13px; color: #3a4f6a;
    flex-shrink: 0;
}}
.nav-item.active .nav-arrow {{ color: #3a9fd6; }}
.footer {{
    border-top: 1px solid #1e2a3a;
    padding: 16px 14px 12px;
    margin-top: auto;
}}
.footer-email {{
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 12px;
}}
.footer-email i {{ font-size: 22px; color: #3a9fd6; }}
.footer-email span {{
    font-size: 13px; color: #5a7090;
    word-break: break-all;
    font-family: 'DM Sans', sans-serif;
}}
.btn-sair {{
    display: flex; align-items: center; justify-content: center;
    gap: 10px; width: 100%; padding: 7px 0;
    border: 1px solid #1e2a3a; border-radius: 10px;
    background: transparent; cursor: pointer;
    font-size: 15px; font-weight: 600; color: #5a7090;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.15s;
}}
.btn-sair:hover {{
    background: #1a2535; color: #e2eaf5;
    border-color: #3a9fd6;
}}
.btn-sair i {{ font-size: 16px; }}
</style>
 
<body>
<div class="logo-wrap">
    {'<img src="' + logo_white_src + '" />' if logo_white_src else '<div style="font-size:20px;font-weight:700;color:#fff">Marketylics</div>'}
    <div class="logo-sub">Competitive Intelligence</div>
</div>
<div class="sec">
    <span class="sec-dot"></span>
    <span class="sec-label">Dados Principais</span>
    <span class="sec-line"></span>
</div>
<div class="nav-list">
    <a class="nav-item {'active' if pagina_atual == 'home' else ''}" onclick="nav('home')">
        <span class="nav-icon"><i class="fa-solid fa-building-columns"></i></span>
        <span class="nav-label">Minha Empresa</span>
    </a>
    <a class="nav-item {'active' if pagina_atual == 'cad' else ''}" onclick="nav('cad')">
        <span class="nav-icon"><i class="fa-solid fa-crosshairs"></i></span>
        <span class="nav-label">Concorrentes</span>
    </a>
</div>
<div class="sec">
    <span class="sec-dot"></span>
    <span class="sec-label">Análise Competitiva</span>
    <span class="sec-line"></span>
</div>
<div class="nav-list">
    <a class="nav-item {'active' if pagina_atual == 'geral' else ''}" onclick="nav('geral')">
        <span class="nav-icon"><i class="fa-solid fa-chart-bar"></i></span>
        <span class="nav-label">Visão Geral</span>
        <span class="nav-arrow"><i class="fa-solid fa-chevron-right"></i></span>
    </a>
    <a class="nav-item {'active' if pagina_atual == 'redes' else ''}" onclick="nav('redes')">
        <span class="nav-icon"><i class="fa-brands fa-instagram"></i></span>
        <span class="nav-label">Redes Sociais</span>
        <span class="nav-arrow"><i class="fa-solid fa-chevron-right"></i></span>
    </a>
    <a class="nav-item {'active' if pagina_atual == 'sites' else ''}" onclick="nav('sites')">
        <span class="nav-icon"><i class="fa-solid fa-magnifying-glass-chart"></i></span>
        <span class="nav-label">Confronto de Sites</span>
        <span class="nav-arrow"><i class="fa-solid fa-chevron-right"></i></span>
    </a>
    <a class="nav-item {'active' if pagina_atual == 'ads' else ''}" onclick="nav('ads')">
        <span class="nav-icon"><i class="fa-solid fa-rectangle-ad"></i></span>
        <span class="nav-label">Biblioteca de Ads</span>
        <span class="nav-arrow"><i class="fa-solid fa-chevron-right"></i></span>
    </a>
    <a class="nav-item {'active' if pagina_atual == 'insights' else ''}" onclick="nav('insights')">
        <span class="nav-icon"><i class="fa-solid fa-lightbulb"></i></span>
        <span class="nav-label">Insights</span>
        <span class="nav-arrow"><i class="fa-solid fa-chevron-right"></i></span>
    </a>
</div>
<div class="footer">
    <div class="footer-email">
        <i class="fa-solid fa-circle-user"></i>
        <span>{user_email}</span>
    </div>
    <button class="btn-sair" onclick="nav('sair')">
        <i class="fa-solid fa-right-from-bracket"></i>
        Sair
    </button>
</div>
</body>
<script>
function nav(page) {{
    const buttons = window.parent.document.querySelectorAll('[data-testid="stSidebar"] button');
    for (const btn of buttons) {{
        if (btn.innerText.trim() === page) {{
            btn.click();
            break;
        }}
    }}
}}
</script>
"""

    components.html(menu_html, height=620, scrolling=False)

# ---------------------------------------------------
# HELPER — CABEÇALHO COM PERÍODO
# ---------------------------------------------------

def cabecalho_analise(titulo, subtitulo=""):
    import datetime
    h1, h2 = st.columns([6, 3])
    with h1:
        st.markdown(
            f"<h1 style='font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0;font-family:DM Sans,sans-serif'>{titulo}</h1>",
            unsafe_allow_html=True
        )
        if subtitulo:
            st.markdown(f"<div style='font-size:16px;color:#6b7280;margin-top:3px'>{subtitulo}</div>", unsafe_allow_html=True)
    with h2:
        periodo = st.selectbox(
            "Período",
            ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Últimos 12 meses", "Todo o período"],
            index=1,
            label_visibility="collapsed"
        )
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0 24px 0'/>", unsafe_allow_html=True)
    periodo_map = {
        "Últimos 7 dias": 7, "Últimos 30 dias": 30,
        "Últimos 90 dias": 90, "Últimos 12 meses": 365, "Todo o período": None,
    }
    dias = periodo_map[periodo]
    if dias:
        data_inicio = (datetime.date.today() - datetime.timedelta(days=dias)).strftime("%Y-%m-%d")
    else:
        data_inicio = None
    return periodo, data_inicio

def cabecalho_simples(titulo, subtitulo=""):
    st.markdown(
        f"<h1 style='font-size:28px;font-weight:600;color:#111827;"
        f"letter-spacing:-0.5px;margin:0;font-family:DM Sans,sans-serif'>{titulo}</h1>",
        unsafe_allow_html=True,
    )
    if subtitulo:
        st.markdown(
            f"<div style='font-size:16px;color:#6b7280;margin-top:3px'>{subtitulo}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0 24px 0'/>",
        unsafe_allow_html=True,
    )

# ===================================================
# PÁGINAS
# ===================================================

# ---------------------------------------------------
# HOME — Minha Empresa
# ---------------------------------------------------

if st.session_state.pagina == "home":
 
    emp = st.session_state.dados["minha_empresa"]
    tem_dados = empresa_tem_dados(emp)
 
    if not tem_dados or st.session_state.editar_empresa:
 
        st.markdown("""
        <style>
        html body section.main [data-testid="stVerticalBlockBorderWrapper"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] > div > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] > div > div > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] > div > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] .stElementContainer,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] .stElementContainer > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stTextInput"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stTextInput"] > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stSelectbox"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stSelectbox"] > div,
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"],
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            background-color: #ffffff !important;
        }
        html body section.main [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e5e7eb !important;
            border-radius: 14px !important;
            padding: 20px 32px !important;
            margin-bottom: 0px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
        }
        html body section.main div[data-testid="stForm"],
        html body section.main div[data-testid="stForm"] > div,
        html body section.main div[data-testid="stForm"] > div > div,
        html body section.main div[data-testid="stForm"] [data-testid="stVerticalBlock"],
        html body section.main div[data-testid="stForm"] [data-testid="stHorizontalBlock"],
        html body section.main div[data-testid="stForm"] [data-testid="column"],
        html body section.main div[data-testid="stForm"] [data-testid="column"] > div,
        html body section.main div[data-testid="stForm"] .stElementContainer,
        html body section.main div[data-testid="stForm"] .stElementContainer > div,
        html body section.main div[data-testid="stForm"] div[data-testid="stTextInput"],
        html body section.main div[data-testid="stForm"] div[data-testid="stTextInput"] > div,
        html body section.main div[data-testid="stForm"] div[data-testid="stSelectbox"],
        html body section.main div[data-testid="stForm"] div[data-testid="stSelectbox"] > div,
        html body section.main div[data-testid="stForm"] [data-baseweb="select"],
        html body section.main div[data-testid="stForm"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            background-color: #ffffff !important;
        }
        html body section.main div[data-testid="stForm"] {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 14px !important;
            padding: 28px 32px !important;
            margin-bottom: 0px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
        }
        </style>
        """, unsafe_allow_html=True)
 
        st.markdown("""
        <style>
        @import url(https://db.onlinewebfonts.com/c/411b9832f1ad24e045b36f92814dac58?family=Animo+DEMO);
        .st-key-btn_editar_empresa { display: none !important; }
        </style>
        """, unsafe_allow_html=True)
 
        h1, h2 = st.columns([7, 3])
        with h1:
            st.markdown(
                "<h1 style='font-size:32px;font-weight:700;color:#1a2e4a;"
                "text-transform:uppercase;margin:0;"
                "font-family:\"Animo DEMO\",\"DM Sans\",sans-serif'>"
                "Minha Empresa</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:14px;color:#6b7280;'>"
                "Gerencie as informações e tenha uma visão geral da sua empresa.</div>",
                unsafe_allow_html=True,
            )
        with h2:
            st.markdown("<div style='padding-top:6px;'/>", unsafe_allow_html=True)
            btn_editar = st.button(
                "Editar Empresa",
                type="primary",
                use_container_width=True,
                key="btn_editar_empresa",
            )
            if btn_editar:
                st.session_state.editar_empresa = True
                st.rerun()
 
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0 20px 0'/>",
            unsafe_allow_html=True,
        )
 
        def sec_label(label):
            st.markdown(
                f"<div style='font-size:11px;font-weight:700;color:#9ca3af;"
                f"text-transform:uppercase;letter-spacing:1px;"
                f"margin-bottom:12px'>{label}</div>",
                unsafe_allow_html=True,
            )
 
        def form_divider():
            st.markdown(
                "<div style='margin:16px 0;border-top:1px solid #f3f4f6'/>",
                unsafe_allow_html=True,
            )
 
        with st.container(border=True):
            sec_label("Identificação")
            c1, c2 = st.columns(2)
            emp["nome"] = c1.text_input("Nome da Empresa", value=emp["nome"], key="edit_nome")
            site_digitado = c2.text_input("Site", value=emp["site"], key="edit_site")
            emp["site"] = limpar_site(site_digitado)
 
        st.markdown("<div style='height:12px'/>", unsafe_allow_html=True)
 
        with st.container(border=True):
            sec_label("Setor")
            c3, c4 = st.columns(2)
            setor_opcoes = list(SUBNICHOS.keys())
            setor_idx = setor_opcoes.index(emp["setor"]) if emp["setor"] in setor_opcoes else 0
 
            def on_setor_change():
                emp["tipo"] = ""
                st.session_state["_tipo_reset"] = True
 
            emp["setor"] = c3.selectbox(
                "Setor",
                setor_opcoes,
                index=setor_idx,
                key="sel_setor",
                on_change=on_setor_change,
            )
 
            subnichos_disponiveis = SUBNICHOS.get(emp["setor"], [])
            tipo_idx = 0 if st.session_state.get("_tipo_reset") else (
                subnichos_disponiveis.index(emp["tipo"]) if emp["tipo"] in subnichos_disponiveis else 0
            )
            st.session_state["_tipo_reset"] = False
 
            emp["tipo"] = c4.selectbox(
                "Sub-nicho",
                subnichos_disponiveis,
                index=tipo_idx,
                key="sel_tipo",
            )
 
        st.markdown("<div style='height:12px'/>", unsafe_allow_html=True)
 
        with st.form("cad_empresa", clear_on_submit=False):
 
            sec_label("Redes Sociais")
            c5, c6 = st.columns(2)
            emp["instagram"] = c5.text_input("Instagram", value=emp["instagram"])
            emp["fb_page"]   = c6.text_input("Facebook",  value=emp["fb_page"])
 
            servicos_text = st.text_input(
                "Serviços (separados por vírgula)",
                value=", ".join(emp["servicos"]),
            )
            emp["servicos"] = [s.strip() for s in servicos_text.split(",") if s.strip()]
 
            form_divider()
 
            sec_label("Localização")
            loc1, loc2 = st.columns(2)
            estados = list(ESTADOS_CIDADES.keys())
            estado_index = estados.index(emp["estado"]) if emp["estado"] in estados else 0
            emp["estado"] = loc1.selectbox("Estado", estados, index=estado_index)
            cidades = ESTADOS_CIDADES.get(emp["estado"], [])
            cidade_index = cidades.index(emp["cidade"]) if emp["cidade"] in cidades else 0
            emp["cidade"] = loc2.selectbox("Cidade", cidades, index=cidade_index)
 
            form_divider()
 
            col_salvar, col_cancelar = st.columns(2)
            salvar   = col_salvar.form_submit_button("Salvar",   use_container_width=True)
            cancelar = col_cancelar.form_submit_button("Cancelar", use_container_width=True)
 
            if cancelar:
                st.session_state.editar_empresa = False
                st.rerun()
 
            if salvar:
                emp["nome"] = st.session_state.get("edit_nome", emp["nome"])
                emp["site"] = limpar_site(st.session_state.get("edit_site", emp["site"]))
                if emp["nome"].strip():
                    st.session_state.editar_empresa = False
                    salvar_dados_usuario(st.session_state.user.id)
                    st.success("Empresa salva com sucesso!")
                    st.rerun()
                else:
                    st.error("Informe pelo menos o nome da empresa.")
 
    else:
 
        st.markdown("""
        <style>
        .st-key-btn_editar_empresa_hidden { display: none !important; }
        </style>
        """, unsafe_allow_html=True)
 
        h1, h2 = st.columns([7, 3])
        with h1:
            components.html("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@font-face {
    font-family: 'Animo';
    src: url('https://raw.githubusercontent.com/thiagomktsantos/marketylics/63946b2d891db6b45cc75a45550b7aa5fe67244a/utils/Animo-font.otf') format('opentype');
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent; overflow: hidden; }
.titulo {
    font-family: 'Animo', 'DM Sans', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #1a2e4a;
    text-transform: uppercase;
    margin: 0 0 6px 0;
    letter-spacing: 0.5px;
}
.sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: #6b7280;
}
</style>
<div class="titulo">Minha Empresa</div>
<div class="sub">Gerencie as informações e tenha uma visão geral da sua empresa.</div>
""", height=70)
 
        with h2:
            st.markdown("<div style='padding-top:6px;'/>", unsafe_allow_html=True)
            btn_editar = st.button(
                "Editar Empresa",
                type="primary",
                use_container_width=True,
                key="btn_editar_empresa",
            )
            if btn_editar:
                st.session_state.editar_empresa = True
                st.rerun()
 
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e5e7eb;margin:4px 0 20px 0'/>",
            unsafe_allow_html=True,
        )
 
        cor_empresa = get_minha_empresa_color()
        avatar = gerar_avatar(emp["nome"])
        loc = emp["cidade"] or ""
        if emp["estado"]:
            loc += (", " if loc else "") + emp["estado"]
        servicos_html = (
            "".join([f"<span class='empresa-tag'>{s}</span>" for s in emp["servicos"]])
            if emp["servicos"] else "<span style='color:#9ca3af;font-size:14px'>—</span>"
        )
 
        components.html(f"""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
}}
body {{
    background: transparent;
    overflow: hidden;
    padding-bottom: 2px;
}}
.empresa-card {{
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    overflow: hidden;
    position: relative;
}}
.empresa-card-deco {{
    position: absolute; top: 0; right: 0;
    width: 260px; height: 110px;
    pointer-events: none; opacity: 0.4;
}}
.empresa-card-body {{ padding: 24px 28px; }}
.empresa-top {{
    display: flex; align-items: center; gap: 16px;
    margin-bottom: 20px; padding-bottom: 18px;
    border-bottom: 1px solid #f3f4f6;
}}
.empresa-avatar {{
    width: 52px; height: 52px; min-width: 52px;
    border-radius: 50%; background: {cor_empresa};
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.empresa-nome {{
    font-size: 20px; font-weight: 700; color: #111827;
    margin-bottom: 2px; letter-spacing: -0.3px;
}}
.empresa-sub {{ font-size: 13px; color: #9ca3af; }}
.empresa-grid {{
    display: grid;
    grid-template-columns: 1fr 1px 1fr 1px 1fr;
    gap: 0;
}}
.empresa-divider {{
    background: #f0f0f0; margin: 0 24px; align-self: stretch;
}}
.empresa-col {{ padding: 0 4px; }}
.empresa-sec-title {{
    font-size: 10px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.2px;
    color: #9ca3af; margin-bottom: 14px;
    padding-bottom: 8px; border-bottom: 1px solid #f3f4f6;
}}
.empresa-row {{
    display: flex; align-items: flex-start;
    gap: 10px; margin-bottom: 12px;
}}
.empresa-ico {{
    width: 36px; height: 36px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    border-radius: 9px;
}}
.empresa-ico svg {{ width: 20px; height: 20px; }}
.empresa-lbl {{
    font-size: 11px; color: #9ca3af;
    display: block; margin-bottom: 1px;
}}
.empresa-val {{
    font-size: 14px; color: #111827; font-weight: 600;
}}
.empresa-tags-wrap {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.empresa-tag {{
    background: #eff6ff; color: #1d4ed8;
    border: 1px solid #bfdbfe;
    padding: 4px 12px; border-radius: 20px;
    font-size: 13px; font-weight: 500;
}}
@media (max-width: 700px) {{
    .empresa-grid {{ grid-template-columns: 1fr !important; }}
    .empresa-divider {{ display: none !important; }}
    .empresa-col {{
        padding: 16px 0 0 0 !important;
        border-top: 1px solid #f3f4f6;
    }}
    .empresa-col:first-child {{
        padding-top: 0 !important;
        border-top: none;
    }}
    .empresa-card-deco {{ display: none; }}
    .empresa-card-body {{ padding: 20px 18px; }}
}}
</style>
</head>
<body>
<div class="empresa-card" id="card">
    <svg class="empresa-card-deco" viewBox="0 0 260 110" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMaxYMin meet">
        <path d="M 0 88 C 55 64 110 76 170 50 C 210 34 238 26 260 14" stroke="#93c5fd" stroke-width="1.5" fill="none"/>
        <circle cx="170" cy="50" r="3.5" fill="#60a5fa"/>
        <circle cx="238" cy="26" r="3.5" fill="#60a5fa"/>
        <circle cx="254" cy="16" r="4" fill="#3b82f6"/>
        <rect x="185" y="58" width="11" height="38" rx="3" fill="#93c5fd" opacity="0.5"/>
        <rect x="202" y="46" width="11" height="50" rx="3" fill="#60a5fa" opacity="0.6"/>
        <rect x="219" y="33" width="11" height="63" rx="3" fill="#3b82f6" opacity="0.68"/>
        <rect x="236" y="20" width="11" height="76" rx="3" fill="#2563eb" opacity="0.75"/>
    </svg>
    <div class="empresa-card-body">
        <div class="empresa-top">
            <div class="empresa-avatar">{avatar}</div>
            <div>
                <div class="empresa-nome">{emp['nome']}</div>
                <div class="empresa-sub">{emp['setor']}{' · ' + emp['tipo'] if emp['tipo'] else ''}</div>
            </div>
        </div>
        <div class="empresa-grid">
            <div class="empresa-col">
                <div class="empresa-sec-title">Presença Digital</div>
                <div class="empresa-row">
                    <span class="empresa-ico" style="background:#f3f4f6;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8"
                             stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="2" y1="12" x2="22" y2="12"/>
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10
                                     15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                        </svg>
                    </span>
                    <div>
                        <span class="empresa-lbl">Site</span>
                        <span class="empresa-val">{emp['site'] or '—'}</span>
                    </div>
                </div>
                <div class="empresa-row">
                    <span class="empresa-ico" style="background:#fff0f6;">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <defs>
                                <linearGradient id="ig_emp" x1="0%" y1="100%" x2="100%" y2="0%">
                                    <stop offset="0%"   stop-color="#f09433"/>
                                    <stop offset="25%"  stop-color="#e6683c"/>
                                    <stop offset="50%"  stop-color="#dc2743"/>
                                    <stop offset="75%"  stop-color="#cc2366"/>
                                    <stop offset="100%" stop-color="#bc1888"/>
                                </linearGradient>
                            </defs>
                            <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#ig_emp)"/>
                            <circle cx="12" cy="12" r="4.5" stroke="white" stroke-width="1.8" fill="none"/>
                            <circle cx="17.5" cy="6.5" r="1.2" fill="white"/>
                        </svg>
                    </span>
                    <div>
                        <span class="empresa-lbl">Instagram</span>
                        <span class="empresa-val">{emp['instagram'] or '—'}</span>
                    </div>
                </div>
                <div class="empresa-row">
                    <span class="empresa-ico" style="background:#e8f0fe;">
                        <svg viewBox="0 0 24 24" fill="#1877F2">
                            <path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073
                                     C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047
                                     V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236
                                     2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268
                                     h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/>
                        </svg>
                    </span>
                    <div>
                        <span class="empresa-lbl">Facebook</span>
                        <span class="empresa-val">{emp['fb_page'] or '—'}</span>
                    </div>
                </div>
            </div>
            <div class="empresa-divider"></div>
            <div class="empresa-col">
                <div class="empresa-sec-title">Localização</div>
                <div class="empresa-row">
                    <span class="empresa-ico" style="background:#f3f4f6;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8"
                             stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                    </span>
                    <div>
                        <span class="empresa-lbl">Cidade / Estado</span>
                        <span class="empresa-val">{loc or '—'}</span>
                    </div>
                </div>
            </div>
            <div class="empresa-divider"></div>
            <div class="empresa-col">
                <div class="empresa-sec-title">Serviços</div>
                <div class="empresa-tags-wrap">{servicos_html}</div>
            </div>
        </div>
    </div>
</div>
<script>
function ajustarAltura() {{
    var card = document.querySelector('.card');
    if (!card) return;
    var h = card.getBoundingClientRect().height;
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var j = 0; j < iframes.length; j++) {{
        try {{
            if (iframes[j].contentWindow === window) {{
                iframes[j].style.height = (h + 8) + 'px';
                break;
            }}
        }} catch(e) {{}}
    }}
}}
document.addEventListener('DOMContentLoaded', ajustarAltura);
window.addEventListener('load', ajustarAltura);
setTimeout(ajustarAltura, 300);
setTimeout(ajustarAltura, 800);
</script>
</body>
</html>
        """, height=320, scrolling=False)
 
        st.markdown("""
        <div style='background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;
                    padding:14px 20px;display:flex;align-items:center;gap:16px;
                    margin-top:8px;box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
            <div style='width:42px;height:42px;border-radius:10px;background:#eff6ff;
                        display:flex;align-items:center;justify-content:center;flex-shrink:0'>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                    <path d="M9 12l2 2 4-4" stroke="#3a9fd6" stroke-width="2.2"
                          stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"
                          stroke="#3a9fd6" stroke-width="2"
                          stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <div style='font-size:14px;font-weight:600;color:#0f172a'>
                    Mantenha suas informações atualizadas
                </div>
                <div style='font-size:13px;color:#64748b;margin-top:2px'>
                    Dados atualizados garantem análises mais precisas e relatórios mais completos.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# PAGINA - CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.markdown("""
    <style>
    div[data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 14px !important;
        padding: 28px 32px !important;
        margin-bottom: 28px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    }
    .st-key-ads_id_hidden {
        display: none !important;
        height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    top1, top2 = st.columns([7, 3])
    with top1:
        components.html("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@font-face {
    font-family: 'Animo';
    src: url('https://raw.githubusercontent.com/thiagomktsantos/marketylics/63946b2d891db6b45cc75a45550b7aa5fe67244a/utils/Animo-font.otf') format('opentype');
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent; overflow: hidden; }
.titulo {
    font-family: 'Animo', 'DM Sans', sans-serif;
    font-size: 32px; font-weight: 700; color: #1a2e4a;
    text-transform: uppercase; margin: 0 0 6px 0; letter-spacing: 0.5px;
}
.sub { font-family: 'DM Sans', sans-serif; font-size: 14px; color: #6b7280; }
</style>
<div class="titulo">Concorrentes</div>
<div class="sub">Acompanhe e gerencie seus concorrentes para uma análise mais estratégica.</div>
""", height=70)

    with top2:
        st.markdown("<div style='padding-top:6px'/>", unsafe_allow_html=True)
        if st.button("＋ Adicionar", use_container_width=True, type="primary"):
            st.session_state.mostrar_form_concorrente = True
            st.session_state.editando_concorrente = None
            st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:4px 0 24px 0'/>", unsafe_allow_html=True)

    if st.session_state.mostrar_form_concorrente or st.session_state.editando_concorrente is not None:
        concorrente_edit = None
        if st.session_state.editando_concorrente is not None:
            concorrente_edit = st.session_state.dados["concorrentes"][st.session_state.editando_concorrente]

        titulo_form = "✏️ Editar Concorrente" if concorrente_edit else "➕ Novo Concorrente"
        st.markdown(f"<div style='font-size:16px;font-weight:700;color:#111827;margin-bottom:16px'>{titulo_form}</div>", unsafe_allow_html=True)

        with st.form("cad_concorrente", clear_on_submit=False):
            st.markdown("<div style='font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px'>Identificação</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome do Concorrente", value=(concorrente_edit["nome"] if concorrente_edit else ""))
            u = c2.text_input("URL do Site", value=(concorrente_edit["url"] if concorrente_edit else ""))

            st.markdown("<div style='margin:16px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px'>Redes Sociais</div>", unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            insta_handle = c3.text_input("Instagram", value=(concorrente_edit["instagram"] if concorrente_edit else "@"))
            fb_p = c4.text_input("Facebook", value=(concorrente_edit["fb_page"] if concorrente_edit else ""))

            ads_manual = st.text_input(
                "ads_id_hidden",
                value=(concorrente_edit.get("ads_id", "") if concorrente_edit else ""),
                key="ads_id_hidden",
                label_visibility="hidden",
                autocomplete="off",
            )

            col1, col2 = st.columns(2)
            salvar   = col1.form_submit_button("Salvar",   use_container_width=True)
            cancelar = col2.form_submit_button("Cancelar", use_container_width=True)

            if cancelar:
                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None
                st.rerun()

            if salvar:
                clean_handle = obter_instagram_handle(insta_handle)
                fb_clean     = obter_facebook_handle(fb_p)
                site_clean   = limpar_site(u)
                existing_ads_id  = (concorrente_edit.get("ads_id", "") if concorrente_edit else "").strip()
                existing_page_pic = (concorrente_edit.get("ads_page_pic", "") if concorrente_edit else "")
                dados_novos = {
                    "nome":         n,
                    "url":          site_clean,
                    "instagram":    clean_handle,
                    "fb_page":      fb_clean,
                    "ads_id":       existing_ads_id,
                    "ads_page_pic": existing_page_pic,
                }
                if st.session_state.editando_concorrente is not None:
                    st.session_state.dados["concorrentes"][st.session_state.editando_concorrente] = dados_novos
                else:
                    st.session_state.dados["concorrentes"].append(dados_novos)
                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None
                salvar_dados_usuario(st.session_state.user.id)
                st.rerun()

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:
        hide_btns_css = "\n".join([
            f".st-key-editar_{i} button, .st-key-remove_{i} button {{ display: none !important; }}"
            for i in range(len(concorrentes))
        ])
        st.markdown(f"<style>{hide_btns_css}</style>", unsafe_allow_html=True)

        cols = st.columns(2)
        for i, c in enumerate(concorrentes):
            with cols[i % 2]:
                avatar     = gerar_avatar(c["nome"])
                cor_avatar = get_concorrente_color(i)
                uid        = f"conc_{i}"

                card_html = f"""<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
    overflow: hidden;
}}
body {{ padding-bottom: 4px; }}
.card {{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    overflow: hidden;
}}
.card-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 20px 16px;
}}
.avatar {{
    width: 44px; height: 44px;
    border-radius: 50%;
    background: {cor_avatar};
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; color: #fff;
    flex-shrink: 0;
}}
.name {{
    font-size: 16px; font-weight: 700; color: #111827;
}}
.divider {{
    height: 1px; background: #f3f4f6; margin: 0 20px;
}}
.card-body {{
    padding: 14px 20px 18px;
    display: flex; flex-direction: column; gap: 10px;
}}
.row {{
    display: flex; align-items: center; gap: 12px;
}}
.icon-wrap {{
    width: 34px; height: 34px;
    border-radius: 8px;
    background: #f3f4f6;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
.row-info {{
    display: flex; flex-direction: column; gap: 1px;
    min-width: 0; flex: 1;
}}
.row-label {{
    font-size: 11px; color: #9ca3af;
}}
.row-value {{
    font-size: 13px; color: #111827; font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.card-footer {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    border-top: 1px solid #f3f4f6;
}}
.footer-btn {{
    padding: 11px 0;
    text-align: center;
    font-size: 15px; font-weight: 600;
    color: #6b7280;
    cursor: pointer;
    background: transparent;
    border: none;
    font-family: 'DM Sans', sans-serif;
    transition: background 0.12s;
    display: flex; align-items: center; justify-content: center; gap: 6px;
}}
.footer-btn:hover {{
    background: #f9fafb;
    color: #111827;
}}
.footer-btn.danger {{
    border-left: 1px solid #f3f4f6;
}}
.footer-btn.danger:hover {{
    background: #fef2f2;
}}
</style>
</head>
<body>
<div class="card" id="card_{uid}">
    <div class="card-header">
        <div class="avatar">{avatar}</div>
        <div class="name">{c['nome']}</div>
    </div>
    <div class="divider"></div>
    <div class="card-body">
        <div class="row">
            <div class="icon-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6b7280"
                     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10
                             15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
            </div>
            <div class="row-info">
                <span class="row-label">Site</span>
                <span class="row-value">{c['url'] or '—'}</span>
            </div>
        </div>
        <div class="row">
            <div class="icon-wrap" style="background:#fff0f6;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="ig_{uid}" x1="0%" y1="100%" x2="100%" y2="0%">
                            <stop offset="0%"   stop-color="#f09433"/>
                            <stop offset="25%"  stop-color="#e6683c"/>
                            <stop offset="50%"  stop-color="#dc2743"/>
                            <stop offset="75%"  stop-color="#cc2366"/>
                            <stop offset="100%" stop-color="#bc1888"/>
                        </linearGradient>
                    </defs>
                    <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#ig_{uid})"/>
                    <circle cx="12" cy="12" r="4.5" stroke="white" stroke-width="1.8" fill="none"/>
                    <circle cx="17.5" cy="6.5" r="1.2" fill="white"/>
                </svg>
            </div>
            <div class="row-info">
                <span class="row-label">Instagram</span>
                <span class="row-value">{c['instagram'] or '—'}</span>
            </div>
        </div>
        <div class="row">
            <div class="icon-wrap" style="background:#e8f0fe;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2">
                    <path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073
                             C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047
                             V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236
                             2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268
                             h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/>
                </svg>
            </div>
            <div class="row-info">
                <span class="row-label">Facebook</span>
                <span class="row-value">{c['fb_page'] or '—'}</span>
            </div>
        </div>
    </div>
    <div class="card-footer">
        <button class="footer-btn" onclick="acionar('editar_{i}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Editar
        </button>
        <button class="footer-btn danger" onclick="acionar('remove_{i}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                <path d="M10 11v6M14 11v6"/>
                <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
            </svg>
            Remover
        </button>
    </div>
</div>
<script>
function acionar(key) {{
    var selector = '[data-testid="stButton"] button, button';
    var btns = window.parent.document.querySelectorAll(selector);
    var keyMap = {{
        'editar_{i}':  'Editar Concorrente',
        'remove_{i}':  'Remover Concorrente',
    }};
    var label = keyMap[key];
    var found = [];
    btns.forEach(function(b) {{
        if (b.innerText.trim() === label) found.push(b);
    }});
    if (found[{i}]) {{ found[{i}].click(); return; }}
    if (found[0])   {{ found[0].click(); }}
}}

function ajustarAltura() {{
    var card = document.getElementById('card_{uid}');
    if (!card) return;
    var h = card.getBoundingClientRect().height;
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var j = 0; j < iframes.length; j++) {{
        try {{
            if (iframes[j].contentWindow === window) {{
                iframes[j].style.height = (h + 8) + 'px';
                break;
            }}
        }} catch(e) {{}}
    }}
}}
document.addEventListener('DOMContentLoaded', ajustarAltura);
window.addEventListener('load', ajustarAltura);
setTimeout(ajustarAltura, 100);
setTimeout(ajustarAltura, 400);
</script>
</body>
</html>"""

                components.html(card_html, height=260, scrolling=False)

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Editar Concorrente", key=f"editar_{i}", use_container_width=True):
                        st.session_state.editando_concorrente = i
                        st.session_state.mostrar_form_concorrente = False
                        st.rerun()
                with b2:
                    if st.button("Remover Concorrente", key=f"remove_{i}", use_container_width=True):
                        st.session_state.dados["concorrentes"].pop(i)
                        salvar_dados_usuario(st.session_state.user.id)
                        st.rerun()

                st.markdown("<div style='height:16px'/>", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style='background:#fff;border:1px dashed #d1d5db;border-radius:14px;
                    padding:48px 32px;text-align:center;margin-top:8px'>
            <div style='font-size:32px;margin-bottom:12px'>🎯</div>
            <div style='font-size:16px;font-weight:600;color:#374151;margin-bottom:6px'>Nenhum concorrente cadastrado</div>
            <div style='font-size:14px;color:#9ca3af'>Clique em <b>＋ Adicionar</b> para começar a monitorar seus concorrentes.</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# PAGINA - CONFRONTO DE SITES
# ---------------------------------------------------
 
elif st.session_state.pagina == "sites":
 
    import datetime as _dt
 
    emp = st.session_state.dados["minha_empresa"]
    concorrentes = st.session_state.dados["concorrentes"]
 
    st.markdown("""
    <style>
    @import url(https://db.onlinewebfonts.com/c/411b9832f1ad24e045b36f92814dac58?family=Animo+DEMO);
    </style>
    """, unsafe_allow_html=True)
 
    h1, h2 = st.columns([7, 3])
    with h1:
        components.html("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@font-face {
    font-family: 'Animo';
    src: url('https://raw.githubusercontent.com/thiagomktsantos/marketylics/63946b2d891db6b45cc75a45550b7aa5fe67244a/utils/Animo-font.otf') format('opentype');
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent; overflow: hidden; }
.titulo {
    font-family: 'Animo', 'DM Sans', sans-serif;
    font-size: 32px; font-weight: 700; color: #1a2e4a;
    text-transform: uppercase; margin: 0 0 6px 0; letter-spacing: 0.5px;
}
.sub { font-family: 'DM Sans', sans-serif; font-size: 14px; color: #6b7280; }
</style>
<div class="titulo">Confronto de Sites</div>
<div class="sub">Análise comparativa de posicionamento via IA.</div>
""", height=65)
 
    with h2:
        gerar_btn = st.button("Gerar Relatório", type="primary", use_container_width=True)
        ultimo_relatorio = st.session_state.get("sites_ultima_geracao", "")
        if ultimo_relatorio:
            st.markdown(
                f"<div style='font-size:13px;color:#6b7280;text-align:center;margin-top:-8px'>"
                f"🕒 Última análise: <b>{ultimo_relatorio}</b></div>",
                unsafe_allow_html=True,
            )
 
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 20px 0'/>", unsafe_allow_html=True)
 
    sites_disponiveis = []
    if emp.get("site"):
        sites_disponiveis.append({"nome": emp["nome"], "url": emp["site"], "tipo": "minha", "instagram": emp.get("instagram", "")})
    for c in concorrentes:
        if c.get("url"):
            sites_disponiveis.append({"nome": c["nome"], "url": c["url"], "tipo": "concorrente", "instagram": c.get("instagram", "")})
 
    if not sites_disponiveis:
        st.info("Cadastre o site da sua empresa e de pelo menos um concorrente para usar esta funcionalidade.")
        st.stop()
 
    cols_sites = st.columns(min(len(sites_disponiveis), 4))
 
    for idx_s, s in enumerate(sites_disponiveis):
        chave = f"sites_analise_{idx_s}"
        if chave not in st.session_state:
            st.session_state[chave] = ""
 
    ghost_css = "\n".join([
        f".st-key-btn_site_ia_{i} {{ display: none !important; }}"
        for i in range(len(sites_disponiveis))
    ])
    st.markdown(f"<style>{ghost_css}</style>", unsafe_allow_html=True)
 
    site_ia_triggers = {}
    for idx_s in range(len(sites_disponiveis)):
        triggered = st.button(
            f"_site_ia_trigger_{idx_s}_",
            key=f"btn_site_ia_{idx_s}",
            use_container_width=False,
        )
        site_ia_triggers[idx_s] = triggered
 
    for idx_s, s in enumerate(sites_disponiveis):
        with cols_sites[idx_s % 4]:
            is_minha   = s["tipo"] == "minha"
            cor_avatar = get_minha_empresa_color() if is_minha else get_concorrente_color(idx_s - 1)
            badge_bg   = "#eff6ff" if is_minha else "#f3f4f6"
            badge_txt  = "#1d4ed8" if is_minha else "#6b7280"
            badge_brd  = "#bfdbfe" if is_minha else "#e5e7eb"
            badge_lbl  = "Minha Empresa" if is_minha else "Concorrente"
            avatar_letras = gerar_avatar(s["nome"])
            uid = f"site_{idx_s}"
 
            card_html = f"""<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
    overflow: hidden;
}}
.card {{
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    overflow: hidden;
}}
.card-header {{
    display: flex; align-items: center; gap: 12px;
    padding: 16px 16px 14px 16px;
    border-bottom: 1px solid #f3f4f6;
}}
.avatar {{
    width: 44px; height: 44px; border-radius: 50%;
    background: {cor_avatar};
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.nome-wrap {{ flex: 1; min-width: 0; }}
.nome {{
    font-size: 16px; font-weight: 700; color: #111827;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.badge {{
    display: inline-block;
    background: {badge_bg}; color: {badge_txt};
    border: 1px solid {badge_brd};
    padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; margin-top: 4px;
}}
.url-row {{
    padding: 10px 16px;
    font-size: 14px; color: #0d1117;
    word-break: break-all;
    border-bottom: 1px solid #f3f4f6;
    display: flex; align-items: center; gap: 6px;
}}
.url-label {{ font-size: 14px; font-weight: 700; color: #0d1117; flex-shrink: 0; }}
.preview-wrap {{
    margin: 12px 12px 0 12px;
    border-radius: 8px; overflow: hidden;
    border: 1px solid #e5e7eb; background: #f9fafb;
    aspect-ratio: 16 / 9;
    width: calc(100% - 24px);
    position: relative;
}}
.preview-wrap img {{
    width: 100%; height: 100%; display: block;
    border-radius: 8px; object-fit: cover; object-position: top;
}}
.btn-wrap {{ padding: 12px 12px 14px 12px; }}
.btn-analisar {{
    width: 100%; padding: 10px 0;
    border: 1px solid #3a9fd6; border-radius: 8px;
    background: #eff6ff; font-size: 14px; font-weight: 700; color: #1d4ed8;
    cursor: pointer; font-family: 'DM Sans', sans-serif;
    transition: background 0.15s;
    display: flex; align-items: center; justify-content: center; gap: 6px;
}}
.btn-analisar:hover {{ background: #dbeafe; }}
</style>
</head>
<body>
<div class="card" id="card_{uid}">
    <div class="card-header">
        <div class="avatar">{avatar_letras}</div>
        <div class="nome-wrap">
            <div class="nome">{s['nome']}</div>
            <div class="badge">{badge_lbl}</div>
        </div>
    </div>
    <div class="url-row">
        <span class="url-label">Site:</span>
        <span>{s['url']}</span>
    </div>
    <div class="preview-wrap">
        <img
            src="https://api.microlink.io/?url=https://{s['url']}&screenshot=true&meta=false&embed=screenshot.url"
            onerror="this.parentElement.innerHTML='<div style=\\'padding:32px 10px;text-align:center;font-size:12px;color:#9ca3af\\'>📷 Prévia indisponível</div>'"
            loading="lazy"
            alt="Preview {s['nome']}"
        />
    </div>
    <div class="btn-wrap">
        <button class="btn-analisar" onclick="triggerAnalise({idx_s})">
            Analisar este site 🤖
        </button>
    </div>
</div>
<script>
function triggerAnalise(idx) {{
    var targetText = '_site_ia_trigger_' + idx + '_';
    var btns = window.parent.document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {{
        if (btns[i].innerText.trim() === targetText) {{
            btns[i].click();
            return;
        }}
    }}
}}
 
function ajustarAltura() {{
    var card = document.getElementById('card_{uid}');
    if (!card) return;
    var h = card.getBoundingClientRect().height;
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{
            if (iframes[i].contentWindow === window) {{
                iframes[i].style.height = (h + 12) + 'px';
                break;
            }}
        }} catch(e) {{}}
    }}
}}
 
if (window.ResizeObserver) {{
    var ro = new ResizeObserver(ajustarAltura);
    ro.observe(document.body);
}}
document.addEventListener('DOMContentLoaded', ajustarAltura);
window.addEventListener('load', ajustarAltura);
setTimeout(ajustarAltura, 200);
setTimeout(ajustarAltura, 600);
setTimeout(ajustarAltura, 1200);
</script>
</body>
</html>"""
 
            components.html(card_html, height=480, scrolling=False)
 
            if site_ia_triggers[idx_s]:
                if gemini_model is None:
                    st.session_state[f"sites_analise_{idx_s}"] = "Configure GEMINI_API_KEY nos secrets."
                else:
                    with st.spinner(f"Analisando {s['nome']}…"):
                        conteudo_site = extrair_conteudo_site(s["url"])
                        try:
                            prompt_individual = f"""
Você é um especialista em marketing digital e posicionamento de marca.
Analise o conteúdo extraído do site abaixo e gere uma análise individual detalhada em português.
 
Empresa: {s['nome']}
URL: {s['url']}
Tipo: {"Minha Empresa" if is_minha else "Concorrente"}
 
Conteúdo extraído do site:
{conteudo_site[:4000] if conteudo_site else "Não foi possível extrair conteúdo."}
 
---
 
Responda com as seguintes seções:
 
### 📌 Proposta de Valor
Qual é a proposta central comunicada no site?
 
### 🎯 Posicionamento
Como esta empresa se posiciona no mercado? (premium, popular, nicho, generalista etc.)
 
### 🔑 Mensagens Principais
Quais são os termos, promessas e mensagens mais repetidos?
 
### 🛠️ Serviços / Produtos Destacados
Liste os principais serviços ou produtos apresentados no site.
 
### ✅ Pontos Fortes
3 pontos positivos observados na comunicação do site.
 
### ⚠️ Pontos de Atenção
2 pontos que poderiam ser melhorados.
 
### 💡 Recomendação
1 ação concreta de alto impacto para melhorar o posicionamento.
 
Seja direto e objetivo, baseando-se apenas no conteúdo real do site.
"""
                            resp = gemini_model.generate_content(prompt_individual)
                            st.session_state[f"sites_analise_{idx_s}"] = resp.text
                            st.rerun()
                        except Exception as e:
                            st.session_state[f"sites_analise_{idx_s}"] = f"Erro: {e}"
 
            analise_ind = st.session_state.get(f"sites_analise_{idx_s}", "")
            if analise_ind:
                st.markdown(f"""
                <div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;
                            padding:14px 16px;font-size:13px;color:#374151;line-height:1.75;
                            max-height:280px;overflow-y:auto;margin-top:6px;margin-bottom:4px'>
                    {analise_ind.replace(chr(10), "<br>")}
                </div>
                """, unsafe_allow_html=True)
 
    if gerar_btn:
        st.session_state.relatorio_gemini = ""
        st.session_state.relatorio_sites = {}
 
        with st.status("📡 Lendo os sites...", expanded=True) as status:
            for s in sites_disponiveis:
                st.write(f"Acessando **{s['nome']}** ({s['url']})…")
                conteudo = extrair_conteudo_site(s["url"])
                st.session_state.relatorio_sites[s["url"]] = conteudo
                if conteudo and not conteudo.startswith("[Erro"):
                    palavras = len(conteudo.split())
                    st.write(f"✅ {palavras} palavras extraídas")
                else:
                    st.write(f"⚠️ Não foi possível extrair conteúdo")
            status.update(label="✅ Sites lidos! Gerando análise com Gemini…", state="running")
 
            empresa_principal = None
            concorrentes_data = []
            for s in sites_disponiveis:
                item = {
                    "nome": s["nome"],
                    "url":  s["url"],
                    "conteudo": st.session_state.relatorio_sites.get(s["url"], ""),
                }
                if s["tipo"] == "minha":
                    empresa_principal = item
                else:
                    concorrentes_data.append(item)
 
            if empresa_principal is None and sites_disponiveis:
                empresa_principal = {
                    "nome": sites_disponiveis[0]["nome"],
                    "url":  sites_disponiveis[0]["url"],
                    "conteudo": st.session_state.relatorio_sites.get(sites_disponiveis[0]["url"], ""),
                }
 
            relatorio = gerar_relatorio_posicionamento(empresa_principal, concorrentes_data)
            st.session_state.relatorio_gemini = relatorio
            st.session_state["sites_ultima_geracao"] = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")
            status.update(label="✅ Relatório gerado!", state="complete")
 
    if st.session_state.relatorio_gemini:
        st.markdown(
            "<div style='font-size:20px;font-weight:700;color:#111827;"
            "font-family:DM Sans,sans-serif;margin-bottom:12px'>"
            "📋 Relatório Geral de Posicionamento Competitivo</div>",
            unsafe_allow_html=True,
        )
 
        col_titulo_salvar, col_btn_salvar = st.columns([5, 2])
        with col_titulo_salvar:
            nome_analise = st.text_input(
                "Nome para salvar",
                placeholder="Ex: Análise maio/2025",
                label_visibility="collapsed",
                key="nome_analise_input",
            )
        with col_btn_salvar:
            if st.button("💾 Salvar Análise Geral", use_container_width=True):
                titulo_salvo = nome_analise.strip() or _dt.datetime.now().strftime("Análise %d/%m/%Y %H:%M")
                if "analises_salvas" not in st.session_state:
                    st.session_state.analises_salvas = []
                st.session_state.analises_salvas.append({
                    "titulo": titulo_salvo,
                    "data": _dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "relatorio": st.session_state.relatorio_gemini,
                    "sites": [s["nome"] for s in sites_disponiveis],
                    "tipo": "geral",
                })
                st.toast(f"✅ Análise «{titulo_salvo}» salva!", icon="✅")
 
        st.markdown(st.session_state.relatorio_gemini)
 
        with st.expander("🔎 Ver conteúdo extraído dos sites"):
            for s in sites_disponiveis:
                conteudo = st.session_state.relatorio_sites.get(s["url"], "")
                st.markdown(f"**{s['nome']}** — `{s['url']}`")
                if conteudo:
                    st.text_area(
                        label="",
                        value=conteudo[:2000] + ("…" if len(conteudo) > 2000 else ""),
                        height=180,
                        key=f"txt_{s['url']}",
                        disabled=True,
                    )
                else:
                    st.warning("Nenhum conteúdo extraído.")
                st.markdown("---")
 
    st.markdown("<div style='margin:16px 0 0 0;border-top:1px solid #e5e7eb'/>", unsafe_allow_html=True)
 
    analises = st.session_state.get("analises_salvas", [])
    analises_gerais      = [(i, a) for i, a in enumerate(analises) if a.get("tipo", "geral") == "geral"]
    analises_individuais = [(i, a) for i, a in enumerate(analises) if a.get("tipo") == "individual"]
 
    acoes_salvas = {}
    for i, a in enumerate(analises):
        acoes_salvas[f"rm_{i}"] = st.button(f"_rm_analise_{i}_", key=f"btn_rm_analise_{i}")
 
    rm_css = "\n".join([
        f".st-key-btn_rm_analise_{i} {{ display: none !important; }}"
        for i in range(len(analises))
    ])
    st.markdown(f"<style>{rm_css}</style>", unsafe_allow_html=True)
 
    for i in range(len(analises) - 1, -1, -1):
        if acoes_salvas.get(f"rm_{i}"):
            st.session_state.analises_salvas.pop(i)
            st.rerun()
 
    def _card_analise(idx_real, analise, tipo):
        titulo    = analise.get("titulo", "—")
        data      = analise.get("data", "—")
        sites_str = ", ".join(analise.get("sites", []))
        relatorio = (analise.get("relatorio") or "").replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        icone     = "📄" if tipo == "geral" else "🌐"
 
        return f"""
        <div class="item" id="item_{idx_real}">
            <div class="item-header" onclick="toggleItem({idx_real})">
                <div class="item-left">
                    <span class="item-icon">{icone}</span>
                    <div>
                        <div class="item-titulo">{titulo}</div>
                        <div class="item-meta">{data}{" · " + sites_str if sites_str else ""}</div>
                    </div>
                </div>
                <span class="item-chevron" id="chev_{idx_real}">▼</span>
            </div>
            <div class="item-body" id="body_{idx_real}" style="display:none">
                <div class="item-relatorio">{(analise.get("relatorio") or "").replace(chr(10), "<br>")}</div>
                <div class="item-acoes">
                    <button class="btn-dl" onclick="baixar({idx_real}, `{relatorio}`, `{titulo.replace(' ','_')}`)">⬇️ Baixar .txt</button>
                    <button class="btn-rm" onclick="remover({idx_real})">🗑️ Remover</button>
                </div>
            </div>
        </div>
        """
 
    itens_geral = "".join(
        _card_analise(i, a, "geral")
        for i, a in reversed(analises_gerais)
    ) if analises_gerais else """
        <div style='padding:36px 24px;text-align:center;color:#9ca3af;font-size:14px;
                    border:1px dashed #d1d5db;border-radius:10px;margin:16px 0'>
            Nenhuma análise geral salva ainda.<br>Gere um relatório e clique em <b>💾 Salvar Análise</b>.
        </div>"""
 
    itens_individual = "".join(
        _card_analise(i, a, "individual")
        for i, a in reversed(analises_individuais)
    ) if analises_individuais else """
        <div style='padding:36px 24px;text-align:center;color:#9ca3af;font-size:14px;
                    border:1px dashed #d1d5db;border-radius:10px;margin:16px 0'>
            Nenhuma análise por site salva ainda.<br>
            Use o botão <b>Analisar este site 🤖</b> em cada card.
        </div>"""
 
    analises_html = f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ background:transparent; font-family:'DM Sans',sans-serif; -webkit-font-smoothing:antialiased; }}
body {{ background:transparent; overflow:visible; padding-bottom:8px; }}
.wrap {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; }}
.wrap-header {{ padding:14px 18px; font-size:14px; font-weight:800; color:#1a2e4a; text-transform:uppercase; letter-spacing:0.3px; border-bottom:1px solid #e5e7eb; background:#fff; }}
.tabs {{ display:flex; border-bottom:1px solid #e5e7eb; background:#f9fafb; }}
.tab {{ flex:1; padding:11px 0; text-align:center; font-size:14px; font-weight:600; color:#9ca3af; cursor:pointer; border:none; background:transparent; border-bottom:2px solid transparent; margin-bottom:-1px; font-family:'DM Sans',sans-serif; transition:color 0.15s; }}
.tab:hover {{ color:#374151; background:#f3f4f6; }}
.tab.active {{ color:#1a2e4a; border-bottom:2px solid #3a9fd6; background:#fff; }}
.panel {{ display:none; padding:12px 14px; }}
.panel.active {{ display:block; }}
.item {{ border:1px solid #e5e7eb; border-radius:10px; margin-bottom:10px; overflow:hidden; background:#fff; }}
.item-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 16px; cursor:pointer; background:#f9fafb; transition:background 0.12s; }}
.item-header:hover {{ background:#f3f4f6; }}
.item-left {{ display:flex; align-items:center; gap:12px; flex:1; min-width:0; }}
.item-icon {{ font-size:18px; flex-shrink:0; }}
.item-titulo {{ font-size:14px; font-weight:700; color:#111827; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.item-meta {{ font-size:12px; color:#9ca3af; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.item-chevron {{ font-size:11px; color:#9ca3af; flex-shrink:0; margin-left:10px; transition:transform 0.2s; }}
.item-chevron.open {{ transform:rotate(180deg); }}
.item-body {{ padding:16px; border-top:1px solid #f3f4f6; }}
.item-relatorio {{ font-size:13px; color:#374151; line-height:1.75; max-height:320px; overflow-y:auto; padding-right:4px; margin-bottom:14px; }}
.item-acoes {{ display:flex; gap:10px; padding-top:12px; border-top:1px solid #f3f4f6; }}
.btn-dl {{ flex:1; padding:9px; border-radius:8px; border:1px solid #3a9fd6; background:#eff6ff; font-size:13px; font-weight:700; color:#1d4ed8; cursor:pointer; font-family:'DM Sans',sans-serif; transition:background 0.15s; }}
.btn-dl:hover {{ background:#dbeafe; }}
.btn-rm {{ padding:9px 16px; border-radius:8px; border:1px solid #fca5a5; background:#fef2f2; font-size:13px; font-weight:700; color:#dc2626; cursor:pointer; font-family:'DM Sans',sans-serif; transition:background 0.15s; white-space:nowrap; }}
.btn-rm:hover {{ background:#fee2e2; }}
</style>
<div class="wrap">
    <div class="wrap-header">Análises Salvas</div>
    <div class="tabs">
        <button class="tab active" onclick="showTab('geral', this)">Análise Geral 📊</button>
        <button class="tab"        onclick="showTab('individual', this)">Análise por Site 🔍</button>
    </div>
    <div id="panel-geral" class="panel active">{itens_geral}</div>
    <div id="panel-individual" class="panel">{itens_individual}</div>
</div>
<script>
function showTab(name, el) {{
    document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active'); }});
    document.querySelectorAll('.panel').forEach(function(p) {{ p.classList.remove('active'); }});
    document.getElementById('panel-' + name).classList.add('active');
    el.classList.add('active');
    ajustarAltura();
}}
function toggleItem(idx) {{
    var body = document.getElementById('body_' + idx);
    var chev = document.getElementById('chev_' + idx);
    var aberto = body.style.display !== 'none';
    body.style.display = aberto ? 'none' : 'block';
    chev.classList.toggle('open', !aberto);
    setTimeout(ajustarAltura, 50);
}}
function remover(idx) {{
    var targetText = '_rm_analise_' + idx + '_';
    var btns = window.parent.document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {{
        if (btns[i].innerText.trim() === targetText) {{ btns[i].click(); return; }}
    }}
}}
function baixar(idx, conteudo, nome) {{
    var blob = new Blob([conteudo], {{type: 'text/plain;charset=utf-8'}});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = nome + '.txt';
    a.click();
}}
function ajustarAltura() {{
    var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{
            if (iframes[i].contentWindow === window) {{
                iframes[i].style.height = (h + 8) + 'px';
                break;
            }}
        }} catch(e) {{}}
    }}
}}
var ro = new ResizeObserver(ajustarAltura);
ro.observe(document.body);
document.addEventListener('DOMContentLoaded', ajustarAltura);
window.addEventListener('load', ajustarAltura);
setTimeout(ajustarAltura, 200);
setTimeout(ajustarAltura, 600);
</script>
"""
 
    components.html(analises_html, height=60, scrolling=False)

# ---------------------------------------------------
# PAGINA - ADS (Biblioteca de Anúncios com Meta Ad Library API)
# ---------------------------------------------------
 
elif st.session_state.pagina == "ads":

    import datetime as _dt
    import json as _json
    import base64 as _b64
    import time as _time

    emp   = st.session_state.dados["minha_empresa"]
    concs = st.session_state.dados["concorrentes"]
 
    CACHE_TTL_HORAS = 24
    APIFY_ACTOR_ID  = "curious_coder~facebook-ads-library-scraper"
 
    # ── FIX 1: salvar_cache_ads robusto ──
    def salvar_cache_ads(dados: dict):
        try:
            user_id = st.session_state.user.id
            existing = supabase.table("ci_dados").select("*").eq("user_id", user_id).execute()
            if existing.data:
                supabase.table("ci_dados").update({"ads_cache": dados}).eq("user_id", user_id).execute()
            else:
                payload = {
                    "user_id": user_id,
                    "minha_empresa": st.session_state.dados.get("minha_empresa", {}),
                    "concorrentes": st.session_state.dados.get("concorrentes", []),
                    "metricas_redes": st.session_state.get("metricas_redes", {}),
                    "ads_cache": dados,
                }
                supabase.table("ci_dados").insert(payload).execute()
        except Exception as e:
            st.toast(f"⚠️ Erro ao salvar cache de ads: {e}", icon="⚠️")
 
    def carregar_cache_ads() -> dict:
        try:
            res = (
                supabase.table("ci_dados")
                .select("ads_cache")
                .eq("user_id", st.session_state.user.id)
                .execute()
            )
            if res.data and res.data[0].get("ads_cache"):
                return res.data[0]["ads_cache"]
        except Exception:
            pass
        return {}
 
    def cache_esta_fresco(ts_str: str) -> bool:
        if not ts_str:
            return False
        try:
            ts = _dt.datetime.strptime(ts_str, "%d/%m/%Y %H:%M")
            return (_dt.datetime.now() - ts).total_seconds() < CACHE_TTL_HORAS * 3600
        except Exception:
            return False
 
    def _url_para_base64(url: str) -> str:
        if not url or not url.startswith("http"):
            return ""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.facebook.com/",
            }
            r = requests.get(url, headers=headers, timeout=10, stream=True)
            if r.status_code != 200:
                return ""
            ct = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            if not ct.startswith("image/"):
                ct = "image/jpeg"
            data = _b64.b64encode(r.content).decode("utf-8")
            return f"data:{ct};base64,{data}"
        except Exception:
            return ""
 
    def _microlink_screenshot(snap_url: str) -> str:
        if not snap_url:
            return ""
        import urllib.parse
        encoded = urllib.parse.quote(snap_url, safe="")
        return f"https://api.microlink.io/?url={encoded}&screenshot=true&meta=false&embed=screenshot.url"
 
    def _extract_video_thumbnail(ad: dict) -> str:
        snapshot = ad.get("snapshot") or {}
        cards    = snapshot.get("cards") or []
        for k in ("thumbnail_url", "preview_image_url", "image_url", "original_image_url"):
            v = ad.get(k) or snapshot.get(k) or ""
            if v and v.startswith("http"):
                return v
        for card in cards:
            if not isinstance(card, dict):
                continue
            for k in ("thumbnail_url", "preview_image_url", "image_url"):
                v = card.get(k, "")
                if v and v.startswith("http"):
                    return v
        return ""
 
    def _truncar(txt, n=160):
        if not txt:
            return ""
        txt = str(txt).strip()
        return txt[:n] + "…" if len(txt) > n else txt
 
    def _is_dynamic(txt):
        if not txt:
            return False
        return bool(re.search(r'\{\{[^}]+\}\}', txt))
 
    def _clean_dynamic(txt):
        if not txt:
            return ""
        cleaned = re.sub(r'\{\{[^}]+\}\}', '', txt).strip()
        lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
        return ' '.join(lines)
 
    def _dias_ativo(start_raw: str) -> str:
        if not start_raw:
            return ""
        meses = ['jan','fev','mar','abr','mai','jun',
                 'jul','ago','set','out','nov','dez']
        try:
            ts_int = int(str(start_raw).strip())
            if ts_int > 10**9:
                dto = _dt.datetime.utcfromtimestamp(ts_int)
            else:
                raise ValueError
        except (ValueError, OSError):
            try:
                dto = _dt.datetime.strptime(str(start_raw)[:10], "%Y-%m-%d")
            except Exception:
                return str(start_raw)[:10]
        data_fmt = f"{dto.day} de {meses[dto.month-1]} de {dto.year}"
        dias = (_dt.datetime.now() - dto).days
        if dias == 0:
            dias_str = "hoje"
        elif dias == 1:
            dias_str = "1 dia ativo"
        else:
            dias_str = f"{dias} dias ativo"
        return f"Veiculação iniciada: {data_fmt} ({dias_str})"
 
    def _extract_images(ad: dict) -> list:
        imgs = []
        seen = set()
        def add(url):
            url = (url or "").strip()
            if url and url not in seen and url.startswith("http"):
                seen.add(url); imgs.append(url)
        snapshot = ad.get("snapshot") or {}
        cards    = snapshot.get("cards") or []
        for k in ("image_url","original_image_url","resized_image_url",
                  "thumbnail_url","preview_image_url","full_picture"):
            add(ad.get(k))
        for k in ("image_url","original_image_url","resized_image_url",
                  "thumbnail_url","background_image"):
            add(snapshot.get(k))
        for card in cards:
            if not isinstance(card, dict): continue
            for k in ("original_image_url","image_url","resized_image_url",
                      "thumbnail_url","picture"):
                add(card.get(k))
        for obj in (ad.get("creative_images") or []):
            if isinstance(obj, dict):
                for k in ("original_image_url","image_url","url"):
                    add(obj.get(k))
            elif isinstance(obj, str): add(obj)
        for obj in (ad.get("images") or []):
            if isinstance(obj, dict):
                for k in ("original_image_url","image_url","url","src"):
                    add(obj.get(k))
            elif isinstance(obj, str): add(obj)
        return imgs
 
    def _extract_copy(ad: dict) -> dict:
        snapshot = ad.get("snapshot") or {}
        cards    = snapshot.get("cards") or []
        def first_str(val):
            if isinstance(val, list):
                for v in val:
                    if v and isinstance(v, str) and v.strip():
                        return v.strip()
            if isinstance(val, str) and val.strip():
                return val.strip()
            return ""
        body  = (first_str(ad.get("ad_creative_bodies"))
                 or first_str(snapshot.get("body"))
                 or first_str(ad.get("body"))
                 or first_str(ad.get("message"))
                 or first_str(snapshot.get("message")))
        title = (first_str(ad.get("ad_creative_link_titles"))
                 or first_str(snapshot.get("title"))
                 or first_str(ad.get("title"))
                 or first_str(snapshot.get("link_title")))
        desc  = (first_str(ad.get("ad_creative_link_descriptions"))
                 or first_str(snapshot.get("link_description"))
                 or first_str(ad.get("description"))
                 or first_str(snapshot.get("description")))
        cta   = (first_str(ad.get("cta_type"))
                 or first_str(snapshot.get("cta_type"))
                 or first_str(ad.get("call_to_action_type")))
        caption = (first_str(snapshot.get("caption"))
                   or first_str(ad.get("caption")))
        if not body and cards:
            for card in cards:
                if isinstance(card, dict):
                    v = first_str(card.get("body") or card.get("message") or card.get("title") or "")
                    if v:
                        body = v
                        break
        return {"body": body, "title": title, "desc": desc, "cta": cta, "caption": caption}
 
    def _extract_videos(ad: dict) -> list:
        vids = []
        seen = set()
        snapshot = ad.get("snapshot") or {}
        cards    = snapshot.get("cards") or []
        def add(url):
            url = (url or "").strip()
            if url and url not in seen and url.startswith("http"):
                seen.add(url); vids.append(url)
        for k in ("video_hd_url","video_sd_url","video_url"):
            add(ad.get(k)); add(snapshot.get(k))
        for card in cards:
            if isinstance(card, dict):
                for k in ("video_hd_url","video_sd_url","video_url"):
                    add(card.get(k))
        return vids
 
    def _normalizar_item_apify(item: dict) -> dict:
        snapshot = item.get("snapshot") or {}
        cards    = snapshot.get("cards") or []
 
        ad_id   = str(item.get("adArchiveID") or item.get("ad_archive_id") or item.get("id") or "")
        page_id = str(item.get("pageID") or item.get("page_id") or "")
        page_name = (item.get("pageName") or item.get("page_name") or snapshot.get("page_name") or "")
        page_profile_picture = (
            item.get("pageProfilePicture")
            or item.get("page_profile_picture")
            or snapshot.get("page_profile_picture_url")
            or ""
        )
 
        images = _extract_images(item)
        videos = _extract_videos(item)
        copy = _extract_copy(item)
 
        plats = (item.get("publisherPlatform")
                 or item.get("publisher_platforms")
                 or snapshot.get("publisher_platforms")
                 or [])
        if isinstance(plats, str): plats = [plats]
        if not plats: plats = ["facebook", "instagram"]
 
        raw_media_type = (item.get("mediaType") or item.get("media_type") or "").upper()
        has_video   = bool(videos) or raw_media_type == "VIDEO"
        has_cards   = len(cards) > 1 and not has_video
        has_image   = bool(images) and not has_video
 
        if has_video:   fmt = "Vídeo 🎬"
        elif has_cards: fmt = "Carrossel 🎠"
        elif has_image: fmt = "Imagem 🖼️"
        else:           fmt = "Texto 📝"
 
        is_dyn  = (_is_dynamic(copy["body"]) or _is_dynamic(copy["title"]) or _is_dynamic(copy["desc"]))
        body_c  = _clean_dynamic(copy["body"])  if _is_dynamic(copy["body"])  else copy["body"]
        title_c = _clean_dynamic(copy["title"]) if _is_dynamic(copy["title"]) else copy["title"]
        desc_c  = _clean_dynamic(copy["desc"])  if _is_dynamic(copy["desc"])  else copy["desc"]
 
        imp = item.get("impressionsWithIndex") or item.get("impressions") or {}
        if isinstance(imp, dict):
            lo = imp.get("lowerBound") or imp.get("lower_bound") or ""
            hi = imp.get("upperBound") or imp.get("upper_bound") or ""
            imp_str = f"{lo}–{hi}" if (lo or hi) else ""
        else:
            imp_str = str(imp) if imp else ""
 
        baixo_volume = bool(
            item.get("isLowVolumeImpressions")
            or item.get("low_volume")
            or item.get("low_volume_impressions")
            or (isinstance(imp, dict) and imp.get("lowerBound") == "<100")
            or imp_str == "<100"
        )
 
        start_raw = (
            item.get("startDate")
            or item.get("ad_delivery_start_time")
            or item.get("start_date")
            or ""
        )
        start_fmt = _dias_ativo(str(start_raw)) if start_raw else ""
 
        snap_url = (item.get("adSnapshotURL")
                    or item.get("ad_snapshot_url")
                    or (f"https://www.facebook.com/ads/library/?id={ad_id}" if ad_id else ""))
 
        images_b64 = []
        if images:
            b64 = _url_para_base64(images[0])
            images_b64.append(b64 if b64 else images[0])
            images_b64.extend(images[1:3])
 
        video_thumb_url = _extract_video_thumbnail(item) if has_video else ""
        video_thumb_b64 = _url_para_base64(video_thumb_url) if video_thumb_url else ""
 
        return {
            "id":                  ad_id,
            "page_name":           page_name,
            "page_id":             page_id,
            "page_profile_picture": page_profile_picture,
            "body":                body_c,
            "body_raw":            copy["body"],
            "title":               title_c,
            "description":         desc_c,
            "cta":                 copy["cta"],
            "caption":             copy["caption"],
            "images":              images,
            "images_b64":          images_b64,
            "videos":              videos,
            "video_thumb":         video_thumb_b64 or video_thumb_url,
            "snapshot_url":        snap_url,
            "data_inicio":         start_fmt,
            "data_raw":            str(start_raw),
            "impressoes":          imp_str,
            "baixo_volume":        baixo_volume,
            "plataformas":         plats,
            "formato":             fmt,
            "is_dynamic":          is_dyn,
        }
 
    def _apify_run_sync(search_term: str, limit: int = 100) -> tuple:
        api_token = st.secrets.get("APIFY_TOKEN", "")
        if not api_token:
            return [], [], "APIFY_TOKEN não configurada nos secrets."
 
        run_url = (
            f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs"
            f"?token={api_token}"
        )
 
        import urllib.parse
        search_term_stripped = search_term.strip()
 
        if search_term_stripped.isdigit():
            ad_library_url = (
                f"https://www.facebook.com/ads/library/"
                f"?active_status=active&ad_type=all&country=BR"
                f"&is_targeted_country=false&media_type=all"
                f"&search_type=page&sort_data[direction]=desc"
                f"&sort_data[mode]=total_impressions"
                f"&view_all_page_id={search_term_stripped}"
            )
        else:
            query_encoded = urllib.parse.quote(search_term_stripped)
            ad_library_url = (
                f"https://www.facebook.com/ads/library/"
                f"?active_status=active&ad_type=all&country=BR"
                f"&is_targeted_country=false&media_type=all"
                f"&search_type=page&sort_data[direction]=desc"
                f"&sort_data[mode]=total_impressions"
                f"&q={query_encoded}"
            )
 
        payload = {
            "urls": [{"url": ad_library_url}],
            "count": limit,
            "scrapeAdDetails": False,
            "scrapePageAds.activeStatus": "active",
            "scrapePageAds.countryCode": "BR",
            "scrapePageAds.sortBy": "impressions_desc",
        }
 
        try:
            r_start = requests.post(run_url, json=payload, timeout=30)
            r_start.raise_for_status()
            run_data = r_start.json()
        except Exception as e:
            return [], [], f"Erro ao iniciar run Apify: {e}"
 
        run_id     = run_data.get("data", {}).get("id") or run_data.get("id")
        dataset_id = run_data.get("data", {}).get("defaultDatasetId") or run_data.get("defaultDatasetId")
 
        if not run_id:
            return [], [], f"Apify não retornou run ID. Resposta: {run_data}"
 
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_token}"
        deadline   = _time.time() + 180
        status     = "RUNNING"
        while _time.time() < deadline:
            try:
                r_st   = requests.get(status_url, timeout=15)
                jdata  = r_st.json().get("data", {})
                status = jdata.get("status", "RUNNING")
                if not dataset_id:
                    dataset_id = jdata.get("defaultDatasetId") or dataset_id
            except Exception:
                pass
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
            _time.sleep(5)
 
        if status != "SUCCEEDED":
            return [], [], f"Run Apify terminou com status: {status}"
 
        if not dataset_id:
            return [], [], "Apify não retornou dataset ID."
 
        items_url = (
            f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            f"?token={api_token}&limit={limit}&clean=true"
        )
        try:
            r_items = requests.get(items_url, timeout=30)
            r_items.raise_for_status()
            raw_items = r_items.json()
        except Exception as e:
            return [], [], f"Erro ao ler dataset Apify: {e}"
 
        if not isinstance(raw_items, list):
            raw_items = raw_items.get("items", []) if isinstance(raw_items, dict) else []
 
        if not raw_items:
            return [], [], None
 
        ads_normalizados = [_normalizar_item_apify(item) for item in raw_items]
        return ads_normalizados, raw_items[:3], None
 
    def buscar_ads_apify(query: str, limit: int = 100) -> tuple:
        return _apify_run_sync(query.strip(), limit=limit)
 
    def executar_busca(empresas: list, query_values: dict, forcar: bool = False):
        erros  = {}
        novos  = {}
        cache_atual = dict(st.session_state.ads_cache or {})
 
        with st.status("Buscando anúncios...", expanded=True) as status:
            for e in empresas:
                ck = e["nome"]
 
                entrada_cache = cache_atual.get(ck, {})
                if not forcar and entrada_cache and cache_esta_fresco(entrada_cache.get("ts", "")):
                    st.write(f"✅ **{ck}** — usando cache ({entrada_cache.get('ts','')}, {len(entrada_cache.get('data',[]))} anúncios)")
                    continue
 
                if e["tipo"] == "minha":
                    ads_id_salvo = st.session_state.dados["minha_empresa"].get("ads_id", "").strip()
                else:
                    ads_id_salvo = st.session_state.dados["concorrentes"][e["idx"]].get("ads_id", "").strip()
 
                query = ads_id_salvo or query_values.get(ck, "").strip()
 
                if not query:
                    continue
 
                label = f"page_id: {query}" if query.isdigit() else f"keyword: {query}"
                st.write(f"Buscando **{ck}** ({label})...")
                ads, raw, erro = buscar_ads_apify(query)
                if erro:
                    erros[ck] = erro
                    st.write(f"❌ {erro}")
                else:
                    novos[ck] = {
                        "data":  ads,
                        "ts":    _dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "nome":  ck,
                        "query": query,
                    }
                    st.write(f"✅ {len(ads)} anúncios encontrados")
            status.update(label="✅ Busca concluída!", state="complete")
 
        cache_atual.update(novos)
        st.session_state.ads_cache = cache_atual
        st.session_state.ads_erro  = erros
        salvar_cache_ads(cache_atual)
        st.rerun()
 
    # ── Session state ─────────────────────────────────────────────────
    if "ads_cache" not in st.session_state:
        st.session_state.ads_cache = carregar_cache_ads()
    if "ads_erro" not in st.session_state:
        st.session_state.ads_erro = {}
    if "ads_onboarding_empresa" not in st.session_state:
        st.session_state.ads_onboarding_empresa = None
    if "ads_onboarding_paginas" not in st.session_state:
        st.session_state.ads_onboarding_paginas = []
    if "ads_onboarding_termo" not in st.session_state:
        st.session_state.ads_onboarding_termo = ""
    if "ads_editando_empresa" not in st.session_state:
        st.session_state.ads_editando_empresa = None
 
    def safe_key(s):
        return re.sub(r"[^a-zA-Z0-9_]", "_", s)
 
    todas_empresas = []
    if emp.get("nome"):
        todas_empresas.append({"nome": emp["nome"], "tipo": "minha", "idx": 0})
    for i, c in enumerate(concs):
        if c.get("nome"):
            todas_empresas.append({"nome": c["nome"], "tipo": "concorrente", "idx": i})
 
    def empresa_tem_ads_id(e: dict) -> bool:
        if e["tipo"] == "minha":
            return bool(emp.get("ads_id", "").strip())
        else:
            cd = concs[e["idx"]]
            return bool(cd.get("ads_id", "").strip())
 
    def salvar_ads_id(e: dict, ads_id: str, page_pic: str = ""):
        if e["tipo"] == "minha":
            st.session_state.dados["minha_empresa"]["ads_id"] = ads_id
            if page_pic:
                st.session_state.dados["minha_empresa"]["ads_page_pic"] = page_pic
        else:
            st.session_state.dados["concorrentes"][e["idx"]]["ads_id"] = ads_id
            if page_pic:
                st.session_state.dados["concorrentes"][e["idx"]]["ads_page_pic"] = page_pic
        salvar_dados_usuario(st.session_state.user.id)
 
    def buscar_paginas_facebook(termo: str) -> list:
        ads, _, erro = _apify_run_sync(termo, limit=20)
        if erro or not ads:
            return []
        paginas = {}
        for ad in ads:
            pid  = ad.get("page_id", "") or ""
            nome = ad.get("page_name", "") or ""
            pic  = ad.get("page_profile_picture", "") or ""
            if nome and nome not in paginas:
                paginas[nome] = {"nome": nome, "page_id": pid, "total_ads": 0, "profile_picture": pic}
            if nome in paginas:
                paginas[nome]["total_ads"] += 1
                if not paginas[nome]["profile_picture"] and pic:
                    paginas[nome]["profile_picture"] = pic
        return sorted(paginas.values(), key=lambda x: x["total_ads"], reverse=True)
 
    def _avatar_html_empresa(e: dict, size: int = 42) -> str:
        is_minha = e["tipo"] == "minha"
        cor = get_minha_empresa_color() if is_minha else get_concorrente_color(e["idx"])
        nome = e["nome"]
        av = gerar_avatar(nome)
 
        if is_minha:
            pic = st.session_state.dados["minha_empresa"].get("ads_page_pic", "") or ""
        else:
            pic = st.session_state.dados["concorrentes"][e["idx"]].get("ads_page_pic", "") or ""
 
        if not pic:
            cache_entry = st.session_state.ads_cache.get(nome, {})
            ads_data = cache_entry.get("data", [])
            for ad in ads_data:
                p = ad.get("page_profile_picture", "") or ""
                if p and p.startswith("http"):
                    pic = p
                    break
 
        if pic:
            return (
                f'<div style="width:{size}px;height:{size}px;border-radius:50%;overflow:hidden;'
                f'flex-shrink:0;border:2px solid #e5e7eb;">'
                f'<img src="{pic}" style="width:100%;height:100%;object-fit:cover;display:block" '
                f'onerror="this.parentElement.style.background=\'{cor}\';'
                f'this.parentElement.innerHTML=\'<div style=&quot;display:flex;align-items:center;'
                f'justify-content:center;width:100%;height:100%;font-size:{int(size*0.35)}px;'
                f'font-weight:700;color:#fff&quot;>{av}</div>\'" />'
                f'</div>'
            )
        return (
            f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{cor};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:{int(size*0.35)}px;font-weight:700;color:#fff;flex-shrink:0">{av}</div>'
        )
 
    # ── Cabeçalho ────────────────────────────────────────────────────
    h1_col, h2_col = st.columns([7, 3])
    with h1_col:
        components.html("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@font-face {
    font-family: 'Animo';
    src: url('https://raw.githubusercontent.com/thiagomktsantos/marketylics/63946b2d891db6b45cc75a45550b7aa5fe67244a/utils/Animo-font.otf') format('opentype');
}
* { margin:0; padding:0; box-sizing:border-box; }
html, body { background:transparent; overflow:hidden; }
.titulo { font-family:'Animo','DM Sans',sans-serif; font-size:32px; font-weight:700; color:#1a2e4a; text-transform:uppercase; margin:0 0 6px 0; letter-spacing:0.5px; }
.sub    { font-family:'DM Sans',sans-serif; font-size:14px; color:#6b7280; }
</style>
<div class="titulo">Biblioteca de Ads</div>
<div class="sub">Criativos, copies e formatos dos anúncios dos seus concorrentes.</div>
""", height=65)
 
    with h2_col:
        gerar_btn_ads = st.button(
            "🔍 Buscar / Atualizar Anúncios",
            type="primary",
            use_container_width=True,
            key="ads_buscar_topo_btn",
        )
        if st.session_state.ads_cache:
            _tss = [v.get("ts", "") for v in st.session_state.ads_cache.values() if v.get("ts")]
            if _tss:
                _ts_antigo = min(_tss)
                st.markdown(
                    f"<div style='font-size:13px;color:#6b7280;text-align:center;margin-top:-8px'>"
                    f"🕒 Última busca: <b>{_ts_antigo}</b></div>",
                    unsafe_allow_html=True,
                )
 
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 16px 0'/>", unsafe_allow_html=True)
 
    if not todas_empresas:
        st.info("Cadastre sua empresa e concorrentes para usar esta funcionalidade.")
        st.stop()
 
    if not st.secrets.get("APIFY_TOKEN", ""):
        st.warning("Configure `APIFY_TOKEN` no secrets.toml para usar esta funcionalidade.")
 
    empresas_sem_config   = [e for e in todas_empresas if not empresa_tem_ads_id(e)]
    empresas_configuradas = [e for e in todas_empresas if empresa_tem_ads_id(e)]
 
    # ── Render seleção de páginas (resultado da busca) ────────────────
    def _render_paginas_resultado(e, sk, ck):
        paginas = st.session_state.ads_onboarding_paginas
        termo_buscado = st.session_state.ads_onboarding_termo
        if not paginas:
            st.warning(f"Nenhuma página encontrada para «{termo_buscado}». Tente um nome diferente.")
            return
        st.markdown(
            "<div style='font-size:13px;font-weight:600;color:#374151;margin:8px 0 10px 0'>"
            "Páginas encontradas — selecione a correta:</div>",
            unsafe_allow_html=True,
        )
        n_pags = min(len(paginas), 6)
        cols_pag = st.columns(min(n_pags, 3))
        for ip, pag in enumerate(paginas[:6]):
            with cols_pag[ip % 3]:
                pag_av  = gerar_avatar(pag["nome"])
                pag_cor = AVATAR_COLORS[ip % len(AVATAR_COLORS)]
                pag_pic = pag.get("profile_picture", "")
                page_id_display = f" · ID: {pag['page_id']}" if pag.get("page_id") else ""
 
                if pag_pic and pag_pic.startswith("http"):
                    avatar_cell = (
                        f'<div style="width:44px;height:44px;border-radius:50%;overflow:hidden;'
                        f'flex-shrink:0;border:2px solid #e5e7eb">'
                        f'<img src="{pag_pic}" style="width:100%;height:100%;object-fit:cover;display:block" '
                        f'onerror="this.parentElement.style.background=\'{pag_cor}\';'
                        f'this.parentElement.innerHTML=\'<div style=&quot;display:flex;align-items:center;'
                        f'justify-content:center;width:100%;height:100%;font-size:15px;font-weight:700;'
                        f'color:#fff&quot;>{pag_av}</div>\'" /></div>'
                    )
                else:
                    avatar_cell = (
                        f'<div style="width:44px;height:44px;border-radius:50%;background:{pag_cor};'
                        f'display:flex;align-items:center;justify-content:center;'
                        f'font-size:15px;font-weight:700;color:#fff;flex-shrink:0">{pag_av}</div>'
                    )
 
                st.markdown(
                    f"<div style='background:#f9fafb;border:1.5px solid #e2e8f0;border-radius:12px;"
                    f"padding:14px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px'>"
                    f"{avatar_cell}"
                    f"<div style='flex:1;min-width:0'>"
                    f"<div style='font-size:14px;font-weight:700;color:#111827;white-space:nowrap;"
                    f"overflow:hidden;text-overflow:ellipsis'>{pag['nome']}</div>"
                    f"<div style='font-size:12px;color:#6b7280;margin-top:2px'>📢 {pag['total_ads']} anúncio(s){page_id_display}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                id_para_salvar = pag.get("page_id") or pag["nome"]
                pic_para_salvar = pag.get("profile_picture", "")
 
                if st.button(
                    f"✅ Usar esta",
                    key=f"sel_pag_{sk}_{ip}",
                    use_container_width=True,
                    type="primary",
                ):
                    salvar_ads_id(e, id_para_salvar, page_pic=pic_para_salvar)
                    st.session_state.ads_onboarding_empresa = None
                    st.session_state.ads_onboarding_paginas = []
                    st.session_state.ads_editando_empresa = None
                    st.toast(f"✅ Página «{pag['nome']}» configurada! ID: {id_para_salvar}", icon="✅")
                    st.rerun()
 
        with st.expander("Não encontrou? Digite manualmente (nome ou ID numérico)"):
            col_m1, col_m2 = st.columns([4, 2])
            with col_m1:
                manual = st.text_input(
                    "Nome exato ou ID numérico",
                    placeholder="Ex: Kedu Educação  ou  102803918240129",
                    key=f"_manual_{sk}",
                )
            with col_m2:
                st.markdown("<div style='height:28px'/>", unsafe_allow_html=True)
                if st.button("💾 Salvar", key=f"btn_manual_{sk}", use_container_width=True):
                    if manual.strip():
                        salvar_ads_id(e, manual.strip())
                        st.session_state.ads_onboarding_empresa = None
                        st.session_state.ads_onboarding_paginas = []
                        st.session_state.ads_editando_empresa = None
                        st.toast(f"✅ «{manual.strip()}» salvo!", icon="✅")
                        st.rerun()
 
    # ── Empresas configuradas ─────────────────────────────────────────
    if empresas_configuradas:
        st.markdown(
            "<div style='font-size:12px;font-weight:700;color:#9ca3af;text-transform:uppercase;"
            "letter-spacing:0.8px;margin-bottom:10px'>✅ Páginas configuradas</div>",
            unsafe_allow_html=True,
        )
 
        # CSS: esconde todos os trigger buttons fantasmas
        ghost_css = "\n".join([
            f".st-key-cfg_edit_trigger_{safe_key(e['nome'])}_{ci} {{ display: none !important; }}"
            for ci, e in enumerate(empresas_configuradas)
        ])
        st.markdown(f"<style>{ghost_css}</style>", unsafe_allow_html=True)
 
        # Registrar trigger buttons ANTES de renderizar os cards
        edit_triggers = {}
        for ci, e in enumerate(empresas_configuradas):
            sk = safe_key(e["nome"])
            triggered = st.button(
                f"cfg_edit_trigger_{sk}_{ci}",
                key=f"cfg_edit_trigger_{sk}_{ci}",
            )
            edit_triggers[ci] = triggered
 
        # Processar cliques de "editar"
        for ci, e in enumerate(empresas_configuradas):
            if edit_triggers[ci]:
                st.session_state.ads_editando_empresa = e["nome"]
                st.session_state.ads_onboarding_empresa = None
                st.session_state.ads_onboarding_paginas = []
                st.rerun()
 
        cfg_cols = st.columns(2)
        for ci, e in enumerate(empresas_configuradas):
            ck       = e["nome"]
            sk       = safe_key(ck)
            is_minha = e["tipo"] == "minha"
            badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
            badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
            badge_txt = "#1d4ed8" if is_minha else "#6b7280"
            badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
            ads_id_atual = emp.get("ads_id", "") if is_minha else concs[e["idx"]].get("ads_id", "")
            is_editing = (st.session_state.ads_editando_empresa == ck)
            avatar_html = _avatar_html_empresa(e, size=42)
            edit_trigger_key = f"cfg_edit_trigger_{sk}_{ci}"
 
            with cfg_cols[ci % 2]:
                if not is_editing:
                    # ── Card normal (só visualização) ──────────────────
                    components.html(f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background:transparent; font-family:'DM Sans',sans-serif; overflow:hidden; -webkit-font-smoothing:antialiased; }}
body {{ padding-bottom:4px; }}
.card {{ background:#fff; border:1px solid #e5e7eb; border-radius:14px; overflow:hidden; }}
.card-body {{ display:flex; align-items:center; gap:14px; padding:16px 20px; border-bottom:1px solid #f3f4f6; }}
.info {{ flex:1; min-width:0; }}
.nome {{ font-size:16px; font-weight:700; color:#111827; margin-bottom:4px; }}
.badges {{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; }}
.badge {{ padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600;
    background:{badge_bg}; color:{badge_txt}; border:1px solid {badge_brd}; }}
.badge-id {{ background:#dcfce7; color:#15803d; border:1px solid #86efac;
    padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:160px; }}
.edit-btn {{ width:100%; padding:10px 0; background:#fff;
    border:none; border-top:1px solid #f3f4f6;
    font-size:14px; font-weight:600; color:#6b7280;
    cursor:pointer; font-family:'DM Sans',sans-serif;
    display:flex; align-items:center; justify-content:center; gap:8px;
    transition:all 0.12s ease; }}
.edit-btn:hover {{ background:#f9fafb; color:#111827; }}
</style>
<div class="card">
    <div class="card-body">
        {avatar_html}
        <div class="info">
            <div class="nome">{ck}</div>
            <div class="badges">
                <span class="badge">{badge_lbl}</span>
                <span class="badge-id">✅ {ads_id_atual}</span>
            </div>
        </div>
    </div>
    <button class="edit-btn" onclick="triggerBtn('{edit_trigger_key}')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        Editar página
    </button>
</div>
<script>
function triggerBtn(key) {{
    var btns = window.parent.document.querySelectorAll('button');
    for (var b of btns) {{ if (b.innerText.trim() === key) {{ b.click(); return; }} }}
}}
function ajustarAltura() {{
    var h = document.body.scrollHeight;
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{ if (iframes[i].contentWindow === window) {{
            iframes[i].style.height = (h + 8) + 'px'; break;
        }} }} catch(err) {{}}
    }}
}}
if (window.ResizeObserver) new ResizeObserver(ajustarAltura).observe(document.body);
setTimeout(ajustarAltura, 100);
</script>
""", height=118, scrolling=False)
 
                else:
                    # ── Card em modo edição ──
                    novo_id_key  = f"_inline_edit_{sk}_{ci}"
                    buscar_key   = f"buscar_cfg_{sk}_{ci}"
                    salvar_key   = f"salvar_cfg_{sk}_{ci}"
                    cancel_key   = f"cancel_edit_{sk}_{ci}"

                    # Card superior — identificação
                    st.markdown(f"""
                    <div style='background:#fff;border:1.5px solid #3a9fd6;border-radius:14px;
                                overflow:hidden;margin-bottom:4px'>
                        <div style='display:flex;align-items:center;gap:14px;padding:16px 20px'>
                            {avatar_html}
                            <div style='flex:1;min-width:0'>
                                <div style='font-size:16px;font-weight:700;color:#111827'>{ck}</div>
                                <span style='background:{badge_bg};color:{badge_txt};
                                             border:1px solid {badge_brd};padding:2px 10px;
                                             border-radius:20px;font-size:11px;font-weight:600'>
                                    {badge_lbl}
                                </span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Card inferior — edição
                    st.markdown(f"""
                    <style>
                    .st-key-inline_edit_{sk}_{ci} [data-testid="stVerticalBlockBorderWrapper"],
                    .st-key-inline_edit_{sk}_{ci} [data-testid="stVerticalBlock"],
                    .st-key-inline_edit_{sk}_{ci} .stElementContainer,
                    .st-key-inline_edit_{sk}_{ci} .stElementContainer > div,
                    .st-key-inline_edit_{sk}_{ci} div[data-testid="stTextInput"],
                    .st-key-inline_edit_{sk}_{ci} div[data-testid="stTextInput"] > div,
                    .st-key-inline_edit_{sk}_{ci} div[data-testid="stTextInput"] input {{
                        background-color: #ffffff !important;
                        background: #ffffff !important;
                    }}
                    .st-key-inline_edit_{sk}_{ci} [data-testid="stVerticalBlockBorderWrapper"] {{
                        border: 1.5px solid #e5e7eb !important;
                        border-radius: 14px !important;
                        padding: 16px 20px !important;
                    }}
                    .st-key-inline_edit_{sk}_{ci} button[kind="primary"] {{
                        background: #0780c0 !important;
                        color: #ffffff !important;
                        border: none !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)

                    with st.container(border=True, key=f"inline_edit_{sk}_{ci}"):
                        st.markdown(
                            "<div style='font-size:11px;font-weight:700;color:#9ca3af;"
                            "text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 8px 0'>"
                            "Nome ou ID numérico da página</div>",
                            unsafe_allow_html=True,
                        )

                        novo_id = st.text_input(
                            "ID ou nome",
                            value=ads_id_atual,
                            key=novo_id_key,
                            label_visibility="collapsed",
                            placeholder="Ex: Nome da Página  ou  102803918240129",
                        )
                        col_b, col_s, col_c = st.columns([2, 2, 1])
                        with col_b:
                            buscar_clicked = st.button("Buscar páginas", key=buscar_key,
                                                       use_container_width=True, type="primary")
                        with col_s:
                            salvar_clicked = st.button("Salvar Página", key=salvar_key,
                                                       use_container_width=True)
                        with col_c:
                            cancel_clicked = st.button("Cancelar", key=cancel_key,
                                                       use_container_width=True)

                    if buscar_clicked and novo_id.strip():
                        st.session_state.ads_onboarding_empresa = ck
                        st.session_state.ads_onboarding_termo   = novo_id.strip()
                        with st.spinner(f"Buscando «{novo_id.strip()}»…"):
                            paginas = buscar_paginas_facebook(novo_id.strip())
                        st.session_state.ads_onboarding_paginas = paginas
                        st.rerun()

                    if salvar_clicked and novo_id.strip():
                        salvar_ads_id(e, novo_id.strip())
                        st.session_state.ads_editando_empresa    = None
                        st.session_state.ads_onboarding_empresa  = None
                        st.session_state.ads_onboarding_paginas  = []
                        st.toast(f"✅ Salvo: {novo_id.strip()}", icon="✅")
                        st.rerun()

                    if cancel_clicked:
                        st.session_state.ads_editando_empresa    = None
                        st.session_state.ads_onboarding_empresa  = None
                        st.session_state.ads_onboarding_paginas  = []
                        st.rerun()

                    if (st.session_state.ads_onboarding_empresa == ck
                            and st.session_state.ads_onboarding_paginas):
                        _render_paginas_resultado(e, sk, ck)
 
    # ── Empresas sem configuração ─────────────────────────────────────
    if empresas_sem_config:
        st.markdown(
            "<div style='font-size:12px;font-weight:700;color:#9ca3af;text-transform:uppercase;"
            "letter-spacing:0.8px;margin:16px 0 10px 0'>⚠️ Páginas não configuradas</div>",
            unsafe_allow_html=True,
        )
        for e in empresas_sem_config:
            ck       = e["nome"]
            sk       = safe_key(ck)
            is_minha = e["tipo"] == "minha"
            cor      = get_minha_empresa_color() if is_minha else get_concorrente_color(e["idx"])
            av       = gerar_avatar(ck)
            badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
            badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
            badge_txt = "#1d4ed8" if is_minha else "#6b7280"
            badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
 
            st.markdown(f"""
            <div style='background:#fff;border:1px solid #e5e7eb;border-radius:14px;
                        padding:14px 18px;display:flex;align-items:center;gap:12px;
                        margin-bottom:10px'>
                <div style='width:42px;height:42px;border-radius:50%;background:{cor};
                            display:flex;align-items:center;justify-content:center;
                            font-size:14px;font-weight:700;color:#fff;flex-shrink:0'>{av}</div>
                <div>
                    <div style='font-size:15px;font-weight:700;color:#111827'>{ck}</div>
                    <div style='display:flex;align-items:center;gap:6px;margin-top:4px;flex-wrap:wrap'>
                        <span style='background:{badge_bg};color:{badge_txt};
                                     border:1px solid {badge_brd};padding:2px 8px;
                                     border-radius:20px;font-size:11px;font-weight:600'>{badge_lbl}</span>
                        <span style='background:#fef9c3;color:#854d0e;border:1px solid #fde68a;
                                     padding:2px 8px;border-radius:20px;font-size:11px;
                                     font-weight:600'>⚠️ Não configurado</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
 
            col_inp, col_btn_b, col_btn_s = st.columns([4, 2, 2])
            with col_inp:
                termo_input = st.text_input(
                    "Nome ou ID da página",
                    value=ck,
                    placeholder=f"Ex: {ck}  ou  102803918240129",
                    key=f"_termo_uncfg_{sk}",
                    label_visibility="collapsed",
                )
            with col_btn_b:
                if st.button("🔍 Buscar", key=f"buscar_uncfg_{sk}", use_container_width=True, type="primary"):
                    if termo_input.strip():
                        st.session_state.ads_onboarding_empresa = ck
                        st.session_state.ads_onboarding_termo   = termo_input.strip()
                        with st.spinner(f"Buscando «{termo_input.strip()}»…"):
                            paginas = buscar_paginas_facebook(termo_input.strip())
                        st.session_state.ads_onboarding_paginas = paginas
                        st.rerun()
            with col_btn_s:
                if st.button("💾 Salvar ID", key=f"salvar_uncfg_{sk}", use_container_width=True):
                    if termo_input.strip():
                        salvar_ads_id(e, termo_input.strip())
                        st.session_state.ads_onboarding_empresa = None
                        st.session_state.ads_onboarding_paginas = []
                        st.toast(f"✅ Salvo!", icon="✅")
                        st.rerun()
 
            if (st.session_state.ads_onboarding_empresa == ck
                    and st.session_state.ads_onboarding_paginas is not None):
                if not st.session_state.ads_onboarding_paginas:
                    st.warning("Nenhuma página encontrada. Tente outro nome ou cole o ID numérico.")
                else:
                    _render_paginas_resultado(e, sk, ck)
 
            st.markdown("<div style='height:4px'/>", unsafe_allow_html=True)
 
    if not empresas_configuradas:
        st.info("Configure pelo menos uma empresa acima para buscar anúncios.")
        st.stop()
 
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0 20px 0'/>", unsafe_allow_html=True)
 
    # ── Controles de busca ────────────────────────────────────────────
    query_values = {}
    for e in empresas_configuradas:
        ck = e["nome"]
        ads_id_salvo = emp.get("ads_id","") if e["tipo"]=="minha" else concs[e["idx"]].get("ads_id","")
        query_values[ck] = ads_id_salvo
 
    bcol1, bcol2, bcol3 = st.columns([3, 2, 2])
    with bcol1:
        buscar_inline = st.button(
            "🔍 Buscar / Atualizar",
            use_container_width=True, type="primary",
            key="ads_buscar_inline_btn",
        )
    with bcol2:
        forcar_atualizacao = st.button(
            "🔄 Forçar atualização",
            use_container_width=True,
            key="ads_forcar_btn",
            help="Ignora o cache e busca tudo novamente na API",
        )
    with bcol3:
        limpar_cache = st.button("🗑️ Limpar Cache", use_container_width=True, key="ads_limpar_cache_btn")
 
    if limpar_cache:
        st.session_state.ads_cache = {}
        st.session_state.ads_erro  = {}
        salvar_cache_ads({})
        st.toast("Cache limpo!", icon="🗑️")
        st.rerun()
 
    if gerar_btn_ads or buscar_inline:
        if not query_values:
            st.warning("Configure pelo menos uma empresa antes de buscar.")
        else:
            executar_busca(
                [e for e in todas_empresas if empresa_tem_ads_id(e)],
                query_values,
                forcar=False,
            )
 
    if forcar_atualizacao:
        if not query_values:
            st.warning("Configure pelo menos uma empresa antes de buscar.")
        else:
            executar_busca(
                [e for e in todas_empresas if empresa_tem_ads_id(e)],
                query_values,
                forcar=True,
            )
 
    empresas_com_dados = [
        e for e in todas_empresas
        if e["nome"] in st.session_state.ads_cache or e["nome"] in st.session_state.ads_erro
    ]
 
    if not empresas_com_dados:
        st.markdown("""
        <div style='background:#fff;border:1px dashed #d1d5db;border-radius:14px;
                    padding:48px 32px;text-align:center;margin-top:8px'>
            <div style='font-size:32px;margin-bottom:12px'>📢</div>
            <div style='font-size:16px;font-weight:600;color:#374151;margin-bottom:6px'>Nenhum dado carregado ainda</div>
            <div style='font-size:14px;color:#9ca3af'>Configure as páginas e clique em <b>Buscar / Atualizar</b>.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
 
    st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)
    abas_ads = st.tabs([e["nome"] for e in empresas_com_dados])
 
    def _plat_svg_js(uid: str) -> str:
        return f"""
(function(){{
    var plats={{}};
    try {{ plats = __PLATS_{uid}__; }} catch(e) {{ return; }}
    var C = '#9ca3af';
    var SVGS = {{
        "facebook": '<svg width="14" height="14" viewBox="0 0 24 24" fill="'+C+'"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/></svg>',
        "instagram": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="2" y="2" width="20" height="20" rx="5" fill="'+C+'"/><circle cx="12" cy="12" r="4.5" stroke="white" stroke-width="1.8" fill="none"/><circle cx="17.5" cy="6.5" r="1.2" fill="white"/></svg>',
        "messenger": '<svg width="16" height="16" viewBox="0 0 24 24" fill="'+C+'"><path d="M12 0C5.373 0 0 4.975 0 11.111c0 3.497 1.745 6.616 4.472 8.652V24l4.086-2.242c1.09.301 2.246.464 3.442.464 6.627 0 12-4.975 12-11.111S18.627 0 12 0zm1.191 14.963l-3.055-3.26-5.963 3.26L10.732 8.4l3.131 3.259L19.752 8.4l-6.561 6.563z"/></svg>',
        "whatsapp":  '<svg width="16" height="16" viewBox="0 0 24 24" fill="'+C+'"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>',
        "audience_network": '<svg width="16" height="16" viewBox="0 0 24 24" fill="'+C+'"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg>',
        "threads": '<svg width="16" height="16" viewBox="0 0 192 192" fill="'+C+'"><path d="M141.537 88.988a66.667 66.667 0 00-2.518-1.143c-1.482-27.307-16.403-42.94-41.457-43.1h-.34c-14.986 0-27.449 6.396-35.12 18.036l13.779 9.452c5.73-8.695 14.724-10.548 21.348-10.548h.229c8.249.053 14.474 2.452 18.503 7.129 2.932 3.405 4.893 8.111 5.864 14.05-7.314-1.243-15.224-1.626-23.68-1.14-23.82 1.371-39.134 15.264-38.105 34.568.522 9.792 5.4 18.216 13.735 23.719 7.047 4.652 16.124 6.927 25.557 6.412 12.458-.683 22.231-5.436 29.049-14.127 5.178-6.6 8.453-15.153 9.899-25.93 5.937 3.583 10.337 8.298 12.767 13.966 4.132 9.635 4.373 25.468-8.546 38.376-11.319 11.308-24.925 16.2-45.488 16.351-22.809-.169-40.06-7.484-51.275-21.742C35.236 139.966 29.808 120.682 29.605 96c.203-24.682 5.63-43.966 16.133-57.317C56.954 24.425 74.204 17.11 97.013 16.94c22.975.17 40.526 7.52 52.171 21.847 5.71 7.026 10.015 15.86 12.853 26.162l16.147-4.308c-3.44-12.68-8.853-23.606-16.219-32.668C147.036 9.607 125.202.195 97.07 0h-.113C68.882.195 47.292 9.642 32.788 28.08 19.882 44.485 13.224 67.315 13.001 96v.027c.224 28.686 6.882 51.516 19.788 67.92C47.292 182.358 68.882 191.805 96.957 192h.114c24.92-.173 42.433-6.695 56.854-21.101 18.941-18.925 18.352-42.444 12.139-56.924-4.51-10.507-13.192-19.01-24.527-24.987zm-45.458 43.051c-10.443.588-21.287-4.098-26.698-11.76-3.28-4.626-3.27-9.498.028-13.062 3.853-4.194 10.08-6.386 17.537-6.386.799 0 1.609.024 2.427.074 9.335.539 16.788 3.712 20.91 8.931 2.653 3.367 3.604 7.573 2.733 12.094-1.765 9.151-10.228 9.867-16.937 10.109z"/></svg>'
    }};
    var el = document.getElementById('plat_icons_{uid}');
    if (!el) return;
    if (!plats || plats.length === 0) {{ el.innerHTML='<span style="color:#9ca3af;font-size:12px">—</span>'; return; }}
    el.innerHTML = plats.map(function(p) {{
        var key = p.toLowerCase().replace(' ','_').replace('-','_');
        var svg = SVGS[key] || '';
        return '<span class="plat-badge" title="'+p+'">'+(svg||('<span style="font-size:10px;color:#9ca3af">'+p[0].toUpperCase()+'</span>'))+'</span>';
    }}).join('');
}})();
"""
 
    def _copy_block_html(text: str, uid: str, max_chars: int = 120) -> str:
        if not text:
            return ""
        text = text.strip()
        safe_full = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if len(text) <= max_chars:
            display = safe_full.replace("\n", "<br>")
            return f'<div class="copy-body">{display}</div>'
        short = safe_full[:max_chars].replace("\n", " ")
        rest  = safe_full[max_chars:].replace("\n", "<br>")
        return (
            f'<div class="copy-body">'
            f'{short}'
            f'<span id="cm_{uid}" style="display:none">{rest}</span>'
            f'<button id="cb_{uid}" '
            f'onclick="var m=document.getElementById(\'cm_{uid}\');'
            f'var b=document.getElementById(\'cb_{uid}\');'
            f'if(m.style.display===\'none\'){{m.style.display=\'inline\';b.textContent=\'ver menos\'}}'
            f'else{{m.style.display=\'none\';b.textContent=\'ver mais\'}}" '
            f'style="background:none;border:none;color:#3a9fd6;font-weight:700;'
            f'font-size:13px;cursor:pointer;padding:0;margin-left:4px;'
            f'font-family:DM Sans,sans-serif;white-space:nowrap;vertical-align:baseline">'
            f'ver mais</button>'
            f'</div>'
        )
 
    def render_ads_empresa(emp_item):
        ck       = emp_item["nome"]
        nome     = emp_item["nome"]
        is_minha = emp_item["tipo"] == "minha"
        cor_av   = get_minha_empresa_color() if is_minha else get_concorrente_color(emp_item["idx"])
        avatar   = gerar_avatar(nome)
 
        if emp_item["tipo"] == "minha":
            configured_page = emp.get("ads_id","").strip()
        else:
            configured_page = concs[emp_item["idx"]].get("ads_id","").strip()
 
        if ck in st.session_state.ads_erro:
            st.error(f"Erro: {st.session_state.ads_erro[ck]}")
            return
 
        cache_entry = st.session_state.ads_cache.get(ck)
        if not cache_entry:
            st.info("Sem dados. Configure a página e clique em Buscar.")
            return
 
        ads_list_raw = cache_entry["data"]
        ts           = cache_entry["ts"]
        query        = cache_entry.get("query","")
        fresco_aba   = cache_esta_fresco(ts)
 
        if configured_page:
            if configured_page.isdigit():
                filtered = [a for a in ads_list_raw if str(a.get("page_id","")).strip() == configured_page]
                ads_list = filtered if filtered else ads_list_raw
            else:
                configured_lower = configured_page.lower()
                exact = [a for a in ads_list_raw if (a.get("page_name") or "").strip().lower() == configured_lower]
                if exact:
                    ads_list = exact
                else:
                    partial = [a for a in ads_list_raw
                               if configured_lower in (a.get("page_name") or "").strip().lower()
                               or (a.get("page_name") or "").strip().lower() in configured_lower]
                    ads_list = partial if partial else ads_list_raw
        else:
            ads_list = ads_list_raw
 
        if emp_item["tipo"] == "minha":
            page_pic_empresa = st.session_state.dados["minha_empresa"].get("ads_page_pic", "") or ""
        else:
            page_pic_empresa = st.session_state.dados["concorrentes"][emp_item["idx"]].get("ads_page_pic", "") or ""
 
        if not page_pic_empresa:
            for ad in ads_list:
                p = ad.get("page_profile_picture", "") or ""
                if p and p.startswith("http"):
                    page_pic_empresa = p
                    break
 
        if page_pic_empresa:
            avatar_empresa_html = (
                f'<div style="width:44px;height:44px;border-radius:50%;overflow:hidden;'
                f'flex-shrink:0;border:2px solid #e5e7eb;">'
                f'<img src="{page_pic_empresa}" style="width:100%;height:100%;object-fit:cover;display:block" '
                f'onerror="this.parentElement.style.background=\'{cor_av}\';'
                f'this.parentElement.innerHTML=\'<div style=&quot;display:flex;align-items:center;'
                f'justify-content:center;width:100%;height:100%;font-size:16px;font-weight:700;'
                f'color:#fff&quot;>{avatar}</div>\'" /></div>'
            )
        else:
            avatar_empresa_html = (
                f'<div style="width:44px;height:44px;border-radius:50%;background:{cor_av};'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:16px;font-weight:700;color:#fff;flex-shrink:0">{avatar}</div>'
            )
 
        badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
        badge_txt = "#1d4ed8" if is_minha else "#6b7280"
        badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
        badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
        cor_ts    = "#15803d" if fresco_aba else "#92400e"
        bg_ts     = "#f0fdf4" if fresco_aba else "#fffbeb"
        brd_ts    = "#86efac" if fresco_aba else "#fcd34d"
        ico_ts    = "✅"      if fresco_aba else "🕐"
 
        import urllib.parse as _urlparse
        if configured_page and configured_page.isdigit():
            lib_url = (
                f"https://www.facebook.com/ads/library/"
                f"?active_status=active&ad_type=all&country=BR"
                f"&is_targeted_country=false&media_type=all"
                f"&search_type=page&sort_data[direction]=desc"
                f"&sort_data[mode]=total_impressions"
                f"&view_all_page_id={configured_page}"
            )
        elif query:
            lib_url = (
                f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all"
                f"&country=BR&q={_urlparse.quote(query)}"
            )
        else:
            lib_url = ""
 
        page_display = configured_page if configured_page else "—"
 
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:14px;margin-bottom:20px;
                    padding:16px 20px;background:#fff;border:1px solid #e5e7eb;border-radius:12px'>
            {avatar_empresa_html}
            <div style='flex:1;min-width:0'>
                <div style='font-size:17px;font-weight:700;color:#111827'>{nome}</div>
                <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:4px'>
                    <span style='background:{badge_bg};color:{badge_txt};border:1px solid {badge_brd};
                                 padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>{badge_lbl}</span>
                    <span style='background:{bg_ts};color:{cor_ts};border:1px solid {brd_ts};
                                 padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>
                        {ico_ts} Cache: {ts}
                    </span>
                    <span style='background:#f0f9ff;color:#0369a1;border:1px solid #bae6fd;
                                 padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>
                        📄 {page_display}
                    </span>
                </div>
            </div>
            <div style='display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex-shrink:0'>
                <div style='text-align:right'>
                    <div style='font-size:28px;font-weight:800;color:#111827'>{len(ads_list)}</div>
                    <div style='font-size:12px;color:#9ca3af'>anúncios encontrados</div>
                </div>
                {f'<a href="{lib_url}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;background:#1877F2;color:#fff;padding:7px 14px;border-radius:8px;font-size:13px;font-weight:700;text-decoration:none;white-space:nowrap">🔗 Ver no Ad Library</a>' if lib_url else ''}
            </div>
        </div>""", unsafe_allow_html=True)
 
        if not ads_list:
            st.info("Nenhum anúncio encontrado. Verifique o ID/nome da página.")
            if lib_url:
                st.link_button("🔍 Verificar no Ad Library", lib_url)
            return
 
        fcol1, fcol2, fcol3 = st.columns([3, 2, 2])
        with fcol1:
            busca_texto = st.text_input(
                "Filtrar", placeholder="Pesquisar no copy…",
                key=f"ads_busca_{safe_key(ck)}", label_visibility="collapsed",
            )
        with fcol2:
            filtro_fmt = st.selectbox(
                "Formato",
                ["Todos"] + sorted(set(a["formato"] for a in ads_list)),
                key=f"ads_fmt_{safe_key(ck)}", label_visibility="collapsed",
            )
        with fcol3:
            plats_todas = sorted(set(p for a in ads_list for p in (a["plataformas"] or [])))
            filtro_plat = st.selectbox(
                "Plataforma",
                ["Todas"] + [p.capitalize() for p in plats_todas],
                key=f"ads_plat_{safe_key(ck)}", label_visibility="collapsed",
            )
 
        ads_f = ads_list
        if busca_texto:
            q     = busca_texto.lower()
            ads_f = [a for a in ads_f if
                     q in (a.get("body") or "").lower() or
                     q in (a.get("title") or "").lower() or
                     q in (a.get("body_raw") or "").lower()]
        if filtro_fmt != "Todos":
            ads_f = [a for a in ads_f if a["formato"] == filtro_fmt]
        if filtro_plat != "Todas":
            ads_f = [a for a in ads_f if filtro_plat.lower() in (a["plataformas"] or [])]
 
        if not ads_f:
            st.warning("Nenhum anúncio com os filtros aplicados.")
            return
 
        n_video     = sum(1 for a in ads_f if "Vídeo"     in a["formato"])
        n_imagem    = sum(1 for a in ads_f if "Imagem"    in a["formato"])
        n_carrossel = sum(1 for a in ads_f if "Carrossel" in a["formato"])
        n_dynamic   = sum(1 for a in ads_f if a.get("is_dynamic"))
 
        st.markdown(f"""
        <div style='display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap'>
            <div style='flex:1;min-width:80px;background:#f0fdf4;border:1px solid #86efac;border-radius:10px;padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#15803d'>{len(ads_f)}</div>
                <div style='font-size:12px;color:#16a34a;font-weight:600'>Total</div></div>
            <div style='flex:1;min-width:80px;background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#92400e'>{n_imagem}</div>
                <div style='font-size:12px;color:#b45309;font-weight:600'>Imagens</div></div>
            <div style='flex:1;min-width:80px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#1e40af'>{n_video}</div>
                <div style='font-size:12px;color:#1d4ed8;font-weight:600'>Vídeos</div></div>
            <div style='flex:1;min-width:80px;background:#f5f3ff;border:1px solid #c4b5fd;border-radius:10px;padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#5b21b6'>{n_carrossel}</div>
                <div style='font-size:12px;color:#6d28d9;font-weight:600'>Carrossel</div></div>
            {f"<div style='flex:1;min-width:80px;background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:12px 16px;text-align:center'><div style='font-size:22px;font-weight:800;color:#c2410c'>{n_dynamic}</div><div style='font-size:12px;color:#ea580c;font-weight:600'>Dinâmicos</div></div>" if n_dynamic > 0 else ""}
        </div>""", unsafe_allow_html=True)
 
        cta_labels = {
            "LEARN_MORE":"Saiba Mais","SIGN_UP":"Cadastre-se","CONTACT_US":"Fale Conosco",
            "GET_QUOTE":"Solicitar Orçamento","BOOK_TRAVEL":"Reservar",
            "WHATSAPP_MESSAGE":"Enviar Mensagem","SEND_WHATSAPP_MESSAGE":"WhatsApp",
            "MESSAGE_PAGE":"Enviar Mensagem","SHOP_NOW":"Comprar Agora","DOWNLOAD":"Baixar",
            "WATCH_MORE":"Ver Mais","APPLY_NOW":"Candidatar-se","GET_OFFER":"Ver Oferta",
            "SUBSCRIBE":"Assinar","CALL_NOW":"Ligar Agora","SEND_MESSAGE":"Enviar Mensagem",
            "GET_DIRECTIONS":"Como Chegar","BUY_NOW":"Comprar","DONATE":"Doar",
            "OPEN_LINK":"Abrir Link","NO_BUTTON":"",
        }
 
        cols_ads = st.columns(3)
        for j, ad in enumerate(ads_f):
            with cols_ads[j % 3]:
                snap_url    = ad.get("snapshot_url") or ""
                images      = ad.get("images") or []
                images_b64  = ad.get("images_b64") or []
                videos      = ad.get("videos") or []
                video_thumb = ad.get("video_thumb") or ""
                is_dyn      = ad.get("is_dynamic", False)
                baixo_vol   = ad.get("baixo_volume", False)
                ad_id       = ad.get("id","")
                ad_id_short = ad_id[:15] + "…" if len(ad_id) > 15 else ad_id
                plats       = ad.get("plataformas") or []
                plat_js     = _json.dumps([p.lower() for p in plats])
                data_inicio = ad.get("data_inicio","")
                impressoes  = ad.get("impressoes","")
                body        = ad.get("body")        or ""
                title       = ad.get("title")       or ""
                desc        = ad.get("description") or ""
                cta         = ad.get("cta")         or ""
                uid         = f"{safe_key(ck)}_{j}"
                page_pic    = ad.get("page_profile_picture") or ""
                microlink_url = _microlink_screenshot(snap_url)
 
                img_primary = images_b64[0] if images_b64 else (images[0] if images else "")
                img_fallbacks = []
                if images_b64 and len(images_b64) > 1:
                    img_fallbacks.extend(images_b64[1:])
                img_fallbacks.extend([u for u in images if u not in img_fallbacks])
                if microlink_url:
                    img_fallbacks.append(microlink_url)
                srcs_js = _json.dumps(img_fallbacks)
 
                if videos:
                    if snap_url:
                        _snap_safe    = snap_url.replace("'", "\\'")
                        video_onclick = f"onclick=\"window.open('{_snap_safe}','_blank')\""
                        video_style   = "cursor:pointer;"
                    else:
                        video_onclick = ""
                        video_style   = ""
                    if video_thumb:
                        media_block = f"""
<div class="media-block video-thumb-block" {video_onclick} style="{video_style}position:relative;">
    <img src="{video_thumb}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;"
         onerror="this.style.display='none';document.getElementById('vfallback_{uid}').style.display='flex'" />
    <div id="vfallback_{uid}" style="display:none;position:absolute;inset:0;
         background:linear-gradient(135deg,#0f1f35,#1a3a5c);align-items:center;justify-content:center;flex-direction:column;gap:8px">
        <svg width="36" height="36" viewBox="0 0 54 54" fill="none">
            <circle cx="27" cy="27" r="27" fill="rgba(255,255,255,0.15)"/>
            <polygon points="22,18 40,27 22,36" fill="white"/>
        </svg>
    </div>
    <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;">
        <div style="width:52px;height:52px;border-radius:50%;background:rgba(0,0,0,0.55);backdrop-filter:blur(2px);
                    display:flex;align-items:center;justify-content:center;">
            <svg width="22" height="22" viewBox="0 0 54 54" fill="none"><polygon points="18,14 42,27 18,40" fill="white"/></svg>
        </div>
    </div>
    {'<div style="position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.6);color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:4px;font-family:DM Sans,sans-serif;">▶ VER VÍDEO</div>' if snap_url else ''}
</div>"""
                    else:
                        media_block = f"""
<div class="media-block video-block" {video_onclick} style="{video_style}">
    <div class="video-play-icon">
        <svg width="48" height="48" viewBox="0 0 54 54" fill="none">
            <circle cx="27" cy="27" r="27" fill="rgba(255,255,255,0.15)"/>
            <circle cx="27" cy="27" r="20" fill="rgba(255,255,255,0.2)"/>
            <polygon points="22,18 40,27 22,36" fill="white"/>
        </svg>
    </div>
    <div style="font-size:11px;color:rgba(255,255,255,0.75);margin-top:8px;font-family:'DM Sans',sans-serif;">{'Clique para ver o vídeo' if snap_url else 'Vídeo'}</div>
</div>"""
                elif img_primary:
                    media_block = f"""
<div class="media-block img-block" id="mwrap_{uid}" style="position:relative;cursor:pointer"
     onclick="openModal_{uid}(document.getElementById('mimg_{uid}') ? document.getElementById('mimg_{uid}').src : '{img_primary.replace("'","")}', '{snap_url.replace("'","")}', false)">
    <img id="mimg_{uid}" src="{img_primary}" loading="lazy"
        style="width:100%;height:100%;object-fit:cover;display:block;"
        onerror="imgFallback_{uid}(this)" />
    <div id="merr_{uid}" style="display:none;width:100%;height:100%;align-items:center;justify-content:center;
         flex-direction:column;gap:8px;background:#f9fafb;position:absolute;top:0;left:0;">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
        </svg>
        <span style="font-size:12px;color:#3a9fd6;font-weight:600;">{'Ver criativo →' if snap_url else 'Sem imagem'}</span>
    </div>
    <div style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.45);border-radius:6px;
                padding:3px 7px;font-size:11px;color:#fff;font-weight:600;pointer-events:none;">🔍 Ampliar</div>
</div>
<script>
var _srcs_{uid}={srcs_js};
var _idx_{uid}=0;
function imgFallback_{uid}(img){{
    _idx_{uid}++;
    if(_idx_{uid}<_srcs_{uid}.length){{img.src=_srcs_{uid}[_idx_{uid}];}}
    else{{img.style.display='none';var e=document.getElementById('merr_{uid}');if(e)e.style.display='flex';}}
}}
</script>"""
                else:
                    if microlink_url:
                        media_block = f"""
<div class="media-block img-block" id="mwrap_{uid}" style="position:relative;cursor:pointer"
     onclick="openModal_{uid}('{microlink_url.replace("'","")}', '{snap_url.replace("'","")}', false)">
    <img id="mimg_{uid}" src="{microlink_url}" loading="lazy"
        style="width:100%;height:100%;object-fit:cover;display:block;"
        onerror="this.style.display='none';document.getElementById('mnomedia_{uid}').style.display='flex'" />
    <div id="mnomedia_{uid}" style="display:none;width:100%;height:100%;align-items:center;justify-content:center;
         flex-direction:column;gap:8px;background:#f9fafb;position:absolute;top:0;left:0;">
        <span style="font-size:12px;color:#3a9fd6;font-weight:600;">Ver criativo →</span>
    </div>
    <div style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.45);border-radius:6px;
                padding:3px 7px;font-size:11px;color:#fff;font-weight:600;pointer-events:none;">🔍 Ampliar</div>
</div>"""
                    else:
                        _sv = snap_url.replace("'", "")
                        _nm_attrs = ('style="cursor:pointer" onclick="openModal_' + uid + "('', '" + _sv + "', false)\"") if snap_url else ""
                        _nm_color = "#3a9fd6" if snap_url else "#c4c4c4"
                        _nm_label = "Ver criativo \u2192" if snap_url else "Sem criativo"
                        media_block = (
                            '<div class="media-block no-media-block" ' + _nm_attrs + '>'
                            '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.2">'
                            '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>'
                            '<polyline points="21 15 16 10 5 21"/>'
                            '</svg>'
                            '<span style="font-size:12px;color:' + _nm_color + ';font-weight:600;margin-top:8px;">' + _nm_label + '</span>'
                            '</div>'
                        )
 
                cta_display = cta_labels.get(cta.upper() if cta else "", cta)
 
                baixo_vol_badge = (
                    '<span style="background:#fff3e0;color:#e65100;border:1px solid #ffcc80;'
                    'padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;margin-left:6px;">'
                    '⚠️ Baixo volume</span>'
                ) if baixo_vol else ""
 
                if page_pic and page_pic.startswith("http"):
                    page_avatar_html = (
                        f'<div class="page-avatar" style="overflow:hidden;padding:0">'
                        f'<img src="{page_pic}" style="width:100%;height:100%;object-fit:cover;display:block;border-radius:50%"'
                        f' onerror="this.parentElement.style.background=\'{cor_av}\';this.parentElement.innerHTML=\'{avatar}\'" />'
                        f'</div>'
                    )
                else:
                    page_avatar_html = f'<div class="page-avatar">{avatar}</div>'
 
                lib_btn_html = ""
                if snap_url:
                    lib_btn_html = f"""
<a href="{snap_url}" target="_blank" class="lib-btn">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
         stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <polyline points="15 3 21 3 21 9"/>
        <line x1="10" y1="14" x2="21" y2="3"/>
    </svg>
    Ver criativo no Ad Library
</a>"""
 
                card_html = f"""<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent;font-family:'DM Sans',-apple-system,sans-serif;-webkit-font-smoothing:antialiased;overflow:visible;}}
body{{padding-bottom:8px;}}
.card{{background:#fff;border:1px solid #dde1e7;border-radius:12px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 1px 4px rgba(0,0,0,0.06);}}
.status-bar{{display:flex;align-items:center;justify-content:space-between;padding:10px 14px 8px;border-bottom:1px solid #f0f2f5;background:#fafbfc;flex-wrap:wrap;gap:6px;}}
.status-dot{{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:#1aab40;}}
.status-dot::before{{content:'';width:8px;height:8px;border-radius:50%;background:#1aab40;flex-shrink:0;}}
.ad-id{{font-size:10px;color:#8a8d91;font-family:monospace;}}
.meta-info{{padding:8px 14px 10px;border-bottom:1px solid #f0f2f5;background:#fafbfc;}}
.meta-row{{display:flex;align-items:center;gap:6px;font-size:12px;color:#65676b;font-weight:400;margin-bottom:5px;flex-wrap:wrap;line-height:1.5;}}
.meta-row:last-child{{margin-bottom:0;}}
.meta-label{{font-size:12px;color:#65676b;font-weight:600;flex-shrink:0;}}
.plat-icons{{display:flex;align-items:center;gap:5px;flex-wrap:wrap;}}
.plat-badge{{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;background:transparent;}}
.dynamic-badge{{display:inline-flex;align-items:center;gap:4px;background:#fff3e0;color:#e65100;border:1px solid #ffcc80;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;margin-left:4px;}}
.copy-section{{padding:12px 14px 10px;border-bottom:1px solid #f0f2f5;}}
.page-header{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}
.page-avatar{{width:34px;height:34px;border-radius:50%;background:{cor_av};display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0;}}
.page-name{{font-size:13px;font-weight:700;color:#050505;line-height:1.2;}}
.page-sponsored{{font-size:11px;color:#65676b;}}
.copy-body{{font-size:14px;color:#050505;line-height:1.65;white-space:pre-line;word-break:break-word;}}
.copy-title{{font-size:14px;font-weight:700;color:#050505;margin-top:8px;line-height:1.4;}}
.copy-desc{{font-size:12px;color:#65676b;margin-top:3px;line-height:1.4;}}
.no-copy{{font-size:13px;color:#bcc0c4;font-style:italic;}}
.media-block{{width:100%;position:relative;overflow:hidden;background:#f0f2f5;height:220px;}}
.img-block{{height:220px;}}
.video-thumb-block{{height:220px;}}
.video-block{{height:220px;background:linear-gradient(135deg,#0f1f35 0%,#1a3a5c 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;}}
.video-play-icon{{display:flex;align-items:center;justify-content:center;transition:transform 0.2s;}}
.video-block:hover .video-play-icon{{transform:scale(1.1);}}
.no-media-block{{height:120px;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#f7f8fa;border-top:1px solid #f0f2f5;border-bottom:1px solid #f0f2f5;gap:8px;}}
.cta-footer{{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:#f7f8fa;border-top:1px solid #e4e6ea;gap:10px;min-height:50px;}}
.cta-domain{{font-size:11px;color:#65676b;text-transform:uppercase;letter-spacing:0.3px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.cta-btn{{background:#e4e6eb;color:#050505;border:none;border-radius:6px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;font-family:'DM Sans',sans-serif;text-decoration:none;display:inline-block;transition:background 0.15s;flex-shrink:0;}}
.cta-btn:hover{{background:#d8dadf;}}
.lib-btn{{display:flex;align-items:center;justify-content:center;gap:7px;width:100%;padding:10px;background:#1877F2;color:#fff;border:none;border-radius:0 0 10px 10px;font-size:13px;font-weight:700;text-decoration:none;font-family:'DM Sans',sans-serif;transition:background 0.15s;}}
.lib-btn:hover{{background:#166fe5;}}
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.82);z-index:99999;align-items:center;justify-content:center;backdrop-filter:blur(3px);}}
.modal-overlay.open{{display:flex;}}
.modal-box{{background:#1a1a2e;border-radius:16px;max-width:90vw;max-height:90vh;overflow:hidden;position:relative;display:flex;flex-direction:column;align-items:center;box-shadow:0 24px 80px rgba(0,0,0,0.6);}}
.modal-close{{position:absolute;top:12px;right:14px;background:rgba(255,255,255,0.15);border:none;border-radius:50%;width:34px;height:34px;font-size:18px;color:#fff;cursor:pointer;z-index:10;display:flex;align-items:center;justify-content:center;}}
.modal-close:hover{{background:rgba(255,255,255,0.3);}}
.modal-img{{max-width:80vw;max-height:78vh;object-fit:contain;border-radius:10px;display:block;}}
.modal-video-wrap{{display:flex;flex-direction:column;align-items:center;gap:16px;padding:32px 24px;}}
.modal-video-btn{{display:inline-flex;align-items:center;gap:8px;background:#1877F2;color:#fff;padding:12px 24px;border-radius:10px;font-size:15px;font-weight:700;text-decoration:none;font-family:'DM Sans',sans-serif;}}
.modal-video-thumb{{max-width:70vw;max-height:55vh;object-fit:contain;border-radius:10px;opacity:0.85;}}
</style>
</head><body>
<div class="card">
    <div class="status-bar">
        <div style="display:flex;align-items:center;gap:6px">
            <div class="status-dot">Ativo</div>
            {baixo_vol_badge}
        </div>
        {f'<span class="ad-id">ID: {ad_id_short}</span>' if ad_id_short else ''}
    </div>
    <div class="meta-info">
        {f'<div class="meta-row"><span class="meta-label">{data_inicio}</span></div>' if data_inicio else ''}
        <div class="meta-row">
            <span class="meta-label">Plataformas:</span>
            <span id="plat_icons_{uid}" class="plat-icons"></span>
        </div>
        {f'<div class="meta-row"><span class="meta-label">Impressões:</span>&nbsp;{impressoes}</div>' if impressoes else ''}
    </div>
    <div class="copy-section">
        <div class="page-header">
            {page_avatar_html}
            <div>
                <div class="page-name">{ad.get("page_name") or nome}{' <span class="dynamic-badge">⚡ Dinâmico</span>' if is_dyn else ''}</div>
                <div class="page-sponsored">Patrocinado</div>
            </div>
        </div>
        {_copy_block_html(body, uid)}
        {f'<div class="copy-title">{title}</div>' if title else ''}
        {f'<div class="copy-desc">{_truncar(desc,120)}</div>' if desc else ''}
        {'<div class="no-copy">Sem copy disponível.</div>' if not body and not title and not desc else ''}
    </div>
    {media_block}
    <div class="cta-footer">
        <span class="cta-domain">{ad.get("caption") or (snap_url.replace("https://","").split("/")[0] if snap_url else "")}</span>
        <a href="{snap_url or '#'}" target="_blank" class="cta-btn" {'style="pointer-events:none;opacity:0.4"' if not snap_url else ''}>
            {cta_display or "Ver detalhes"}
        </a>
    </div>
    {lib_btn_html}
</div>
 
<div class="modal-overlay" id="modal_{uid}" onclick="if(event.target===this)closeModal_{uid}()">
    <div class="modal-box" id="modalbox_{uid}">
        <button class="modal-close" onclick="closeModal_{uid}()">✕</button>
        <div id="modalcontent_{uid}"></div>
    </div>
</div>
 
<script>
var __PLATS_{uid}__ = {plat_js};
{_plat_svg_js(uid)}
 
function openModal_{uid}(imgSrc, snapUrl, isVideo) {{
    var overlay = document.getElementById('modal_{uid}');
    var content = document.getElementById('modalcontent_{uid}');
    content.innerHTML = '';
    if (isVideo) {{
        var wrap = document.createElement('div');
        wrap.className = 'modal-video-wrap';
        if (imgSrc) {{
            var thumb = document.createElement('img');
            thumb.src = imgSrc;
            thumb.className = 'modal-video-thumb';
            thumb.onerror = function() {{ this.style.display='none'; }};
            wrap.appendChild(thumb);
        }}
        if (snapUrl) {{
            var btn = document.createElement('a');
            btn.href = snapUrl;
            btn.target = '_blank';
            btn.className = 'modal-video-btn';
            btn.innerHTML = '▶ Abrir vídeo no Ad Library';
            wrap.appendChild(btn);
        }} else {{
            var msg = document.createElement('div');
            msg.style.cssText = 'color:#aaa;font-size:14px;padding:12px';
            msg.textContent = 'Vídeo não disponível para visualização direta.';
            wrap.appendChild(msg);
        }}
        content.appendChild(wrap);
    }} else {{
        if (imgSrc) {{
            var img = document.createElement('img');
            img.src = imgSrc;
            img.className = 'modal-img';
            img.onerror = function() {{
                this.style.display='none';
                if (snapUrl) window.open(snapUrl, '_blank');
            }};
            content.appendChild(img);
        }} else if (snapUrl) {{
            window.open(snapUrl, '_blank');
            return;
        }}
    }}
    overlay.classList.add('open');
}}
 
function closeModal_{uid}() {{
    document.getElementById('modal_{uid}').classList.remove('open');
}}
 
function syncHeight_{uid}() {{
    var h = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        document.body.offsetHeight
    );
    var frames = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {{
        try {{
            if (frames[i].contentWindow === window) {{
                frames[i].style.height = (h + 16) + 'px';
                frames[i].style.minHeight = 'unset';
                break;
            }}
        }} catch(e) {{}}
    }}
}}
 
document.addEventListener('DOMContentLoaded', function() {{ setTimeout(syncHeight_{uid}, 50); }});
window.addEventListener('load', function() {{ syncHeight_{uid}(); }});
document.querySelectorAll('img').forEach(function(img) {{
    img.addEventListener('load', function() {{ setTimeout(syncHeight_{uid}, 30); }});
    img.addEventListener('error', function() {{ setTimeout(syncHeight_{uid}, 30); }});
}});
if (window.ResizeObserver) {{
    var _ro_{uid} = new ResizeObserver(function() {{ syncHeight_{uid}(); }});
    _ro_{uid}.observe(document.body);
}}
setTimeout(syncHeight_{uid}, 200);
setTimeout(syncHeight_{uid}, 600);
setTimeout(syncHeight_{uid}, 1400);
</script>
</body></html>"""
 
                components.html(card_html, height=620, scrolling=False)
                st.markdown("<div style='height:12px'/>", unsafe_allow_html=True)
 
        st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 20px 0'/>", unsafe_allow_html=True)
 
        chave_ia = f"ia_ads_{safe_key(ck)}"
        if chave_ia not in st.session_state:
            st.session_state[chave_ia] = ""
 
        resumo_ads = "\n".join([
            f"- [{a['formato']}{'(dinâmico)' if a.get('is_dynamic') else ''}] "
            f"Título: {_truncar(a.get('title',''),60) or '—'} | "
            f"Copy: {_truncar(a.get('body',''),100) or '—'} | "
            f"Impressões: {a['impressoes'] or '—'}"
            for a in ads_f[:15]
        ])
 
        ia_html_content = st.session_state.get(chave_ia,"").replace("\n","<br>")
        if ia_html_content:
            st.markdown(f"""
            <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:8px'>
                <div style='padding:14px 18px;font-size:14px;font-weight:800;color:#1a2e4a;
                            text-transform:uppercase;letter-spacing:0.3px;border-bottom:1px solid #e5e7eb'>
                    📊 Análise Estratégica com IA
                </div>
                <div style='padding:16px 18px;font-size:14px;color:#374151;line-height:1.75'>
                    {ia_html_content}
                </div>
            </div>""", unsafe_allow_html=True)
 
        col_ia, _ = st.columns([2, 5])
        with col_ia:
            gerar_ia = st.button(
                "🔄 Nova Análise" if ia_html_content else "🤖 Analisar com IA",
                key=f"btn_ia_ads_{safe_key(ck)}",
                use_container_width=True,
                type="primary",
            )
 
        if gerar_ia:
            if gemini_model is None:
                st.session_state[chave_ia] = "Configure GEMINI_API_KEY nos secrets."
            else:
                with st.spinner("Analisando com IA…"):
                    try:
                        n_dyn = sum(1 for a in ads_f if a.get("is_dynamic"))
                        n_vid = sum(1 for a in ads_f if "Vídeo"  in a["formato"])
                        n_img = sum(1 for a in ads_f if "Imagem" in a["formato"])
                        prompt_ads = f"""Você é especialista em mídia paga e marketing digital.
Analise os anúncios de "{nome}" e gere um relatório estratégico completo em português.
 
Empresa: {nome} | Total: {len(ads_f)} | {n_img} imagens | {n_vid} vídeos | {n_dyn} dinâmicos
 
Amostra:
{resumo_ads}
 
---
### 🎯 Estratégia de Mídia
### 📝 Padrões de Copy e Mensagem
### 🖼️ Análise de Formatos
### ⚡ Uso de Anúncios Dinâmicos
### 📊 Estimativa de Investimento e Alcance
### ⚠️ Pontos de Atenção
### 💡 Oportunidades Competitivas (3 ações concretas)"""
                        resp = gemini_model.generate_content(prompt_ads)
                        st.session_state[chave_ia] = resp.text
                        st.rerun()
                    except Exception as ex:
                        st.session_state[chave_ia] = f"Erro: {ex}"
                        st.rerun()
 
    for aba, emp_item in zip(abas_ads, empresas_com_dados):
        with aba:
            render_ads_empresa(emp_item)
 
# ---------------------------------------------------
# PAGINA - INSIGHTS
# ---------------------------------------------------

elif st.session_state.pagina == "insights":

    periodo, data_inicio = cabecalho_analise("✨ Insights", "Estratégias geradas por IA para vencer a concorrência")
    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:
        col_sel, col_btn = st.columns([4, 2])
        with col_sel:
            target = st.selectbox(
                "Gerar estratégia contra:",
                [c["nome"] for c in concorrentes],
                label_visibility="collapsed"
            )
        with col_btn:
            gerar = st.button("⚡ Gerar Insight", type="primary", use_container_width=True)

        if gerar:
            with st.spinner("Gerando insight..."):
                resposta = consultar_ia(f"Gere um battle card focado em vencer o concorrente {target} considerando o período: {periodo}.")
                st.markdown(resposta)
    else:
        st.info("Adicione concorrentes para gerar insights estratégicos.")

# ---------------------------------------------------
# PAGINA - REDES SOCIAIS
# ---------------------------------------------------

elif st.session_state.pagina == "redes":
 
    import datetime
    import plotly.graph_objects as go
    import json
 
    emp = st.session_state.dados["minha_empresa"]
    concorrentes = st.session_state.dados["concorrentes"]
 
    st.markdown("""
    <style>
    @import url(https://db.onlinewebfonts.com/c/411b9832f1ad24e045b36f92814dac58?family=Animo+DEMO);
 
    div[data-testid="stTabs"] > div:first-child {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        gap: 4px !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #6b7280 !important;
        border-bottom: none !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 10px 24px !important;
        background: transparent !important;
        transition: all 0.15s !important;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover {
        background: #f3f4f6 !important;
        color: #111827 !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #0e2a47 !important;
        color: #ffffff !important;
        border-bottom: none !important;
        box-shadow: 0 2px 8px rgba(14,42,71,0.18) !important;
    }
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
 
    h1, h2 = st.columns([7, 3])
    with h1:
        components.html("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@font-face {
    font-family: 'Animo';
    src: url('https://raw.githubusercontent.com/thiagomktsantos/marketylics/63946b2d891db6b45cc75a45550b7aa5fe67244a/utils/Animo-font.otf') format('opentype');
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { background: transparent; overflow: hidden; }
.titulo {
    font-family: 'Animo', 'DM Sans', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #1a2e4a;
    text-transform: uppercase;
    margin: 0 0 6px 0;
    letter-spacing: 0.5px;
}
.sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: #6b7280;
}
</style>
<div class="titulo">Redes Sociais</div>
<div class="sub">Acompanhe e compare métricas do Instagram dos seus concorrentes em tempo real.</div>
""", height=65)

    with h2:
        coletar = st.button(
            "Coletar dados",
            type="primary",
            use_container_width=True,
        )
        ultima_coleta = st.session_state.metricas_redes.get("ultima_coleta", "")
        if ultima_coleta:
            st.markdown(
                f"<div style='font-size:13px;color:#6b7280;text-align:center;margin-top:-8px'>"
                f"🕒 Última coleta: <b>{ultima_coleta}</b></div>",
                unsafe_allow_html=True,
            )
    st.markdown(
        "<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 20px 0'/>",
        unsafe_allow_html=True,
    )
 
    def fmt_num(n):
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.1f}K"
        return str(int(n))
 
    def salvar_cache_redes(dados: list):
        try:
            payload = {
                "user_id": st.session_state.user.id,
                "minha_empresa": st.session_state.dados["minha_empresa"],
                "concorrentes": st.session_state.dados["concorrentes"],
                "metricas_redes": {
                    "ultima_coleta": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "dados": dados,
                },
            }
            supabase.table("ci_dados").upsert(payload, on_conflict="user_id").execute()
        except Exception as e:
            st.toast(f"⚠️ Erro ao salvar cache: {e}", icon="⚠️")
 
    def carregar_cache_redes() -> dict:
        try:
            res = (
                supabase.table("ci_dados")
                .select("metricas_redes")
                .eq("user_id", st.session_state.user.id)
                .execute()
            )
            if res.data and res.data[0].get("metricas_redes"):
                return res.data[0]["metricas_redes"]
        except Exception:
            pass
        return {}
 
    @st.cache_data(ttl=1800, show_spinner=False)
    def coletar_rapidapi(handle: str) -> dict:
        handle_limpo = handle.lstrip("@").strip()
        if not handle_limpo:
            return {"erro": "Handle vazio"}
        try:
            rapidapi_key = st.secrets.get("RAPIDAPI_KEY", "")
            if not rapidapi_key:
                return {"erro": "RAPIDAPI_KEY não configurada"}
 
            headers = {
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": "instagram-looter2.p.rapidapi.com",
            }
 
            r = requests.get(
                f"https://instagram-looter2.p.rapidapi.com/profile?username={handle_limpo}",
                headers=headers,
                timeout=15,
            )
            data = r.json()
            user_data = data
            if isinstance(data, dict):
                if "data" in data:   user_data = data["data"]
                elif "user" in data: user_data = data["user"]
 
            if not user_data or "message" in user_data:
                return {"erro": user_data.get("message", "Perfil não encontrado")}
 
            seg         = int(user_data.get("follower_count") or user_data.get("edge_followed_by", {}).get("count") or 0)
            total_posts = int(user_data.get("media_count") or user_data.get("edge_owner_to_timeline_media", {}).get("count") or 0)
            pk          = str(user_data.get("pk") or user_data.get("id") or "").strip()
 
            posts_data = []
            if pk:
                for endpoint in [
                    f"https://instagram-looter2.p.rapidapi.com/user-feeds?id={pk}&count=12&allow_restricted_media=false",
                    f"https://instagram-looter2.p.rapidapi.com/user-medias?id={pk}&count=12",
                ]:
                    try:
                        rp    = requests.get(endpoint, headers=headers, timeout=15)
                        pr    = rp.json()
                        items = pr if isinstance(pr, list) else pr.get("items", [])
                        if items:
                            for p in items[:12]:
                                likes    = int(p.get("like_count") or 0)
                                comments = int(p.get("comment_count") or 0)
                                thumb    = ""
                                if p.get("image_versions2"):
                                    cands = p["image_versions2"].get("candidates", [])
                                    if cands: thumb = cands[-1].get("url", "")
                                elif p.get("thumbnail_url"):
                                    thumb = p["thumbnail_url"]
                                caption  = ""
                                if p.get("caption"):
                                    caption = (
                                        p["caption"].get("text", "")
                                        if isinstance(p["caption"], dict)
                                        else str(p["caption"])
                                    )[:500]
                                taken_at = p.get("taken_at", 0)
                                date_str = ""
                                if taken_at:
                                    try:
                                        date_str = datetime.datetime.fromtimestamp(taken_at).strftime("%d/%m/%Y")
                                    except Exception:
                                        pass
                                posts_data.append({
                                    "likes":    likes,
                                    "comments": comments,
                                    "thumb":    thumb,
                                    "caption":  caption,
                                    "date":     date_str,
                                    "is_video": p.get("media_type", 1) == 2,
                                })
                            break
                    except Exception:
                        continue
 
            if posts_data:
                eng_medio = sum(p["likes"] + p["comments"] for p in posts_data) / len(posts_data)
                eng_pct   = round(eng_medio / seg * 100, 2) if seg > 0 else 0.0
            else:
                eng_pct   = 3.0 if seg <= 10_000 else (2.0 if seg <= 50_000 else (1.5 if seg <= 100_000 else 1.0))
                eng_medio = round(seg * eng_pct / 100, 1)
 
            return {
                "handle":       "@" + handle_limpo,
                "nome_exibido": user_data.get("full_name") or user_data.get("username", handle_limpo),
                "seguidores":   seg,
                "seguindo":     int(user_data.get("following_count") or 0),
                "total_posts":  total_posts,
                "bio":          (user_data.get("biography") or "")[:120],
                "is_verified":  user_data.get("is_verified", False),
                "eng_medio":    round(eng_medio, 1),
                "eng_pct":      eng_pct,
                "posts":        posts_data,
                "fonte":        "rapidapi",
                "erro":         None,
            }
        except Exception as e:
            return {"erro": str(e)}
 
    todas = []
    if emp.get("nome") and emp.get("instagram") and emp["instagram"] not in ("@", ""):
        todas.append({"key": "__minha__", "nome": emp["nome"], "instagram": emp["instagram"], "tipo": "minha"})
    for i, c in enumerate(concorrentes):
        if c.get("instagram") and c["instagram"] not in ("@", ""):
            todas.append({"key": f"conc_{i}", "nome": c["nome"], "instagram": c["instagram"], "tipo": "concorrente"})
 
    if not todas:
        st.info("Cadastre pelo menos um Instagram (sua empresa ou concorrente) para usar esta página.")
        st.stop()
 
    if not st.secrets.get("RAPIDAPI_KEY", ""):
        st.warning("Configure `RAPIDAPI_KEY` no secrets.toml para coletar dados.")
 
    cache = carregar_cache_redes()
 
    if coletar:
        coletar_rapidapi.clear()
        resultados_lista = []
        with st.spinner("Coletando perfis…"):
            for e in todas:
                r = coletar_rapidapi(e["instagram"])
                resultados_lista.append({**e, **(r or {"erro": "Sem resposta"})})
        salvar_cache_redes(resultados_lista)
        cache = {
            "ultima_coleta": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "dados": resultados_lista,
        }
        st.toast("✅ Dados coletados e salvos!", icon="✅")
 
    ok = []
    if cache.get("dados"):
        ok    = [r for r in cache["dados"] if not r.get("erro")]
        erros = [r for r in cache["dados"] if r.get("erro")]
        for r in erros:
            st.warning(f"⚠️ {r['nome']}: {r['erro']}")
 
    if not ok:
        st.info("Clique em **Coletar dados** para buscar os dados do Instagram.")
        st.stop()
 
# ══════════════════════════════════════════════════════════════════════
# PAGINA - REDES SOCIAIS - GRÁFICOS COMPARATIVOS
# ══════════════════════════════════════════════════════════════════════
 
    # ← USANDO a paleta global para as cores dos gráficos
    CORES = AVATAR_COLORS

    nomes_ok   = [x["nome"] for x in ok]
    segs_ok    = [x.get("seguidores", 0) for x in ok]
    eng_pct_ok = [x.get("eng_pct", 0.0) for x in ok]
    cores_ok   = [get_avatar_color(i) for i in range(len(ok))]
 
    st.markdown(
        "<div style='font-size:18px;font-weight:700;color:#1a2e4a;"
        "font-family:\"Source Sans\",sans-serif;"
        "letter-spacing:0px;text-transform:uppercase'>"
        "Comparativo com todos os perfis</div>",
        unsafe_allow_html=True,
    )
 
    st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_seg = go.Figure(
            go.Bar(
                x=nomes_ok,
                y=segs_ok,
                marker=dict(color=cores_ok, line=dict(width=0)),
                text=[fmt_num(s) for s in segs_ok],
                textposition="outside",
                cliponaxis=False,
                textfont=dict(family="DM Sans", size=14, color="#111827"),
            )
        )
        fig_seg.update_layout(
            height=190,
            margin=dict(t=20, b=30, l=25, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            font=dict(family="DM Sans, sans-serif", color="#374151", size=13),
            bargap=0.45,
            xaxis=dict(showgrid=False, tickfont=dict(family="DM Sans", size=13, color="#374151"), showline=False),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6", zeroline=False, tickfont=dict(family="DM Sans", size=12, color="#6b7280")),
        )
        fig_seg_json = json.dumps(fig_seg.to_dict(), default=str)
        components.html(f"""
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                    padding:20px 16px 24px 16px;overflow:visible">
            <div style="font-size:14px;font-weight:800;color:#1a2e4a;
                        font-family:'DM Sans',sans-serif;letter-spacing:0.3px;text-transform:uppercase;
                        padding:0 4px 12px 4px;border-bottom:1px solid #e5e7eb;
                        margin-bottom:4px">NÚMERO DE SEGUIDORES</div>
            <div id="graf_seg"></div>
        </div>
        <script>
            var fig = {fig_seg_json};
            Plotly.newPlot('graf_seg', fig.data, fig.layout, {{displayModeBar: false, responsive: true}});
        </script>
        """, height=275)

    with col_g2:
        fig_eng = go.Figure(
            go.Bar(
                x=nomes_ok,
                y=eng_pct_ok,
                marker=dict(color=cores_ok, line=dict(width=0)),
                text=[f"{v:.2f}%" for v in eng_pct_ok],
                textposition="outside",
                cliponaxis=False,
                textfont=dict(family="DM Sans", size=14, color="#111827"),
            )
        )
        fig_eng.update_layout(
            height=190,
            margin=dict(t=20, b=30, l=25, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            font=dict(family="DM Sans, sans-serif", color="#374151", size=13),
            bargap=0.45,
            xaxis=dict(showgrid=False, tickfont=dict(family="DM Sans", size=13, color="#374151"), showline=False),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6", zeroline=False, ticksuffix="%",
                       tickfont=dict(family="DM Sans", size=12, color="#6b7280")),
        )
        fig_eng_json = json.dumps(fig_eng.to_dict(), default=str)
        components.html(f"""
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;
                    padding:20px 16px 24px 16px;overflow:visible">
            <div style="font-size:14px;font-weight:800;color:#1a2e4a;
                        font-family:'DM Sans',sans-serif;letter-spacing:0.3px;text-transform:uppercase;
                        padding:0 4px 12px 4px;border-bottom:1px solid #e5e7eb;
                        margin-bottom:4px">TAXA DE ENGAJAMENTO (%)</div>
            <div id="graf_eng"></div>
        </div>
        <script>
            var fig = {fig_eng_json};
            Plotly.newPlot('graf_eng', fig.data, fig.layout, {{displayModeBar: false, responsive: true}});
        </script>
        """, height=275)
 
# ══════════════════════════════════════════════════════════════════════
# PAGINA - REDES SOCIAIS - ABAS POR PERFIL
# ══════════════════════════════════════════════════════════════════════
    abas = st.tabs([r["nome"] for r in ok])
 
    for idx, (aba, r) in enumerate(zip(abas, ok)):
        with aba:
            is_minha  = r["tipo"] == "minha"
            badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
            badge_txt = "#1d4ed8" if is_minha else "#6b7280"
            badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
            badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
            # ← USANDO a função global de cor
            cor = get_avatar_color(idx)
            bio_txt   = (r.get("bio") or "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")
            eng_est   = len(r.get("posts", [])) == 0
            posts_list = r.get("posts", [])
 
            components.html(f"""
            <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
            <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            html, body {{ background: transparent; font-family: 'DM Sans', sans-serif; overflow: hidden; }}
            .header {{
                display: flex; align-items: center; gap: 16px;
                padding: 16px 0 20px 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 4px;
            }}
            .avatar {{
                width: 52px; height: 52px; border-radius: 50%;
                background: {cor};
                display: flex; align-items: center; justify-content: center;
                font-size: 18px; font-weight: 700; color: #fff; flex-shrink: 0;
            }}
            .nome {{ font-size: 20px; font-weight: 700; color: #111827; letter-spacing: -0.3px; }}
            .handle {{ font-size: 14px; font-weight: 400; color: #9ca3af; margin-left: 6px; }}
            .badge {{
                display: inline-block; background: {badge_bg}; color: {badge_txt};
                border: 1px solid {badge_brd}; padding: 2px 10px; border-radius: 20px;
                font-size: 11px; font-weight: 600; margin-top: 4px;
            }}
            </style>
            <div class="header">
                <div class="avatar">{gerar_avatar(r["nome"])}</div>
                <div>
                    <div class="nome">{r["nome"]}<span class="handle">{r.get("handle","")}</span></div>
                    <div class="badge">{badge_lbl}</div>
                </div>
            </div>
            """, height=90, scrolling=False)
 
            col_metricas, col_bio = st.columns([1, 1], gap="large")
 
            with col_metricas:
                st.markdown(f"""
<div style='background:#fff;border-radius:12px'>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px'>
        <div style='padding:16px 8px;background:#f9fafb;border-radius:10px;
                    display:flex;flex-direction:column;align-items:center;text-align:center'>
            <div style='display:flex;align-items:center;gap:8px'>
                <img src="https://raw.githubusercontent.com/thiagomktsantos/marketylics/74c3f239fe53f7942ad04589f552043ea8d4e9f4/images/icons/users-solid_blue.png" style="width:28px;height:28px;object-fit:contain" />
                <span style='font-size:24px;font-weight:700;color:#111827;letter-spacing:-1px'>
                    {fmt_num(r.get("seguidores",0))}
                </span>
            </div>
            <span style='font-size:13px;color:#000;font-weight:600;
                         letter-spacing:0.8px'>Seguidores</span>
        </div>
        <div style='padding:16px 8px;background:#f9fafb;border-radius:10px;
                    display:flex;flex-direction:column;align-items:center;text-align:center'>
            <div style='display:flex;align-items:center;gap:8px'>
                <img src="https://raw.githubusercontent.com/thiagomktsantos/marketylics/74c3f239fe53f7942ad04589f552043ea8d4e9f4/images/icons/camera-solid_blue.png" style="width:28px;height:28px;object-fit:contain" />
                <span style='font-size:24px;font-weight:700;color:#111827;letter-spacing:-1px'>
                    {fmt_num(r.get("total_posts",0))}
                </span>
            </div>
            <span style='font-size:13px;color:#000;font-weight:600;
                         letter-spacing:0.8px'>Posts</span>
        </div>
        <div style='padding:16px 8px;background:#f9fafb;border-radius:10px;
                    display:flex;flex-direction:column;align-items:center;text-align:center'>
            <div style='display:flex;align-items:center;gap:8px'>
                <img src="https://raw.githubusercontent.com/thiagomktsantos/marketylics/74c3f239fe53f7942ad04589f552043ea8d4e9f4/images/icons/heart-solid_blue.png" style="width:28px;height:28px;object-fit:contain" />
                <span style='font-size:24px;font-weight:700;color:#111827;letter-spacing:-1px'>
                    {fmt_num(int(r.get("eng_medio",0)))}
                </span>
            </div>
            <span style='font-size:13px;color:#000;font-weight:600;
                         letter-spacing:0.8px'>Engajamento Médio</span>
        </div>
        <div style='padding:16px 8px;background:#f9fafb;border-radius:10px;
                    display:flex;flex-direction:column;align-items:center;text-align:center'>
            <div style='display:flex;align-items:center;gap:8px'>
                <img src="https://raw.githubusercontent.com/thiagomktsantos/marketylics/74c3f239fe53f7942ad04589f552043ea8d4e9f4/images/icons/chart-line-solid.png" style="width:28px;height:28px;object-fit:contain" />
                <span style='font-size:24px;font-weight:700;color:#111827;letter-spacing:-1px'>
                    {r.get("eng_pct",0):.2f}%
                </span>
            </div>
            <span style='font-size:13px;color:#000;font-weight:600;
                         letter-spacing:0.8px'>Engajamento %{"*" if eng_est else ""}</span>
        </div>
    </div>
    {"<div style='font-size:11px;color:#9ca3af;margin-top:10px'>* Engajamento estimado por benchmark (posts não disponíveis)</div>" if eng_est else ""}
</div>
""", unsafe_allow_html=True)
 
            with col_bio:
                chave_bio_ia = f"ia_bio_{r.get('handle','').replace('@','')}"
                if chave_bio_ia not in st.session_state:
                    st.session_state[chave_bio_ia] = ""
 
                components.html(f"""
                <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
                <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                html, body {{ background:transparent; font-family:'DM Sans',sans-serif; overflow:hidden; -webkit-font-smoothing:antialiased; }}
                .wrap {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden;margin-left: 16px; }}
                .hdr {{ padding:12px 16px; font-size:14px; font-weight:800; color:#1a2e4a;
                        text-transform:uppercase; letter-spacing:0.3px;
                        border-bottom:1px solid #e5e7eb; background:#fff; }}
                .body {{ padding:14px 16px; }}
                .bio-text {{ font-size:14px; color:#374151; line-height:1.7; min-height:40px;
                             font-style:italic; margin-bottom:16px; }}
                .btn-ia {{
                    width:100%; padding:10px; border: 1px solid rgb(58, 159, 214); border-radius:8px;
                    background: rgb(239, 246, 255); font-size:14px; font-weight:600; color: rgb(29, 78, 216);
                    cursor:pointer; font-family:'DM Sans',sans-serif; transition:background 0.15s;
                }}
                .btn-ia:hover {{ background:#f3f4f6; }}
                </style>
                <div class="wrap">
                    <div class="hdr">Bio</div>
                    <div class="body">
                        <div class="bio-text">
                            {f'&ldquo;{bio_txt}&rdquo;' if bio_txt
                              else '<span style="color:#d1d5db">Sem bio cadastrada</span>'}
                        </div>
                        <div style="border-top:1px solid #f3f4f6;padding-top:14px">
                            <button class="btn-ia" onclick="
                                const btns = window.parent.document.querySelectorAll('button');
                                for (const b of btns) {{
                                    if (b.innerText.trim() === '__bio_{idx}__') {{ b.click(); break; }}
                                }}
                            ">Analisar Bio 🤖</button>
                        </div>
                    </div>
                </div>
                """, height=200, scrolling=False)
 
                st.markdown(f"""
                <style>
                div[data-testid="stButton"][data-key="btn_bio_ia_{idx}"],
                .st-key-btn_bio_ia_{idx} {{
                    position: fixed !important;
                    top: -9999px !important;
                    left: -9999px !important;
                    width: 1px !important;
                    height: 1px !important;
                    overflow: hidden !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                    visibility: hidden !important;
                }}
                </style>
                """, unsafe_allow_html=True)
 
                analisar_bio = st.button(
                    f"__bio_{idx}__",
                    key=f"btn_bio_ia_{idx}",
                    use_container_width=True,
                )
                if analisar_bio:
                    if gemini_model is None:
                        st.session_state[chave_bio_ia] = "Configure GEMINI_API_KEY nos secrets."
                    else:
                        with st.spinner("Analisando bio…"):
                            try:
                                prompt_bio = f"""
Analise a bio do Instagram abaixo e responda em português de forma direta e objetiva:
 
Bio: "{bio_txt}"
Perfil: {r.get('handle','')} — {r.get('nome_exibido','')}
Seguidores: {r.get('seguidores',0)} | Engajamento: {r.get('eng_pct',0):.2f}%
 
Responda com:
### Posicionamento
Qual é o posicionamento transmitido pela bio?
 
### Pontos Fortes
(2 pontos positivos da bio)
 
### O que melhorar
(2 sugestões concretas de melhoria)
 
### Bio sugerida
Escreva uma versão melhorada da bio (máx. 150 caracteres).
"""
                                resp = gemini_model.generate_content(prompt_bio)
                                st.session_state[chave_bio_ia] = resp.text
                            except Exception as e:
                                st.session_state[chave_bio_ia] = f"Erro: {e}"
 
                if st.session_state.get(chave_bio_ia):
                    st.markdown(f"""
                    <div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;
                                padding:14px 16px;font-size:13px;color:#374151;line-height:1.7;
                                max-height:220px;overflow-y:auto;margin-top:10px'>
                        {st.session_state[chave_bio_ia].replace(chr(10), "<br>")}
                    </div>
                    """, unsafe_allow_html=True)
 
            st.markdown(
                "<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 14px 0'/>",
                unsafe_allow_html=True,
            )
 
# ══════════════════════════════════════════════════════════════
# PAGINA - REDES SOCIAIS - POSTAGENS
# ══════════════════════════════════════════════════════════════

            def _fmt(n):
                n = int(n or 0)
                if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
                if n >= 1_000:     return f"{n/1_000:.1f}K"
                return str(n)

            def _esc(s):
                return (s or "").replace("\\", "\\\\").replace("'", "\\'").replace('"', "&quot;").replace("\n", " ").replace("\r", "")

            if not posts_list:
                tbl_rows = '<tr><td colspan="7" style="text-align:center;color:#9ca3af;padding:24px">Sem posts disponíveis.</td></tr>'
            else:
                tbl_rows = ""
                for p in posts_list:
                    thumb    = p.get("thumb", "")
                    cap      = p.get("caption", "")
                    cap_esc  = _esc(cap)
                    cap_preview = _esc(cap[:95]) if len(cap) > 95 else _esc(cap)
                    has_more = len(cap) > 110
                    isVid    = p.get("is_video", False)
                    likes    = p.get("likes", 0)
                    coms     = p.get("comments", 0)

                    img_cell = (
                        f'<img src="{thumb}" style="width:48px;height:48px;border-radius:8px;'
                        f'object-fit:cover;border:1px solid #e5e7eb;display:block;cursor:pointer" '
                        f'onclick="openImg(\'{_esc(thumb)}\')" '
                        f'onerror="this.outerHTML=\'&lt;div style=&quot;width:48px;height:48px;border-radius:8px;background:#f3f4f6;display:flex;align-items:center;justify-content:center;font-size:11px;color:#9ca3af&quot;&gt;📷&lt;/div&gt;\'" />'
                    ) if thumb else (
                        f'<div style="width:48px;height:48px;border-radius:8px;background:#f3f4f6;'
                        f'display:flex;align-items:center;justify-content:center;font-size:20px">{"🎬" if isVid else "📷"}</div>'
                    )

                    ver_copy = ""
                    if cap:
                        ver_copy = "<span style='color:#1e3050;font-weight:700;font-style:normal;flex-shrink:0;white-space:nowrap;margin-left:4px'>[🔍 ver copy]</span>"

                    copy_cell = (
                        f'<div onclick="openCopy2(\'{cap_esc}\')" '
                        f'style="cursor:pointer;display:flex;align-items:center;width:100%;overflow:hidden">'
                        f'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
                        f'color:#374151;font-style:italic">{cap_preview}{"…" if has_more else ""}</span>'
                        f'{ver_copy}'
                        f'</div>'
                    ) if cap else '<span style="color:#d1d5db">—</span>'

                    tbl_rows += (
                        f"<tr>"
                        f"<td>{p.get('date','—')}</td>"
                        f"<td>{img_cell}</td>"
                        f"<td>{'Vídeo' if isVid else 'Foto'}</td>"
                        f"<td>{_fmt(likes)}</td>"
                        f"<td>{_fmt(coms)}</td>"
                        f"<td>{_fmt(likes+coms)}</td>"
                        f"<td>{copy_cell}</td>"
                        f"</tr>"
                    )

            components.html(f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background:transparent; font-family:'DM Sans',sans-serif; -webkit-font-smoothing:antialiased; overflow:hidden; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; table-layout:fixed; }}
th {{
    background:#f9fafb; color:#6b7280; font-weight:700;
    padding:12px 14px; text-align:left; border-bottom:2px solid #e5e7eb;
    font-size:11px; text-transform:uppercase; letter-spacing:0.6px;
    position:sticky; top:0; z-index:1;
}}
td {{
    padding:8px 14px; border-bottom:1px solid #f3f4f6;
    color:#374151; background:#fff; vertical-align:middle;
    line-height:1.4; overflow:hidden;
}}
tr:last-child td {{ border-bottom:none; }}
tr:hover td {{ background:#f9fafb; }}
th:nth-child(1), td:nth-child(1) {{ width:90px; }}
th:nth-child(2), td:nth-child(2) {{ width:68px; text-align:center; }}
th:nth-child(3), td:nth-child(3) {{ width:60px; text-align:center; }}
th:nth-child(4), td:nth-child(4) {{ width:80px; text-align:center; }}
th:nth-child(5), td:nth-child(5) {{ width:100px; text-align:center; }}
th:nth-child(6), td:nth-child(6) {{ width:100px; text-align:center; }}
th:nth-child(7), td:nth-child(7) {{ width:auto; min-width:0; }}
td:nth-child(7) {{ overflow:hidden; }}
.modal-bg {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9000; align-items:center; justify-content:center; }}
.modal-bg.open {{ display:flex; }}
.modal {{ background:#fff; border-radius:14px; padding:24px; max-width:400px; width:90%; max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.25); position:relative; }}
.modal-title {{ font-size:13px; font-weight:700; color:#1a2e4a; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #f3f4f6; }}
.modal-text {{ font-size:14px; color:#374151; line-height:1.7; white-space:pre-wrap; }}
.modal-img {{ width:100%; border-radius:10px; object-fit:cover; border:1px solid #e5e7eb; margin-bottom:10px; }}
.modal-close {{ position:absolute; top:14px; right:16px; background:none; border:none; font-size:18px; color:#9ca3af; cursor:pointer; }}
.modal-close:hover {{ color:#111827; }}
</style>
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
    <div style="padding:14px 18px;font-size:14px;font-weight:800;color:#1a2e4a;
                text-transform:uppercase;letter-spacing:0.3px;border-bottom:1px solid #e5e7eb;
                background:#fff;">Postagens</div>
    <div style="max-height:460px;overflow-y:auto;overflow-x:hidden">
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Criativo</th>
                    <th>Tipo</th>
                    <th>Curtidas</th>
                    <th>Comentários</th>
                    <th>Engaj.</th>
                    <th>Copy</th>
                </tr>
            </thead>
            <tbody>{tbl_rows}</tbody>
        </table>
    </div>
</div>
<div class="modal-bg" id="modal2" onclick="if(event.target===this)this.classList.remove('open')">
    <div class="modal">
        <button class="modal-close" onclick="document.getElementById('modal2').classList.remove('open')">✕</button>
        <div class="modal-title" id="modal2-title"></div>
        <img id="modal2-img" class="modal-img" src="" style="display:none" />
        <div class="modal-text" id="modal2-text"></div>
    </div>
</div>
<script>
function openImg(url) {{
    document.getElementById('modal2-title').textContent = 'Imagem do Post';
    var img = document.getElementById('modal2-img');
    img.src = url; img.style.display = 'block';
    document.getElementById('modal2-text').textContent = '';
    document.getElementById('modal2').classList.add('open');
}}
function openCopy2(txt) {{
    document.getElementById('modal2-title').textContent = 'Copy Completa';
    document.getElementById('modal2-img').style.display = 'none';
    document.getElementById('modal2-text').textContent = txt;
    document.getElementById('modal2').classList.add('open');
}}
</script>
""", height=520, scrolling=False)
 
# ══════════════════════════════════════════════════════════════
# REDES SOCIAIS - ANÁLISE DE IA
# ══════════════════════════════════════════════════════════════
 
            st.markdown("<div/>", unsafe_allow_html=True)
 
            chave_criativo = f"ia_criativo_{r['handle']}"
            chave_copy     = f"ia_copy_{r['handle']}"
            chave_geral    = f"ia_geral_{r['handle']}"
            for ch in [chave_criativo, chave_copy, chave_geral]:
                if ch not in st.session_state:
                    st.session_state[ch] = ""
 
            resumo_posts = "\n".join([
                f"- {p.get('date','')} | {p.get('likes',0)} curtidas "
                f"{p.get('comments',0)} comentários | {p.get('caption','')[:80]}"
                for p in posts_list[:12]
            ]) if posts_list else "Sem posts disponíveis."
 
            perfil_ctx = f"""
Perfil: {r.get('handle','')} — {r.get('nome_exibido','')}
Bio: {r.get('bio','')}
Seguidores: {r.get('seguidores',0)} | Posts: {r.get('total_posts',0)} | Eng. médio: {r.get('eng_medio',0)} ({r.get('eng_pct',0):.2f}%)
Últimos posts:
{resumo_posts}
"""
 
            st.markdown(f"""
            <style>
            .st-key-btn_criativo_{idx}, .st-key-btn_copy_{idx}, .st-key-btn_geral_{idx} {{
                position: fixed !important; top: -9999px !important; left: -9999px !important;
                width: 1px !important; height: 1px !important; overflow: hidden !important;
                opacity: 0 !important; pointer-events: none !important; visibility: hidden !important;
            }}
            </style>
            """, unsafe_allow_html=True)

            if st.button(f"__criativo_{idx}__", key=f"btn_criativo_{idx}", use_container_width=True):
                if gemini_model is None:
                    st.session_state[chave_criativo] = "Configure GEMINI_API_KEY nos secrets."
                else:
                    with st.spinner("Analisando criativos…"):
                        try:
                            resp = gemini_model.generate_content(f"""
{perfil_ctx}
Analise os CRIATIVOS (imagens/vídeos) deste perfil com base nas legendas e métricas.
Responda em português com:
### Análise de Criativo
**Estilo visual predominante:** ...
**Formatos mais usados:** ...
**Posts com melhor desempenho:** ...
**Pontos fortes visuais:** (3 pontos)
**O que melhorar:** (2 pontos)
Seja direto e objetivo.
""")
                            st.session_state[chave_criativo] = resp.text
                            st.rerun()
                        except Exception as e:
                            st.session_state[chave_criativo] = f"Erro: {e}"

            if st.button(f"__copy_{idx}__", key=f"btn_copy_{idx}", use_container_width=True):
                if gemini_model is None:
                    st.session_state[chave_copy] = "Configure GEMINI_API_KEY nos secrets."
                else:
                    with st.spinner("Analisando copies…"):
                        try:
                            resp = gemini_model.generate_content(f"""
{perfil_ctx}
Analise as LEGENDAS (copy) deste perfil Instagram.
Responda em português com:
### Análise de Copy
**Tom de voz predominante:** ...
**Uso de CTAs:** ...
**Uso de hashtags:** ...
**Pontos fortes nas legendas:** (3 pontos)
**O que melhorar:** (2 pontos)
Seja direto e objetivo.
""")
                            st.session_state[chave_copy] = resp.text
                            st.rerun()
                        except Exception as e:
                            st.session_state[chave_copy] = f"Erro: {e}"

            if st.button(f"__geral_{idx}__", key=f"btn_geral_{idx}", use_container_width=True):
                if gemini_model is None:
                    st.session_state[chave_geral] = "Configure GEMINI_API_KEY nos secrets."
                else:
                    with st.spinner("Gerando análise geral…"):
                        try:
                            resp = gemini_model.generate_content(f"""
{perfil_ctx}
Faça uma análise geral estratégica deste perfil Instagram.
Responda em português com:
### Análise Geral
**Posicionamento:** ...
**Frequência de posts:** ...
### Pontos Fortes (3 pontos)
### Pontos de Atenção (2 pontos)
### Recomendações Estratégicas (3 ações concretas)
Seja direto e objetivo.
""")
                            st.session_state[chave_geral] = resp.text
                            st.rerun()
                        except Exception as e:
                            st.session_state[chave_geral] = f"Erro: {e}"

            criativo_html = st.session_state.get(chave_criativo, "").replace(chr(10), "<br>")
            copy_html     = st.session_state.get(chave_copy, "").replace(chr(10), "<br>")
            geral_html    = st.session_state.get(chave_geral, "").replace(chr(10), "<br>")

            def _panel_ia(html_content, btn_label, btn_trigger):
                btn_html = f"""
                    <div style="padding:16px 18px;border-top:1px solid #f3f4f6">
                        <button onclick="
                            const btns = window.parent.document.querySelectorAll('button');
                            for (const b of btns) {{
                                if (b.innerText.trim() === '{btn_trigger}') {{ b.click(); break; }}
                            }}
                        " style="
                            width:100%;padding:10px;border:1px solid #3a9fd6;border-radius:8px;
                            background:#eff6ff;font-size:14px;font-weight:700;color:#1d4ed8;
                            cursor:pointer;font-family:'DM Sans',sans-serif;transition:background 0.15s;
                        "
                        onmouseover="this.style.background='#dbeafe'"
                        onmouseout="this.style.background='#eff6ff'">
                            {btn_label}
                        </button>
                    </div>
                """
                if html_content:
                    return (
                        f'<div style="padding:16px 18px;font-size:14px;color:#374151;line-height:1.75">'
                        f'{html_content}</div>'
                        f'{btn_html}'
                    )
                return (
                    f'<div style="padding:24px 18px;text-align:center;font-size:14px;color:#9ca3af">'
                    f'Clique no botão abaixo para gerar a análise.</div>'
                    f'{btn_html}'
                )

            ia_html = f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ background:transparent; font-family:'DM Sans',sans-serif; -webkit-font-smoothing:antialiased; }}
body {{ background:transparent; overflow:visible; padding-bottom:8px; }}
.ia-wrap {{
    background:#fff;
    border:1px solid #e5e7eb;
    border-radius:12px;
    overflow:hidden;
}}
.ia-header {{
    padding:14px 18px;
    font-size:14px; font-weight:800; color:#1a2e4a;
    text-transform:uppercase; letter-spacing:0.3px;
    border-bottom:1px solid #e5e7eb;
    background:#fff;
}}
.tabs {{
    display:flex;
    border-bottom:1px solid #e5e7eb;
    background:#f9fafb;
}}
.tab {{
    flex:1; padding:11px 0; text-align:center;
    font-size:14px; font-weight:600; color:#9ca3af;
    cursor:pointer; border:none; background:transparent;
    border-bottom:2px solid transparent; margin-bottom:-1px;
    font-family:'DM Sans',sans-serif; transition:color 0.15s;
}}
.tab:hover {{ color:#374151; background:#f3f4f6; }}
.tab.active {{
    color:#1a2e4a;
    border-bottom:2px solid #3a9fd6;
    background:#fff;
}}
.panel {{ display:none; }}
.panel.active {{ display:block; }}
</style>

<div class="ia-wrap">
    <div class="ia-header">Análise de Conteúdos</div>
    <div class="tabs">
        <button class="tab active"        onclick="showTab('geral',this)">Analisar Postagens 🖼️</button>
        <button class="tab"        onclick="showTab('criativo',this)">Analisar Criativos 🎨</button>
        <button class="tab"        onclick="showTab('copy',this)">Analisar Copys 📝</button>
    </div>
    <div id="panel-geral" class="panel">
        {_panel_ia(geral_html, "Gerar Análise de Postagens 🤖", f"__geral_{idx}__")}
    </div>
    <div id="panel-criativo" class="panel active">
        {_panel_ia(criativo_html, "Gerar Análise de Criativos 🤖", f"__criativo_{idx}__")}
    </div>
    <div id="panel-copy" class="panel">
        {_panel_ia(copy_html, "Gerar Análise de Copys 🤖", f"__copy_{idx}__")}
    </div>
</div>

<script>
function enviarAltura() {{
    var h = document.documentElement.scrollHeight || document.body.scrollHeight;
    window.parent.postMessage({{ type: 'setHeight', height: h }}, '*');
}}

function showTab(name, el) {{
    document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active'); }});
    document.querySelectorAll('.panel').forEach(function(p) {{ p.classList.remove('active'); }});
    document.getElementById('panel-' + name).classList.add('active');
    el.classList.add('active');
    setTimeout(enviarAltura, 50);
}}

var ro = new ResizeObserver(enviarAltura);
ro.observe(document.body);
document.addEventListener('DOMContentLoaded', enviarAltura);
window.addEventListener('load', enviarAltura);
setTimeout(enviarAltura, 100);
setTimeout(enviarAltura, 500);
setTimeout(enviarAltura, 1000);
</script>
"""
            components.html(ia_html, height=420, scrolling=False)

            st.markdown(f"""
<script>
(function() {{
    var listeners = window._iaListeners || 0;
    if (listeners >= {idx + 1}) return;
    window._iaListeners = listeners + 1;

    window.addEventListener('message', function(e) {{
        if (!e.data || e.data.type !== 'setHeight') return;
        var iframes = document.querySelectorAll('iframe');
        iframes.forEach(function(iframe) {{
            try {{
                if (iframe.contentWindow === e.source) {{
                    iframe.style.height = e.data.height + 'px';
                    iframe.style.minHeight = 'unset';
                    iframe.style.maxHeight = 'none';
                }}
            }} catch(err) {{}}
        }});
    }});
}})();
</script>
""", unsafe_allow_html=True)
