import streamlit as st
import google.generativeai as genai
import pandas as pd

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------

st.set_page_config(
    page_title="IA Competitive Intelligence",
    layout="wide"
)

# ---------------------------------------------------
# CONFIGURAÇÃO GEMINI
# ---------------------------------------------------

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
else:
    model = None

# ---------------------------------------------------
# ESTADO DA SESSÃO
# ---------------------------------------------------

if "dados" not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "",
            "setor": "Marketing",
            "tipo": "",
            "instagram": "@",
            "fb_page": "",
            "servicos": []
        },
        "concorrentes": []
    }

if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

if "mostrar_form_concorrente" not in st.session_state:
    st.session_state.mostrar_form_concorrente = False

# ---------------------------------------------------
# FUNÇÃO IA
# ---------------------------------------------------

def consultar_ia(prompt):
    if model is None:
        return "Erro: Chave API não configurada."

    emp = st.session_state.dados["minha_empresa"]

    contexto = f"""
    Empresa: {emp['nome']}
    Setor: {emp['setor']}
    Instagram: {emp['instagram']}
    """

    resposta = model.generate_content(contexto + "\n" + prompt)
    return resposta.text

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Dashboard")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# ---------------------------------------------------
# CSS GLOBAL
# ---------------------------------------------------

st.markdown("""
<style>

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #1e2327 !important;
}

.sidebar-header {
    color: #afb1b3;
    font-size: 11px;
    font-weight: 700;
    padding: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* MENU */
[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    background: transparent !important;
    color: #eee !important;
    border: none !important;
    border-bottom: 1px solid #2c3338 !important;
    text-align: left !important;
    padding: 15px 20px !important;
    font-size: 15px !important;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #2c3338 !important;
}

/* BOTÃO ADICIONAR */
.add-button button {
    background: #2271b1 !important;
    border-radius: 10px !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    height: 45px !important;
}

/* CARD CONCORRENTE */
.card-concorrente {
    background: linear-gradient(180deg, #1f2937, #111827);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #2d3748;
    margin-bottom: 20px;
    transition: all 0.2s ease;
}

.card-concorrente:hover {
    border-color: #3b82f6;
    transform: translateY(-3px);
}

.nome-card {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 16px;
}

.info-card {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #cbd5e1;
    font-size: 14px;
    margin-bottom: 10px;
}

.info-icon {
    width: 20px;
    text-align: center;
}

.info-text {
    word-break: break-word;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# MENU LATERAL
# ---------------------------------------------------

with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)

    if st.button("🏠 Minha Empresa"):
        st.session_state.pagina = "home"

    if st.button("👥 Concorrentes"):
        st.session_state.pagina = "cad"

    st.markdown('<div class="sidebar-header">Análise</div>', unsafe_allow_html=True)

    if st.button("📊 Visão Geral"):
        st.session_state.pagina = "geral"

    if st.button("📢 Biblioteca de Ads"):
        st.session_state.pagina = "ads"

    if st.button("💡 IA Battle Cards"):
        st.session_state.pagina = "insights"

# ---------------------------------------------------
# HOME
# ---------------------------------------------------

if st.session_state.pagina == "home":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]

    col1, col2 = st.columns(2)
    emp["nome"] = col1.text_input("Nome da Empresa", emp["nome"])
    emp["setor"] = col1.selectbox("Setor", ["Marketing", "Tecnologia", "Varejo", "Saúde", "Educação"])
    emp["tipo"] = col2.text_input("Sub-nicho", emp["tipo"])

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    top1, top2 = st.columns([8, 2])
    with top1:
        st.title("👥 Concorrentes")

    with top2:
        st.markdown('<div class="add-button">', unsafe_allow_html=True)
        add = st.button("➕ Adicionar", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if add:
        st.session_state.mostrar_form_concorrente = True
        st.rerun()

    if st.session_state.mostrar_form_concorrente:
        with st.form("cad_concorrente", clear_on_submit=True):
            nome = st.text_input("Nome do Concorrente")
            url = st.text_input("Site")
            insta = st.text_input("Instagram", "@")
            salvar = st.form_submit_button("Salvar")

            if salvar and nome:
                st.session_state.dados["concorrentes"].append({
                    "nome": nome,
                    "url": url,
                    "instagram": insta,
                    "fb_page": ""
                })
                st.session_state.mostrar_form_concorrente = False
                st.rerun()

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:
        cols = st.columns(3)
        for i, c in enumerate(concorrentes):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card-concorrente">
                    <div class="nome-card">{c['nome']}</div>

                    <div class="info-card">
                        <span class="info-icon">🌐</span>
                        <span class="info-text">{c['url'] or 'Sem site'}</span>
                    </div>

                    <div class="info-card">
                        <span class="info-icon">📸</span>
                        <span class="info-text">{c['instagram'] or 'Sem Instagram'}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑️ Remover", key=f"rm_{i}", use_container_width=True):
                    st.session_state.dados["concorrentes"].pop(i)
                    st.rerun()
    else:
        st.info("Nenhum concorrente cadastrado.")

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------

elif st.session_state.pagina == "geral":
    st.title("📊 Visão Geral")
    if st.session_state.dados["concorrentes"]:
        st.dataframe(pd.DataFrame(st.session_state.dados["concorrentes"]))
    else:
        st.warning("Sem dados.")

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif st.session_state.pagina == "ads":
    st.title("📢 Biblioteca de Ads")
    for c in st.session_state.dados["concorrentes"]:
        url = f"https://www.facebook.com/ads/library/?q={c['nome']}&country=BR"
        st.link_button(f"Abrir Ads – {c['nome']}", url)

# ---------------------------------------------------
# IA BATTLE CARDS
# ---------------------------------------------------

elif st.session_state.pagina == "insights":
    st.title("💡 IA Battle Cards")
    concs = st.session_state.dados["concorrentes"]

    if concs:
        alvo = st.selectbox("Concorrente:", [c["nome"] for c in concs])
        if st.button("Gerar Estratégia", type="primary"):
            with st.spinner("Gerando estratégia..."):
                st.markdown(consultar_ia(f"Gere um battle card contra {alvo}"))
    else:
        st.info("Cadastre concorrentes primeiro.")
