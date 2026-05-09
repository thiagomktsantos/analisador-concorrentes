import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS "WP-ULTIMATE" (CORREÇÃO DE SOBREPOSIÇÃO) ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR TUDO: Remove espaços automáticos */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
        }

        /* 3. TÍTULO: Ajustado para não ser coberto pelo hover */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            /* Aumentamos o padding inferior (25px) para afastar o hover */
            padding: 40px 20px 25px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
            margin: 0px !important;
            display: block;
            border-bottom: 1px solid #2c3338; /* Linha sutil abaixo do título */
        }

        /* 4. BOTÕES: Alinhamento total à esquerda */
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
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
        }

        /* CORREÇÃO DO JUSTIFY-CENTER (Sua descoberta) */
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

        /* 5. HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Cor de fundo quando a página está selecionada (Azul WordPress) */
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
    # Cabeçalho com padding extra na base para evitar que o hover do botão encoste
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

    # Botão Sair separado
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO ---
st.title(st.session_state.pagina)
