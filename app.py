import streamlit as st
import google.generativeai as genai
from streamlit_option_menu import option_menu

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS DEFINITIVO: LINHA 100%, SEM SOBREPOSIÇÃO E ALINHADO À ESQUERDA ---
st.markdown("""
    <style>
        /* Fundo da barra lateral */
        [data-testid="stSidebar"] {
            background-color: #2c3338 !important;
        }

        /* ZERAR PADDING DA SIDEBAR: Isso faz o menu encostar nas bordas (100% horizontal) */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }

        /* TÍTULO DO MENU: Com respiro para não ser coberto */
        .menu-title {
            color: #afb1b3 !important;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11px;
            padding: 40px 20px 20px 20px !important; /* Mais espaço no topo e base */
            letter-spacing: 1px;
            background-color: #2c3338;
        }

        /* AJUSTE DO CONTAINER DO MENU PARA LARGURA TOTAL */
        .nav-link-container {
            margin: 0 !important;
        }

        /* Forçar alinhamento à esquerda nos itens do option_menu */
        .nav-link {
            text-align: left !important;
            padding: 12px 20px !important;
            border-radius: 0px !important;
            margin: 0px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. CONFIGURAÇÃO DA IA E SESSÃO ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key não encontrada nos Secrets.")
    st.stop()

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- 4. TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ WP-Admin Login")
    if st.button("Fazer Login"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- 5. MENU LATERAL (option_menu) ---
with st.sidebar:
    # Título protegido
    st.markdown('<div class="menu-title">Painel de Controle</div>', unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=[
            "Minha empresa", 
            "Análise de concorrentes", 
            "Geral", 
            "Análise de sites", 
            "Análise de redes sociais", 
            "Análise de anúncios", 
            "Insights"
        ],
        icons=["house", "people", "speedometer2", "browser-chrome", "instagram", "megaphone", "lightbulb"],
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {
                "padding": "0!important", 
                "background-color": "#2c3338",
                "border-radius": "0px"
            },
            "icon": {"color": "#a7aaad", "font-size": "16px"}, 
            "nav-link": {
                "font-size": "14px", 
                "color": "#eee",
                "text-align": "left", 
                "margin": "0px", 
                "border-bottom": "1px solid #3c434a",
                "border-radius": "0px"
            },
            "nav-link-selected": {
                "background-color": "#2271b1", # Azul WordPress
                "font-weight": "normal"
            },
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# --- 6. LÓGICA DE CARREGAMENTO DAS PÁGINAS ---
# O 'selected' atualiza automaticamente ao clicar, o Streamlit recarrega a página sozinho.

if selected == "Minha empresa":
    st.title("🏢 Configurações da Empresa")
    st.write("Aqui você configura os dados do seu negócio.")

elif selected == "Análise de concorrentes":
    st.title("👥 Gerenciar Concorrentes")
    st.info("Adicione concorrentes para monitorar.")

elif selected == "Geral":
    st.title("📊 Dashboard Geral")

elif selected == "Análise de sites":
    st.title("🌐 Auditoria de Sites")

elif selected == "Análise de redes sociais":
    st.title("📱 Monitoramento Social")

elif selected == "Análise de anúncios":
    st.title("📢 Biblioteca de Ads")

elif selected == "Insights":
    st.title("💡 Inteligência Estratégica")
