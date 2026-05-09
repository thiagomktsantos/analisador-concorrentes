import streamlit as st
import google.generativeai as genai
from streamlit_option_menu import option_menu
import pandas as pd
import trafilatura

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Admin Panel - Análise de Concorrentes", layout="wide")

# --- ESTILO WORDPRESS (CSS CUSTOMIZADO) ---
st.markdown("""
    <style>
        /* Cor do fundo da barra lateral (Chumbo WordPress) */
        [data-testid="stSidebar"] {
            background-color: #2c3338 !important;
        }
        
        /* Ajuste de padding e cores do menu */
        .nav-link {
            font-size: 14px !important;
            text-align: left !important;
            margin: 0px !important;
            --hover-color: #353c41 !important;
            color: #eee !important;
        }

        .nav-link-selected {
            background-color: #2271b1 !important; /* Azul WordPress */
            color: white !important;
        }

        /* Título do Menu */
        .menu-title {
            color: #afb1b3 !important;
            font-weight: bold !important;
            text-transform: uppercase;
            font-size: 12px;
            padding: 10px 0 5px 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("API Key não encontrada.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {"minha_empresa": {}, "concorrentes": []}
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ WP-Admin Login")
    if st.button("Fazer Login"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL ESTILO WORDPRESS ---
with st.sidebar:
    st.markdown('<div class="menu-title">Painel de Controle</div>', unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=[
            "Minha empresa", 
            "Análise de concorrentes", 
            "Geral", 
            "Análise de sites", 
            "Análise de redes sociais", 
            "Análise de anúncios", 
            "Insights"
        ],
        icons=[
            "house",          # Minha empresa
            "people",         # Análise de concorrentes
            "speedometer2",   # Geral (Dashboard)
            "browser-chrome", # Sites
            "instagram",      # Redes Sociais
            "megaphone",      # Anúncios
            "lightbulb"       # Insights
        ],
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#2c3338"},
            "icon": {"color": "#a7aaad", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "14px", 
                "text-align": "left", 
                "margin":"0px", 
                "border-bottom": "1px solid #3c434a"
            },
            "nav-link-selected": {"background-color": "#2271b1"},
        }
    )
    
    # Simulação de hierarquia visual para as subpáginas
    st.markdown("""
        <style>
            /* Indentação para as sub-páginas */
            div[id^="option-menu-item-2"], /* Geral */
            div[id^="option-menu-item-3"], /* Sites */
            div[id^="option-menu-item-4"], /* Redes Sociais */
            div[id^="option-menu-item-5"]  /* Anúncios */
            { padding-left: 25px !important; opacity: 0.8; font-size: 13px !important; }
        </style>
    """, unsafe_allow_html=True)

    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# --- LÓGICA DAS PÁGINAS ---

if selected == "Minha empresa":
    st.title("🏢 Configurações da Empresa")
    # Form aqui...

elif selected == "Análise de concorrentes":
    st.title("👥 Gerenciar Concorrentes")
    st.info("Adicione os concorrentes que aparecerão nas sub-análises.")
    # Cadastro aqui...

elif selected == "Geral":
    st.title("📊 Dashboard Geral")
    # Métricas aqui...

elif selected == "Análise de sites":
    st.title("🌐 Auditoria de Sites")
    # IA analisa sites...

elif selected == "Análise de redes sociais":
    st.title("📱 Monitoramento Social")
    # IA analisa posts...

elif selected == "Análise de anúncios":
    st.title("📢 Biblioteca de Ads")
    # Links para Facebook Ads...

elif selected == "Insights":
    st.title("💡 Inteligência Estratégica")
    # Relatório final...
