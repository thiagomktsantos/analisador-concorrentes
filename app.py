import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS "WP-ULTIMATE" (LINHAS TOTAIS E TÍTULO REPOSICIONADO) ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR TUDO: Remove todos os espaços internos que o Streamlit cria */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        /* Forçar os blocos a ocuparem 100% da largura */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
        }

        /* 3. TÍTULO: Agora com espaço suficiente para não ser coberto */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 30px 20px 15px 20px !important; /* Aumentei o topo para 30px */
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #101214; /* Fundo levemente mais escuro para o título */
            margin-bottom: 0px;
        }

        /* 4. BOTÕES: ALINHAMENTO TOTAL À ESQUERDA (Sua descoberta aplicada) */
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
            border-bottom: 1px solid #2c3338 !important; /* Linha de fora a fora */
            margin: 0px !important;
            display: flex !important;
            justify-content: flex-start !important;
        }

        /* RESOLVENDO O PROBLEMA DO JUSTIFY-CENTER (Sua descoberta) */
        /* Alvejamos o container interno flex do botão */
        div.stButton > button > div {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
            display: flex !important;
        }

        /* Forçar o texto (markdown) a também não centralizar */
        div.stButton > button div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            text-align: left !important;
        }

        /* 5. HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Botão Ativo / Clicado */
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
    # Cabeçalho agora com fundo escuro e respiro no topo
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

    # Espaço para o botão sair no final
    st.markdown("<div style='height: 60px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO ---
st.title(st.session_state.pagina)
st.write(f"Bem-vindo à seção: {st.session_state.pagina}")
