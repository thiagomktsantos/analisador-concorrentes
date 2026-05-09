import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- CSS DEFINITIVO: DESIGN CHUMBO INTEGRADO COM DIVISORES ---
st.markdown("""
    <style>
        /* 1. Fundo total da barra lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. Remover o fundo preto do topo e zerar paddings */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0px !important;
            padding-top: 0px !important;
        }

        /* 3. Título do Painel (Removendo o fundo preto) */
        .sidebar-header {
            color: #ffffff !important;
            font-size: 13px !important;
            font-weight: 700;
            padding: 30px 20px 15px 20px;
            background-color: #1e2327 !important; /* Mesma cor do fundo */
            text-transform: uppercase;
            letter-spacing: 1.5px;
            border-bottom: 1px solid #3c434a; /* Linha abaixo do título */
        }

        /* 4. ESTILO DOS BOTÕES (MENU) */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important; /* Chumbo */
            color: #ffffff !important; /* Texto Branco */
            padding: 15px 25px !important;
            text-align: left !important;
            font-size: 14px !important;
            display: block !important;
            margin: 0px !important;
            
            /* DIVISOR: Linha horizontal fina entre botões */
            border-bottom: 1px solid #2d3339 !important; 
        }

        /* 5. Hover (ao passar o mouse) */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
            border-bottom: 1px solid #2d3339 !important;
        }

        /* 6. Botão Ativo (Destaque para a página atual) */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder ícones e menu padrão */
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Ajuste do botão Sair (Remover linha debaixo dele se quiser) */
        .exit-btn div.stButton > button {
            margin-top: 40px !important;
            border-top: 1px solid #3c434a !important;
            border-bottom: none !important;
            color: #ff4b4b !important;
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
if 'dados' not in st.session_state:
    st.session_state.dados = {"minha_empresa": {"nome": "", "setor": "", "descricao": ""}, "concorrentes": []}
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Acesso ao Sistema")
    if st.button("Entrar no Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL ---
with st.sidebar:
    # Título sem fundo preto
    st.markdown('<div class="sidebar-header">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Botões com divisores automáticos via CSS
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    # Botão Sair com estilo diferente
    st.markdown('<div class="exit-btn">', unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina
st.title(f"📍 {pag}")

if pag == "Minha empresa":
    st.info("Preencha os dados da sua empresa aqui.")
    # Coloque seus inputs aqui...

elif pag == "Análise de concorrentes":
    st.write("Gerencie sua lista de concorrentes.")
    # Coloque sua lógica de cadastro aqui...

elif pag == "Geral":
    st.metric("Total Monitorado", len(st.session_state.dados["concorrentes"]))

# ... (Repetir para as outras páginas)
