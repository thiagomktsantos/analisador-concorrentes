import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS "WP-ULTIMATE" (FIX DE SOBREPOSIÇÃO E LARGURA TOTAL) ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR TUDO: Remove os paddings que criam o "vão" lateral */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
        }

        /* 3. TÍTULO: Isolado com margem inferior para proteger do hover */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 45px 20px 20px 20px !important; /* Aumentamos o respiro inferior */
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
            margin: 0px !important;
            display: block !important;
            /* Linha opcional para delimitar o título */
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
            border-bottom: 1px solid #2c3338 !important; /* Linha de ponta a ponta */
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
        }

        /* CORREÇÃO DO JUSTIFY-CENTER (Sua descoberta aplicada de forma estável) */
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

        /* 5. HOVER: Agora limitado ao espaço do botão sem subir no título */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Estado Selecionado */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Ocultar elementos nativos do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"

# --- 4. MENU LATERAL ---
with st.sidebar:
    # Cabeçalho protegido
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

    # Botão Sair no final
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO PRINCIPAL ---
st.title(st.session_state.pagina)
st.write(f"Você está em: {st.session_state.pagina}")
