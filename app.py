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
    """Retorna a cor do avatar de acordo com o índice, sempre respeitando a paleta global."""
    return AVATAR_COLORS[index % len(AVATAR_COLORS)]

def get_minha_empresa_color() -> str:
    """Cor fixa para 'Minha Empresa' (sempre a primeira da paleta)."""
    return AVATAR_COLORS[0]

def get_concorrente_color(concorrente_index: int) -> str:
    """Cor para concorrente, começando do índice 1 da paleta (após 'Minha Empresa')."""
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
    """Garante que a URL tenha schema HTTP para Trafilatura."""
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
    """Carrega empresa e concorrentes salvos no Supabase."""
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
            "servicos": []
        },
        "concorrentes": [],
        "metricas_redes": {},
    }

def salvar_dados_usuario(user_id: str):
    """Upsert dos dados no Supabase."""
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
    st.session_state.auth_tab = "login"   # "login" | "cadastro"
if "dados" not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "", "setor": "Marketing", "tipo": "",
            "estado": "", "cidade": "",
            "instagram": "@", "fb_page": "", "site": "",
            "servicos": []
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
    st.session_state.relatorio_sites = {}   # cache: {url: conteudo_extraido}
if "relatorio_gemini" not in st.session_state:
    st.session_state.relatorio_gemini = ""
if "analises_salvas" not in st.session_state:
    st.session_state.analises_salvas = []
    
empresa = st.session_state.dados["minha_empresa"]
campos_padrao = {
    "estado": "", "cidade": "", "instagram": "@",
    "fb_page": "", "site": "", "servicos": []
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

        # Tenta trafilatura primeiro
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

        # Fallback: extrai texto bruto removendo tags
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
    """Gera relatório comparativo de posicionamento usando Gemini."""
    if gemini_model is None:
        return "Erro: Chave API Gemini não configurada."

    # Monta contexto de cada site
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

/* ── BOTÕES PADRÃO (secundário) ── */
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

/* ── BOTÃO PRIMARY ── */
section.main div.stButton > button[kind="primary"],
[data-testid="stMainBlockContainer"] button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: #0780c0 !important;
    color: #ffffff !important;
    border: none !important;
}
section.main div.stButton > button[kind="primary"]:hover,
[data-testid="stMainBlockContainer"] button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    background: #065f9e !important;
    color: #ffffff !important;
}

/* ── BOTÕES DE FORMULÁRIO ── */
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

/* ── Tabs ── */
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

/* ── Logo do sidebar ── */
.sb-logo { padding:22px 18px 16px; border-bottom:1px solid #1e2530; margin-bottom:8px; }
.sb-logo-sub { font-size:8.4px; color:#3a9fd6; font-weight:600; letter-spacing:2px; text-transform:uppercase; text-align:center; font-family:'DM Sans',sans-serif; }

/* ── Botões invisíveis do sidebar ── */
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

/* ── Containers com borda — fundo branco forçado ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border-color: #e5e7eb !important;
    border-radius: 12px !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div > div,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    background: #ffffff !important;
}
[data-testid="stVerticalBlockBorderWrapper"] iframe,
[data-testid="stVerticalBlockBorderWrapper"] canvas,
[data-testid="stVerticalBlockBorderWrapper"] img {
    background: transparent !important;
}

/* ── Garante branco em todas as camadas internas do container ── */
[data-testid="stVerticalBlockBorderWrapper"] *:not(iframe):not(canvas):not(img):not(svg):not(path):not(circle):not(rect) {
    background-color: #ffffff !important;
}

/* ── Botões fantasma da página Sites — esconde via atributo data-testid + key ── */
button[data-testid="baseButton-secondary"][kind="secondary"]:has(~ *) {
    display: none !important;
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
    
# No bloco if not st.session_state.logado:
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
                        st.session_state.dados = {
                            "minha_empresa": dados_db["minha_empresa"] or {
                                "nome": "", "setor": "Marketing", "tipo": "",
                                "estado": "", "cidade": "",
                                "instagram": "@", "fb_page": "", "site": "",
                                "servicos": []
                            },
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

    # ── Botões invisíveis — acionados pelo JS do components.html
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

    # ── Menu HTML
    pagina_atual = st.session_state.pagina
    user_email = st.session_state.user.email if st.session_state.user else ""

    def item_html(icon, label, key):
        ativo = "background:#1e2a3a;color:#e5e7eb;" if pagina_atual == key else "color:#8a95a3;"
        return f"""
        <a onclick="nav('{key}')" style="
            display:flex;align-items:center;gap:11px;
            padding:9px 14px;margin:1px 4px;border-radius:7px;
            text-decoration:none;font-size:15px;font-weight:600;
            font-family:'DM Sans',sans-serif;cursor:pointer;
            {ativo}transition:background 0.15s,color 0.15s;
        "
        onmouseover="this.style.background='#1e2a3a';this.style.color='#e5e7eb'"
        onmouseout="this.style.background='{'#1e2a3a' if pagina_atual == key else 'transparent'}';this.style.color='{'#e5e7eb' if pagina_atual == key else '#8a95a3'}'">
            <i class="{icon}" style="width:18px;text-align:center;font-size:15px;flex-shrink:0"></i>
            <span>{label}</span>
        </a>"""

    sep = lambda label: f"""
        <div style="padding:5px 8px;font-size:11px;font-weight:700;text-transform:uppercase;
                    letter-spacing:1.6px;color:#008fcc;font-family:'DM Sans',sans-serif;
                    margin:12px 4px 2px;background:#052f46;border-radius:5px">
            {label}
        </div>"""

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
 
/* ── Logo ── */
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
 
/* ── Section separator ── */
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
 
/* ── Nav items ── */
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
 
/* ── Footer ── */
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
 
<!-- Logo -->
<div class="logo-wrap">
    {'<img src="' + logo_white_src + '" />' if logo_white_src else '<div style="font-size:20px;font-weight:700;color:#fff">Marketylics</div>'}
    <div class="logo-sub">Competitive Intelligence</div>
</div>
 
<!-- ── DADOS PRINCIPAIS ── -->
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
 
<!-- ── ANÁLISE COMPETITIVA ── -->
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
 
<!-- Footer -->
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
        div[data-testid="stForm"] {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 14px !important;
            padding: 28px 32px !important;
            margin-bottom: 0px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
        }
        div[data-testid="stForm"] > div,
        div[data-testid="stForm"] > div > div {
            background: #ffffff !important;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 14px !important;
            padding: 20px 32px !important;
            margin-bottom: 0px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div,
        [data-testid="stVerticalBlockBorderWrapper"] > div > div,
        [data-testid="stVerticalBlockBorderWrapper"] > div > div > div,
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
            background: #ffffff !important;
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

        # ── FORM 1 — Identificação (sem submit button)
        with st.form("cad_empresa", clear_on_submit=False):
            sec_label("Identificação")
            c1, c2 = st.columns(2)
            emp["nome"] = c1.text_input("Nome da Empresa", value=emp["nome"])
            site_digitado = c2.text_input("Site", value=emp["site"])
            emp["site"] = limpar_site(site_digitado)

        st.markdown("<div style='height:12px'/>", unsafe_allow_html=True)

        # ── SETOR — fora do form para reatividade em tempo real
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

        # ── FORM 2 — Redes, Serviços, Localização e botões
        with st.form("cad_empresa_2", clear_on_submit=False):

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
                if emp["nome"].strip():
                    st.session_state.editar_empresa = False
                    salvar_dados_usuario(st.session_state.user.id)
                    st.success("Empresa salva com sucesso!")
                    st.rerun()
                else:
                    st.error("Informe pelo menos o nome da empresa.")

    # ----------------------------------------------------------
    # MODO VISUALIZAÇÃO
    # ----------------------------------------------------------
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
    background: #f3f4f6; border-radius: 9px;
}}
.empresa-ico svg {{ width: 18px; height: 18px; }}
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
                    <span class="empresa-ico">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <defs><linearGradient id="ig_grad" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#f09433"/>
                                <stop offset="100%" stop-color="#bc1888"/>
                            </linearGradient></defs>
                            <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#ig_grad)"/>
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
                    <span class="empresa-ico">
                        <svg viewBox="0 0 24 24" fill="#1877F2">
                            <path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/>
                        </svg>
                    </span>
                    <div>
                        <span class="empresa-lbl">Facebook</span>
                        <span class="empresa-val">{emp['fb_page'] or '—'}</span>
                    </div>
                </div>
                <div class="empresa-row">
                    <span class="empresa-ico">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="2" y1="12" x2="22" y2="12"/>
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                        </svg>
                    </span>
                    <div>
                        <span class="empresa-lbl">Site</span>
                        <span class="empresa-val">{emp['site'] or '—'}</span>
                    </div>
                </div>
            </div>

            <div class="empresa-divider"></div>

            <div class="empresa-col">
                <div class="empresa-sec-title">Localização</div>
                <div class="empresa-row">
                    <span class="empresa-ico">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
        const card = document.getElementById('card');
        const h = card.getBoundingClientRect().height;
        window.parent.document.querySelectorAll('iframe').forEach(function(iframe) {{
            if (iframe.contentWindow === window) {{
                iframe.style.height = (h + 4) + 'px';
            }}
        }});
    }}
    document.addEventListener('DOMContentLoaded', ajustarAltura);
    window.addEventListener('load', ajustarAltura);
    window.addEventListener('resize', ajustarAltura);
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
# CONCORRENTES
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
            ads_manual = st.text_input("ID Manual Ads (Opcional)", value=(concorrente_edit["ads_id"] if concorrente_edit else ""))

            col1, col2 = st.columns(2)
            salvar = col1.form_submit_button("Salvar", use_container_width=True)
            cancelar = col2.form_submit_button("Cancelar", use_container_width=True)

            if cancelar:
                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None
                st.rerun()

            if salvar:
                clean_handle = obter_instagram_handle(insta_handle)
                fb_clean = obter_facebook_handle(fb_p)
                site_clean = limpar_site(u)
                search_term = ads_manual or fb_clean or clean_handle.lstrip("@") or n
                dados_novos = {
                    "nome": n, "url": site_clean,
                    "instagram": clean_handle, "fb_page": fb_clean,
                    "ads_id": search_term
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
        cols = st.columns(2)
        for i, c in enumerate(concorrentes):
            with cols[i % 2]:
                avatar = gerar_avatar(c["nome"])
                # ← USANDO a função global de cor para concorrentes
                cor_avatar = get_concorrente_color(i)

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
}}
body {{ padding-bottom: 4px; }}
.card {{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    overflow: hidden;
}}
.card-body {{ padding: 24px 24px 20px 24px; }}
.header {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding-bottom: 18px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 18px;
}}
.avatar {{
    width: 52px; height: 52px;
    border-radius: 50%;
    background: {cor_avatar};
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 700; color: #fff;
    flex-shrink: 0;
}}
.name {{
    font-size: 17px; font-weight: 700; color: #111827;
    flex: 1; letter-spacing: -0.3px;
}}
.row {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 14px;
}}
.row:last-child {{ margin-bottom: 0; }}
.ico {{
    width: 38px; height: 38px;
    border-radius: 10px;
    background: #f3f4f6;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
.ico svg {{ width: 20px; height: 20px; }}
.info {{ flex: 1; min-width: 0; }}
.lbl {{
    font-size: 11px; color: #9ca3af;
    display: block; margin-bottom: 1px; font-weight: 500;
}}
.val {{
    font-size: 14px; color: #111827;
    font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    display: block;
}}
</style>
</head>
<body>
<div class="card">
  <div class="card-body">
    <div class="header">
      <div class="avatar">{avatar}</div>
      <div class="name">{c['nome']}</div>
    </div>

    <div class="row">
      <div class="ico">
        <svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
      </div>
      <div class="info">
        <span class="lbl">Site</span>
        <span class="val">{c['url'] or '—'}</span>
      </div>
    </div>

    <div class="row">
      <div class="ico" style="background:#fff0f6;">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="ig_{i}" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#f09433"/>
              <stop offset="25%" stop-color="#e6683c"/>
              <stop offset="50%" stop-color="#dc2743"/>
              <stop offset="75%" stop-color="#cc2366"/>
              <stop offset="100%" stop-color="#bc1888"/>
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#ig_{i})"/>
          <circle cx="12" cy="12" r="4.5" stroke="white" stroke-width="1.8" fill="none"/>
          <circle cx="17.5" cy="6.5" r="1.2" fill="white"/>
        </svg>
      </div>
      <div class="info">
        <span class="lbl">Instagram</span>
        <span class="val">{c['instagram'] or '—'}</span>
      </div>
    </div>

    <div class="row">
      <div class="ico" style="background:#e8f0fe;">
        <svg viewBox="0 0 24 24" fill="#1877F2">
          <path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/>
        </svg>
      </div>
      <div class="info">
        <span class="lbl">Facebook</span>
        <span class="val">{c['fb_page'] or '—'}</span>
      </div>
    </div>

  </div>
</div>
</body>
</html>"""

                components.html(card_html, height=280, scrolling=False)

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
# VISÃO GERAL
# ---------------------------------------------------

elif st.session_state.pagina == "geral":

    periodo, data_inicio = cabecalho_analise("📊 Visão Geral", "Resumo dos concorrentes cadastrados")
    concorrentes = st.session_state.dados["concorrentes"]
    emp = st.session_state.dados["minha_empresa"]

    if not concorrentes:
        st.warning("Nenhum concorrente cadastrado ainda.")
    else:
        st.markdown("<div style='font-size:13px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px'>Minha Empresa</div>", unsafe_allow_html=True)
        cor_emp = get_minha_empresa_color()
        st.markdown(f"""
        <div style='background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;display:flex;align-items:center;gap:16px;margin-bottom:24px'>
            <div style='width:40px;height:40px;border-radius:50%;background:{cor_emp};display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;flex-shrink:0'>{gerar_avatar(emp['nome'])}</div>
            <div>
                <div style='font-size:16px;font-weight:600;color:#111827'>{emp['nome'] or '—'}</div>
                <div style='font-size:13px;color:#6b7280'>{emp['setor']}{' · ' + emp['tipo'] if emp['tipo'] else ''} · {emp['cidade'] or ''}{', ' + emp['estado'] if emp['estado'] else ''}</div>
            </div>
            <div style='margin-left:auto;display:flex;gap:24px'>
                <div style='text-align:center'><div style='font-size:11px;color:#9ca3af;margin-bottom:2px'>Instagram</div><div style='font-size:14px;font-weight:500;color:#111827'>{emp['instagram'] or '—'}</div></div>
                <div style='text-align:center'><div style='font-size:11px;color:#9ca3af;margin-bottom:2px'>Site</div><div style='font-size:14px;font-weight:500;color:#111827'>{emp['site'] or '—'}</div></div>
                <div style='text-align:center'><div style='font-size:11px;color:#9ca3af;margin-bottom:2px'>Serviços</div><div style='font-size:14px;font-weight:500;color:#111827'>{len(emp['servicos'])}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:13px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px'>Concorrentes</div>", unsafe_allow_html=True)
        df = pd.DataFrame(concorrentes)
        df.columns = ["Nome", "Site", "Instagram", "Facebook", "Ads ID"]
        st.dataframe(df[["Nome", "Site", "Instagram", "Facebook"]], use_container_width=True, height=min(400, 60 + len(concorrentes) * 55))

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
<div class="titulo">Confronto de Sites</div>
<div class="sub">Análise comparativa de posicionamento via IA.</div>
""", height=65)

    with h2:
        gerar_btn = st.button(
            "Gerar Relatório",
            type="primary",
            use_container_width=True,
        )
        ultimo_relatorio = st.session_state.get("sites_ultima_geracao", "")
        if ultimo_relatorio:
            st.markdown(
                f"<div style='font-size:13px;color:#6b7280;text-align:center;margin-top:-8px'>"
                f"🕒 Última análise: <b>{ultimo_relatorio}</b></div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        "<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 20px 0'/>",
        unsafe_allow_html=True,
    )
 
    # ── Monta lista de sites
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
 
    # Inicializa estados de análise individual
    for idx_s, s in enumerate(sites_disponiveis):
        chave = f"sites_analise_{idx_s}"
        if chave not in st.session_state:
            st.session_state[chave] = ""

    # ── CSS estático para esconder botões fantasma pelo key do Streamlit
    ghost_css = "\n".join([
        f".st-key-btn_site_ia_{i} {{ display: none !important; }}"
        for i in range(len(sites_disponiveis))
    ])
    st.markdown(f"<style>{ghost_css}</style>", unsafe_allow_html=True)

    # ── Botões fantasma — criados ANTES dos cards
    site_ia_triggers = {}
    for idx_s in range(len(sites_disponiveis)):
        triggered = st.button(
            f"_site_ia_trigger_{idx_s}_",
            key=f"btn_site_ia_{idx_s}",
            use_container_width=False,
        )
        site_ia_triggers[idx_s] = triggered

    # ── Cards
    for idx_s, s in enumerate(sites_disponiveis):
        with cols_sites[idx_s % 4]:
            is_minha  = s["tipo"] == "minha"
            cor_avatar = get_minha_empresa_color() if is_minha else get_concorrente_color(idx_s - 1)
            badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
            badge_txt = "#1d4ed8" if is_minha else "#6b7280"
            badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
            badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
            avatar_letras = gerar_avatar(s["nome"])

            components.html(f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background:transparent; font-family:'DM Sans',sans-serif; -webkit-font-smoothing:antialiased; overflow:visible; }}
.card {{
    background:#fff; border:1px solid #e5e7eb; border-radius:14px;
    overflow:hidden; padding:0;
}}
.card-header {{
    display:flex; align-items:center; gap:12px;
    padding:16px 16px 14px 16px;
    border-bottom:1px solid #f3f4f6;
}}
.avatar {{
    width:44px; height:44px; border-radius:50%;
    background:{cor_avatar};
    display:flex; align-items:center; justify-content:center;
    font-size:16px; font-weight:700; color:#fff; flex-shrink:0;
    letter-spacing:0.5px;
}}
.nome-wrap {{ flex:1; min-width:0; }}
.nome {{
    font-size:16px; font-weight:700; color:#111827;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    letter-spacing:-0.2px;
}}
.badge {{
    display:inline-block;
    background:{badge_bg}; color:{badge_txt};
    border:1px solid {badge_brd};
    padding:2px 10px; border-radius:20px;
    font-size:11px; font-weight:600; margin-top:4px;
}}
.url-row {{
    padding:10px 16px;
    font-size:15px; color:#0d1117;
    word-break:break-all;
    border-bottom:1px solid #f3f4f6;
    display:flex; align-items:center; gap:6px;
}}
.url-label {{
    font-size:15px; font-weight:700; color:#0d1117;
    flex-shrink:0;
}}
.preview-wrap {{
    margin:12px 12px 0 12px;
    border-radius:8px; overflow:hidden;
    border:1px solid #e5e7eb; background:#f9fafb;
    min-height:110px;
}}
.preview-wrap img {{
    width:100%; display:block; border-radius:8px;
}}
.btn-wrap {{
    padding:12px 12px 14px 12px;
}}
.btn-analisar {{
    width:100%; padding:10px 0;
    border:1px solid #3a9fd6; border-radius:8px;
    background:#eff6ff; font-size:14px; font-weight:700; color:#1d4ed8;
    cursor:pointer; font-family:'DM Sans',sans-serif;
    transition:background 0.15s;
    display:flex; align-items:center; justify-content:center; gap:6px;
}}
.btn-analisar:hover {{ background:#dbeafe; }}
</style>
<div class="card">
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
    var card = document.querySelector('.card');
    if (!card) return;
    var h = card.getBoundingClientRect().height;
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(f) {{
        try {{ if (f.contentWindow === window) f.style.height = (h + 8) + 'px'; }} catch(e) {{}}
    }});
}}
document.addEventListener('DOMContentLoaded', ajustarAltura);
window.addEventListener('load', ajustarAltura);
setTimeout(ajustarAltura, 300);
setTimeout(ajustarAltura, 800);
</script>
""", height=380, scrolling=False)

            # ── Processa clique do botão fantasma
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

            # ── Exibe análise individual
            analise_ind = st.session_state.get(f"sites_analise_{idx_s}", "")
            if analise_ind:
                st.markdown(f"""
                <div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;
                            padding:14px 16px;font-size:13px;color:#374151;line-height:1.75;
                            max-height:280px;overflow-y:auto;margin-top:6px;margin-bottom:4px'>
                    {analise_ind.replace(chr(10), "<br>")}
                </div>
                """, unsafe_allow_html=True)

    # ── Gerar relatório geral
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
 
    # ── Exibe relatório geral
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

    # ── Separador antes das análises salvas
    st.markdown(
        "<div style='margin:16px 0 0 0;border-top:1px solid #e5e7eb'/>",
        unsafe_allow_html=True,
    )

    analises = st.session_state.get("analises_salvas", [])
    analises_gerais      = [(i, a) for i, a in enumerate(analises) if a.get("tipo", "geral") == "geral"]
    analises_individuais = [(i, a) for i, a in enumerate(analises) if a.get("tipo") == "individual"]

    # ── Botões fantasma para remover análises salvas
    acoes_salvas = {}
    for i, a in enumerate(analises):
        acoes_salvas[f"rm_{i}"] = st.button(f"_rm_analise_{i}_", key=f"btn_rm_analise_{i}")

    # CSS para esconder botões fantasma de remoção
    rm_css = "\n".join([
        f".st-key-btn_rm_analise_{i} {{ display: none !important; }}"
        for i in range(len(analises))
    ])
    st.markdown(f"<style>{rm_css}</style>", unsafe_allow_html=True)

    # Processa remoções
    for i in range(len(analises) - 1, -1, -1):
        if acoes_salvas.get(f"rm_{i}"):
            st.session_state.analises_salvas.pop(i)
            st.rerun()

    # ── Monta HTML dos itens para cada aba
    def _card_analise(idx_real, analise, tipo):
        titulo   = analise.get("titulo", "—")
        data     = analise.get("data", "—")
        sites_str = ", ".join(analise.get("sites", []))
        relatorio = (analise.get("relatorio") or "").replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        icone    = "📄" if tipo == "geral" else "🌐"

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

.wrap {{
    background:#fff;
    border:1px solid #e5e7eb;
    border-radius:12px;
    overflow:hidden;
}}
.wrap-header {{
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
.panel {{ display:none; padding:12px 14px; }}
.panel.active {{ display:block; }}

.item {{
    border:1px solid #e5e7eb;
    border-radius:10px;
    margin-bottom:10px;
    overflow:hidden;
    background:#fff;
}}
.item-header {{
    display:flex; align-items:center; justify-content:space-between;
    padding:14px 16px; cursor:pointer;
    background:#f9fafb;
    transition:background 0.12s;
}}
.item-header:hover {{ background:#f3f4f6; }}
.item-left {{
    display:flex; align-items:center; gap:12px; flex:1; min-width:0;
}}
.item-icon {{ font-size:18px; flex-shrink:0; }}
.item-titulo {{
    font-size:14px; font-weight:700; color:#111827;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}}
.item-meta {{
    font-size:12px; color:#9ca3af; margin-top:2px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}}
.item-chevron {{
    font-size:11px; color:#9ca3af; flex-shrink:0; margin-left:10px;
    transition:transform 0.2s;
}}
.item-chevron.open {{ transform:rotate(180deg); }}
.item-body {{
    padding:16px;
    border-top:1px solid #f3f4f6;
}}
.item-relatorio {{
    font-size:13px; color:#374151; line-height:1.75;
    max-height:320px; overflow-y:auto;
    padding-right:4px; margin-bottom:14px;
}}
.item-acoes {{
    display:flex; gap:10px; padding-top:12px;
    border-top:1px solid #f3f4f6;
}}
.btn-dl {{
    flex:1; padding:9px; border-radius:8px;
    border:1px solid #3a9fd6; background:#eff6ff;
    font-size:13px; font-weight:700; color:#1d4ed8;
    cursor:pointer; font-family:'DM Sans',sans-serif;
    transition:background 0.15s;
}}
.btn-dl:hover {{ background:#dbeafe; }}
.btn-rm {{
    padding:9px 16px; border-radius:8px;
    border:1px solid #fca5a5; background:#fef2f2;
    font-size:13px; font-weight:700; color:#dc2626;
    cursor:pointer; font-family:'DM Sans',sans-serif;
    transition:background 0.15s;
    white-space:nowrap;
}}
.btn-rm:hover {{ background:#fee2e2; }}
</style>

<div class="wrap">
    <div class="wrap-header">Análises Salvas</div>
    <div class="tabs">
        <button class="tab active" onclick="showTab('geral', this)">Análise Geral 📊</button>
        <button class="tab"        onclick="showTab('individual', this)">Análise por Site 🔍</button>
    </div>
    <div id="panel-geral" class="panel active">
        {itens_geral}
    </div>
    <div id="panel-individual" class="panel">
        {itens_individual}
    </div>
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
    iframes.forEach(function(f) {{
        try {{ if (f.contentWindow === window) f.style.height = (h + 8) + 'px'; }} catch(e) {{}}
    }});
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
# Substitui o bloco: elif st.session_state.pagina == "ads":
# Cole este bloco no lugar do bloco "ads" existente no seu app.py
# ---------------------------------------------------
 
elif st.session_state.pagina == "ads":
 
    import datetime as _dt
 
    emp   = st.session_state.dados["minha_empresa"]
    concs = st.session_state.dados["concorrentes"]
 
    # ── Cabeçalho
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
<div class="titulo">Biblioteca de Ads</div>
<div class="sub">Criativos, copies e formatos dos anúncios ativos dos seus concorrentes.</div>
""", height=65)
 
    with h2:
        st.markdown("<div style='padding-top:6px'/>", unsafe_allow_html=True)
        buscar_btn = st.button("🔍 Buscar Anúncios", type="primary", use_container_width=True)
 
    st.markdown(
        "<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 20px 0'/>",
        unsafe_allow_html=True,
    )
 
    # ── Verifica token
    META_TOKEN = st.secrets.get("META_ACCESS_TOKEN", "")
    if not META_TOKEN:
        st.warning(
            "⚠️ Configure `META_ACCESS_TOKEN` no Streamlit Secrets.\n\n"
            "Formato: `APP_ID|APP_SECRET` (ex: `1234567890|abc123def456`)"
        )
        st.stop()
 
    # ── Monta lista de empresas
    todas_empresas = []
    if emp.get("nome"):
        ads_id_emp = emp.get("fb_page") or emp.get("instagram", "").lstrip("@") or emp.get("nome", "")
        todas_empresas.append({
            "nome": emp["nome"],
            "ads_id": ads_id_emp,
            "tipo": "minha",
            "idx": 0,
        })
    for i, c in enumerate(concs):
        todas_empresas.append({
            "nome": c["nome"],
            "ads_id": c.get("ads_id", "") or c.get("fb_page", "") or c.get("nome", ""),
            "tipo": "concorrente",
            "idx": i,
        })
 
    if not todas_empresas:
        st.info("Cadastre sua empresa e concorrentes para visualizar anúncios.")
        st.stop()
 
    # ── Cache de anúncios no session_state
    if "ads_cache" not in st.session_state:
        st.session_state.ads_cache = {}        # { ads_id: { "data": [...], "ts": "..." } }
    if "ads_erro" not in st.session_state:
        st.session_state.ads_erro = {}         # { ads_id: "mensagem de erro" }
    if "ads_selecionado" not in st.session_state:
        st.session_state.ads_selecionado = None  # ads_id do painel aberto
 
    # ── Função busca Meta Ad Library
    def buscar_ads_meta(search_term: str, token: str, limit: int = 20) -> tuple:
        """
        Retorna (lista_de_anuncios, erro_str)
        Cada anúncio: { id, page_name, status, body, title, link_url,
                        image_url, video_url, formato, plataformas,
                        data_inicio, impressoes }
        """
        url = "https://graph.facebook.com/v21.0/ads_archive"
        params = {
            "search_terms": search_term,
            "ad_active_status": "ACTIVE",
            "ad_reached_countries": '["BR"]',
            "fields": (
                "id,page_name,ad_creative_bodies,ad_creative_link_captions,"
                "ad_creative_link_descriptions,ad_creative_link_titles,"
                "ad_snapshot_url,ad_delivery_start_time,"
                "impressions,publisher_platforms,media_type"
            ),
            "limit": limit,
            "access_token": token,
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
 
            if "error" in data:
                return [], data["error"].get("message", "Erro desconhecido da API")
 
            ads_raw = data.get("data", [])
            resultado = []
            for ad in ads_raw:
                bodies = ad.get("ad_creative_bodies") or []
                titles = ad.get("ad_creative_link_titles") or []
                descs  = ad.get("ad_creative_link_descriptions") or []
                caps   = ad.get("ad_creative_link_captions") or []
                plats  = ad.get("publisher_platforms") or []
                media  = ad.get("media_type", "")
 
                # Normaliza formato
                if media in ("VIDEO", "video"):
                    fmt = "Vídeo 🎬"
                elif media in ("IMAGE", "image"):
                    fmt = "Imagem 🖼️"
                elif plats:
                    fmt = "Carrossel 🎠" if len(bodies) > 1 else "Imagem 🖼️"
                else:
                    fmt = "Desconhecido"
 
                # Impressões
                imp = ad.get("impressions", {})
                imp_str = ""
                if isinstance(imp, dict):
                    lo = imp.get("lower_bound", "")
                    hi = imp.get("upper_bound", "")
                    if lo or hi:
                        imp_str = f"{lo}–{hi}"
 
                resultado.append({
                    "id":           ad.get("id", ""),
                    "page_name":    ad.get("page_name", ""),
                    "body":         bodies[0] if bodies else "",
                    "bodies":       bodies,
                    "title":        titles[0] if titles else "",
                    "description":  descs[0]  if descs  else "",
                    "caption":      caps[0]   if caps   else "",
                    "snapshot_url": ad.get("ad_snapshot_url", ""),
                    "data_inicio":  ad.get("ad_delivery_start_time", "")[:10] if ad.get("ad_delivery_start_time") else "",
                    "impressoes":   imp_str,
                    "plataformas":  plats,
                    "formato":      fmt,
                    "media_type":   media,
                })
 
            return resultado, None
 
        except Exception as e:
            return [], str(e)
 
    # ── Disparar busca
    if buscar_btn:
        st.session_state.ads_cache = {}
        st.session_state.ads_erro  = {}
        with st.spinner("Buscando anúncios na Meta Ad Library…"):
            for emp_item in todas_empresas:
                term = emp_item["ads_id"]
                if not term:
                    continue
                ads, erro = buscar_ads_meta(term, META_TOKEN)
                if erro:
                    st.session_state.ads_erro[term] = erro
                else:
                    st.session_state.ads_cache[term] = {
                        "data": ads,
                        "ts": _dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "nome": emp_item["nome"],
                    }
 
    # ── Seletor de empresa (tabs)
    tab_labels = [e["nome"] for e in todas_empresas]
    if tab_labels:
        abas_ads = st.tabs(tab_labels)
    else:
        st.info("Nenhuma empresa cadastrada.")
        st.stop()
 
    # ── Funções de formatação
    def _plat_icons(plats):
        icons = {
            "facebook":  "🔵 Facebook",
            "instagram": "📸 Instagram",
            "messenger": "💬 Messenger",
            "audience_network": "🌐 Audience Network",
        }
        return " · ".join(icons.get(p, p.capitalize()) for p in (plats or []))
 
    def _truncar(txt, n=120):
        if not txt:
            return "—"
        return txt[:n] + "…" if len(txt) > n else txt
 
    # ── Função render anúncios de uma empresa
    def render_ads_empresa(emp_item):
        term     = emp_item["ads_id"]
        nome     = emp_item["nome"]
        is_minha = emp_item["tipo"] == "minha"
        idx_cor  = emp_item["idx"]
        cor_av   = get_minha_empresa_color() if is_minha else get_concorrente_color(idx_cor)
        avatar   = gerar_avatar(nome)
 
        # Erro de busca
        if term in st.session_state.ads_erro:
            st.error(f"Erro ao buscar anúncios de **{nome}**: {st.session_state.ads_erro[term]}")
            _link_fallback(term, nome)
            return
 
        # Ainda sem dados
        if term not in st.session_state.ads_cache:
            _estado_vazio(nome, term, cor_av, avatar, is_minha)
            return
 
        cache_entry = st.session_state.ads_cache[term]
        ads_list    = cache_entry["data"]
        ts          = cache_entry["ts"]
 
        # Cabeçalho da empresa
        badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
        badge_txt = "#1d4ed8" if is_minha else "#6b7280"
        badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
        badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
 
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:14px;margin-bottom:20px;
                    padding:16px 20px;background:#fff;border:1px solid #e5e7eb;
                    border-radius:12px'>
            <div style='width:44px;height:44px;border-radius:50%;background:{cor_av};
                        display:flex;align-items:center;justify-content:center;
                        font-size:16px;font-weight:700;color:#fff;flex-shrink:0'>{avatar}</div>
            <div style='flex:1'>
                <div style='font-size:17px;font-weight:700;color:#111827'>{nome}</div>
                <div style='display:flex;align-items:center;gap:8px;margin-top:4px'>
                    <span style='background:{badge_bg};color:{badge_txt};border:1px solid {badge_brd};
                                 padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>
                        {badge_lbl}
                    </span>
                    <span style='font-size:12px;color:#9ca3af'>Busca: <b>{term}</b></span>
                    <span style='font-size:12px;color:#9ca3af'>· Última busca: {ts}</span>
                </div>
            </div>
            <div style='text-align:right;flex-shrink:0'>
                <div style='font-size:28px;font-weight:800;color:#111827'>{len(ads_list)}</div>
                <div style='font-size:12px;color:#9ca3af'>anúncios ativos</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
        if not ads_list:
            st.info(f"Nenhum anúncio ativo encontrado para **{nome}** com o termo `{term}`.")
            _link_fallback(term, nome)
            return
 
        # Filtros
        fcol1, fcol2, fcol3 = st.columns([3, 2, 2])
        with fcol1:
            busca_texto = st.text_input(
                "Filtrar por texto",
                placeholder="Pesquisar no copy…",
                key=f"ads_busca_{term}",
                label_visibility="collapsed",
            )
        with fcol2:
            formatos_disponiveis = sorted(set(a["formato"] for a in ads_list))
            filtro_fmt = st.selectbox(
                "Formato",
                ["Todos os formatos"] + formatos_disponiveis,
                key=f"ads_fmt_{term}",
                label_visibility="collapsed",
            )
        with fcol3:
            plats_todas = sorted(set(p for a in ads_list for p in (a["plataformas"] or [])))
            filtro_plat = st.selectbox(
                "Plataforma",
                ["Todas as plataformas"] + [p.capitalize() for p in plats_todas],
                key=f"ads_plat_{term}",
                label_visibility="collapsed",
            )
 
        # Aplica filtros
        ads_filtrados = ads_list
        if busca_texto:
            q = busca_texto.lower()
            ads_filtrados = [
                a for a in ads_filtrados
                if q in (a.get("body") or "").lower()
                or q in (a.get("title") or "").lower()
                or q in (a.get("description") or "").lower()
            ]
        if filtro_fmt and filtro_fmt != "Todos os formatos":
            ads_filtrados = [a for a in ads_filtrados if a["formato"] == filtro_fmt]
        if filtro_plat and filtro_plat != "Todas as plataformas":
            filtro_plat_lower = filtro_plat.lower()
            ads_filtrados = [a for a in ads_filtrados if filtro_plat_lower in (a["plataformas"] or [])]
 
        if not ads_filtrados:
            st.warning("Nenhum anúncio encontrado com os filtros aplicados.")
            return
 
        # ── Estatísticas rápidas
        n_video  = sum(1 for a in ads_filtrados if "Vídeo" in a["formato"])
        n_imagem = sum(1 for a in ads_filtrados if "Imagem" in a["formato"])
        n_outros = len(ads_filtrados) - n_video - n_imagem
 
        st.markdown(f"""
        <div style='display:flex;gap:12px;margin-bottom:20px'>
            <div style='flex:1;background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                        padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#15803d'>{len(ads_filtrados)}</div>
                <div style='font-size:12px;color:#16a34a;font-weight:600'>Total Exibido</div>
            </div>
            <div style='flex:1;background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;
                        padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#92400e'>{n_imagem}</div>
                <div style='font-size:12px;color:#b45309;font-weight:600'>Imagens</div>
            </div>
            <div style='flex:1;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                        padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#1e40af'>{n_video}</div>
                <div style='font-size:12px;color:#1d4ed8;font-weight:600'>Vídeos</div>
            </div>
            <div style='flex:1;background:#f5f3ff;border:1px solid #c4b5fd;border-radius:10px;
                        padding:12px 16px;text-align:center'>
                <div style='font-size:22px;font-weight:800;color:#5b21b6'>{n_outros}</div>
                <div style='font-size:12px;color:#6d28d9;font-weight:600'>Outros</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
        # ── Grid de cards de anúncios
        cols_ads = st.columns(3)
        for j, ad in enumerate(ads_filtrados):
            with cols_ads[j % 3]:
                body_preview  = _truncar(ad["body"], 100)
                title_preview = _truncar(ad["title"], 60)
                desc_preview  = _truncar(ad["description"], 80)
                plat_txt      = _plat_icons(ad["plataformas"])
                snapshot_url  = ad.get("snapshot_url", "")
 
                # Badge formato
                fmt = ad["formato"]
                if "Vídeo" in fmt:
                    fmt_bg, fmt_txt, fmt_brd = "#eff6ff", "#1d4ed8", "#bfdbfe"
                elif "Imagem" in fmt:
                    fmt_bg, fmt_txt, fmt_brd = "#fef3c7", "#92400e", "#fcd34d"
                else:
                    fmt_bg, fmt_txt, fmt_brd = "#f5f3ff", "#5b21b6", "#c4b5fd"
 
                # Monta copy HTML
                copy_sections = []
                if ad["title"]:
                    copy_sections.append(
                        f"<div style='font-size:13px;font-weight:700;color:#111827;margin-bottom:4px'>{title_preview}</div>"
                    )
                if ad["body"]:
                    copy_sections.append(
                        f"<div style='font-size:13px;color:#374151;line-height:1.6;font-style:italic'>{body_preview}</div>"
                    )
                if ad["description"]:
                    copy_sections.append(
                        f"<div style='font-size:12px;color:#6b7280;margin-top:4px'>{desc_preview}</div>"
                    )
                copy_html_inner = (
                    "\n".join(copy_sections)
                    if copy_sections
                    else "<div style='font-size:13px;color:#9ca3af;font-style:italic'>Sem copy disponível</div>"
                )
 
                st.markdown(f"""
                <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                            overflow:hidden;margin-bottom:4px;height:100%'>
                    <!-- Topo do card -->
                    <div style='padding:14px 16px 10px 16px;border-bottom:1px solid #f3f4f6'>
                        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px'>
                            <span style='background:{fmt_bg};color:{fmt_txt};border:1px solid {fmt_brd};
                                         padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700'>
                                {fmt}
                            </span>
                            <span style='font-size:11px;color:#9ca3af'>{ad["data_inicio"] or "—"}</span>
                        </div>
                        <!-- Page name -->
                        <div style='font-size:12px;color:#6b7280;margin-bottom:2px'>
                            📄 {ad["page_name"] or nome}
                        </div>
                        <!-- Impressões -->
                        {"<div style='font-size:12px;color:#059669;font-weight:600'>👁️ " + ad["impressoes"] + " impressões</div>" if ad["impressoes"] else ""}
                    </div>
                    <!-- Copy -->
                    <div style='padding:14px 16px;min-height:90px'>
                        {copy_html_inner}
                    </div>
                    <!-- Plataformas -->
                    <div style='padding:0 16px 10px 16px'>
                        <div style='font-size:11px;color:#9ca3af'>{plat_txt or "—"}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
                # Botão para abrir criativo no Facebook
                if snapshot_url:
                    st.link_button(
                        "🔗 Ver criativo completo",
                        snapshot_url,
                        use_container_width=True,
                    )
                else:
                    fallback_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&q={term}&search_type=keyword_unordered"
                    st.link_button(
                        "🔍 Abrir Ad Library",
                        fallback_url,
                        use_container_width=True,
                    )
 
                st.markdown("<div style='height:12px'/>", unsafe_allow_html=True)
 
        # ── Análise IA dos anúncios
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e5e7eb;margin:8px 0 20px 0'/>",
            unsafe_allow_html=True,
        )
 
        chave_ia_ads = f"ia_ads_{term}"
        if chave_ia_ads not in st.session_state:
            st.session_state[chave_ia_ads] = ""
 
        # Botão fantasma para análise IA
        st.markdown(f"""
        <style>
        .st-key-btn_ia_ads_{term.replace('-','_').replace('.','_').replace('|','_')} {{
            position: fixed !important; top: -9999px !important; left: -9999px !important;
            width: 1px !important; height: 1px !important; overflow: hidden !important;
            opacity: 0 !important; pointer-events: none !important; visibility: hidden !important;
        }}
        </style>
        """, unsafe_allow_html=True)
 
        safe_term = term.replace("-","_").replace(".","_").replace("|","_").replace("@","")
 
        ia_ads_btn = st.button(
            f"__ia_ads_{safe_term}__",
            key=f"btn_ia_ads_{safe_term}",
            use_container_width=True,
        )
 
        # Resumo dos anúncios para o prompt
        resumo_ads = "\n".join([
            f"- [{a['formato']}] Título: {a['title'][:60] if a['title'] else '—'} | "
            f"Copy: {a['body'][:80] if a['body'] else '—'} | "
            f"Impressões: {a['impressoes'] or '—'} | Plataformas: {', '.join(a['plataformas'] or [])}"
            for a in ads_filtrados[:15]
        ])
 
        ia_result_html = st.session_state.get(chave_ia_ads, "").replace("\n", "<br>")
 
        def _btn_ia_trigger(safe_term_val):
            return f"__ia_ads_{safe_term_val}__"
 
        ia_panel_content = ""
        if ia_result_html:
            ia_panel_content = f"""
            <div style='padding:16px 18px;font-size:14px;color:#374151;line-height:1.75;
                        max-height:400px;overflow-y:auto'>
                {ia_result_html}
            </div>
            <div style='padding:0 18px 18px 18px'>
                <button onclick="
                    const btns = window.parent.document.querySelectorAll('button');
                    for (const b of btns) {{
                        if (b.innerText.trim() === '__ia_ads_{safe_term}__') {{ b.click(); break; }}
                    }}
                " style='width:100%;padding:10px;border:1px solid #3a9fd6;border-radius:8px;
                          background:#eff6ff;font-size:14px;font-weight:700;color:#1d4ed8;
                          cursor:pointer;font-family:DM Sans,sans-serif'>
                    🔄 Gerar Nova Análise
                </button>
            </div>
            """
        else:
            ia_panel_content = f"""
            <div style='padding:24px 18px;text-align:center;font-size:14px;color:#9ca3af'>
                Clique no botão abaixo para uma análise estratégica dos anúncios com IA.
            </div>
            <div style='padding:0 18px 18px 18px'>
                <button onclick="
                    const btns = window.parent.document.querySelectorAll('button');
                    for (const b of btns) {{
                        if (b.innerText.trim() === '__ia_ads_{safe_term}__') {{ b.click(); break; }}
                    }}
                " style='width:100%;padding:10px;border:1px solid #3a9fd6;border-radius:8px;
                          background:#eff6ff;font-size:14px;font-weight:700;color:#1d4ed8;
                          cursor:pointer;font-family:DM Sans,sans-serif'>
                    🤖 Analisar Anúncios com IA
                </button>
            </div>
            """
 
        components.html(f"""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ background:transparent; font-family:'DM Sans',sans-serif; }}
body {{ background:transparent; overflow:visible; padding-bottom:8px; }}
.wrap {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; }}
.hdr {{ padding:14px 18px; font-size:14px; font-weight:800; color:#1a2e4a;
        text-transform:uppercase; letter-spacing:0.3px;
        border-bottom:1px solid #e5e7eb; background:#fff; }}
</style>
<div class="wrap">
    <div class="hdr">📊 Análise Estratégica dos Anúncios com IA</div>
    {ia_panel_content}
</div>
<script>
function ajustarAltura() {{
    var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(f) {{
        try {{ if (f.contentWindow === window) f.style.height = (h + 8) + 'px'; }} catch(e) {{}}
    }});
}}
var ro = new ResizeObserver(ajustarAltura);
ro.observe(document.body);
document.addEventListener('DOMContentLoaded', ajustarAltura);
window.addEventListener('load', ajustarAltura);
setTimeout(ajustarAltura, 200);
</script>
""", height=200, scrolling=False)
 
        if ia_ads_btn:
            if gemini_model is None:
                st.session_state[chave_ia_ads] = "Configure GEMINI_API_KEY nos secrets."
            else:
                with st.spinner("Analisando anúncios com IA…"):
                    try:
                        prompt_ads = f"""
Você é um especialista em mídia paga e marketing digital.
Analise os anúncios ativos abaixo de "{nome}" na Meta Ad Library e gere um relatório estratégico em português.
 
Empresa: {nome}
Total de anúncios analisados: {len(ads_filtrados)}
Formatos: {n_imagem} imagens | {n_video} vídeos | {n_outros} outros
 
Anúncios (amostra):
{resumo_ads}
 
---
 
Responda com as seguintes seções:
 
### 🎯 Estratégia de Mídia
Qual é a estratégia geral identificada nos anúncios? (ex: conversão, awareness, remarketing)
 
### 📝 Padrões de Copy
Quais são os padrões de linguagem, CTAs e mensagens mais recorrentes?
 
### 🖼️ Formatos Predominantes
Quais formatos estão sendo mais usados e o que isso indica?
 
### 📣 Plataformas e Distribuição
Como está sendo feita a distribuição entre as plataformas da Meta?
 
### ⚠️ Pontos de Atenção
2 observações críticas sobre a estratégia de ads.
 
### 💡 Oportunidades Competitivas
3 oportunidades concretas para superar esta empresa nos anúncios.
 
Seja direto, objetivo e baseado nos dados reais dos anúncios.
"""
                        resp = gemini_model.generate_content(prompt_ads)
                        st.session_state[chave_ia_ads] = resp.text
                        st.rerun()
                    except Exception as e:
                        st.session_state[chave_ia_ads] = f"Erro: {e}"
                        st.rerun()
 
    # ── Função estado vazio (sem busca ainda)
    def _estado_vazio(nome, term, cor_av, avatar, is_minha):
        badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
        badge_txt = "#1d4ed8" if is_minha else "#6b7280"
        badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
        badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
 
        st.markdown(f"""
        <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;
                    padding:32px;text-align:center;margin-bottom:24px'>
            <div style='width:56px;height:56px;border-radius:50%;background:{cor_av};
                        display:flex;align-items:center;justify-content:center;
                        font-size:20px;font-weight:700;color:#fff;margin:0 auto 14px'>
                {avatar}
            </div>
            <div style='font-size:17px;font-weight:700;color:#111827;margin-bottom:6px'>{nome}</div>
            <span style='background:{badge_bg};color:{badge_txt};border:1px solid {badge_brd};
                         padding:2px 12px;border-radius:20px;font-size:12px;font-weight:600'>
                {badge_lbl}
            </span>
            <div style='margin-top:16px;font-size:14px;color:#6b7280'>
                Busca: <b style='color:#111827'>{term}</b>
            </div>
            <div style='margin-top:20px;padding:14px;background:#f9fafb;border-radius:10px;
                        font-size:13px;color:#9ca3af'>
                Clique em <b style='color:#111827'>🔍 Buscar Anúncios</b> para carregar os anúncios ativos.
            </div>
        </div>
        """, unsafe_allow_html=True)
        _link_fallback(term, nome)
 
    def _link_fallback(term, nome):
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&q={term}&search_type=keyword_unordered"
        st.markdown(
            f"<div style='text-align:center;font-size:13px;color:#9ca3af;margin-top:8px'>"
            f"Ou abra diretamente: "
            f"<a href='{url}' target='_blank' style='color:#3a9fd6;text-decoration:none'>"
            f"Ad Library → {nome}</a></div>",
            unsafe_allow_html=True,
        )
 
    # ── Renderiza aba de cada empresa
    for aba, emp_item in zip(abas_ads, todas_empresas):
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
# REDES SOCIAIS - GRÁFICOS COMPARATIVOS
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
# REDES SOCIAIS - ABAS POR PERFIL
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
# REDES SOCIAIS - POSTAGENS
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
