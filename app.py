import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS DEFINITIVO (FOCO EM ALINHAMENTO À ESQUERDA) ---
st.markdown("""
    <style>
        /* 1. Fundo total da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. Remover o padding do container da sidebar e forçar largura total */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
            width: 100% !important;
        }

        /* 3. Título do Menu */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 25px 20px 10px 20px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* 4. RESET TOTAL DOS BOTÕES PARA ALINHAMENTO À ESQUERDA */
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
            
            /* ALINHAMENTO REAL À ESQUERDA */
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            text-align: left !important;
            
            font-size: 14px !important;
            font-weight: 400 !important;
            transition: all 0.1s;
            border-bottom: 1px solid #2c3338 !important;
        }

        /* 5. Ajuste específico para o texto dentro do botão (remover centralização do Streamlit) */
        div.stButton > button div[data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            text-align: left !important;
            width: 100% !important;
        }

        /* 6. Efeito Hover (Azul WordPress suave) */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* 7. Efeito Selecionado (Azul WordPress Vibrante) */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* Esconder ícones e menus padrão */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ESTADO E LOGIN ---
if 'pagina' not in st.session_state: st.session_state.pagina = "🏠 Minha empresa"
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🖥️ WP-Admin Style Login")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- 4. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # Criamos os botões. O texto deve ser idêntico ao que você quer mostrar.
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

    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

# --- 5. CONTEÚDO PRINCIPAL ---
# Limpamos o título para não repetir o emoji se não quiser
titulo_limpo = st.session_state.pagina

st.title(f"{titulo_limpo}")
st.write(f"Você está visualizando a seção de **{titulo_limpo}**.")

# Exemplo de conteúdo para "Minha Empresa"
if "Minha empresa" in st.session_state.pagina:
    st.info("Configure os dados da sua empresa para que a IA gere relatórios personalizados.")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Nome da Empresa")
        st.text_area("Descrição do Negócio")
    with col2:
        st.selectbox("Setor", ["Tecnologia", "Varejo", "Educação", "Saúde"])
        st.button("Salvar Alterações")
