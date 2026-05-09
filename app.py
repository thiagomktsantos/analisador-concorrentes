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

# --- 3. ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "", 
            "setor": "Marketing", 
            "tipo": "Agência de Marketing", 
            "servicos": [] 
        },
        "concorrentes": [],
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

if 'pagina' not in st.session_state:
    st.session_state.pagina = "🏠 Minha empresa"

# --- 4. FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    if model is None: return "Erro: Chave API Gemini não configurada."
    try: return model.generate_content(prompt).text
    except Exception as e: return f"IA indisponível: {str(e)}"

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
        
        .service-tag {
            background-color: #2c3338; color: white; padding: 5px 15px;
            border-radius: 20px; display: inline-block; margin: 5px; border: 1px solid #444;
        }
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
    for label, key in paginas.items():
        if st.session_state.pagina == label:
             st.markdown(f"<style>#btn_{key} {{ background-color: #2271b1 !important; color: white !important; }}</style>", unsafe_allow_html=True)
        if st.button(label, key=f"btn_{key}"):
            st.session_state.pagina = label
            st.rerun()

    st.markdown("<div style='height: 50px; border-bottom: 1px solid #2c3338;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.logado = False
        st.rerun()

# --- 8. LÓGICA DAS PÁGINAS ---
pg = st.session_state.pagina

if pg == "🏠 Minha empresa":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    
    col1, col2 = st.columns(2)
    st.session_state.dados["minha_empresa"]["nome"] = col1.text_input("Nome da sua Empresa", emp.get("nome", ""))
    
    # 1. SELEÇÃO DE SETOR
    opcoes_setor = ["Marketing", "Tecnologia", "Varejo", "Saúde", "Educação", "Financeiro", "Alimentação", "Indústria", "Outros"]
    current_setor = emp.get("setor", "Marketing")
    idx_setor = opcoes_setor.index(current_setor) if current_setor in opcoes_setor else 0
    setor_sel = col1.selectbox("Setor", opcoes_setor, index=idx_setor)
    st.session_state.dados["minha_empresa"]["setor"] = setor_sel

    # 2. SELEÇÃO DE TIPO DINÂMICO
    if setor_sel == "Marketing":
        opcoes_tipo = ["Agência de Marketing", "Consultoria", "Infoprodutos", "B2B", "B2C", "Outros"]
    else:
        opcoes_tipo = ["Agência", "SaaS / Software", "E-commerce", "Consultoria", "B2B", "B2C", "Outros"]
    
    current_tipo = emp.get("tipo", "")
    idx_tipo = opcoes_tipo.index(current_tipo) if current_tipo in opcoes_tipo else 0
    st.session_state.dados["minha_empresa"]["tipo"] = col2.selectbox("Tipo de Empresa", opcoes_tipo, index=idx_tipo)

    # 3. GERENCIADOR DE SERVIÇOS
    st.write("---")
    st.subheader("🛠️ Nossos Serviços")
    
    col_add, col_btn = st.columns([4, 1])
    novo_servico = col_add.text_input("Adicionar novo serviço", key="input_servico")
    if col_btn.button("➕ Adicionar", use_container_width=True):
        if novo_servico and novo_servico not in emp["servicos"]:
            st.session_state.dados["minha_empresa"]["servicos"].append(novo_servico)
            st.rerun()

    if emp["servicos"]:
        for idx, serv in enumerate(emp["servicos"]):
            c_serv, c_del = st.columns([8, 1])
            c_serv.markdown(f"<div class='service-tag'>{serv}</div>", unsafe_allow_html=True)
            if c_del.button("🗑️", key=f"del_serv_{idx}"):
                st.session_state.dados["minha_empresa"]["servicos"].pop(idx)
                st.rerun()

    st.write("---")
    if st.button("💾 Salvar Alterações"):
        st.success("Dados salvos com sucesso!")

elif pg == "👥 Análise de concorrentes":
    st.title("👥 Cadastro de Concorrentes")
    with st.form("form_c"):
        n = st.text_input("Nome")
        u = st.text_input("URL Site")
        i = st.text_input("Instagram")
        f = st.text_input("Facebook")
        a = st.text_input("ID Ads")
        if st.form_submit_button("Adicionar"):
            st.session_state.dados["concorrentes"].append({
                "nome": n, "url": u, "instagram": i, "facebook": f, "ads_id": a,
                "analise_site": "", "social": ""
            })
            st.rerun()
    for idx, c in enumerate(st.session_state.dados["concorrentes"]):
        with st.expander(f"📌 {c['nome']}"):
            st.write(f"IG: {c['instagram']} | FB: {c['facebook']}")
            if st.button("Remover", key=f"rm_{idx}"):
                st.session_state.dados["concorrentes"].pop(idx)
                st.rerun()

elif pg == "📊 Geral":
    st.title("📊 Geral")
    if st.session_state.dados["concorrentes"]:
        st.table(pd.DataFrame(st.session_state.dados["concorrentes"])[["nome", "url", "instagram", "facebook"]])

elif pg == "🌐 Análise de sites":
    st.title("🌐 Análise de Sites")
    concs = st.session_state.dados["concorrentes"]
    if concs:
        sel = st.selectbox("Concorrente", [c["nome"] for c in concs])
        c_obj = next(item for item in concs if item["nome"] == sel)
        if st.button("Analisar"):
            with st.spinner("IA lendo..."):
                txt = trafilatura.extract(trafilatura.fetch_url(c_obj["url"]))
                res = consultar_ia(f"Analise: {txt[:2000]}") if txt else "Erro ao ler site."
                c_obj["analise_site"] = res
                st.markdown(res)

elif pg == "📱 Análise de redes sociais":
    st.title("📱 Redes Sociais")
    copy = st.text_area("Cole a copy aqui")
    if st.button("Analisar"):
        st.markdown(consultar_ia(f"Analise esta copy: {copy}"))

elif pg == "📢 Análise de anúncios":
    st.title("📢 Ads")
    for c in st.session_state.dados["concorrentes"]:
        st.link_button(f"Anúncios de {c['nome']}", f"https://www.facebook.com/ads/library/?q={c['ads_id'] or c['nome']}&country=BR")

elif pg == "💡 Insights":
    st.title("💡 Insights")
    if st.button("Gerar Plano"):
        st.markdown(consultar_ia(f"Gere um plano estratégico para superar os concorrentes {st.session_state.dados['concorrentes']} com base na minha empresa {st.session_state.dados['minha_empresa']}"))
