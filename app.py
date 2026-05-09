import streamlit as st
import google.generativeai as genai
import trafilatura
from duckduckgo_search import DDGS
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro", layout="wide")

# --- CSS PARA MENU "CHUMBO" PROFISSIONAL (100% WIDTH) ---
st.markdown("""
    <style>
        /* Fundo da barra lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
            padding: 0px !important;
        }
        
        /* Título do Painel */
        .sidebar-title {
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 20px 15px;
            background-color: #101214;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* ESTILIZAÇÃO DOS BOTÕES DO MENU */
        div.stButton > button {
            width: 100% !important;
            border-radius: 0px !important;
            border: none !important;
            background-color: #2c3338 !important; /* Cor Chumbo */
            color: #d1d1d1 !important;
            padding: 12px 20px !important;
            text-align: left !important;
            font-size: 14px !important;
            display: flex !important;
            align-items: center !important;
            margin-bottom: 1px !important;
            transition: all 0.3s !important;
        }

        /* Hover (Passar o mouse) */
        div.stButton > button:hover {
            background-color: #353c41 !important;
            color: #72aee6 !important;
        }

        /* Botão Selecionado (Destaque Azul WordPress) */
        .st-emotion-cache-12888p9.e1nzilvr4 { /* Alvo específico de botões em colunas se necessário */ }
        
        /* Classe customizada para o botão ativo via Session State */
        /* Como o Streamlit não tem 'active class' nativa no botão, 
           usamos a lógica de cor no python abaixo */

        /* Ajuste de margens da barra lateral */
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="stSidebar"] .block-container {padding-top: 0px !important;}
        
        /* Espaçamento para Sub-itens */
        .indent { padding-left: 30px !important; font-size: 13px !important; background-color: #23282d !important; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("API Key ausente nos Secrets.")
    st.stop()

# --- ESTADO DA SESSÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = "Minha empresa"
if 'dados' not in st.session_state:
    st.session_state.dados = {"minha_empresa": {"nome": "", "setor": "", "descricao": ""}, "concorrentes": []}
if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login Administrativo")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL (SISTEMA DE BOTÕES 100%) ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">PAINEL DE CONTROLE</div>', unsafe_allow_html=True)
    
    # Função para criar os botões com lógica de cor "Selecionado"
    def menu_item(label, is_subitem=False):
        style = "indent" if is_subitem else ""
        # Se a página atual for o label, mudamos a cor do botão no estilo
        # (Para manter simples e funcional no Streamlit, usamos o clique como gatilho)
        if st.button(label, key=f"btn_{label}", help=label):
            st.session_state.pagina = label
            st.rerun()

    menu_item("🏠 Minha empresa")
    menu_item("👥 Análise de concorrentes")
    # Sub-itens com recuo visual no texto
    menu_item("      📊 Geral", is_subitem=True)
    menu_item("      🌐 Análise de sites", is_subitem=True)
    menu_item("      📱 Análise de redes sociais", is_subitem=True)
    menu_item("      📢 Análise de anúncios", is_subitem=True)
    menu_item("💡 Insights")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()

# --- LÓGICA DE NAVEGAÇÃO E CONTEÚDO ---
pagina = st.session_state.pagina.strip()

if "Minha empresa" in pagina:
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    st.session_state.dados["minha_empresa"]["nome"] = st.text_input("Nome", emp["nome"])
    st.session_state.dados["minha_empresa"]["setor"] = st.text_input("Setor", emp["setor"])
    st.session_state.dados["minha_empresa"]["descricao"] = st.text_area("Descrição", emp["descricao"])
    if st.button("Salvar Alterações"):
        st.success("Dados salvos!")

elif "Análise de concorrentes" in pagina:
    st.title("👥 Concorrentes")
    with st.form("cad"):
        n = st.text_input("Nome")
        u = st.text_input("URL")
        if st.form_submit_button("Cadastrar"):
            st.session_state.dados["concorrentes"].append({"nome": n, "url": u, "site_data": "", "social_data": ""})
            st.success(f"{n} adicionado!")
    
    if st.session_state.dados["concorrentes"]:
        st.write(pd.DataFrame(st.session_state.dados["concorrentes"])[["nome", "url"]])

elif "Geral" in pagina:
    st.title("📊 Visão Geral")
    st.metric("Total de Concorrentes", len(st.session_state.dados["concorrentes"]))

elif "Análise de sites" in pagina:
    st.title("🌐 Auditoria de Sites")
    concs = st.session_state.dados["concorrentes"]
    if not concs: st.warning("Cadastre concorrentes primeiro.")
    else:
        alvo = st.selectbox("Escolha um concorrente", [c["nome"] for c in concs])
        if st.button("Analisar com IA"):
            with st.spinner("Lendo site..."):
                item = next(c for c in concs if c["nome"] == alvo)
                txt = trafilatura.extract(trafilatura.fetch_url(item["url"]))
                if txt:
                    res = model.generate_content(f"Resuma a estratégia deste site: {txt[:3000]}").text
                    item["site_data"] = res
                    st.markdown(res)

elif "Análise de redes sociais" in pagina:
    st.title("📱 Redes Sociais")
    st.info("Cole legendas de posts para análise de IA.")
    copy = st.text_area("Legenda do post")
    if st.button("Analisar Tom de Voz"):
        res = model.generate_content(f"Analise o tom de voz deste post: {copy}").text
        st.write(res)

elif "Análise de anúncios" in pagina:
    st.title("📢 Anúncios")
    for c in st.session_state.dados["concorrentes"]:
        st.link_button(f"Facebook Ads: {c['nome']}", f"https://www.facebook.com/ads/library/?q={c['nome']}&country=BR")

elif "Insights" in pagina:
    st.title("💡 Insights")
    if st.button("Gerar Relatório Estratégico"):
        ctx = f"Empresa: {st.session_state.dados['minha_empresa']} Concorrentes: {st.session_state.dados['concorrentes']}"
        res = model.generate_content(f"Dê 3 conselhos de marketing para esta empresa superar os concorrentes: {ctx}").text
        st.markdown(res)
