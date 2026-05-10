import streamlit as st
import google.generativeai as genai
import pandas as pd
import trafilatura
import streamlit.components.v1 as components

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
[data-testid="stSidebar"] {
    background-color: #1e2327;
}
.sidebar-header {
    color: #afb1b3;
    font-size: 11px;
    font-weight: 700;
    padding: 20px;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# MENU LATERAL
# ---------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados</div>', unsafe_allow_html=True)
    if st.button("🏠 Minha Empresa"): st.session_state.pagina = "home"
    if st.button("👥 Concorrentes"): st.session_state.pagina = "cad"

    st.markdown('<div class="sidebar-header">Análise</div>', unsafe_allow_html=True)
    if st.button("📊 Visão Geral"): st.session_state.pagina = "geral"
    if st.button("📢 Biblioteca de Ads"): st.session_state.pagina = "ads"
    if st.button("💡 IA Battle Cards"): st.session_state.pagina = "insights"

# ---------------------------------------------------
# HOME
# ---------------------------------------------------
if st.session_state.pagina == "home":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    emp["nome"] = st.text_input("Nome", emp["nome"])
    emp["instagram"] = st.text_input("Instagram", emp["instagram"])

# ---------------------------------------------------
# CONCORRENTES (CARD CORRIGIDO AQUI)
# ---------------------------------------------------
elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    if st.button("➕ Adicionar"):
        st.session_state.mostrar_form_concorrente = True

    if st.session_state.mostrar_form_concorrente:
        with st.form("cad_conc"):
            nome = st.text_input("Nome")
            site = st.text_input("Site")
            insta = st.text_input("Instagram")
            fb = st.text_input("Facebook")
            salvar = st.form_submit_button("Salvar")

            if salvar and nome:
                st.session_state.dados["concorrentes"].append({
                    "nome": nome,
                    "url": site,
                    "instagram": insta,
                    "fb_page": fb
                })
                st.session_state.mostrar_form_concorrente = False
                st.rerun()

    # ---- CARDS VISUAIS (HTML REAL) ----
    for c in st.session_state.dados["concorrentes"]:
        components.html(f"""
        <style>
        .card {{
            background: linear-gradient(180deg,#1f2937,#111827);
            padding: 24px;
            border-radius: 18px;
            color: #fff;
            margin-bottom: 16px;
            border: 1px solid #2d3748;
        }}
        .nome {{ font-size:22px;font-weight:700;margin-bottom:14px }}
        .info {{ font-size:15px;color:#e5e7eb;margin-bottom:8px }}
        </style>

        <div class="card">
            <div class="nome">{c['nome']}</div>
            <div class="info">🌐 {c['url'] or 'Sem site'}</div>
            <div class="info">📸 {c['instagram'] or 'Sem Instagram'}</div>
            <div class="info">👍 {c['fb_page'] or 'Sem Facebook'}</div>
        </div>
        """, height=230)

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------
elif st.session_state.pagina == "geral":
    st.title("📊 Visão Geral")
    df = pd.DataFrame(st.session_state.dados["concorrentes"])
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# ADS
# ---------------------------------------------------
elif st.session_state.pagina == "ads":
    st.title("📢 Biblioteca de Ads")
    for c in st.session_state.dados["concorrentes"]:
        st.link_button(
            f"Abrir Ads – {c['nome']}",
            f"https://www.facebook.com/ads/library/?q={c['nome']}&country=BR"
        )

# ---------------------------------------------------
# IA
# ---------------------------------------------------
elif st.session_state.pagina == "insights":
    st.title("💡 IA Battle Cards")
    nomes = [c["nome"] for c in st.session_state.dados["concorrentes"]]
    if nomes:
        alvo = st.selectbox("Concorrente", nomes)
        if st.button("Gerar"):
            st.markdown(consultar_ia(f"Gere um battle card contra {alvo}"))
