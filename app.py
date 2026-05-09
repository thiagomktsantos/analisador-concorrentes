import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS AJUSTADO (FOCO NO PRIMEIRO BOTÃO) ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR ESPAÇOS LATERAIS (Para linha 100%) */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
        }

        /* 3. TÍTULO DO PAINEL */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 35px 20px 10px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
        }

        /* 4. AJUSTE DO PRIMEIRO BOTÃO (O SEGREDO ESTÁ AQUI) */
        /* Adicionamos uma margem no topo APENAS do primeiro botão para ele não encostar no título */
        div.stButton:nth-of-type(1) {
            margin-top: 15px !important;
        }

        /* 5. ESTILO GERAL DOS BOTÕES */
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
            padding: 14px 20px !important;
            font-size: 15px !important;
            transition: all 0.1s;
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
        }

        /* SUA DESCOBERTA: Alinhamento à esquerda corrigindo o Flex interno */
        div.stButton > button > div {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
            display: flex !important;
        }

        div.stButton > button div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            text-align: left !important;
        }

        /* 6. HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Ocultar elementos nativos */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    paginas = [
        "🏠 Minha empresa", 
        "👥 Análise de concorrentes", 
        "📊 Geral", 
        "🌐 Análise de sites", 
        "📱 Análise de redes sociais", 
        "📢 Análise de anúncios", 
        "💡 Insights"
    ]

    for p in paginas:
        if st.button(p, key=f"btn_{p}"):
            st.session_state.pagina = p

    st.markdown("<div style='height: 80px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Logout")

# --- 5. CONTEÚDO PRINCIPAL ---
st.title(st.session_state.pagina)
