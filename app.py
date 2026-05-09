import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Admin Panel", layout="wide")

# --- 2. CSS DEFINITIVO (HIERARQUIA E LARGURA TOTAL) ---
st.markdown("""
    <style>
        /* Fundo total da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* ZERAR PADDING: Garante que a linha ocupe 100% horizontal */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        /* TÍTULO DA SEÇÃO (Ex: Dados Principais) */
        .sidebar-section-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 25px 20px 10px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
        }

        /* ESTILO GERAL DOS BOTÕES */
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
            padding: 12px 20px !important;
            font-size: 14px !important;
            transition: all 0.1s;
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
        }

        /* INDENTAÇÃO PARA SUB-MENUS (Recuo à esquerda) */
        .sub-menu div.stButton > button {
            padding-left: 40px !important; /* Cria o efeito de sub-item */
            font-size: 13px !important;
            opacity: 0.9;
        }

        /* CORREÇÃO DO JUSTIFY-CONTENT (Sua descoberta) */
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

        /* HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder menu nativo */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Minha empresa"

# --- 4. MENU LATERAL COM SUBMENUS ---
with st.sidebar:
    # --- GRUPO 1 ---
    st.markdown('<div class="sidebar-section-header">Dados Principais</div>', unsafe_allow_html=True)
    
    # Usamos um container com a classe 'sub-menu' para os itens recuados
    with st.container():
        st.markdown('<div class="sub-menu">', unsafe_allow_html=True)
        if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
        if st.button("👥 Concorrentes"): st.session_state.pagina = "Concorrentes"
        st.markdown('</div>', unsafe_allow_html=True)

    # --- GRUPO 2 ---
    st.markdown('<div class="sidebar-section-header">Análises e Insights</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="sub-menu">', unsafe_allow_html=True)
        if st.button("📊 Geral"): st.session_state.pagina = "Geral"
        if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
        if st.button("📱 Redes sociais"): st.session_state.pagina = "Redes sociais"
        if st.button("📢 Anúncios"): st.session_state.pagina = "Anúncios"
        if st.button("💡 Insights"): st.session_state.pagina = "Insights"
        st.markdown('</div>', unsafe_allow_html=True)

    # Botão Sair
    st.markdown("<div style='height: 60px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.write("Saindo...")

# --- 5. CARREGAMENTO DAS PÁGINAS ---
pag = st.session_state.pagina

if pag == "Minha empresa":
    st.title("🏢 Dados da Minha Empresa")
    st.write("Configure as informações do seu negócio aqui.")

elif pag == "Concorrentes":
    st.title("👥 Gestão de Concorrentes")
    st.write("Adicione e gerencie as empresas que você deseja monitorar.")

elif pag == "Geral":
    st.title("📊 Dashboard Geral")

elif pag == "Análise de sites":
    st.title("🌐 Auditoria de Sites")

elif pag == "Insights":
    st.title("💡 Insights Estratégicos")
