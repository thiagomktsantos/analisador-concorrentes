import streamlit as st
import google.generativeai as genai
import pandas as pd
import trafilatura
import streamlit.components.v1 as components  # <<< ÚNICA ADIÇÃO

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

    try:
        emp = st.session_state.dados["minha_empresa"]

        contexto = f"""
Empresa: {emp['nome']}
Setor: {emp['setor']}
Instagram: {emp['instagram']}
"""

        resposta = model.generate_content(contexto + "\n" + prompt)
        return resposta.text

    except Exception as e:
        return f"Erro: {str(e)}"

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
[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    background-color: transparent !important;
    color: #eee !important;
    border: none !important;
    border-bottom: 1px solid #2c3338 !important;
    text-align: left !important;
    padding: 15px 20px !important;
}
.add-button button {
    background: #2271b1 !important;
    border-radius: 10px !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    height: 45px !important;
}
.card-concorrente {
    background: #1f2937;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #2d3748;
    margin-bottom: 15px;
}
.nome-card {
    font-size: 22px;
    font-weight: 700;
    color: white;
    margin-bottom: 15px;
}
.info-card {
    color: #cbd5e1;
    margin-bottom: 10px;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# MENU LATERAL
# ---------------------------------------------------

with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)
    if st.button("🏠 Minha Empresa"): st.session_state.pagina = "home"
    if st.button("👥 Concorrentes"): st.session_state.pagina = "cad"

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                # 🔥 CORREÇÃO DEFINITIVA DO CARD
                components.html(
f"""
<div class="card-concorrente">
  <div class="nome-card">{c['nome']}</div>
  <div class="info-card">🌐 {c['url'] or 'Sem site'}</div>
  <div class="info-card">📸 {c['instagram'] or 'Sem Instagram'}</div>
  <div class="info-card">👍 {c['fb_page'] or 'Sem Facebook'}</div>
</div>
""",
height=220
                )

                if st.button("🗑️ Remover", key=f"remove_{i}", use_container_width=True):
                    st.session_state.dados["concorrentes"].pop(i)
                    st.rerun()

    else:
        st.info("Nenhum concorrente cadastrado.")
