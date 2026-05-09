import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- CSS DEFINITIVO: FUNDO CHUMBO E TEXTO BRANCO ---
st.markdown("""
    <style>
        /* 1. Fundo total da barra lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. Remover espaços extras no topo e laterais do menu */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-top: 0px !important;
            gap: 0px !important;
        }

        /* 3. Título do Painel */
        .sidebar-header {
            color: #ffffff !important;
            font-size: 14px !important;
            font-weight: bold;
            padding: 25px 20px;
            background-color: #101214;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* 4. ESTILO DOS BOTÕES (MENU) */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important; /* Cor Chumbo igual ao fundo */
            color: #ffffff !important; /* Texto Branco */
            padding: 12px 25px !important;
            text-align: left !important;
            font-size: 15px !important;
            display: block !important;
            transition: background 0.2s !important;
            margin: 0px !important;
        }

        /* 5. Efeito Hover (ao passar o mouse) */
        div.stButton > button:hover {
            background-color: #2c3338 !important; /* Um tom de chumbo levemente mais claro */
            color: #ffffff !important;
            border: none !important;
        }

        /* 6. Efeito Ativo/Foco (quando clicado) */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important; /* Azul WordPress para indicar onde você está */
            color: #ffffff !important;
            box-shadow: none !important;
        }

        /* 7. Estilo específico para Sub-itens (indentação) */
        .indent-text {
            padding-left: 20px;
            font-size: 14px;
            opacity: 0.8;
        }

        /* Esconder menu padrão do Streamlit na lateral */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Configure sua API KEY nos Secrets do Streamlit.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Minha empresa"
if 'dados' not in st.session_state:
    st.session_state.dados = {"minha_empresa": {"nome": "", "setor": "", "descricao": ""}, "concorrentes": []}
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Login Dashboard")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL (BOTÕES CHUMBO 100% WIDTH) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # Lista de itens do menu
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

# --- CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina

if pag == "Minha empresa":
    st.title("🏢 Minha Empresa")
    # Campos de input aqui...

elif pag == "Análise de concorrentes":
    st.title("👥 Gestão de Concorrentes")
    # Cadastro de concorrentes aqui...

elif pag == "Geral":
    st.title("📊 Visão Geral")
    st.write(f"Concorrentes cadastrados: {len(st.session_state.dados['concorrentes'])}")

elif pag == "Análise de sites":
    st.title("🌐 Análise de Sites")
    # Lógica de IA...

elif pag == "Análise de anúncios":
    st.title("📢 Anúncios Ativos")
    # Links para Facebook Ads...

elif pag == "Insights":
    st.title("💡 Insights Estratégicos")
    # Relatório Final...

# Rodapé ou Informação da página atual
st.sidebar.markdown(f"<div style='color: #666; padding: 20px; font-size: 12px;'>Página atual: {pag}</div>", unsafe_allow_html=True)
