import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Competitor Analysis Pro", layout="wide")

# --- CSS ULTRA-AGRESSIVO PARA 100% DE LARGURA E DESIGN CHUMBO ---
st.markdown("""
    <style>
        /* 1. ZERA TUDO: Remove paddings e margins da barra lateral e seus containers internos */
        [data-testid="stSidebar"] > div:first-child {
            padding: 0px !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        [data-testid="stSidebar"] .st-emotion-cache-17l6985 {
            padding: 0px !important;
        }
        
        /* 2. FUNDO CHUMBO TOTAL */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 3. CABEÇALHO DO PAINEL (100% LARGURA) */
        .sidebar-header {
            color: #ffffff !important;
            font-size: 13px !important;
            font-weight: 700;
            padding: 30px 20px 20px 20px;
            background-color: #1e2327 !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 1px solid #3c434a; /* Linha de separação */
            width: 100%;
        }

        /* 4. BOTÕES DO MENU (FORÇADOS A 100% E SEM BORDAS) */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important;
            color: #ffffff !important;
            padding: 20px 25px !important; /* Aumenta a área de clique */
            text-align: left !important;
            font-size: 15px !important;
            display: flex !important;
            align-items: center !important;
            margin: 0px !important;
            
            /* A LINHA 100% QUE ENCOSTA NAS LATERAIS */
            border-bottom: 1px solid #3c434a !important; 
        }

        /* 5. EFEITO AO PASSAR O MOUSE (HOVER) */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
            border-bottom: 1px solid #3c434a !important;
        }

        /* 6. ESTADO ATIVO (QUANDO CLICADO) */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* 7. BOTÃO SAIR (No final da lista) */
        .exit-btn div.stButton > button {
            margin-top: 40px !important;
            border-top: 1px solid #3c434a !important;
            color: #ff6b6b !important;
        }

        /* Esconder ícones e navegação padrão do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
        .st-emotion-cache-6qob1r {display: none;} /* Esconde o botão de fechar sidebar se necessário */
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Configure sua API KEY.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Minha empresa"
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'dados' not in st.session_state:
    st.session_state.dados = {"minha_empresa": {}, "concorrentes": []}

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Login Dashboard")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL (BOTÕES 100%) ---
with st.sidebar:
    # Título do Painel
    st.markdown('<div class="sidebar-header">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Lista de Botões (O CSS fará com que a linha de baixo encoste nas bordas)
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    # Seção Sair
    st.markdown('<div class="exit-btn">', unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina
st.title(f"📍 {pag}")

if pag == "Minha empresa":
    st.info("Preencha aqui os dados da sua empresa.")
    with st.container():
        nome = st.text_input("Nome da Empresa")
        setor = st.text_input("Setor")
        if st.button("Salvar"):
            st.success("Dados salvos!")

elif pag == "Análise de concorrentes":
    st.subheader("Gerenciar Concorrentes")
    with st.form("cad_concorrente"):
        c_nome = st.text_input("Nome do Concorrente")
        c_site = st.text_input("URL do Site")
        if st.form_submit_button("Cadastrar"):
            st.session_state.dados["concorrentes"].append({"nome": c_nome, "url": c_site})
            st.toast("Concorrente adicionado!")

elif pag == "Geral":
    st.write("Dashboard geral de análises.")
    if st.session_state.dados["concorrentes"]:
        st.table(st.session_state.dados["concorrentes"])
    else:
        st.warning("Nenhum concorrente cadastrado.")

# (As demais páginas seguem a mesma lógica...)
