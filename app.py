import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- CSS DEFINITIVO: 100% LARGURA E DESIGN CHUMBO ---
st.markdown("""
    <style>
        /* 1. ZERAR O PADDING DA BARRA LATERAL (Isso faz o conteúdo encostar nas bordas) */
        [data-testid="stSidebar"] > div:first-child {
            padding-left: 0px !important;
            padding-right: 0px !important;
            padding-top: 0px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }

        /* 2. FUNDO CHUMBO TOTAL */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 3. TÍTULO DO PAINEL */
        .sidebar-header {
            color: #ffffff !important;
            font-size: 12px !important;
            font-weight: 700;
            padding: 30px 20px 20px 20px;
            background-color: #1e2327 !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 1px solid #3c434a; /* Linha abaixo do título */
        }

        /* 4. BOTÕES 100% LARGURA E SEM BORDAS ARREDONDADAS */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important;
            color: #ffffff !important;
            padding: 18px 25px !important; /* Mais altura para o botão */
            text-align: left !important;
            font-size: 15px !important;
            display: block !important;
            margin: 0px !important;
            
            /* A LINHA 100% (Agora ela encosta na lateral porque o pai tem padding 0) */
            border-bottom: 1px solid #3c434a !important; 
        }

        /* 5. HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder o menu de navegação nativo */
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Ajuste do botão Sair no final */
        .exit-section {
            margin-top: 50px;
            border-top: 1px solid #3c434a;
        }
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

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Login Dashboard")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL (SISTEMA DE BOTÕES 100%) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Criando os botões. Como o padding do sidebar é 0, eles encostarão nas bordas.
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    # Seção de saída
    st.markdown('<div class="exit-section">', unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONTEÚDO DAS PÁGINAS ---
pag_atual = st.session_state.pagina
st.title(f"📍 {pag_atual}")

if pag_atual == "Minha empresa":
    st.info("Configurações da sua organização.")
    # Adicione seus inputs aqui...

elif pag_atual == "Análise de concorrentes":
    st.subheader("Gerenciar Concorrentes")
    # Lógica de cadastro...

# Adicione as outras páginas conforme necessário...
