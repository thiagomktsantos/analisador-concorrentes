import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import trafilatura

# Configuração da Página
st.set_page_config(page_title="Analisador de Concorrentes IA", layout="wide")

# --- CONFIGURAÇÃO DA IA (Gemini) ---
# No Streamlit Cloud, você adicionará sua chave em "Secrets"
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("API Key do Gemini não encontrada. Adicione-a nos Secrets do Streamlit.")

model = genai.GenerativeModel('gemini-pro')

# --- ESTADO DA SESSÃO (Banco de Dados Temporário) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'minha_empresa' not in st.session_state:
    st.session_state.minha_empresa = {"nome": "", "setor": "", "descricao": ""}
if 'concorrentes' not in st.session_state:
    st.session_state.concorrentes = []

# --- FUNÇÕES DE AJUDA ---
def analisar_texto_ia(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na análise: {e}"

def buscar_sites_concorrentes(segmento):
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(f"melhores empresas de {segmento} brasil", max_results=5)]
    return results

def extrair_conteudo_site(url):
    downloaded = trafilatura.fetch_url(url)
    return trafilatura.extract(downloaded)

# --- TELAS ---

def login_page():
    st.title("🔐 Login - Análise de Concorrentes")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login Usuário"):
            st.session_state.logged_in = True
            st.session_state.user_type = "user"
            st.rerun()
    with col2:
        if st.button("Login Admin"):
            st.session_state.logged_in = True
            st.session_state.user_type = "admin"
            st.rerun()

def main_app():
    st.sidebar.title(f"Bem-vindo, {st.session_state.user_type}")
    menu = st.sidebar.radio("Navegação", ["Minha Empresa", "Geral / Busca", "Análise de Sites", "Redes Sociais", "Anúncios", "Insights"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    # --- PÁGINA: MINHA EMPRESA ---
    if menu == "Minha Empresa":
        st.title("🏢 Minha Empresa")
        st.session_state.minha_empresa['nome'] = st.text_input("Nome da Empresa", st.session_state.minha_empresa['nome'])
        st.session_state.minha_empresa['setor'] = st.text_input("Setor de Atuação", st.session_state.minha_empresa['setor'])
        st.session_state.minha_empresa['descricao'] = st.text_area("Descrição/Diferencial", st.session_state.minha_empresa['descricao'])
        if st.button("Salvar Dados"):
            st.success("Dados salvos!")

    # --- PÁGINA: GERAL / BUSCA ---
    elif menu == "Geral / Busca":
        st.title("🔍 Buscar Concorrentes no Google")
        segmento = st.text_input("Digite o segmento para buscar (ex: Pizzaria em SP)")
        if st.button("Buscar no Google"):
            results = buscar_sites_concorrentes(segmento)
            for r in results:
                st.write(f"**{r['title']}**")
                st.write(r['href'])
                if st.button(f"Adicionar {r['title']} aos concorrentes", key=r['href']):
                    st.session_state.concorrentes.append({"nome": r['title'], "url": r['href']})
                    st.toast("Adicionado!")

    # --- PÁGINA: ANÁLISE DE SITES ---
    elif menu == "Análise de Sites":
        st.title("🌐 Análise de Conteúdo do Site")
        if not st.session_state.concorrentes:
            st.warning("Adicione concorrentes na aba Geral primeiro.")
        else:
            selecionado = st.selectbox("Selecione o concorrente", [c['nome'] for c in st.session_state.concorrentes])
            url = [c['url'] for c in st.session_state.concorrentes if c['nome'] == selecionado][0]
            
            if st.button(f"Analisar site: {url}"):
                with st.spinner("IA Lendo o site..."):
                    texto = extrair_conteudo_site(url)
                    if texto:
                        analise = analisar_texto_ia(f"Analise o posicionamento, pontos fortes e público alvo deste site: {texto[:4000]}")
                        st.markdown(analise)
                    else:
                        st.error("Não consegui ler o conteúdo deste site.")

    # --- PÁGINA: REDES SOCIAIS ---
    elif menu == "Redes Sociais":
        st.title("📱 Análise de Redes Sociais")
        st.info("Cole o texto (copy) de um post do concorrente para a IA analisar o engajamento.")
        copy_post = st.text_area("Texto da publicação do concorrente")
        if st.button("Analisar Copy"):
            analise = analisar_texto_ia(f"Analise a estratégia de copy e o potencial de engajamento deste post de rede social: {copy_post}")
            st.markdown(analise)

    # --- PÁGINA: ANÚNCIOS ---
    elif menu == "Anúncios":
        st.title("📢 Biblioteca de Anúncios")
        st.write("O Facebook não permite extração direta, mas geramos o link oficial de pesquisa:")
        nome_busca = st.text_input("Nome da marca concorrente para ver anúncios")
        if nome_busca:
            link_ads = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={nome_busca}&country=BR&media_type=all"
            st.link_button(f"Ver anúncios de {nome_busca} no Facebook", link_ads)

    # --- PÁGINA: INSIGHTS ---
    elif menu == "Insights":
        st.title("💡 Insights Estratégicos")
        if st.button("Gerar Comparativo SWOT"):
            dados_concorrentes = str(st.session_state.concorrentes)
            minha = st.session_state.minha_empresa
            prompt = f"Com base na minha empresa ({minha}) e meus concorrentes ({dados_concorrentes}), crie uma análise SWOT e sugira 3 ações de marketing."
            insights = analisar_texto_ia(prompt)
            st.markdown(insights)

# --- GERENCIADOR DE NAVEGAÇÃO ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()