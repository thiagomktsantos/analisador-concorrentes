import streamlit as st
from streamlit_option_menu import option_menu
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WP-Admin Competitor Analysis", layout="wide")

# --- CSS CUSTOMIZADO (ESTILO WORDPRESS DARK) ---
st.markdown("""
    <style>
        /* Fundo da barra lateral (Chumbo WordPress) */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* Título do Painel */
        .admin-title {
            color: #f0f0f1;
            font-size: 18px;
            font-weight: bold;
            padding: 20px 15px;
            letter-spacing: 1px;
        }

        /* Estilo dos itens do Menu */
        .nav-link {
            color: #d1d1d1 !important;
            font-size: 14px !important;
            text-align: left !important;
            border-radius: 0px !important;
            padding: 10px 15px !important;
        }

        /* Item selecionado (Azul WordPress) */
        .nav-link-selected {
            background-color: #2271b1 !important;
            color: white !important;
            font-weight: bold !important;
        }

        /* Sub-menus (Recuo visual) */
        div[id^="option-menu-item-2"], 
        div[id^="option-menu-item-3"], 
        div[id^="option-menu-item-4"], 
        div[id^="option-menu-item-5"] {
            padding-left: 30px !important;
            background-color: #262c33 !important;
            font-size: 13px !important;
        }

        /* Hover */
        .nav-link:hover {
            color: #72aee6 !important;
        }

        /* Botão Sair */
        .stButton > button {
            width: 90%;
            margin: 0 auto;
            display: block;
            background-color: transparent;
            color: #646970;
            border: 1px solid #3c434a;
            border-radius: 4px;
        }
        .stButton > button:hover {
            border-color: #d63638;
            color: #d63638;
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Erro: GEMINI_API_KEY não configurada nos Secrets do Streamlit.")
    st.stop()

# --- ESTADO DA SESSÃO (BANCO DE DADOS TEMPORÁRIO) ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {"nome": "", "setor": "", "descricao": ""},
        "concorrentes": [] # Lista de dicts
    }
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO DE IA ---
def analisar_ia(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na análise: {e}"

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🖥️ Painel Administrativo")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Acessar Sistema"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- BARRA LATERAL (MENU WORDPRESS) ---
with st.sidebar:
    st.markdown('<div class="admin-title">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
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
        icons=[
            "house-fill", "people-fill", "speedometer", "window", "instagram", "megaphone-fill", "lightbulb-fill"
        ],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"font-size": "16px"},
            "nav-link-selected": {"background-color": "#2271b1"},
        }
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# --- LÓGICA DAS PÁGINAS ---

# 1. MINHA EMPRESA
if selected == "Minha empresa":
    st.title("🏢 Minha Empresa")
    st.write("Configure o perfil da sua própria empresa para que a IA possa fazer comparações.")
    
    emp = st.session_state.dados["minha_empresa"]
    st.session_state.dados["minha_empresa"]["nome"] = st.text_input("Nome da Empresa", emp["nome"])
    st.session_state.dados["minha_empresa"]["setor"] = st.text_input("Setor de Atuação", emp["setor"])
    st.session_state.dados["minha_empresa"]["descricao"] = st.text_area("Descrição do seu produto/serviço", emp["descricao"])
    
    if st.button("Salvar Perfil"):
        st.success("Perfil atualizado com sucesso!")

# 2. ANÁLISE DE CONCORRENTES (Cadastro)
elif selected == "Análise de concorrentes":
    st.title("👥 Gestão de Concorrentes")
    st.write("Adicione abaixo as empresas que deseja monitorar.")
    
    with st.form("novo_concorrente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome_c = col1.text_input("Nome da Marca")
        url_c = col2.text_input("URL do Site (com https://)")
        ads_c = st.text_input("Nome exato para busca de Anúncios (opcional)")
        if st.form_submit_button("Cadastrar Concorrente"):
            if nome_c and url_c:
                st.session_state.dados["concorrentes"].append({
                    "nome": nome_c, "url": url_c, "ads_name": ads_c, 
                    "site_data": "", "social_data": ""
                })
                st.success(f"{nome_c} adicionado!")
            else:
                st.error("Preencha Nome e URL.")

    st.subheader("Empresas Monitoradas")
    if st.session_state.dados["concorrentes"]:
        df = pd.DataFrame(st.session_state.dados["concorrentes"])[["nome", "url"]]
        st.table(df)
        if st.button("Limpar Lista"):
            st.session_state.dados["concorrentes"] = []
            st.rerun()
    else:
        st.info("Nenhum concorrente cadastrado.")

# 3. GERAL (Resumo)
elif selected == "Geral":
    st.title("📊 Resumo Operacional")
    concs = st.session_state.dados["concorrentes"]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Concorrentes", len(concs))
    c2.metric("Análises de Site", sum(1 for c in concs if c["site_data"]))
    c3.metric("Análises Social", sum(1 for c in concs if c["social_data"]))

# 4. ANÁLISE DE SITES
elif selected == "Análise de sites":
    st.title("🌐 Auditoria de Sites (IA)")
    concs = st.session_state.dados["concorrentes"]
    
    if not concs:
        st.warning("Cadastre um concorrente na página anterior.")
    else:
        alvo = st.selectbox("Selecione um concorrente", [c["nome"] for c in concs])
        item = next(c for c in concs if c["nome"] == alvo)
        
        if st.button(f"Analisar site de {alvo}"):
            with st.spinner("IA extraindo conteúdo e analisando..."):
                downloaded = trafilatura.fetch_url(item["url"])
                texto = trafilatura.extract(downloaded)
                if texto:
                    resumo = analisar_ia(f"Resuma a proposta de valor e estratégia de vendas deste site em tópicos: {texto[:4000]}")
                    item["site_data"] = resumo
                    st.markdown(resumo)
                else:
                    st.error("Não foi possível ler o site. Tente outra URL.")

# 5. ANÁLISE DE REDES SOCIAIS
elif selected == "Análise de redes sociais":
    st.title("📱 Redes Sociais")
    st.write("Cole o texto de uma postagem do concorrente para analisar a estratégia.")
    
    concs = st.session_state.dados["concorrentes"]
    if concs:
        alvo = st.selectbox("Concorrente alvo", [c["nome"] for c in concs])
        item = next(c for c in concs if c["nome"] == alvo)
        copy = st.text_area("Copy (texto) da publicação")
        
        if st.button("Analisar Post"):
            analise = analisar_ia(f"Analise o tom de voz e o gatilho mental deste post: {copy}")
            item["social_data"] = analise
            st.info(analise)

# 6. ANÁLISE DE ANÚNCIOS
elif selected == "Análise de anúncios":
    st.title("📢 Biblioteca de Anúncios")
    st.write("Acesso rápido aos anúncios ativos dos concorrentes no Facebook/Instagram.")
    
    for c in st.session_state.dados["concorrentes"]:
        nome_busca = c["ads_name"] if c["ads_name"] else c["nome"]
        link = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={nome_busca}&country=BR"
        col_n, col_l = st.columns([1, 1])
        col_n.subheader(c["nome"])
        col_l.link_button("Ver Anúncios no Facebook", link)

# 7. INSIGHTS
elif selected == "Insights":
    st.title("💡 Insights Estratégicos")
    if st.button("Gerar Relatório de Inteligência"):
        with st.spinner("IA processando dados cruzados..."):
            ctx = f"Minha empresa: {st.session_state.dados['minha_empresa']}. Concorrentes: {st.session_state.dados['concorrentes']}"
            relatorio = analisar_ia(f"Com base nesses dados de mercado, cite 3 oportunidades de ouro e 1 ameaça: {ctx}")
            st.markdown(relatorio)
