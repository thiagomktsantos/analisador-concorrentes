import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS DEFINITIVO (RESOLVE ALINHAMENTO, LARGURA E SOBREPOSIÇÃO) ---
st.markdown("""
    <style>
        /* 1. Fundo total da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR PADDING: Faz a linha ocupar 100% da largura horizontal */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-left: 0px !important;
            padding-right: 0px !important;
            padding-top: 0px !important;
            gap: 0px !important;
        }
        
        /* Forçar todos os containers internos a ocuparem 100% */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        /* 3. TÍTULO: Espaçamento para não ser coberto pelo hover */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 40px 20px 20px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
            border-bottom: 1px solid #2c3338;
        }

        /* 4. BOTÕES: Alinhamento total à esquerda e largura 100% */
        div.stButton {
            width: 100% !important;
            margin: 0px !important;
        }

        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            color: #eee !important;
            padding: 16px 20px !important;
            font-size: 15px !important;
            transition: all 0.1s;
            border-bottom: 1px solid #2c3338 !important; /* Linha horizontal 100% */
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
        }

        /* A SUA DESCOBERTA: Corrigindo o centro para esquerda no container interno */
        div.stButton > button > div {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
            display: flex !important;
        }

        div.stButton > button div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            text-align: left !important;
            width: 100% !important;
        }

        /* 5. HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Azul WordPress para o botão clicado */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder menu nativo */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO DA SESSÃO (CONTROLE DE NAVEGAÇÃO) ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Minha empresa"

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # Criamos os botões e cada um atualiza a página no st.session_state
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    st.markdown("<div style='height: 80px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.write("Saindo...")

# --- 5. CARREGAMENTO DAS PÁGINAS ---
pag = st.session_state.pagina

if pag == "Minha empresa":
    st.title("🏢 Minha Empresa")
    st.write("Conteúdo da página Minha Empresa.")

elif pag == "Análise de concorrentes":
    st.title("👥 Análise de Concorrentes")
    st.write("Conteúdo da página de Concorrentes.")

elif pag == "Geral":
    st.title("📊 Painel Geral")

elif pag == "Análise de sites":
    st.title("🌐 Análise de Sites")

elif pag == "Análise de redes sociais":
    st.title("📱 Redes Sociais")

elif pag == "Análise de anúncios":
    st.title("📢 Gestão de Anúncios")

elif pag == "Insights":
    st.title("💡 Insights de IA")
