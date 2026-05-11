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
if "mostrar_alerta_saida" not in st.session_state:
    st.session_state.mostrar_alerta_saida = False
if "pagina_destino" not in st.session_state:
    st.session_state.pagina_destino = None
if "relatorio_sites" not in st.session_state:
    st.session_state.relatorio_sites = {}   # cache: {url: conteudo_extraido}
if "relatorio_gemini" not in st.session_state:
    st.session_state.relatorio_gemini = ""

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
    editando = (
        st.session_state.mostrar_form_concorrente
        or st.session_state.editando_concorrente is not None
    )
    if st.session_state.pagina == "cad" and destino != "cad" and editando:
        st.session_state.mostrar_alerta_saida = True
        st.session_state.pagina_destino = destino
    else:
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
    """Extrai texto principal do site via Trafilatura."""
    url_fmt = formatar_url(url)
    if not url_fmt:
        return ""
    try:
        downloaded = trafilatura.fetch_url(url_fmt)
        if not downloaded:
            # Tenta requests como fallback
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CIBot/1.0)"}
            resp = requests.get(url_fmt, headers=headers, timeout=10)
            downloaded = resp.text
        texto = trafilatura.extract(
            downloaded,
            include_tables=True,
            include_links=False,
            include_images=False,
            no_fallback=False,
        )
        return texto or ""
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
}

.page-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;
}
.page-title { font-size: 28px; font-weight: 600; color: #111827; letter-spacing: -0.5px; margin: 0; }
.page-subtitle { font-size: 14px; color: #6b7280; margin-top: 3px; }

section.main div.stButton > button {
    border-radius: 7px !important; font-size: 14px !important; font-weight: 500 !important;
    border: 1px solid #d1d5db !important; background: #ffffff !important;
    color: #374151 !important; box-shadow: none !important;
    padding: 8px 16px !important; transition: all 0.12s ease !important;
    font-family: 'DM Sans', sans-serif !important; min-height: 38px !important;
}
section.main div.stButton > button:hover {
    background: #f9fafb !important; border-color: #9ca3af !important; color: #111827 !important;
}
section.main div.stButton > button[kind="primary"],
section.main div.stFormSubmitButton > button,
section.main div.stFormSubmitButton > button[kind="primary"] {
    background: #111827 !important; color: #ffffff !important; border: none !important;
}
section.main div.stButton > button[kind="primary"]:hover,
section.main div.stFormSubmitButton > button:hover { background: #1f2937 !important; }

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
    font-family: 'DM Sans', sans-serif !important; letter-spacing: -0.4px !important;
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

/* Tabs */
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

if not st.session_state.logado:
    # CSS da tela de login
    st.markdown("""
    <style>
    .auth-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 40px 44px 36px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        font-family: 'DM Sans', sans-serif;
    }
    .auth-title {
        font-size: 26px; font-weight: 700; color: #111827;
        letter-spacing: -0.5px; margin-bottom: 6px;
        font-family: 'DM Sans', sans-serif;
    }
    .auth-sub {
        font-size: 14px; color: #6b7280; margin-bottom: 28px;
        font-family: 'DM Sans', sans-serif;
    }
    .auth-tab-row {
        display: flex; gap: 0; margin-bottom: 24px;
        border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
    }
    .auth-tab {
        flex: 1; padding: 9px 0; text-align: center;
        font-size: 14px; font-weight: 600; cursor: pointer;
        font-family: 'DM Sans', sans-serif; border: none;
        transition: all 0.15s;
    }
    .auth-tab.active { background: #111827; color: #fff; }
    .auth-tab.inactive { background: #fff; color: #9ca3af; }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns([1, 1.4, 1])
    with cols[1]:
        st.markdown("<div style='height:60px'/>", unsafe_allow_html=True)
        st.markdown("""
        <div class="auth-title">CI Dashboard</div>
        <div class="auth-sub">Competitive Intelligence para agências e empresas</div>
        """, unsafe_allow_html=True)

        aba = st.tabs(["🔑 Entrar", "📝 Criar conta"])

        # ── Aba Login
        with aba[0]:
            with st.form("form_login"):
                email_login = st.text_input("E-mail", placeholder="seu@email.com")
                senha_login = st.text_input("Senha", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Entrar", type="primary", use_container_width=True)

            if submit_login:
                if email_login and senha_login:
                    with st.spinner("Autenticando..."):
                        user, err = login_supabase(email_login, senha_login)
                    if user:
                        st.session_state.logado = True
                        st.session_state.user = user
                        # Carrega dados do banco
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

        # ── Aba Cadastro
        with aba[1]:
            with st.form("form_cadastro"):
                email_cad = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
                senha_cad = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="cad_senha")
                senha_cad2 = st.text_input("Confirmar senha", type="password", placeholder="Repita a senha", key="cad_senha2")
                submit_cad = st.form_submit_button("Criar conta", type="primary", use_container_width=True)

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
    st.stop()

# ---------------------------------------------------
# SIDEBAR (apenas quando logado)
# ---------------------------------------------------

with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    [data-testid="stSidebar"] { background-color: #0f1117 !important; border-right: 1px solid #1e2530 !important; }
    .sb-logo { padding: 22px 18px 16px; border-bottom: 1px solid #1e2530; margin-bottom: 8px; }
    .sb-logo-title { font-size: 16px; font-weight: 700; color: #fff; letter-spacing: -0.3px; font-family: DM Sans, sans-serif; }
    .sb-logo-sub { font-size: 11px; color: #3d4f63; margin-top: 3px; font-family: DM Sans, sans-serif; font-weight: 500; }
    .sb-section { padding: 18px 18px 5px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.6px; color: #2d3a4a; font-family: DM Sans, sans-serif; }
    .sb-user { padding: 12px 18px; font-size: 12px; color: #3d4f63; border-top: 1px solid #1e2530; margin-top: 8px; word-break: break-all; }
    [data-testid="stSidebar"] div.stButton { margin-bottom: 0px !important; }
    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important; border-radius: 7px !important;
        background-color: transparent !important; color: #8a95a3 !important;
        border: none !important; text-align: left !important;
        padding: 5px 14px !important; min-height: auto !important;
        font-size: 14.5px !important; font-weight: 700 !important;
        box-shadow: none !important; transition: all 0.15s ease !important;
        font-family: DM Sans, sans-serif !important; line-height: 1.4 !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #161d2a !important; color: #e5e7eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-logo"><div class="sb-logo-title">CI Dashboard</div><div class="sb-logo-sub">Competitive Intelligence</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Dados Principais</div>', unsafe_allow_html=True)
    if st.button("🏛️   Minha Empresa"):   trocar_pagina("home")
    if st.button("🎯   Concorrentes"):     trocar_pagina("cad")

    st.markdown('<div class="sb-section">Análise</div>', unsafe_allow_html=True)
    if st.button("📈   Visão Geral"):      trocar_pagina("geral")
    if st.button("📱   Redes Sociais"):    trocar_pagina("redes")
    if st.button("🔍   Confronto de Sites"): trocar_pagina("sites")
    if st.button("🎬   Biblioteca de Ads"): trocar_pagina("ads")
    if st.button("💡   Insights"):         trocar_pagina("insights")

    # Usuário + Logout
    user_email = st.session_state.user.email if st.session_state.user else ""
    st.markdown(f'<div class="sb-user">👤 {user_email}</div>', unsafe_allow_html=True)
    if st.button("🚪   Sair"):
        logout_supabase()
        for k in ["logado", "user", "dados", "metricas_redes", "pagina",
                  "mostrar_form_concorrente", "editando_concorrente",
                  "editar_empresa", "relatorio_sites", "relatorio_gemini"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ---------------------------------------------------
# POPUP ALERTA SAÍDA
# ---------------------------------------------------

if st.session_state.mostrar_alerta_saida:
    st.markdown("""
    <div class="popup-overlay"></div>
    <div class="popup-box">
        <div class="popup-title">⚠️ Cancelar edição?</div>
        <div class="popup-text">
            Você possui uma edição aberta de concorrente.<br>
            Se sair agora, as alterações não salvas serão perdidas.
        </div>
    </div>
    """, unsafe_allow_html=True)

    p1, p2, p3 = st.columns([1, 1, 1])
    with p2:
        if st.button("✅ Sair e cancelar edição", use_container_width=True):
            st.session_state.mostrar_form_concorrente = False
            st.session_state.editando_concorrente = None
            st.session_state.mostrar_alerta_saida = False
            st.session_state.pagina = st.session_state.pagina_destino
            st.rerun()
        if st.button("❌ Continuar editando", use_container_width=True):
            st.session_state.mostrar_alerta_saida = False
            st.rerun()

# ---------------------------------------------------
# HELPER — CABEÇALHO SEM PERÍODO (para Sites)
# ---------------------------------------------------

def cabecalho_simples(titulo, subtitulo=""):
    h1 = st.columns(1)[0]
    with h1:
        st.markdown(
            f"<h1 style='font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0;font-family:DM Sans,sans-serif'>{titulo}</h1>",
            unsafe_allow_html=True
        )
        if subtitulo:
            st.markdown(f"<div style='font-size:14px;color:#6b7280;margin-top:3px'>{subtitulo}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0 24px 0'/>", unsafe_allow_html=True)

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
            st.markdown(f"<div style='font-size:14px;color:#6b7280;margin-top:3px'>{subtitulo}</div>", unsafe_allow_html=True)
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

        h1, h2 = st.columns([8, 2])
        with h1:
            st.markdown("<h1 style='font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0 0 4px 0;font-family:DM Sans,sans-serif'>Minha Empresa</h1>", unsafe_allow_html=True)
        with h2:
            if tem_dados:
                st.markdown("<div style='padding-top:6px'/>", unsafe_allow_html=True)
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.editar_empresa = False
                    st.rerun()

        SUBNICHOS = {
            "Marketing": ["Agência Digital", "Marketing de Conteúdo", "SEO", "Tráfego Pago", "Social Media", "Branding", "Email Marketing", "Inbound Marketing"],
            "Tecnologia": ["Software House", "SaaS", "Consultoria TI", "Segurança", "Dados & BI", "Mobile", "Cloud", "Inteligência Artificial"],
            "Varejo": ["E-commerce", "Moda", "Eletrônicos", "Alimentos", "Farmácia", "Pet Shop", "Decoração", "Esportes"],
            "Saúde": ["Clínica Médica", "Odontologia", "Psicologia", "Nutrição", "Fisioterapia", "Academia", "Farmácia", "Estética"],
            "Educação": ["Escola", "Curso Online", "Coaching", "Consultoria", "Idiomas", "Pré-vestibular", "Creche", "Faculdade"],
            "Indústria": ["Manufatura", "Construção", "Agronegócio", "Química", "Têxtil", "Metalurgia", "Energia", "Logística"],
        }

        def sec_header(label):
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 4px 12px;border-left:3px solid #e5e7eb;margin:0;font-family:DM Sans,sans-serif'>{label}</div>", unsafe_allow_html=True)

        def divider():
            st.markdown("<div style='margin:20px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            sec_header("Informações Gerais")
            emp["nome"] = st.text_input("Nome da Empresa", emp["nome"])
            col_s, col_t = st.columns(2)
            setor_opcoes = list(SUBNICHOS.keys())
            setor_idx = setor_opcoes.index(emp["setor"]) if emp["setor"] in setor_opcoes else 0
            emp["setor"] = col_s.selectbox("Setor", setor_opcoes, index=setor_idx)
            subnichos_disponiveis = SUBNICHOS.get(emp["setor"], [])
            tipo_idx = subnichos_disponiveis.index(emp["tipo"]) if emp["tipo"] in subnichos_disponiveis else 0
            emp["tipo"] = col_t.selectbox("Sub-nicho", subnichos_disponiveis, index=tipo_idx)

        with col_right:
            sec_header("Serviços")
            servicos_text = st.text_area(
                "Serviços (um por linha)", value="\n".join(emp["servicos"]),
                height=178, label_visibility="collapsed",
                placeholder="Ex:\nTráfego Pago\nSEO\nSocial Media"
            )
            emp["servicos"] = [s.strip() for s in servicos_text.splitlines() if s.strip()]

        divider()
        sec_header("Presença Digital")
        col_ig, col_fb, col_site = st.columns(3)
        emp["instagram"] = col_ig.text_input("Instagram", value=emp["instagram"])
        emp["fb_page"] = col_fb.text_input("Facebook", emp["fb_page"])
        site_digitado = col_site.text_input("Site", emp["site"])
        emp["site"] = limpar_site(site_digitado)

        divider()
        sec_header("Localização")
        loc1, loc2 = st.columns(2)
        estados = list(ESTADOS_CIDADES.keys())
        estado_index = estados.index(emp["estado"]) if emp["estado"] in estados else 0
        emp["estado"] = loc1.selectbox("Estado", estados, index=estado_index)
        cidades = ESTADOS_CIDADES.get(emp["estado"], [])
        cidade_index = cidades.index(emp["cidade"]) if emp["cidade"] in cidades else 0
        emp["cidade"] = loc2.selectbox("Cidade", cidades, index=cidade_index)

        divider()

        if st.button("💾 Salvar Empresa", use_container_width=False):
            if emp["nome"].strip():
                st.session_state.editar_empresa = False
                salvar_dados_usuario(st.session_state.user.id)
                st.success("Empresa salva com sucesso!")
                st.rerun()
            else:
                st.error("Informe pelo menos o nome da empresa.")

    else:
        h1, h2 = st.columns([8, 2])
        with h1:
            st.markdown("<h1 style='font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0;font-family:DM Sans,sans-serif'>Minha Empresa</h1>", unsafe_allow_html=True)
        with h2:
            st.markdown("<div style='padding-top:6px'/>", unsafe_allow_html=True)
            if st.button("✏️ Editar Empresa", use_container_width=True):
                st.session_state.editar_empresa = True
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #e5e7eb;margin:16px 0 24px 0'/>", unsafe_allow_html=True)

        avatar = gerar_avatar(emp["nome"])
        loc = emp['cidade'] or ''
        if emp['estado']:
            loc += (', ' if loc else '') + emp['estado']
        servicos_col_html = "".join([f"<div class='tag'>{s}</div>" for s in emp["servicos"]]) if emp["servicos"] else "<span class='val' style='color:#9ca3af'>—</span>"

        card_html = f"""<!DOCTYPE html>
<html>
<head>
{CARD_FONT_IMPORT}
<style>
{CARD_CSS}
body {{ padding-bottom: 16px; }}
.card {{ background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:28px 32px;margin-bottom:2px; }}
.top {{ display:flex;align-items:center;gap:18px;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid #f3f4f6; }}
.avatar {{ width:56px;height:56px;min-width:56px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:600;color:#fff;flex-shrink:0; }}
.nome {{ font-size:22px;font-weight:600;color:#111827;margin-bottom:3px;letter-spacing:-0.4px; }}
.sub {{ font-size:14px;color:#9ca3af; }}
.grid {{ display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 36px; }}
.sec-title {{ font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #f3f4f6; }}
.row {{ display:flex;align-items:flex-start;gap:12px;margin-bottom:14px; }}
.ico {{ width:20px;height:20px;flex-shrink:0;margin-top:2px;display:flex;align-items:center;justify-content:center; }}
.ico svg {{ width:18px;height:18px; }}
.lbl {{ font-size:12px;color:#9ca3af;display:block;margin-bottom:2px; }}
.val {{ font-size:15px;color:#111827;font-weight:500; }}
.tags-wrap {{ display:flex;flex-wrap:wrap;gap:8px; }}
.tag {{ background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;padding:5px 13px;border-radius:20px;font-size:13px;font-weight:500;display:inline-block; }}
</style>
</head>
<body>
<div class="card">
  <div class="top">
    <div class="avatar">{avatar}</div>
    <div><div class="nome">{emp['nome']}</div><div class="sub">{emp['setor']}{' · ' + emp['tipo'] if emp['tipo'] else ''}</div></div>
  </div>
  <div class="grid">
    <div>
      <div class="sec-title">Presença Digital</div>
      <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="ig" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#f09433"/><stop offset="100%" stop-color="#bc1888"/></linearGradient></defs><rect x="2" y="2" width="20" height="20" rx="5" fill="url(#ig)"/><circle cx="12" cy="12" r="4.5" stroke="white" stroke-width="1.8" fill="none"/><circle cx="17.5" cy="6.5" r="1.2" fill="white"/></svg></span><div><span class="lbl">Instagram</span><span class="val">{emp['instagram'] or '—'}</span></div></div>
      <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/></svg></span><div><span class="lbl">Facebook</span><span class="val">{emp['fb_page'] or '—'}</span></div></div>
      <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></span><div><span class="lbl">Site</span><span class="val">{emp['site'] or '—'}</span></div></div>
    </div>
    <div>
      <div class="sec-title">Localização</div>
      <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></span><div><span class="lbl">Cidade / Estado</span><span class="val">{loc or '—'}</span></div></div>
    </div>
    <div>
      <div class="sec-title">Serviços</div>
      <div class="tags-wrap">{servicos_col_html}</div>
    </div>
  </div>
</div>
</body></html>"""

        n_servicos = len(emp["servicos"])
        linhas_tags = max(1, -(-n_servicos // 2)) if n_servicos > 0 else 1
        altura = 300 + (linhas_tags * 44) + 40
        components.html(card_html, height=altura, scrolling=False)

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    top1, top2 = st.columns([8, 2])
    with top1:
        st.markdown("<h1 style='font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0 0 4px 0;font-family:DM Sans,sans-serif'>Concorrentes</h1>", unsafe_allow_html=True)
    with top2:
        if st.button("➕ Adicionar", use_container_width=True):
            st.session_state.mostrar_form_concorrente = True
            st.session_state.editando_concorrente = None
            st.rerun()

    st.markdown("---")

    if st.session_state.mostrar_form_concorrente or st.session_state.editando_concorrente is not None:
        concorrente_edit = None
        if st.session_state.editando_concorrente is not None:
            concorrente_edit = st.session_state.dados["concorrentes"][st.session_state.editando_concorrente]

        with st.form("cad_concorrente", clear_on_submit=False):
            st.markdown("<div style='font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 4px 12px;border-left:3px solid #e5e7eb;margin:0;font-family:DM Sans,sans-serif'>Identificação</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome do Concorrente", value=(concorrente_edit["nome"] if concorrente_edit else ""))
            u = c2.text_input("URL do Site", value=(concorrente_edit["url"] if concorrente_edit else ""))

            st.markdown("<div style='margin:20px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 4px 12px;border-left:3px solid #e5e7eb;margin:0;font-family:DM Sans,sans-serif'>Redes Sociais</div>", unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            insta_handle = c3.text_input("Instagram", value=(concorrente_edit["instagram"] if concorrente_edit else "@"))
            fb_p = c4.text_input("Facebook", value=(concorrente_edit["fb_page"] if concorrente_edit else ""))
            ads_manual = st.text_input("ID Manual Ads (Opcional)", value=(concorrente_edit["ads_id"] if concorrente_edit else ""))

            col1, col2 = st.columns(2)
            salvar = col1.form_submit_button("Salvar", type="primary")
            cancelar = col2.form_submit_button("Cancelar")

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
        cols = st.columns(3)
        for i, c in enumerate(concorrentes):
            with cols[i % 3]:
                avatar = gerar_avatar(c["nome"])
                card_html = f"""<!DOCTYPE html>
<html>
<head>{CARD_FONT_IMPORT}
<style>{CARD_CSS}
body{{padding-bottom:16px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:22px 24px;margin-bottom:2px}}
.header{{display:flex;align-items:center;gap:14px;margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid #f3f4f6}}
.avatar{{width:46px;height:46px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;color:#fff;flex-shrink:0}}
.name{{font-size:16px;font-weight:600;color:#111827;letter-spacing:-0.3px}}
.row{{display:flex;align-items:flex-start;gap:10px;margin-bottom:13px}}
.ico{{width:20px;height:20px;flex-shrink:0;margin-top:1px;display:flex;align-items:center;justify-content:center}}
.ico svg{{width:17px;height:17px}}
.lbl{{font-size:11px;color:#9ca3af;display:block;margin-bottom:2px}}
.val{{font-size:14px;color:#374151;font-weight:500;word-break:break-all}}
</style>
</head>
<body>
<div class="card">
  <div class="header"><div class="avatar">{avatar}</div><span class="name">{c['nome']}</span></div>
  <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></span><div><span class="lbl">Site</span><span class="val">{c['url'] or '—'}</span></div></div>
  <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="ig2" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#f09433"/><stop offset="100%" stop-color="#bc1888"/></linearGradient></defs><rect x="2" y="2" width="20" height="20" rx="5" fill="url(#ig2)"/><circle cx="12" cy="12" r="4.5" stroke="white" stroke-width="1.8" fill="none"/><circle cx="17.5" cy="6.5" r="1.2" fill="white"/></svg></span><div><span class="lbl">Instagram</span><span class="val">{c['instagram'] or '—'}</span></div></div>
  <div class="row"><span class="ico"><svg viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z"/></svg></span><div><span class="lbl">Facebook</span><span class="val">{c['fb_page'] or '—'}</span></div></div>
</div>
</body></html>"""
                components.html(card_html, height=277, scrolling=False)
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✏️ Editar", key=f"editar_{i}", use_container_width=True):
                        st.session_state.editando_concorrente = i
                        st.session_state.mostrar_form_concorrente = False
                        st.rerun()
                with b2:
                    if st.button("🗑️ Remover", key=f"remove_{i}", use_container_width=True):
                        st.session_state.dados["concorrentes"].pop(i)
                        salvar_dados_usuario(st.session_state.user.id)
                        st.rerun()
    else:
        st.info("Nenhum concorrente cadastrado ainda. Clique em **➕ Adicionar** para começar.")

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
        st.markdown(f"""
        <div style='background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;display:flex;align-items:center;gap:16px;margin-bottom:24px'>
            <div style='width:40px;height:40px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;flex-shrink:0'>{gerar_avatar(emp['nome'])}</div>
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
# CONFRONTO DE SITES  ← NOVA VERSÃO
# ---------------------------------------------------

elif st.session_state.pagina == "sites":

    cabecalho_simples("🌐 Confronto de Sites", "Análise comparativa de posicionamento via IA")

    emp = st.session_state.dados["minha_empresa"]
    concorrentes = st.session_state.dados["concorrentes"]

    # Monta lista de sites disponíveis
    sites_disponiveis = []
    if emp.get("site"):
        sites_disponiveis.append({"nome": emp["nome"], "url": emp["site"], "tipo": "minha"})
    for c in concorrentes:
        if c.get("url"):
            sites_disponiveis.append({"nome": c["nome"], "url": c["url"], "tipo": "concorrente"})

    if not sites_disponiveis:
        st.info("Cadastre o site da sua empresa e de pelo menos um concorrente para usar esta funcionalidade.")
    else:
        # ── Painel de sites detectados
        st.markdown("<div style='font-size:13px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px'>Sites cadastrados</div>", unsafe_allow_html=True)

        cols_sites = st.columns(min(len(sites_disponiveis), 4))
        for idx, s in enumerate(sites_disponiveis):
            with cols_sites[idx % 4]:
                is_minha = s["tipo"] == "minha"
                badge_bg  = "#eff6ff" if is_minha else "#f3f4f6"
                badge_txt = "#1d4ed8" if is_minha else "#6b7280"
                badge_brd = "#bfdbfe" if is_minha else "#e5e7eb"
                badge_lbl = "Minha Empresa" if is_minha else "Concorrente"
                st.markdown(f"""
                <div style='background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;margin-bottom:8px'>
                    <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>
                        <div style='width:34px;height:34px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0'>{gerar_avatar(s['nome'])}</div>
                        <div style='flex:1;min-width:0'>
                            <div style='font-size:14px;font-weight:600;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{s['nome']}</div>
                        </div>
                    </div>
                    <div style='font-size:12px;color:#9ca3af;word-break:break-all;margin-bottom:8px'>{s['url']}</div>
                    <span style='background:{badge_bg};color:{badge_txt};border:1px solid {badge_brd};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>{badge_lbl}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin:8px 0 20px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)

        # ── Botão gerar
        col_btn, col_info = st.columns([2, 5])
        with col_btn:
            gerar = st.button("🔍 Gerar Relatório de Posicionamento", type="primary", use_container_width=True)
        with col_info:
            st.markdown("""
            <div style='padding:10px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;font-size:13px;color:#6b7280;line-height:1.6'>
                O Trafilatura lê o conteúdo de cada site e o Gemini gera um relatório comparativo de posicionamento, mensagens-chave e recomendações estratégicas.
            </div>
            """, unsafe_allow_html=True)

        if gerar:
            st.session_state.relatorio_gemini = ""
            st.session_state.relatorio_sites = {}

            # ── Extração dos sites
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

                # ── Geração do relatório
                empresa_principal = None
                concorrentes_data = []
                for s in sites_disponiveis:
                    item = {
                        "nome": s["nome"],
                        "url": s["url"],
                        "conteudo": st.session_state.relatorio_sites.get(s["url"], ""),
                    }
                    if s["tipo"] == "minha":
                        empresa_principal = item
                    else:
                        concorrentes_data.append(item)

                if empresa_principal is None and sites_disponiveis:
                    empresa_principal = {
                        "nome": sites_disponiveis[0]["nome"],
                        "url": sites_disponiveis[0]["url"],
                        "conteudo": st.session_state.relatorio_sites.get(sites_disponiveis[0]["url"], ""),
                    }

                relatorio = gerar_relatorio_posicionamento(empresa_principal, concorrentes_data)
                st.session_state.relatorio_gemini = relatorio
                status.update(label="✅ Relatório gerado!", state="complete")

        # ── Exibe relatório
        if st.session_state.relatorio_gemini:
            st.markdown("<div style='margin:24px 0 16px 0;border-top:1px solid #e5e7eb'/>", unsafe_allow_html=True)
            st.markdown("""
            <div style='display:flex;align-items:center;gap:10px;margin-bottom:20px'>
                <div style='font-size:20px;font-weight:700;color:#111827;font-family:DM Sans,sans-serif'>📋 Relatório de Posicionamento Competitivo</div>
            </div>
            """, unsafe_allow_html=True)

            # Caixa com background
            st.markdown("""
            <style>
            .relatorio-box {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 28px 32px;
                font-family: 'DM Sans', sans-serif;
                line-height: 1.75;
                color: #1f2937;
            }
            .relatorio-box h3 { font-size:17px;font-weight:700;color:#111827;margin:24px 0 10px; }
            .relatorio-box p  { font-size:15px;color:#374151;margin-bottom:10px; }
            .relatorio-box ul { padding-left:20px;margin-bottom:10px; }
            .relatorio-box li { font-size:15px;color:#374151;margin-bottom:6px; }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(st.session_state.relatorio_gemini)

            # Detalhes de extração
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

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif st.session_state.pagina == "ads":

    periodo, data_inicio = cabecalho_analise("📣 Biblioteca de Ads", "Anúncios ativos da sua empresa e concorrentes no Facebook")
    concs = st.session_state.dados["concorrentes"]
    emp   = st.session_state.dados["minha_empresa"]

    todas_empresas = []
    if emp.get("nome"):
        ads_id_emp = emp.get("fb_page") or emp.get("instagram", "").lstrip("@") or emp.get("nome", "")
        todas_empresas.append({"nome": emp["nome"], "ads_id": ads_id_emp, "tipo": "minha"})
    for c in concs:
        todas_empresas.append({"nome": c["nome"], "ads_id": c["ads_id"], "tipo": "concorrente"})

    if not todas_empresas:
        st.info("Cadastre sua empresa e concorrentes para visualizar anúncios.")
    else:
        cols = st.columns(3)
        for i, empresa_item in enumerate(todas_empresas):
            with cols[i % 3]:
                term   = empresa_item["ads_id"]
                nome   = empresa_item["nome"]
                is_minha = empresa_item["tipo"] == "minha"
                url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&q={term}&search_type=keyword_unordered"
                badge = "<span style='background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>Minha Empresa</span>" if is_minha else "<span style='background:#f3f4f6;color:#6b7280;border:1px solid #e5e7eb;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600'>Concorrente</span>"
                avatar = gerar_avatar(nome)
                card = f"""
                <div style='background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px 22px;margin-bottom:4px'>
                    <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #f3f4f6'>
                        <div style='width:38px;height:38px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0'>{avatar}</div>
                        <div style='flex:1;min-width:0'>
                            <div style='font-size:15px;font-weight:600;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{nome}</div>
                            <div style='margin-top:4px'>{badge}</div>
                        </div>
                    </div>
                    <div style='display:flex;align-items:center;gap:8px;margin-bottom:10px'>
                        <span style='font-size:13px;color:#6b7280'>Busca:</span>
                        <span style='font-size:13px;font-weight:600;color:#111827'>{term}</span>
                    </div>
                    <div style='display:flex;align-items:center;gap:8px'>
                        <span style='font-size:13px;color:#6b7280'>Período:</span>
                        <span style='font-size:13px;font-weight:500;color:#374151'>{periodo}</span>
                    </div>
                </div>
                """
                st.markdown(card, unsafe_allow_html=True)
                st.link_button("🔍 Abrir Biblioteca de Ads →", url, use_container_width=True)
                st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)

# ---------------------------------------------------
# INSIGHTS
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
# REDES SOCIAIS
# ---------------------------------------------------

elif st.session_state.pagina == "redes":

    periodo, data_inicio = cabecalho_analise("📱 Redes Sociais", "Seguidores, posts e engajamento por empresa")

    emp = st.session_state.dados["minha_empresa"]
    concorrentes = st.session_state.dados["concorrentes"]

    todas = []
    if emp.get("nome"):
        todas.append({"key": "__minha__", "nome": emp["nome"], "instagram": emp.get("instagram", ""), "facebook": emp.get("fb_page", ""), "tipo": "minha"})
    for i, c in enumerate(concorrentes):
        todas.append({"key": f"conc_{i}", "nome": c["nome"], "instagram": c.get("instagram", ""), "facebook": c.get("fb_page", ""), "tipo": "concorrente"})

    if not todas:
        st.info("Cadastre sua empresa e concorrentes para visualizar métricas.")
    else:
        metricas = st.session_state.metricas_redes
        for empresa_item in todas:
            k = empresa_item["key"]
            if k not in metricas:
                metricas[k] = {
                    "ig_seguidores": 0, "ig_posts": 0, "ig_engajamento": 0.0,
                    "fb_seguidores": 0, "fb_posts": 0, "fb_engajamento": 0.0,
                }

        IG_LOGO = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="igl" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#f09433"/><stop offset="25%" stop-color="#e6683c"/><stop offset="50%" stop-color="#dc2743"/><stop offset="75%" stop-color="#cc2366"/><stop offset="100%" stop-color="#bc1888"/></linearGradient></defs><rect width="24" height="24" rx="6" ry="6" fill="url(#igl)"/><circle cx="12" cy="12" r="5" stroke="white" stroke-width="1.8" fill="none"/><circle cx="18" cy="6" r="1.4" fill="white"/></svg>"""
        FB_LOGO = """<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="32" height="32" rx="6" fill="#1877F2"/><path d="M21.5 16H18v12H13.5V16H11v-4h2.5v-2.4C13.5 7.1 15 5.5 18.3 5.5c1.3 0 2.7.2 2.7.2V9h-1.5c-1.5 0-2 .9-2 1.9V12H21l-.5 4z" fill="white"/></svg>"""

        aba_ig, aba_fb = st.tabs(["  Instagram  ", "  Facebook  "])

        with aba_ig:
            st.markdown("<div style='height:16px'/>", unsafe_allow_html=True)
            st.markdown(f"""<div style='display:flex;align-items:center;gap:12px;margin-bottom:24px;padding:16px 20px;background:linear-gradient(135deg,#fdf2f8,#fce7f3);border:1px solid #f9a8d4;border-radius:12px'>{IG_LOGO}<div><div style='font-size:17px;font-weight:700;color:#831843;font-family:DM Sans,sans-serif'>Instagram</div><div style='font-size:12px;color:#be185d;margin-top:1px;font-family:DM Sans,sans-serif'>Métricas de presença e engajamento</div></div></div>""", unsafe_allow_html=True)

            empresas_ig = [e for e in todas if bool(e["instagram"])]
            if not empresas_ig:
                st.info("Nenhuma empresa com Instagram cadastrado.")
            else:
                for empresa_item in empresas_ig:
                    k = empresa_item["key"]
                    is_minha = empresa_item["tipo"] == "minha"
                    badge_cor = "#eff6ff" if is_minha else "#f3f4f6"
                    badge_txt_cor = "#1d4ed8" if is_minha else "#6b7280"
                    badge_borda = "#bfdbfe" if is_minha else "#e5e7eb"
                    badge_label = "Minha Empresa" if is_minha else "Concorrente"
                    avatar = gerar_avatar(empresa_item["nome"])
                    handle = empresa_item["instagram"] or "—"
                    st.markdown(f"""<div style='display:flex;align-items:center;gap:14px;margin:12px 0;padding:14px 18px;background:#fff;border:1px solid #e5e7eb;border-radius:10px'><div style='width:40px;height:40px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;flex-shrink:0'>{avatar}</div><div style='flex:1;min-width:0'><div style='font-size:15px;font-weight:700;color:#111827;font-family:DM Sans,sans-serif'>{empresa_item['nome']}</div><div style='font-size:13px;color:#9ca3af;margin-top:1px'>{handle}</div></div><span style='background:{badge_cor};color:{badge_txt_cor};border:1px solid {badge_borda};padding:3px 12px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap'>{badge_label}</span></div>""", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    metricas[k]["ig_seguidores"]  = c1.number_input("👥 Seguidores", min_value=0, step=100, value=metricas[k]["ig_seguidores"], key=f"{k}_ig_seg")
                    metricas[k]["ig_posts"]        = c2.number_input("📝 Posts", min_value=0, step=1, value=metricas[k]["ig_posts"], key=f"{k}_ig_posts")
                    metricas[k]["ig_engajamento"]  = c3.number_input("❤️ Engaj. %", min_value=0.0, step=0.1, format="%.2f", value=metricas[k]["ig_engajamento"], key=f"{k}_ig_eng")
                    st.markdown("<div style='margin:4px 0 12px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)

                st.markdown("<div style='font-size:13px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin:20px 0 10px 0'>Comparativo Instagram</div>", unsafe_allow_html=True)
                rows_ig = [{"Empresa": e["nome"], "Handle": e["instagram"], "Seguidores": metricas[e["key"]]["ig_seguidores"], "Posts": metricas[e["key"]]["ig_posts"], "Engaj. %": metricas[e["key"]]["ig_engajamento"]} for e in empresas_ig]
                st.dataframe(pd.DataFrame(rows_ig), use_container_width=True, hide_index=True)

                if st.button("💾 Salvar métricas de Redes Sociais", key="salvar_ig"):
                    salvar_dados_usuario(st.session_state.user.id)
                    st.success("Métricas salvas!")

        with aba_fb:
            st.markdown("<div style='height:16px'/>", unsafe_allow_html=True)
            st.markdown(f"""<div style='display:flex;align-items:center;gap:12px;margin-bottom:24px;padding:16px 20px;background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1px solid #93c5fd;border-radius:12px'>{FB_LOGO}<div><div style='font-size:17px;font-weight:700;color:#1e3a5f;font-family:DM Sans,sans-serif'>Facebook</div><div style='font-size:12px;color:#1d4ed8;margin-top:1px'>Métricas de presença e engajamento</div></div></div>""", unsafe_allow_html=True)

            empresas_fb = [e for e in todas if bool(e["facebook"])]
            if not empresas_fb:
                st.info("Nenhuma empresa com Facebook cadastrado.")
            else:
                for empresa_item in empresas_fb:
                    k = empresa_item["key"]
                    is_minha = empresa_item["tipo"] == "minha"
                    badge_cor = "#eff6ff" if is_minha else "#f3f4f6"
                    badge_txt_cor = "#1d4ed8" if is_minha else "#6b7280"
                    badge_borda = "#bfdbfe" if is_minha else "#e5e7eb"
                    badge_label = "Minha Empresa" if is_minha else "Concorrente"
                    avatar = gerar_avatar(empresa_item["nome"])
                    handle = empresa_item["facebook"] or "—"
                    st.markdown(f"""<div style='display:flex;align-items:center;gap:14px;margin:12px 0;padding:14px 18px;background:#fff;border:1px solid #e5e7eb;border-radius:10px'><div style='width:40px;height:40px;border-radius:50%;background:#111827;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;flex-shrink:0'>{avatar}</div><div style='flex:1;min-width:0'><div style='font-size:15px;font-weight:700;color:#111827;font-family:DM Sans,sans-serif'>{empresa_item['nome']}</div><div style='font-size:13px;color:#9ca3af;margin-top:1px'>{handle}</div></div><span style='background:{badge_cor};color:{badge_txt_cor};border:1px solid {badge_borda};padding:3px 12px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap'>{badge_label}</span></div>""", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    metricas[k]["fb_seguidores"]  = c1.number_input("👥 Seguidores", min_value=0, step=100, value=metricas[k]["fb_seguidores"], key=f"{k}_fb_seg")
                    metricas[k]["fb_posts"]        = c2.number_input("📝 Posts", min_value=0, step=1, value=metricas[k]["fb_posts"], key=f"{k}_fb_posts")
                    metricas[k]["fb_engajamento"]  = c3.number_input("❤️ Engaj. %", min_value=0.0, step=0.1, format="%.2f", value=metricas[k]["fb_engajamento"], key=f"{k}_fb_eng")
                    st.markdown("<div style='margin:4px 0 12px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)

                st.markdown("<div style='font-size:13px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;margin:20px 0 10px 0'>Comparativo Facebook</div>", unsafe_allow_html=True)
                rows_fb = [{"Empresa": e["nome"], "Página": e["facebook"], "Seguidores": metricas[e["key"]]["fb_seguidores"], "Posts": metricas[e["key"]]["fb_posts"], "Engaj. %": metricas[e["key"]]["fb_engajamento"]} for e in empresas_fb]
                st.dataframe(pd.DataFrame(rows_fb), use_container_width=True, hide_index=True)

                if st.button("💾 Salvar métricas de Redes Sociais", key="salvar_fb"):
                    salvar_dados_usuario(st.session_state.user.id)
                    st.success("Métricas salvas!")
