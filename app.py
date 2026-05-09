import streamlit as st
import google.generativeai as genai
import trafilatura
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Pro - Inteligência de Mercado", layout="wide")

# --- 2. CONFIGURAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

# --- 3. ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "", "setor": "Marketing", "tipo": "Agência de Marketing", "servicos": [] 
        },
        "concorrentes": [], # Lista de dicionários
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"

# --- 4. FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    if model is None: return "Erro: Chave API Gemini não configurada."
    try: 
        return model.generate_content(prompt).text
    except Exception as e: 
        return f"IA indisponível: {str(e)}"

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Administrador")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 6. CSS CUSTOMIZADO (WP-STYLE) ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1e2327 !important; }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding: 0px !important; gap: 0px !important; }
        [data-testid="stSidebar"] .element-container { width: 100% !important; margin: 0px !important; }
        
        /* Cabeçalhos de Categoria no Menu */
        .sidebar-category {
            color: #72aee6 !important; font-size: 10px !important; font-weight: 800;
            padding: 25px 20px 5px 20px !important; text-transform: uppercase;
            letter-spacing: 1.5px; background-color: #1e2327 !important;
        }
        
        .sidebar-header-main {
            color: #afb1b3 !important; font-size: 11px !important; font-weight: 700;
            padding: 40px 20px 10px 20px !important; text-transform: uppercase;
            background-color: #1e2327 !important; display: block !important;
        }

        div.stButton { width: 100% !important; margin: 0px !important; }
        div.stButton > button {
            width: 100% !important; height: 50px !important; border: none !important;
            border-radius: 0px !important; background-color: transparent !important;
            color: #eee !important; padding: 0px 20px !important; font-size: 14px !important;
            border-bottom: 1px solid #2c3338 !important; margin: 0px !important;
            display: flex !important; align-items: center !important; justify-content: flex-start !important;
        }
        div.stButton > button > div { justify-content: flex-start !important; text-align: left !important; width: 100% !important; }
        div.stButton > button:hover { background-color: #2c3338 !important; color: #72aee6 !important; }
        [data-testid="stSidebarNav"] { display: none; }
        
        .service-tag {
            background-color: #2c3338; color: white; padding: 5px 12px;
            border-radius: 15px; display: inline-block; margin: 3px; border: 1px solid #444; font-size: 13px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ORGANIZADO ---
with st.sidebar:
    st.markdown('<div class="sidebar-header-main">Painel de Controle</div>', unsafe_allow_html=True)
    
    # SEÇÃO 1: DADOS PRINCIPAIS
    st.markdown('<div class="sidebar-category">Dados Principais</div>', unsafe_allow_html=True)
    menu_dados = {
        "🏠 Minha empresa": "minha_empresa",
        "👥 Cadastro de concorrentes": "cadastro_concorrentes"
    }
    
    # SEÇÃO 2: ANÁLISES E IA
    st.markdown('<div class="sidebar-category">Análises e IA</div>', unsafe_allow_html=True)
    menu_analise = {
        "🌐 Análise de sites": "analise_sites",
        "📱 Análise de redes sociais": "analise_social",
        "📢 Análise de anúncios": "analise_ads",
        "💡 Insights Comparativos": "insights"
    }

    # Renderização unificada dos botões
    for label, key in {**menu_dados, **menu_analise}.items():
        if st.session_state.pagina == label:
             st.markdown(f"<style>#btn_{key} {{ background-color: #2271b1 !important; color: white !important; }}</style>", unsafe_allow_html=True)
        if st.button(label, key=f"btn_{key}"):
            st.session_state.pagina = label
            st.rerun()

    st.markdown("<div style='height: 40px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair do Sistema", key="btn_logout"):
        st.session_state.logado = False
        st.rerun()

# --- 8. LÓGICA DAS PÁGINAS ---
pg = st.session_state.pagina
concorrentes_cadastrados = st.session_state.dados["concorrentes"]

# PAG: MINHA EMPRESA
if pg == "🏠 Minha empresa":
    st.title("🏢 Configuração: Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    
    col1, col2 = st.columns(2)
    st.session_state.dados["minha_empresa"]["nome"] = col1.text_input("Nome Comercial", emp.get("nome", ""))
    
    opcoes_setor = ["Marketing", "Tecnologia", "Varejo", "Saúde", "Outros"]
    setor_sel = col1.selectbox("Setor de Atuação", opcoes_setor, index=opcoes_setor.index(emp["setor"]) if emp["setor"] in opcoes_setor else 0)
    st.session_state.dados["minha_empresa"]["setor"] = setor_sel

    opcoes_tipo = ["Agência de Marketing", "SaaS", "E-commerce", "Consultoria", "Outros"] if setor_sel == "Marketing" else ["B2B", "B2C", "SaaS", "Varejo", "Outros"]
    st.session_state.dados["minha_empresa"]["tipo"] = col2.selectbox("Tipo de Modelo", opcoes_tipo)

    st.subheader("🛠️ Nossos Serviços/Produtos")
    col_add, col_btn = st.columns([4, 1])
    novo_servico = col_add.text_input("Novo serviço", key="in_serv")
    if col_btn.button("➕ Adicionar", key="add_serv"):
        if novo_servico and novo_servico not in emp["servicos"]:
            st.session_state.dados["minha_empresa"]["servicos"].append(novo_servico)
            st.rerun()

    for idx, serv in enumerate(emp["servicos"]):
        c_s, c_d = st.columns([9, 1])
        c_s.markdown(f"<div class='service-tag'>{serv}</div>", unsafe_allow_html=True)
        if c_d.button("🗑️", key=f"del_s_{idx}"):
            st.session_state.dados["minha_empresa"]["servicos"].pop(idx)
            st.rerun()

# PAG: CADASTRO DE CONCORRENTES
elif pg == "👥 Cadastro de concorrentes":
    st.title("👥 Gestão de Concorrentes")
    with st.form("add_concorrente"):
        st.subheader("Novo Cadastro")
        n = st.text_input("Nome da Empresa")
        u = st.text_input("URL do Site")
        col_s1, col_s2 = st.columns(2)
        i = col_s1.text_input("Instagram (Link)")
        f = col_s2.text_input("Facebook (Link)")
        a = st.text_input("ID/Termo para Biblioteca de Anúncios")
        if st.form_submit_button("💾 Salvar Concorrente"):
            if n and u:
                st.session_state.dados["concorrentes"].append({
                    "nome": n, "url": u, "instagram": i, "facebook": f, "ads_id": a,
                    "analise_site": "", "social_copy": ""
                })
                st.success("Cadastrado!")
                st.rerun()
    
    st.write("---")
    st.subheader("Concorrentes Monitorados")
    if not concorrentes_cadastrados: st.info("Nenhum concorrente cadastrado.")
    for idx, c in enumerate(concorrentes_cadastrados):
        with st.expander(f"🏢 {c['nome']}"):
            st.write(f"**URL:** {c['url']}")
            st.write(f"**Redes:** [IG]({c['instagram']}) | [FB]({c['facebook']})")
            if st.button(f"Excluir {c['nome']}", key=f"rm_{idx}"):
                st.session_state.dados["concorrentes"].pop(idx)
                st.rerun()

# PAG: ANÁLISE DE SITES
elif pg == "🌐 Análise de sites":
    st.title("🌐 Inteligência de Site")
    if not concorrentes_cadastrados: st.warning("Cadastre concorrentes primeiro.")
    else:
        sel = st.selectbox("Selecione o concorrente para analisar o site:", [c["nome"] for c in concorrentes_cadastrados])
        conc_data = next(c for c in concorrentes_cadastrados if c["nome"] == sel)
        
        if st.button(f"Analisar estratégia de {sel}"):
            with st.spinner("IA extraindo e analisando conteúdo..."):
                txt = trafilatura.extract(trafilatura.fetch_url(conc_data["url"]))
                if txt:
                    prompt = f"Com base no conteúdo do site: {txt[:3000]}, identifique a proposta de valor e 3 argumentos de venda."
                    res = consultar_ia(prompt)
                    conc_data["analise_site"] = res
                    st.markdown(res)
                else: st.error("Não foi possível ler o site.")

# PAG: ANÁLISE SOCIAL
elif pg == "📱 Análise de redes sociais":
    st.title("📱 Análise de Copy Social")
    if not concorrentes_cadastrados: st.warning("Cadastre concorrentes primeiro.")
    else:
        sel = st.selectbox("De qual concorrente é esta publicação?", [c["nome"] for c in concorrentes_cadastrados])
        conc_data = next(c for c in concorrentes_cadastrados if c["nome"] == sel)
        copy = st.text_area("Cole a legenda (copy) do post aqui:")
        if st.button("Analisar Funil da Copy"):
            with st.spinner("Analisando..."):
                res = consultar_ia(f"Analise o funil e os gatilhos desta copy de {sel}: {copy}")
                conc_data["social_copy"] = res
                st.markdown(res)

# PAG: ANÁLISE DE ANÚNCIOS
elif pg == "📢 Análise de anúncios":
    st.title("📢 Radar de Anúncios (Ads)")
    if not concorrentes_cadastrados: st.warning("Cadastre concorrentes primeiro.")
    else:
        for c in concorrentes_cadastrados:
            col_a, col_b = st.columns([3, 1])
            col_a.subheader(c['nome'])
            term = c['ads_id'] if c['ads_id'] else c['nome']
            link = f"https://www.facebook.com/ads/library/?q={term}&country=BR"
            col_b.link_button("Ver na Biblioteca ↗", link)

# PAG: INSIGHTS COMPARATIVOS
elif pg == "💡 Insights Comparativos":
    st.title("💡 Insights e Correlação")
    if not concorrentes_cadastrados: st.warning("Dados insuficientes.")
    else:
        if st.button("🚀 Gerar Relatório Comparativo IA"):
            with st.spinner("Cruzando seus dados com os concorrentes..."):
                ctx = f"""
                MINHA EMPRESA: {st.session_state.dados['minha_empresa']}
                CONCORRENTES CADASTRADOS: {st.session_state.dados['concorrentes']}
                """
                prompt = f"Como minha empresa pode se diferenciar oferecendo os serviços {st.session_state.dados['minha_empresa']['servicos']} diante da estratégia desses concorrentes? Responda em tópicos práticos."
                st.markdown(consultar_ia(prompt))
