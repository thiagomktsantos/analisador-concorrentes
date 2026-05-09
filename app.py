import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- 2. CSS DEFINITIVO (ESTILO WORDPRESS ADMIN) ---
# Este bloco remove as margens do Streamlit e força a largura total
st.markdown("""
    <style>
        /* Fundo total da barra lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
            min-width: 260px !important;
        }

        /* CORREÇÃO DE LARGURA: Força os containers internos a ocuparem 100% */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
            width: 100% !important;
        }
        
        /* Remove o 'fit-content' que causava o erro visual que você encontrou */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
        }

        /* Cabeçalho do Menu */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: bold;
            padding: 20px 20px 10px 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* ESTILO DOS BOTÕES (MENU) */
        div.stButton > button {
            width: 100% !important;
            border: none !important;
            border-radius: 0px !important;
            background-color: #1e2327 !important; 
            color: #eee !important; 
            padding: 12px 20px !important;
            text-align: left !important;
            font-size: 14px !important;
            display: block !important;
            transition: all 0.2s;
            margin: 0px !important;
            border-bottom: 1px solid #2c3338 !important;
        }

        /* Efeito Hover */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important; /* Azul claro ao passar o mouse */
        }

        /* Efeito Ativo/Foco */
        div.stButton > button:focus, div.stButton > button:active {
            background-color: #2271b1 !important; 
            color: #ffffff !important;
            box-shadow: none !important;
        }

        /* Esconder o menu de navegação nativo do Streamlit */
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Ajuste do conteúdo principal para não colar no topo */
        .main .block-container {
            padding-top: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Configure sua API KEY nos Secrets do Streamlit.")
    st.stop()

# --- 4. ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Minha empresa"
if 'dados' not in st.session_state:
    st.session_state.dados = {"minha_empresa": {"nome": "", "setor": "", "descricao": ""}, "concorrentes": []}
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Acesso ao Painel")
    col1, col2 = st.columns([1,2])
    with col1:
        if st.button("Fazer Login"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 6. MENU LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # Botões de navegação
    if st.button("🏠 Minha empresa"): st.session_state.pagina = "Minha empresa"
    if st.button("👥 Análise de concorrentes"): st.session_state.pagina = "Análise de concorrentes"
    if st.button("📊 Geral"): st.session_state.pagina = "Geral"
    if st.button("🌐 Análise de sites"): st.session_state.pagina = "Análise de sites"
    if st.button("📱 Análise de redes sociais"): st.session_state.pagina = "Análise de redes sociais"
    if st.button("📢 Análise de anúncios"): st.session_state.pagina = "Análise de anúncios"
    if st.button("💡 Insights"): st.session_state.pagina = "Insights"

    # Rodapé do Menu
    st.markdown("<br><br><hr style='border-color: #3c434a'>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

# --- 7. LÓGICA DE CONTEÚDO DAS PÁGINAS ---
pag = st.session_state.pagina

# Container principal para o conteúdo
with st.container():
    if pag == "Minha empresa":
        st.header("🏢 Configurações da Minha Empresa")
        st.write("Preencha os dados abaixo para personalizar as análises.")
        
        nome = st.text_input("Nome da Empresa", st.session_state.dados["minha_empresa"]["nome"])
        setor = st.text_input("Setor de Atuação", st.session_state.dados["minha_empresa"]["setor"])
        desc = st.text_area("Descrição Curta", st.session_state.dados["minha_empresa"]["descricao"])
        
        if st.button("Salvar Dados"):
            st.session_state.dados["minha_empresa"] = {"nome": nome, "setor": setor, "descricao": desc}
            st.success("Dados salvos com sucesso!")

    elif pag == "Análise de concorrentes":
        st.header("👥 Gestão de Concorrentes")
        st.info("Adicione os sites ou nomes dos concorrentes para monitoramento.")
        # Lógica de cadastro de concorrentes...

    elif pag == "Geral":
        st.header("📊 Visão Geral do Mercado")
        col1, col2, col3 = st.columns(3)
        col1.metric("Empresa", st.session_state.dados["minha_empresa"]["nome"] or "Não definida")
        col2.metric("Concorrentes", len(st.session_state.dados["concorrentes"]))
        col3.metric("Status", "Ativo", delta="IA Online")

    elif pag == "Análise de sites":
        st.header("🌐 Auditoria de Sites")
        url = st.text_input("Insira a URL para analisar")
        if st.button("Analisar com IA"):
            with st.spinner("Extraindo dados e gerando insights..."):
                # Aqui entraria sua lógica de trafilatura e gemini
                st.write("Resultado da análise aparecerá aqui.")

    elif pag == "Análise de anúncios":
        st.header("📢 Biblioteca de Anúncios")
        st.write("Acompanhe as campanhas ativas dos seus concorrentes.")

    elif pag == "Insights":
        st.header("💡 Relatório Estratégico")
        st.write("Análise consolidada baseada em todos os dados coletados.")

# Feedback da página atual no final da sidebar
st.sidebar.markdown(f"""
    <div style='position: fixed; bottom: 10px; left: 20px; color: #666; font-size: 11px;'>
        Página: {pag}
    </div>
""", unsafe_allow_html=True)
