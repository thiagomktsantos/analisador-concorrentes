import streamlit as st
import google.generativeai as genai
import trafilatura
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro - IA Concorrentes", layout="wide")

# --- 2. CONFIGURAÇÃO DA IA ---
# Certifique-se de ter GEMINI_API_KEY nos seus Secrets ou substitua por string para teste local
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    # Apenas para não quebrar o código se não houver chave
    model = None

# --- 3. ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {"nome": "", "setor": "", "descricao": ""},
        "concorrentes": [],
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
    # Aplicando fundo escuro na tela de login também
    st.markdown("<style>button { width: 100%; }</style>", unsafe_allow_html=True)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Administrador")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar Painel"):
            # Lógica simples de acesso (substituir por real se necessário)
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 6. CSS CUSTOMIZADO (WP-STYLE) ---
st.markdown("""
    <style>
        /* 1. Fundo da lateral */
        [data-testid="stSidebar"] {
            background-color: #1e2327 !important;
        }

        /* 2. ZERAR PADDINGS E GAPS DO CONTAINER */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 0px !important;
            gap: 0px !important;
        }
        
        [data-testid="stSidebar"] .element-container {
            width: 100% !important;
            margin: 0px !important;
        }

        /* 3. TÍTULO (Cabeçalho) */
        .sidebar-header {
            color: #afb1b3 !important;
            font-size: 11px !important;
            font-weight: 700;
            padding: 40px 20px 20px 20px !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #1e2327 !important;
            margin: 0px !important;
            display: block !important;
        }

        /* 4. BOTÕES: Altura Fixa de 55px para simetria total */
        div.stButton {
            width: 100% !important;
            margin: 0px !important;
        }

        div.stButton > button {
            width: 100% !important;
            height: 55px !important; 
            border: none !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            color: #eee !important;
            padding: 0px 20px !important; 
            font-size: 15px !important;
            border-bottom: 1px solid #2c3338 !important;
            margin: 0px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
        }

        /* Conteúdo interno do botão alinhado à esquerda */
        div.stButton > button > div {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
        }

        /* 5. HOVER E ESTADO ATIVO */
        div.stButton > button:hover {
            background-color: #2c3338 !important;
            color: #72aee6 !important;
        }

        /* Ocultar elementos nativos */
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Painel de Controle</div>', unsafe_allow_html=True)
    
    # Mapeamento de nomes para os botões com ícones
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
        # Lógica de cor ativa: Se a página atual for essa, mudamos o estilo via CSS injetado
        is_active = st.session_state.pagina == label
        cor_botao = "background-color: #2271b1 !important; color: white !important;" if is_active else ""
        
        # Injeção de estilo temporária para o botão ativo específico
        if is_active:
             st.markdown(f"<style>#btn_{paginas[label]} {{ {cor_botao} }}</style>", unsafe_allow_html=True)

        if st.button(label, key=f"btn_{paginas[label]}"):
            st.session_state.pagina = label
            st.rerun()

    # Espaçador e Botão Sair
    st.markdown("<div style='height: 50px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.logado = False
        st.rerun()

# --- 8. LÓGICA DAS PÁGINAS (CONTEÚDO PRINCIPAL) ---
pg = st.session_state.pagina

# 1. MINHA EMPRESA
if pg == "🏠 Minha empresa":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    st.session_state.dados["minha_empresa"]["nome"] = st.text_input("Nome da sua Empresa", emp["nome"])
    st.session_state.dados["minha_empresa"]["setor"] = st.text_input("Setor/Nicho", emp["setor"])
    st.session_state.dados["minha_empresa"]["descricao"] = st.text_area("Descrição do seu produto/serviço", emp["descricao"])
    if st.button("Salvar Dados"):
        st.success("Dados da empresa salvos!")

# 2. ANÁLISE DE CONCORRENTES
elif pg == "👥 Análise de concorrentes":
    st.title("👥 Cadastro de Concorrentes")
    with st.form("form_concorrente"):
        nome_c = st.text_input("Nome do Concorrente")
        url_c = st.text_input("URL do Site")
        ads_c = st.text_input("ID/Nome Biblioteca de Anúncios")
        if st.form_submit_button("Adicionar Concorrente"):
            if nome_c and url_c:
                st.session_state.dados["concorrentes"].append({
                    "nome": nome_c, "url": url_c, "ads_id": ads_c,
                    "analise_site": "", "social": ""
                })
                st.success(f"{nome_c} adicionado!")
            else: st.error("Nome e URL são obrigatórios.")

    st.subheader("Lista de Concorrentes")
    for i, c in enumerate(st.session_state.dados["concorrentes"]):
        col_c1, col_c2 = st.columns([4, 1])
        col_c1.write(f"**{c['nome']}** - {c['url']}")
        if col_c2.button("Remover", key=f"del_{i}"):
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
        st.table(pd.DataFrame(concs)[["nome", "url", "ads_id"]])

# 4. ANÁLISE DE SITES
elif pg == "🌐 Análise de sites":
    st.title("🌐 Análise de Sites")
    concs = st.session_state.dados["concorrentes"]
    if not concs: st.warning("Cadastre um concorrente.")
    else:
        selecionado = st.selectbox("Escolha um concorrente", [c["nome"] for c in concs])
        conc = next(item for item in concs if item["nome"] == selecionado)
        if st.button(f"Analisar site de {selecionado}"):
            with st.spinner("Extraindo dados..."):
                texto = trafilatura.extract(trafilatura.fetch_url(conc["url"]))
                if texto:
                    res = consultar_ia(f"Analise a estratégia de vendas: {texto[:3000]}")
                    conc["analise_site"] = res
                    st.markdown(res)
                else: st.error("Não foi possível acessar o site.")

# 5. ANÁLISE DE REDES SOCIAIS
elif pg == "📱 Análise de redes sociais":
    st.title("📱 Análise de Redes Sociais")
    concs = st.session_state.dados["concorrentes"]
    if not concs: st.warning("Cadastre um concorrente.")
    else:
        selecionado = st.selectbox("Selecione o concorrente", [c["nome"] for c in concs])
        copy = st.text_area("Cole a legenda do post aqui")
        if st.button("Analisar Engajamento"):
            with st.spinner("Analisando..."):
                res = consultar_ia(f"Analise o objetivo desta copy (venda/autoridade): {copy}")
                next(item for item in concs if item["nome"] == selecionado)["social"] = res
                st.markdown(res)

# 6. ANÁLISE DE ANÚNCIOS
elif pg == "📢 Análise de anúncios":
    st.title("📢 Análise de Anúncios")
    concs = st.session_state.dados["concorrentes"]
    for c in concs:
        col_a, col_b = st.columns([3, 1])
        col_a.subheader(c['nome'])
        term = c['ads_id'] if c['ads_id'] else c['nome']
        link = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={term}&country=BR"
        col_b.link_button("Ver Anúncios", link)

# 7. INSIGHTS
elif pg == "💡 Insights":
    st.title("💡 Insights Estratégicos")
    if st.button("Gerar Relatório com IA"):
        with st.spinner("Processando..."):
            ctx = f"Minha: {st.session_state.dados['minha_empresa']}. Concorrentes: {st.session_state.dados['concorrentes']}"
            st.markdown(consultar_ia(f"Com base nesses dados, qual a melhor estratégia para eu me destacar? {ctx}"))
