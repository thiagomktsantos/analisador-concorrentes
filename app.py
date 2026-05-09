import streamlit as st
import google.generativeai as genai
import trafilatura
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Competitor Dashboard", layout="wide")

# --- CSS DEFINITIVO: LARGURA TOTAL (Borda a Borda) ---
st.markdown("""
    <style>
        /* 1. RESET TOTAL DA SIDEBAR: Remove todos os paddings internos */
        [data-testid="stSidebar"] > div:first-child {
            padding: 0px !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            padding: 0px !important;
        }
        
        /* 2. FUNDO CHUMBO UNIFICADO */
        [data-testid="stSidebar"], [data-testid="stSidebar"] .st-emotion-cache-17l6985 {
            background-color: #1e2327 !important;
        }

        /* 3. CABEÇALHO DO PAINEL (Borda a Borda) */
        .sidebar-header {
            color: #ffffff !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 35px 25px 20px 25px;
            background-color: #1e2327 !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 1px solid #3c434a;
            width: 100%;
            margin: 0px !important;
        }

        /* 4. BOTÕES DO MENU: 100% LARGURA REAL */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important;
            color: #ffffff !important;
            padding: 18px 25px !important;
            text-align: left !important;
            font-size: 14px !important;
            display: block !important;
            margin: 0px !important;
            
            /* Linha divisória 100% largura */
            border-bottom: 1px solid #3c434a !important; 
        }

        /* 5. HOVER E ESTADO SELECIONADO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #ffffff !important;
        }

        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder ícones nativos e navegação do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
        .st-emotion-cache-6qob1r {display: none;}

        /* Botão Sair com destaque vermelho sutil */
        .exit-btn div.stButton > button {
            margin-top: 40px !important;
            border-top: 1px solid #3c434a !important;
            color: #ff6b6b !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("API KEY faltando.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"
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

# --- MENU LATERAL (BOTÕES 100% WIDTH) ---
with st.sidebar:
    # Título do Painel
    st.markdown('<div class="sidebar-header">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Itens do Menu
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "🏠 Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "👥 Análise de concorrentes"
    
    # Sub-itens (A hierarquia é feita com espaços de largura fixa)
    if st.button("     📊 Geral"): st.session_state.pagina = "📊 Geral"
    if st.button("     🌐 Análise de sites"): st.session_state.pagina = "🌐 Análise de sites"
    if st.button("     📱 Análise de redes sociais"): st.session_state.pagina = "📱 Análise de redes sociais"
    if st.button("     📢 Análise de anúncios"): st.session_state.pagina = "📢 Análise de anúncios"
    
    if st.button("💡 Insights"): st.session_state.pagina = "💡 Insights"

    # Botão Sair
    st.markdown('<div class="exit-btn">', unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina
st.title(f"📍 {pag}")

# Lógica das páginas continua abaixo...
if "Minha empresa" in pag:
    st.info("Formulário da Minha Empresa")
elif "Análise de concorrentes" in pag:
    st.write("Cadastro de Concorrentes")
