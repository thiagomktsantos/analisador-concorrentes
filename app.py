import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import re
import unicodedata

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------

st.set_page_config(
    page_title="IA Competitive Intelligence",
    layout="wide"
)

# ---------------------------------------------------
# CONFIGURAÇÃO GEMINI
# ---------------------------------------------------

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
else:
    model = None

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
# ESTADO DA SESSÃO
# ---------------------------------------------------

if "dados" not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "",
            "setor": "Marketing",
            "tipo": "",
            "estado": "",
            "cidade": "",
            "instagram": "@",
            "fb_page": "",
            "site": "",
            "servicos": []
        },
        "concorrentes": []
    }

empresa = st.session_state.dados["minha_empresa"]

campos_padrao = {
    "estado": "",
    "cidade": "",
    "instagram": "@",
    "fb_page": "",
    "site": "",
    "servicos": []
}

for campo, valor in campos_padrao.items():
    if campo not in empresa:
        empresa[campo] = valor

if "logado" not in st.session_state:
    st.session_state.logado = False

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
    url = re.sub(r"[^a-z0-9\.\-]", "", url)
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
# FUNÇÃO IA
# ---------------------------------------------------

def consultar_ia(prompt):
    if model is None:
        return "Erro: Chave API não configurada."
    try:
        emp = st.session_state.dados["minha_empresa"]
        contexto = f"""
Empresa: {emp['nome']}
Setor: {emp['setor']}
Instagram: {emp['instagram']}
"""
        resposta = model.generate_content(contexto + "\n" + prompt)
        return resposta.text
    except Exception as e:
        return f"Erro: {str(e)}"

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Dashboard")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# ---------------------------------------------------
# CSS GLOBAL REDESENHADO
# ---------------------------------------------------

st.markdown("""
<style>

/* ============ IMPORTS ============ */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ============ BASE ============ */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"] {
    background-color: #0f1117 !important;
    border-right: 1px solid #1e2530 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}

.sidebar-logo {
    padding: 22px 20px 16px 20px;
    border-bottom: 1px solid #1e2530;
    margin-bottom: 8px;
}

.sidebar-logo-text {
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.3px;
}

.sidebar-logo-sub {
    font-size: 11px;
    color: #4b5563;
    margin-top: 2px;
    font-weight: 400;
}

.sidebar-section {
    padding: 16px 12px 4px 12px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #2d3748;
}



[data-testid="stSidebar"] div.stButton {
    margin-bottom: 1px !important;
}

/* ============ MAIN CONTENT ============ */
section.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1100px !important;
}

/* ============ PAGE HEADER ============ */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e5e7eb;
}

.page-title {
    font-size: 28px;
    font-weight: 600;
    color: #111827;
    letter-spacing: -0.5px;
    margin: 0;
}

.page-subtitle {
    font-size: 14px;
    color: #6b7280;
    margin-top: 3px;
}

/* ============ BOTÕES PRINCIPAIS ============ */
section.main div.stButton > button {
    border-radius: 7px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    border: 1px solid #d1d5db !important;
    background: #ffffff !important;
    color: #374151 !important;
    box-shadow: none !important;
    padding: 8px 16px !important;
    transition: all 0.12s ease !important;
    font-family: 'DM Sans', sans-serif !important;
    min-height: 38px !important;
}

section.main div.stButton > button:hover {
    background: #f9fafb !important;
    border-color: #9ca3af !important;
    color: #111827 !important;
}

section.main div.stButton > button[kind="primary"],
section.main div.stFormSubmitButton > button,
section.main div.stFormSubmitButton > button[kind="primary"] {
    background: #111827 !important;
    color: #ffffff !important;
    border: none !important;
}

section.main div.stButton > button[kind="primary"]:hover,
section.main div.stFormSubmitButton > button:hover {
    background: #1f2937 !important;
}

/* Override Streamlit red/purple primary everywhere */
section.main button[data-baseweb="button"][kind="primary"] {
    background: #111827 !important;
    color: #ffffff !important;
    border: none !important;
}

/* ============ SECTION HEADERS (form) ============ */
.form-section-header {
    font-size: 13px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 20px 0 12px 0;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 16px;
    font-family: 'DM Sans', sans-serif;
}

/* ============ FORMULÁRIOS ============ */
section.main div[data-testid="stTextInput"] input,
section.main div[data-testid="stSelectbox"] select,
section.main div[data-baseweb="select"] {
    font-size: 15px !important;
    border-radius: 7px !important;
    border: 1px solid #e5e7eb !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #111827 !important;
}

section.main label {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    font-family: 'DM Sans', sans-serif !important;
    margin-bottom: 4px !important;
}

/* ============ TÍTULOS ============ */
section.main h1, section.main h2, section.main h3 {
    font-family: 'DM Sans', sans-serif !important;
    letter-spacing: -0.4px !important;
}

section.main h1 { font-size: 28px !important; font-weight: 600 !important; color: #111827 !important; }
section.main h2 { font-size: 20px !important; font-weight: 600 !important; color: #111827 !important; margin-top: 28px !important; }
section.main h3 { font-size: 16px !important; font-weight: 600 !important; color: #374151 !important; }

/* ============ DIVISOR ============ */
section.main hr {
    border: none !important;
    border-top: 1px solid #f3f4f6 !important;
    margin: 20px 0 !important;
}

/* ============ INFO/WARNING/SUCCESS ============ */
div[data-testid="stInfo"] {
    background: #f0f9ff !important;
    border: 1px solid #bae6fd !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    color: #0c4a6e !important;
    padding: 14px 18px !important;
}

div[data-testid="stWarning"] {
    background: #fffbeb !important;
    border: 1px solid #fcd34d !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}

div[data-testid="stSuccess"] {
    background: #f0fdf4 !important;
    border: 1px solid #86efac !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}

div[data-testid="stError"] {
    background: #fef2f2 !important;
    border: 1px solid #fca5a5 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}

/* ============ EXPANDER ============ */
details summary {
    font-size: 16px !important;
    font-weight: 500 !important;
    padding: 14px 0 !important;
}

/* ============ POPUP OVERLAY ============ */
.popup-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 999999;
    backdrop-filter: blur(2px);
}

.popup-box {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #ffffff;
    width: 480px;
    border-radius: 14px;
    padding: 32px;
    z-index: 9999999;
    border: 1px solid #e5e7eb;
    color: #111827;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}

.popup-title {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #111827;
}

.popup-text {
    color: #6b7280;
    margin-bottom: 24px;
    font-size: 15px;
    line-height: 1.6;
}

/* ============ CARD EMPRESA (IFRAME) ============ */

/* ============ SELECTBOX ============ */
div[data-baseweb="select"] > div {
    border-radius: 7px !important;
    min-height: 42px !important;
    font-size: 15px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ============ DATAFRAME ============ */
div[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #e5e7eb !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0f1117 !important; border-right: 1px solid #1e2530 !important; }
    .sb-logo { padding: 20px 16px 14px; border-bottom: 1px solid #1e2530; margin-bottom: 6px; }
    .sb-logo-title { font-size: 15px; font-weight: 700; color: #fff; letter-spacing: -0.3px; font-family: DM Sans, sans-serif; }
    .sb-logo-sub { font-size: 11px; color: #4b5a6e; margin-top: 2px; font-family: DM Sans, sans-serif; }
    .sb-section { padding: 18px 16px 6px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.4px; color: #2d3a4a; font-family: DM Sans, sans-serif; }
    [data-testid="stSidebar"] div.stButton { margin-bottom: 1px !important; }
    [data-testid="stSidebar"] div.stButton > button {
        width: 100% !important; border-radius: 6px !important;
        background-color: transparent !important; color: #9ca3af !important;
        border: none !important; text-align: left !important;
        padding: 8px 14px !important; min-height: auto !important;
        font-size: 14px !important; font-weight: 400 !important;
        box-shadow: none !important; transition: all 0.12s ease !important;
        font-family: DM Sans, sans-serif !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #1a2030 !important; color: #e5e7eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-logo"><div class="sb-logo-title">CI Dashboard</div><div class="sb-logo-sub">Competitive Intelligence</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Dados Principais</div>', unsafe_allow_html=True)

    if st.button("🏠  Minha Empresa"):
        trocar_pagina("home")

    if st.button("👥  Concorrentes"):
        trocar_pagina("cad")

    st.markdown('<div class="sb-section">Análise</div>', unsafe_allow_html=True)

    if st.button("📊  Visão Geral"):
        trocar_pagina("geral")

    if st.button("🌐  Confronto de Sites"):
        trocar_pagina("sites")

    if st.button("📢  Biblioteca de Ads"):
        trocar_pagina("ads")

    if st.button("💡  IA Battle Cards"):
        trocar_pagina("insights")
# ---------------------------------------------------
# POPUP ALERTA
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
# HOME — Minha Empresa
# ---------------------------------------------------

if st.session_state.pagina == "home":

    emp = st.session_state.dados["minha_empresa"]
    tem_dados = empresa_tem_dados(emp)

    if not tem_dados or st.session_state.editar_empresa:

        h1, h2 = st.columns([8, 2])
        with h1:
            st.markdown("<h1 style=\"font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0 0 4px 0;font-family:DM Sans,sans-serif\">Minha Empresa</h1>", unsafe_allow_html=True)
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
            st.markdown(f"<div style=\"font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 4px 12px;border-left:3px solid #e5e7eb;margin:0;font-family:DM Sans,sans-serif\">{label}</div>", unsafe_allow_html=True)

        def divider():
            st.markdown("<div style='margin:20px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)

        # ── Linha 1: somente Nome
        sec_header("Informações Gerais")
        emp["nome"] = st.text_input("Nome da Empresa", emp["nome"])

        # ── Linha 2: Setor + Sub-nicho (selecionável)
        col_s, col_t = st.columns(2)
        setor_opcoes = list(SUBNICHOS.keys())
        setor_idx = setor_opcoes.index(emp["setor"]) if emp["setor"] in setor_opcoes else 0
        emp["setor"] = col_s.selectbox("Setor", setor_opcoes, index=setor_idx)
        subnichos_disponiveis = SUBNICHOS.get(emp["setor"], [])
        tipo_idx = subnichos_disponiveis.index(emp["tipo"]) if emp["tipo"] in subnichos_disponiveis else 0
        emp["tipo"] = col_t.selectbox("Sub-nicho", subnichos_disponiveis, index=tipo_idx)

        divider()

        # ── Localização
        sec_header("Localização")
        loc1, loc2 = st.columns(2)
        estados = list(ESTADOS_CIDADES.keys())
        estado_index = estados.index(emp["estado"]) if emp["estado"] in estados else 0
        emp["estado"] = loc1.selectbox("Estado", estados, index=estado_index)
        cidades = ESTADOS_CIDADES.get(emp["estado"], [])
        cidade_index = cidades.index(emp["cidade"]) if emp["cidade"] in cidades else 0
        emp["cidade"] = loc2.selectbox("Cidade", cidades, index=cidade_index)

        divider()

        # ── Redes Sociais + Site — 3 colunas na mesma linha
        sec_header("Presença Digital")
        col_ig, col_fb, col_site = st.columns(3)
        emp["instagram"] = col_ig.text_input("Instagram", value=emp["instagram"])
        emp["fb_page"] = col_fb.text_input("Facebook", emp["fb_page"])
        site_digitado = col_site.text_input("Site", emp["site"])
        emp["site"] = limpar_site(site_digitado)

        divider()

        # ── Serviços
        sec_header("Serviços")
        st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)
        col_inp, col_btn = st.columns([5, 1])
        novo_servico = col_inp.text_input("Novo serviço", label_visibility="collapsed", placeholder="Ex: Tráfego Pago")
        adicionar = col_btn.button("＋ Adicionar", use_container_width=True)
        if adicionar and novo_servico.strip():
            emp["servicos"].append(novo_servico.strip())
            st.rerun()

        if emp["servicos"]:
            tags_html = "".join([
                f"<span style='background:#f1f5f9;color:#1e40af;border:1px solid #bfdbfe;padding:5px 14px;border-radius:20px;font-size:14px;margin-right:8px;display:inline-block;margin-bottom:8px;font-family:DM Sans,sans-serif'>{s} <span onclick=\"\" style='cursor:pointer;margin-left:4px;color:#93c5fd'>✕</span></span>"
                for s in emp["servicos"]
            ])
            st.markdown(tags_html, unsafe_allow_html=True)

        divider()

        if st.button("Salvar Empresa", use_container_width=False):
            if emp["nome"].strip():
                st.session_state.editar_empresa = False
                st.success("Empresa salva com sucesso!")
                st.rerun()
            else:
                st.error("Informe pelo menos o nome da empresa.")

    else:
        h1, h2 = st.columns([8, 2])
        with h1:
            st.markdown(
                "<h1 style='font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0;padding:0;font-family:DM Sans,sans-serif'>Minha Empresa</h1>",
                unsafe_allow_html=True
            )
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

        servicos_tags = ""
        if emp["servicos"]:
            tags = "".join([
                f"<span style='background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;padding:5px 14px;border-radius:20px;font-size:13px;margin-right:8px;display:inline-block;margin-bottom:8px'>{s}</span>"
                for s in emp["servicos"]
            ])
            servicos_tags = f"""
            <div style='margin-top:24px;padding-top:20px;border-top:1px solid #f3f4f6'>
                <div style='font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:12px'>Serviços</div>
                {tags}
            </div>"""

        card_html = f"""<!DOCTYPE html>
<html>
<head>
{CARD_FONT_IMPORT}
<style>
{CARD_CSS}
.card {{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 28px 32px;
}}
.top {{
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f3f4f6;
}}
.avatar {{
    width: 56px;
    height: 56px;
    min-width: 56px;
    border-radius: 50%;
    background: #111827;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 600;
    color: #fff;
    flex-shrink: 0;
    letter-spacing: -0.5px;
}}
.nome {{ font-size: 22px; font-weight: 600; color: #111827; margin-bottom: 3px; letter-spacing: -0.4px; }}
.sub {{ font-size: 14px; color: #9ca3af; }}
.grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 48px;
}}
.sec-title {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #9ca3af;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f3f4f6;
}}
.row {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 14px;
}}
.ico {{
    font-size: 16px;
    width: 20px;
    flex-shrink: 0;
    margin-top: 3px;
    color: #6b7280;
}}
.lbl {{ font-size: 12px; color: #9ca3af; display: block; margin-bottom: 2px; }}
.val {{ font-size: 15px; color: #111827; font-weight: 500; }}
</style>
</head>
<body>
<div class="card">
    <div class="top">
        <div class="avatar">{avatar}</div>
        <div>
            <div class="nome">{emp['nome']}</div>
            <div class="sub">{emp['setor']}{' · ' + emp['tipo'] if emp['tipo'] else ''}</div>
        </div>
    </div>
    <div class="grid">
        <div>
            <div class="sec-title">Localização</div>
            <div class="row">
                <span class="ico">📍</span>
                <div><span class="lbl">Cidade / Estado</span><span class="val">{loc or '—'}</span></div>
            </div>
        </div>
        <div>
            <div class="sec-title">Presença Digital</div>
            <div class="row">
                <span class="ico">📷</span>
                <div><span class="lbl">Instagram</span><span class="val">{emp['instagram'] or '—'}</span></div>
            </div>
            <div class="row">
                <span class="ico">🔵</span>
                <div><span class="lbl">Facebook</span><span class="val">{emp['fb_page'] or '—'}</span></div>
            </div>
            <div class="row">
                <span class="ico">🌐</span>
                <div><span class="lbl">Site</span><span class="val">{emp['site'] or '—'}</span></div>
            </div>
        </div>
    </div>
    {servicos_tags}
</div>
</body>
</html>"""

        n_servicos = len(emp["servicos"])
        # 300 base (header + grid) + 80 (services header padding) + rows*50 per 3 items
        if n_servicos > 0:
            linhas = max(1, -(-n_servicos // 3))  # ceiling div
            altura = 320 + 80 + linhas * 52
        else:
            altura = 320
        components.html(card_html, height=altura, scrolling=False)

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    top1, top2 = st.columns([8, 2])
    with top1:
        st.markdown(
            "<h1 style=\"font-size:28px;font-weight:600;color:#111827;letter-spacing:-0.5px;margin:0 0 4px 0;font-family:DM Sans,sans-serif\">Concorrentes</h1>",
            unsafe_allow_html=True
        )
    with top2:
        if st.button("➕ Adicionar", use_container_width=True):
            st.session_state.mostrar_form_concorrente = True
            st.session_state.editando_concorrente = None
            st.rerun()

    st.markdown("---")

    if (st.session_state.mostrar_form_concorrente or st.session_state.editando_concorrente is not None):

        concorrente_edit = None
        if st.session_state.editando_concorrente is not None:
            concorrente_edit = st.session_state.dados["concorrentes"][st.session_state.editando_concorrente]

        with st.form("cad_concorrente", clear_on_submit=False):
            st.markdown("<div style=\"font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 4px 12px;border-left:3px solid #e5e7eb;margin:0;font-family:DM Sans,sans-serif\">Identificação</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            n = c1.text_input("Nome do Concorrente", value=(concorrente_edit["nome"] if concorrente_edit else ""))
            u = c2.text_input("URL do Site", value=(concorrente_edit["url"] if concorrente_edit else ""))

            st.markdown("<div style='margin:20px 0;border-top:1px solid #f3f4f6'/>", unsafe_allow_html=True)
            st.markdown("<div style=\"font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;padding:4px 0 4px 12px;border-left:3px solid #e5e7eb;margin:0;font-family:DM Sans,sans-serif\">Redes Sociais</div>", unsafe_allow_html=True)
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
                search_term = ads_manual or fb_clean or clean_handle.replace("@", "") or n
                dados_novos = {
                    "nome": n,
                    "url": site_clean,
                    "instagram": clean_handle,
                    "fb_page": fb_clean,
                    "ads_id": search_term
                }

                if st.session_state.editando_concorrente is not None:
                    st.session_state.dados["concorrentes"][st.session_state.editando_concorrente] = dados_novos
                else:
                    st.session_state.dados["concorrentes"].append(dados_novos)

                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None
                st.rerun()

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:
        cols = st.columns(3)
        for i, c in enumerate(concorrentes):
            with cols[i % 3]:
                avatar = gerar_avatar(c["nome"])

                card_html = f"""<!DOCTYPE html>
<html>
<head>
{CARD_FONT_IMPORT}
<style>
{CARD_CSS}
.card {{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 4px;
}}
.header {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 18px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f3f4f6;
}}
.avatar {{
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: #111827;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    flex-shrink: 0;
    letter-spacing: -0.5px;
}}
.name {{ font-size: 16px; font-weight: 600; color: #111827; letter-spacing: -0.3px; }}
.row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 13px;
}}
.ico {{ font-size: 16px; width: 20px; flex-shrink: 0; margin-top: 1px; }}
.lbl {{ font-size: 11px; color: #9ca3af; display: block; margin-bottom: 2px; }}
.val {{ font-size: 14px; color: #374151; font-weight: 500; word-break: break-all; }}
</style>
</head>
<body>
<div class="card">
    <div class="header">
        <div class="avatar">{avatar}</div>
        <span class="name">{c['nome']}</span>
    </div>
    <div class="row">
        <span class="ico">🌐</span>
        <div><span class="lbl">Site</span><span class="val">{c['url'] or '—'}</span></div>
    </div>
    <div class="row">
        <span class="ico">📷</span>
        <div><span class="lbl">Instagram</span><span class="val">{c['instagram'] or '—'}</span></div>
    </div>
    <div class="row">
        <span class="ico">🔵</span>
        <div><span class="lbl">Facebook</span><span class="val">{c['fb_page'] or '—'}</span></div>
    </div>
</div>
</body>
</html>"""

                components.html(card_html, height=268, scrolling=False)

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✏️ Editar", key=f"editar_{i}", use_container_width=True):
                        st.session_state.editando_concorrente = i
                        st.session_state.mostrar_form_concorrente = False
                        st.rerun()
                with b2:
                    if st.button("🗑️ Remover", key=f"remove_{i}", use_container_width=True):
                        st.session_state.dados["concorrentes"].pop(i)
                        st.rerun()
    else:
        st.info("Nenhum concorrente cadastrado ainda. Clique em **➕ Adicionar** para começar.")

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------

elif st.session_state.pagina == "geral":

    st.title("📊 Visão Geral")
    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:
        df = pd.DataFrame(concorrentes)
        df.columns = ["Nome", "Site", "Instagram", "Facebook", "Ads ID"]
        st.dataframe(df[["Nome", "Site", "Instagram", "Facebook"]], use_container_width=True, height=400)
    else:
        st.warning("Nenhum concorrente cadastrado ainda.")

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif st.session_state.pagina == "ads":

    st.title("📢 Biblioteca de Ads")
    concs = st.session_state.dados["concorrentes"]

    if not concs:
        st.info("Cadastre concorrentes para acessar a biblioteca de anúncios.")
    else:
        for c in concs:
            with st.expander(f"🔍  {c['nome']}", expanded=True):
                term = c["ads_id"]
                url = f"https://www.facebook.com/ads/library/?q={term}&country=BR&media_type=all"
                st.markdown(f"<span style='font-size:15px;color:#6b7280'>Buscando por: <strong style='color:#111827'>{term}</strong></span>", unsafe_allow_html=True)
                st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)
                st.link_button("Abrir Biblioteca de Ads →", url)

# ---------------------------------------------------
# CONFRONTO DE SITES
# ---------------------------------------------------

elif st.session_state.pagina == "sites":

    st.title("🌐 Confronto de Sites")
    st.markdown("""
    <div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;padding:28px 32px;margin-top:8px'>
        <div style='font-size:18px;font-weight:600;color:#111827;margin-bottom:8px;font-family:DM Sans,sans-serif'>Em desenvolvimento</div>
        <div style='font-size:15px;color:#6b7280;font-family:DM Sans,sans-serif;line-height:1.6'>
            Este módulo permitirá comparar sites de concorrentes em termos de SEO, velocidade, conteúdo e estratégia digital.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# IA BATTLE CARDS
# ---------------------------------------------------

elif st.session_state.pagina == "insights":

    st.title("💡 IA Battle Cards")
    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:
        target = st.selectbox(
            "Gerar estratégia contra:",
            [c["nome"] for c in concorrentes]
        )
        st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)
        if st.button("Gerar Estratégia", type="primary"):
            with st.spinner("Criando Battle Card..."):
                resposta = consultar_ia(f"Gere um battle card focado em vencer o concorrente {target}.")
                st.markdown(resposta)
    else:
        st.info("Adicione concorrentes para gerar battle cards estratégicos.")
