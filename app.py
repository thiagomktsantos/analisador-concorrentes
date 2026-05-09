import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS DEFINITIVO (CORREÇÃO DE ALINHAMENTO E ESPAÇAMENTO) ---
st.markdown("""
    <style>
        /* Fundo total da barra lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* CORREÇÃO DO ESPAÇAMENTO NO TOPO (Evita cobrir o título) */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-top: 20px !important; 
            gap: 0px !important;
        }

        /* FORÇAR LARGURA TOTAL DO CONTEÚDO INTERNO */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
        }

        /* TÍTULO "PAINEL DE CONTROLE" */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 12px !important;
            font-weight: bold;
            padding: 10px 20px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        /* ESTILO DOS BOTÕES (ALINHAMENTO À ESQUERDA) */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: transparent !important; /* Fundo transparente para estilo clean */
            color: #eee !important; 
            padding: 12px 20px !important;
            
            /* ALINHAMENTO À ESQUERDA - O SEGREDO ESTÁ AQUI */
            display: flex !important;
            justify-content: flex-start !important; 
            text-align: left !important;
            
            font-size: 15px !important;
            transition: all 0.2s;
            margin: 0px !important;
            border-bottom: 1px solid #2c3338 !important;
        }

        /* Efeito Hover */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Botão Ativo (Simulação) */
        div.stButton > button:focus {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder o menu nativo do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DA IA E ESTADO ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Configure sua API KEY nos Secrets.")
    st.stop()

if 'pagina' not in st.session_state: st.session_state.pagina = "Minha empresa"
if 'logado' not in st.session_state: st.session_state.logado = False

# --- 4. TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Login Dashboard")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- 5. MENU LATERAL ---
with st.sidebar:
    # Título que não será mais coberto
    st.markdown('<div class="sidebar-header">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Botões agora perfeitamente alinhados à esquerda
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

# --- 6. CONTEÚDO ---
pag = st.session_state.pagina
st.title(f"{pag}")
st.write(f"Você está na página: **{pag}**")
