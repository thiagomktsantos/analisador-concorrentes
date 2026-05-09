import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import trafilatura
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Análise de Concorrentes IA", layout="wide")

# --- CONFIGURAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("Chave API não configurada.")
    st.stop()

# --- ESTADO GLOBAL DA APLICAÇÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {"nome": "", "setor": "", "descricao": ""},
        "concorrentes": [], # Lista de dicts: {"nome": "", "url": "", "analise_site": "", "social": "", "ads_id": ""}
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    try:
        return model.generate_content(prompt).text
    except:
        return "IA indisponível no momento."

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login - Administrador")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Acessar Painel"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MENU LATERAL (CONFORME SOLICITADO) ---
st.sidebar.title("Menu Principal")
menu = st.sidebar.radio("Navegação", [
    "Minha empresa",
    "Análise de concorrentes",
    "Geral",
    "Análise de sites",
    "Análise de redes sociais",
    "Análise de anúncios",
    "Insights"
])

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- LÓGICA DAS PÁGINAS ---

# 1. MINHA EMPRESA
if menu == "Minha empresa":
    st.title("🏢 Minha Empresa")
    st.write("Descreva seu negócio para que a IA possa comparar com os concorrentes.")
    emp = st.session_state.dados["minha_empresa"]
    st.session_state.dados["minha_empresa"]["nome"] = st.text_input("Nome da sua Empresa", emp["nome"])
    st.session_state.dados["minha_empresa"]["setor"] = st.text_input("Setor/Nicho", emp["setor"])
    st.session_state.dados["minha_empresa"]["descricao"] = st.text_area("Descrição do seu produto/serviço", emp["descricao"])
    if st.button("Salvar Dados"):
        st.success("Dados da empresa salvos!")

# 2. ANÁLISE DE CONCORRENTES (Cadastro)
elif menu == "Análise de concorrentes":
    st.title("👥 Cadastro de Concorrentes")
    st.write("Liste abaixo as empresas que você deseja monitorar.")
    
    with st.form("form_concorrente"):
        nome_c = st.text_input("Nome do Concorrente")
        url_c = st.text_input("URL do Site (ex: https://site.com)")
        ads_c = st.text_input("ID ou Nome para Biblioteca de Anúncios (opcional)")
        if st.form_submit_button("Adicionar Concorrente"):
            if nome_c and url_c:
                st.session_state.dados["concorrentes"].append({
                    "nome": nome_c, "url": url_c, "ads_id": ads_c,
                    "analise_site": "", "social": ""
                })
                st.success(f"{nome_c} adicionado!")
            else:
                st.error("Nome e URL são obrigatórios.")

    st.subheader("Lista de Concorrentes Cadastrados")
    if st.session_state.dados["concorrentes"]:
        for i, c in enumerate(st.session_state.dados["concorrentes"]):
            st.write(f"**{c['nome']}** - {c['url']}")
            if st.button(f"Remover {c['nome']}", key=f"del_{i}"):
                st.session_state.dados["concorrentes"].pop(i)
                st.rerun()
    else:
        st.info("Nenhum concorrente cadastrado ainda.")

# 3. GERAL (Dashboard)
elif menu == "Geral":
    st.title("📊 Painel Geral")
    st.write("Resumo do status das suas análises.")
    
    concs = st.session_state.dados["concorrentes"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Concorrentes", len(concs))
    col2.metric("Sites Analisados", sum(1 for c in concs if c["analise_site"]))
    col3.metric("Publicações Analisadas", sum(1 for c in concs if c["social"]))

    if concs:
        df = pd.DataFrame(concs)[["nome", "url", "ads_id"]]
        st.table(df)

# 4. ANÁLISE DE SITES
elif menu == "Análise de sites":
    st.title("🌐 Análise de Sites")
    concs = st.session_state.dados["concorrentes"]
    if not concs:
        st.warning("Cadastre um concorrente primeiro.")
    else:
        selecionado = st.selectbox("Escolha um concorrente", [c["nome"] for c in concs])
        concorrente = next(item for item in concs if item["nome"] == selecionado)
        
        if st.button(f"Analisar site de {selecionado}"):
            with st.spinner("IA analisando conteúdo do site..."):
                texto = trafilatura.extract(trafilatura.fetch_url(concorrente["url"]))
                if texto:
                    prompt = f"Analise a estratégia de vendas deste site e liste 3 pontos fortes: {texto[:3000]}"
                    resultado = consultar_ia(prompt)
                    concorrente["analise_site"] = resultado
                    st.markdown(resultado)
                else:
                    st.error("Não foi possível extrair dados do site.")

# 5. ANÁLISE DE REDES SOCIAIS
elif menu == "Análise de redes sociais":
    st.title("📱 Análise de Redes Sociais")
    concs = st.session_state.dados["concorrentes"]
    if not concs:
        st.warning("Cadastre um concorrente primeiro.")
    else:
        selecionado = st.selectbox("De quem é esta publicação?", [c["nome"] for c in concs])
        concorrente = next(item for item in concs if item["nome"] == selecionado)
        copy = st.text_area("Cole aqui a legenda (copy) do post do concorrente")
        
        if st.button("Analisar Copy e Engajamento"):
            with st.spinner("Analisando..."):
                prompt = f"Analise a copy deste post e diga qual o objetivo dele (venda, autoridade ou engajamento): {copy}"
                resultado = consultar_ia(prompt)
                concorrente["social"] = resultado
                st.markdown(resultado)

# 6. ANÁLISE DE ANÚNCIOS
elif menu == "Análise de anúncios":
    st.title("📢 Análise de Anúncios")
    concs = st.session_state.dados["concorrentes"]
    if not concs:
        st.warning("Cadastre um concorrente primeiro.")
    else:
        for c in concs:
            col_a, col_b = st.columns([2, 1])
            col_a.write(f"**{c['nome']}**")
            search_term = c['ads_id'] if c['ads_id'] else c['nome']
            link = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={search_term}&country=BR"
            col_b.link_button("Ver Anúncios Ativos", link)

# 7. INSIGHTS
elif menu == "Insights":
    st.title("💡 Insights Estratégicos")
    if st.button("Gerar Relatório Final"):
        with st.spinner("A IA está cruzando todas as informações..."):
            contexto = f"""
            Minha Empresa: {st.session_state.dados['minha_empresa']}
            Concorrentes e análises: {st.session_state.dados['concorrentes']}
            """
            prompt = f"Com base nos dados acima, qual deve ser minha prioridade para superar esses concorrentes? Responda em tópicos. {contexto}"
            st.markdown(consultar_ia(prompt))
