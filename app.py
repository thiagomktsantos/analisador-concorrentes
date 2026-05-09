import streamlit as st
import google.generativeai as genai
import trafilatura
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro - IA Concorrentes", layout="wide")

# --- 2. CONFIGURAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

# --- 3. ESTADO DA SESSÃO (ESTRUTURA DE DADOS ATUALIZADA) ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "", 
            "setor": "", 
            "tipo": "", 
            "descricao": ""
        },
        "concorrentes": [], # Lista de dicts com novos campos sociais
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"

# --- 4. FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    if model is None:
        return "Erro: Chave API Gemini não configurada nos Secrets."
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"IA indisponível: {str(e)}"

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<style>button { width: 100%; }</style>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Administrador")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 6. CSS CUSTOMIZADO (MANTENDO O ESTILO SOLICITADO) ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1e2327 !important; }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding: 0px !important; gap: 0px !important; }
        [data-testid="stSidebar"] .element-container { width: 100% !important; margin: 0px !important; }

        .sidebar-header {
            color: #afb1b3 !important; font-size: 11px !important; font-weight: 700;
            padding: 40px 20px 20px 20px !important; text-transform: uppercase;
            letter-spacing: 1px; background-color: #1e2327 !important; margin: 0px !important; display: block !important;
        }

        div.stButton { width: 100% !important; margin: 0px !important; }
        div.stButton > button {
            width: 100% !important; height: 55px !important; border: none !important;
            border-radius: 0px !important; background-color: transparent !important;
            color: #eee !important; padding: 0px 20px !important; font-size: 15px !important;
            border-bottom: 1px solid #2c3338 !important; margin: 0px !important;
            display: flex !important; align-items: center !important; justify-content: flex-start !important;
        }

        div.stButton > button > div { justify-content: flex-start !important; text-align: left !important; width: 100% !important; }
        div.stButton > button:hover { background-color: #2c3338 !important; color: #72aee6 !important; }
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    paginas = {
        "🏠 Minha empresa": "minha_empresa",
        "👥 Análise de concorrentes": "concorrentes",
        "📊 Geral": "geral",
        "🌐 Análise de sites": "sites",
        "📱 Análise de redes sociais": "social",
        "📢 Análise de anúncios": "ads",
        "💡 Insights": "insights"
    }

    for label in paginas.keys():
        is_active = st.session_state.pagina == label
        if is_active:
             st.markdown(f"<style>#btn_{paginas[label]} {{ background-color: #2271b1 !important; color: white !important; }}</style>", unsafe_allow_html=True)

        if st.button(label, key=f"btn_{paginas[label]}"):
            st.session_state.pagina = label
            st.rerun()

    st.markdown("<div style='height: 50px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.logado = False
        st.rerun()

# --- 8. LÓGICA DAS PÁGINAS ---
pg = st.session_state.pagina

# 1. MINHA EMPRESA (CAMPOS ATUALIZADOS)
if pg == "🏠 Minha empresa":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.dados["minha_empresa"]["nome"] = st.text_input("Nome da sua Empresa", emp["nome"])
        st.session_state.dados["minha_empresa"]["setor"] = st.text_input("Setor (ex: Tecnologia, Varejo)", emp["setor"])
    with col2:
        st.session_state.dados["minha_empresa"]["tipo"] = st.text_input("Tipo de Empresa (ex: B2B, B2C, SaaS)", emp["tipo"])
    
    st.session_state.dados["minha_empresa"]["descricao"] = st.text_area("Descrição detalhada do seu produto/serviço", emp["descricao"])
    
    if st.button("Salvar Dados"):
        st.success("Dados da empresa salvos com sucesso!")

# 2. ANÁLISE DE CONCORRENTES (NOVOS CAMPOS SOCIAIS)
elif pg == "👥 Análise de concorrentes":
    st.title("👥 Cadastro de Concorrentes")
    
    with st.form("form_concorrente"):
        st.subheader("Dados Básicos")
        nome_c = st.text_input("Nome do Concorrente")
        url_c = st.text_input("URL do Site (ex: https://site.com)")
        
        st.subheader("Redes Sociais & Ads")
        col_s1, col_s2 = st.columns(2)
        insta_c = col_s1.text_input("Link do Instagram")
        face_c = col_s2.text_input("Link do Facebook")
        ads_c = st.text_input("ID ou Nome para Biblioteca de Anúncios")
        
        if st.form_submit_button("Adicionar Concorrente"):
            if nome_c and url_c:
                st.session_state.dados["concorrentes"].append({
                    "nome": nome_c, 
                    "url": url_c, 
                    "instagram": insta_c,
                    "facebook": face_c,
                    "ads_id": ads_c,
                    "analise_site": "", 
                    "social": ""
                })
                st.success(f"{nome_c} adicionado!")
            else: 
                st.error("Nome e URL são obrigatórios.")

    st.subheader("Lista de Concorrentes")
    for i, c in enumerate(st.session_state.dados["concorrentes"]):
        with st.expander(f"📌 {c['nome']}"):
            st.write(f"**Site:** {c['url']}")
            st.write(f"**Instagram:** {c['instagram'] if c['instagram'] else 'Não informado'}")
            st.write(f"**Facebook:** {c['facebook'] if c['facebook'] else 'Não informado'}")
            if st.button("Remover Concorrente", key=f"del_{i}"):
                st.session_state.dados["concorrentes"].pop(i)
                st.rerun()

# 3. GERAL
elif pg == "📊 Geral":
    st.title("📊 Painel Geral")
    concs = st.session_state.dados["concorrentes"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Concorrentes", len(concs))
    c2.metric("Sites Analisados", sum(1 for c in concs if c["analise_site"]))
    c3.metric("Posts Analisados", sum(1 for c in concs if c["social"]))
    
    if concs:
        df = pd.DataFrame(concs)[["nome", "url", "instagram", "facebook"]]
        st.dataframe(df, use_container_width=True)

# 4. ANÁLISE DE SITES
elif pg == "🌐 Análise de sites":
    st.title("🌐 Análise de Conteúdo de Sites")
    concs = st.session_state.dados["concorrentes"]
    if not concs: st.warning("Cadastre um concorrente primeiro.")
    else:
        selecionado = st.selectbox("Escolha um concorrente para analisar", [c["nome"] for c in concs])
        conc = next(item for item in concs if item["nome"] == selecionado)
        if st.button(f"Analisar estratégia de {selecionado}"):
            with st.spinner("IA lendo o site..."):
                texto = trafilatura.extract(trafilatura.fetch_url(conc["url"]))
                if texto:
                    res = consultar_ia(f"Analise a estratégia de vendas desse site: {texto[:3000]}")
                    conc["analise_site"] = res
                    st.markdown(res)
                else: st.error("Não foi possível acessar o conteúdo do site.")

# 5. ANÁLISE DE REDES SOCIAIS
elif pg == "📱 Análise de redes sociais":
    st.title("📱 Análise de Redes Sociais")
    concs = st.session_state.dados["concorrentes"]
    if not concs: st.warning("Cadastre um concorrente.")
    else:
        selecionado = st.selectbox("Selecione o concorrente", [c["nome"] for c in concs])
        conc_sel = next(item for item in concs if item["nome"] == selecionado)
        
        if conc_sel["instagram"]:
            st.info(f"Link do Instagram: {conc_sel['instagram']}")
        
        copy = st.text_area("Cole aqui a legenda (copy) de um post deste concorrente")
        if st.button("Analisar Copy"):
            with st.spinner("Analisando objetivo..."):
                res = consultar_ia(f"Qual o objetivo e os gatilhos dessa copy? {copy}")
                conc_sel["social"] = res
                st.markdown(res)

# 6. ANÁLISE DE ANÚNCIOS
elif pg == "📢 Análise de anúncios":
    st.title("📢 Análise de Anúncios (Facebook Ads)")
    concs = st.session_state.dados["concorrentes"]
    for c in concs:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.subheader(c['nome'])
            st.write(f"ID de busca: {c['ads_id'] if c['ads_id'] else c['nome']}")
        with col_b:
            term = c['ads_id'] if c['ads_id'] else c['nome']
            link = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={term}&country=BR"
            st.link_button("Ir para Biblioteca ↗", link)

# 7. INSIGHTS
elif pg == "💡 Insights":
    st.title("💡 Insights Estratégicos")
    if st.button("Gerar Plano de Ação Final"):
        with st.spinner("Cruzando todos os dados..."):
            ctx = f"""
            Minha Empresa: {st.session_state.dados['minha_empresa']}
            Setor: {st.session_state.dados['minha_empresa']['setor']}
            Tipo: {st.session_state.dados['minha_empresa']['tipo']}
            Concorrentes Cadastrados: {st.session_state.dados['concorrentes']}
            """
            prompt = f"Com base na minha empresa e nos links/análises dos concorrentes acima, me dê um plano de ação de 5 tópicos para superá-los: {ctx}"
            st.markdown(consultar_ia(prompt))
