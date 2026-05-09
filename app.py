import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS "WP-ULTIMATE" (FIX DE SOBREPOSIÇÃO FINAL) ---
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
        
        /* Forçar largura 100% em todos os containers de elementos */
        [data-testid="stSidebar"] .element-container, 
        [data-testid="stSidebar"] .stVerticalBlock > div {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
            margin: 0px !important;
        }

        /* 3. TÍTULO: Blindado com Z-INDEX e Padding */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 40px 20px 15px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327 !important;
            
            /* Isso impede que o hover do botão passe por cima */
            position: relative !important;
            z-index: 99 !important; 
            margin-bottom: 5px !important; 
            display: block !important;
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
            transition: background 0.1s;
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
            position: relative;
            z-index: 1;
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

        /* 5. HOVER: Com limite claro */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Estado Selecionado / Ativo */
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
    # Cabeçalho blindado com z-index
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

    # Espaçador e Botão Sair
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO PRINCIPAL ---
st.title(st.session_state.pagina)
