import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS "WP-ULTIMATE" (FIX DE TAMANHO E ALINHAMENTO) ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR TUDO: Remove os espaços automáticos para as linhas serem 100% */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
            margin: 0px !important;
        }

        /* 3. TÍTULO DO PAINEL */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 40px 20px 10px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
            display: block !important;
        }

        /* 4. ESPAÇADOR DE SEGURANÇA (Evita que o hover suba no título) */
        .menu-spacer {
            height: 15px;
            background-color: #1e2327;
            border-bottom: 1px solid #2c3338; /* Linha que separa o título dos botões */
        }

        /* 5. BOTÕES: Tamanho Unificado e Alinhamento à Esquerda */
        div.stButton {
            width: 100% !important;
            margin: 0px !important;
        }

        div.stButton > button {
            width: 100% !important;
            height: 55px !important; /* FORÇAR ALTURA IGUAL PARA TODOS */
            border: none !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            color: #eee !important;
            padding: 0px 20px !important; /* Padding lateral apenas, altura controlada pelo height */
            font-size: 15px !important;
            transition: all 0.1s;
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
        }

        /* A SUA DESCOBERTA: Corrigindo o justify-center interno do Streamlit */
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
    # 1. Título
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # 2. Espaçador (O "pulo do gato" para proteger o título e manter o tamanho do botão)
    st.markdown('<div class="menu-spacer"></div>', unsafe_allow_html=True)
    
    # 3. Botões
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

    # Botão Sair
    st.markdown("<div style='height: 60px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO PRINCIPAL ---
st.title(st.session_state.pagina)
