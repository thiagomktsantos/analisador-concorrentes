import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS DEFINITIVO: LINHAS 100% E ALINHAMENTO ---
st.markdown("""
    <style>
        /* 1. Fundo total da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. REMOVER PADDING DO CONTAINER PRINCIPAL (Isso faz a linha chegar na borda) */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-left: 0px !important;
            padding-right: 0px !important;
            padding-top: 0px !important;
            gap: 0px !important;
        }

        /* Forçar todos os sub-containers a ocuparem 100% sem margens */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
        }

        /* 3. Título do Menu (Adicionamos padding aqui já que tiramos do container pai) */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 25px 20px 10px 20px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327;
        }

        /* 4. BOTÕES COM LINHA 100% */
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
            padding: 14px 20px !important; /* Espaçamento interno do botão */
            
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            text-align: left !important;
            
            font-size: 14px !important;
            transition: all 0.1s;
            
            /* A LINHA QUE OCUPA 100% */
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
        }

        /* Ajuste do texto interno para não centralizar nunca */
        div.stButton > button div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            text-align: left !important;
            width: 100% !important;
        }

        /* 5. Efeito Hover e Ativo */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder ícones e menus padrão do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # Lista de páginas
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
        if st.button(p, key=p):
            st.session_state.pagina = p

    # Espaçador e Botão Sair
    st.markdown("<div style='height: 40px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.write("Saindo...")

# --- 5. CONTEÚDO PRINCIPAL ---
pag = st.session_state.pagina
st.title(f"{pag}")

if "Minha empresa" in pag:
    st.write(f"Você está visualizando a seção de {pag}")
    st.info("Configure os dados da sua empresa para que a IA gere relatórios personalizados.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Nome da Empresa")
        st.text_area("Descrição do Negócio")
    with col2:
        st.selectbox("Setor", ["Tecnologia", "Varejo", "Serviços"])
        st.button("Salvar Alterações")
