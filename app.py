import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS AJUSTADO ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR PADDINGS E GAPS DO CONTAINER */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] .element-container {
            width: 100% !important;
            margin: 0px !important;
        }

        /* 3. TÍTULO (Cabeçalho) - Ajustado para alinhar com os botões */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 40px 20px 20px 20px !important; /* Padding inferior ajustado */
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327 !important;
            margin: 0px !important; /* Removido margin-bottom para não quebrar a altura */
            display: block !important;
        }

        /* 4. BOTÕES: Largura 100% e Altura Fixa */
        div.stButton {
            width: 100% !important;
            margin: 0px !important;
        }

        div.stButton > button {
            width: 100% !important;
            height: 55px !important; /* Altura fixa para todos serem iguais */
            border: none !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            color: #eee !important;
            padding: 0px 20px !important; /* Padding vertical removido pois usamos height */
            font-size: 15px !important;
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
        }

        /* CORREÇÃO DO CONTEÚDO INTERNO DO BOTÃO */
        div.stButton > button > div {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
        }

        /* 5. HOVER E ESTADO ATIVO (Baseado na escolha da sessão) */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Estilo para simular o botão selecionado (Azul do WordPress) */
        .st-emotion-cache-12w0qpk.e17nne651 { /* Seletor específico para o botão ativo se clicar */
            background-color: #2271b1 !important;
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
        # Lógica para destacar o botão ativo
        is_active = st.session_state.pagina == p
        style = "background-color: #2271b1 !important; color: white !important;" if is_active else ""
        
        if st.button(p, key=f"btn_{p}"):
            st.session_state.pagina = p
            st.rerun()

    # Espaçador e Botão Sair
    st.markdown("<div style='height: 50px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO PRINCIPAL ---
st.title(st.session_state.pagina)
