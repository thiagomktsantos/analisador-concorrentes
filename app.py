import streamlit as st
import google.generativeai as genai
import trafilatura
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Competitor Dashboard", layout="wide")

# --- CSS ULTRA RESISTENTE: FUNDO CHUMBO, TEXTO BRANCO E LINHAS 100% ---
st.markdown("""
    <style>
        /* 1. Remove todo o padding interno da barra lateral */
        [data-testid="stSidebar"] > div:first-child {
            padding: 0px !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }

        /* 2. Fundo Chumbo em toda a sidebar */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 3. Cabeçalho sem fundo preto e com linha 100% */
        .sidebar-header {
            color: #ffffff !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 35px 25px 15px 25px;
            background-color: #1e2327 !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 1px solid #3c434a;
            width: 100%;
        }

        /* 4. Estilo dos Botões (Menu) - Forçando 100% de largura e texto branco */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important;
            color: #ffffff !important;
            padding: 16px 25px !important;
            text-align: left !important;
            font-size: 14px !important;
            display: block !important;
            margin: 0px !important;
            
            /* A linha horizontal 100% */
            border-bottom: 1px solid #3c434a !important; 
        }

        /* 5. Efeito de Seleção e Hover */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #ffffff !important;
            border-bottom: 1px solid #3c434a !important;
        }

        /* Botão quando está focado ou clicado */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* 6. Indentação para as sub-páginas (Hierarquia) */
        /* Aplicaremos o recuo via Python, mas o CSS garante o alinhamento */
        .indent-btn {
            padding-left: 45px !important;
        }

        /* Esconder ícones nativos do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Ajuste do botão Sair para o final */
        .exit-btn {
            margin-top: 50px;
            border-top: 1px solid #3c434a;
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA IA (GEMINI) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Configure sua API KEY nos Secrets.")
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

# --- MENU LATERAL (ESTILO WORDPRESS) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Itens do Menu
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "🏠 Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "👥 Análise de concorrentes"
    
    # Sub-itens (A indentação é feita com espaços no texto do botão)
    if st.button("ㅤㅤ📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("ㅤㅤ🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("ㅤㅤ📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("ㅤㅤ📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    # Seção Sair
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

# --- CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina
st.title(f"📍 {pag.strip()}")

if "Minha empresa" in pag:
    st.write("Configurações do perfil da sua própria organização.")
    # Adicionar campos de formulário aqui

elif "Análise de concorrentes" in pag:
    st.write("Gerencie os nomes e URLs das empresas concorrentes.")
    # Adicionar formulário de cadastro aqui

elif "Geral" in pag:
    st.write("Visão macro de todos os dados coletados.")

elif "Análise de sites" in pag:
    st.write("A IA analisa o conteúdo e posicionamento dos sites listados.")

elif "Análise de anúncios" in pag:
    st.write("Links diretos para a biblioteca de anúncios ativos.")

elif "Insights" in pag:
    st.write("Relatórios gerados pela IA cruzando os dados.")
