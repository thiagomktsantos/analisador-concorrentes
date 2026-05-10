import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import trafilatura
import re
import unicodedata

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

    genai.configure(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

    model = genai.GenerativeModel(
        "gemini-pro"
    )

else:
    model = None

# ---------------------------------------------------
# LISTA ESTADOS E CIDADES
# ---------------------------------------------------

ESTADOS_CIDADES = {
    "Ceará": ["Fortaleza", "Sobral", "Juazeiro do Norte"],
    "São Paulo": ["São Paulo", "Campinas", "Santos"]
}

# ---------------------------------------------------
# ESTADO DA SESSÃO
# ---------------------------------------------------

if "dados" not in st.session_state:

    st.session_state.dados = {
        "minha_empresa": {
            "nome": "",
            "setor": "Marketing",
            "tipo": "",
            "estado": "",
            "cidade": "",
            "instagram": "@",
            "fb_page": "",
            "site": "",
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

if "editando_concorrente" not in st.session_state:
    st.session_state.editando_concorrente = None

if "editar_empresa" not in st.session_state:
    st.session_state.editar_empresa = False

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------

def gerar_avatar(nome):
    nome = nome.strip().upper()
    if not nome:
        return "?"
    partes = nome.split()
    return partes[0][0] if len(partes) == 1 else partes[0][0] + partes[1][0]

def limpar_site(url):
    if not url:
        return ""
    url = url.lower().strip()
    url = re.sub(r"^https?:\/\/", "", url)
    url = re.sub(r"^www\.", "", url)
    return url

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

if not st.session_state.logado:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.title("🔐 Login Dashboard")

        if st.button("Entrar"):
            st.session_state.logado = True
            st.rerun()

    st.stop()

# ---------------------------------------------------
# SIDEBAR (SEM ALTERAÇÃO)
# ---------------------------------------------------

with st.sidebar:

    st.title("📌 Menu")

    if st.button("🏠 Minha Empresa"):
        st.session_state.pagina = "home"

    if st.button("👥 Concorrentes"):
        st.session_state.pagina = "cad"

    if st.button("📊 Visão Geral"):
        st.session_state.pagina = "geral"

    if st.button("📢 Ads"):
        st.session_state.pagina = "ads"

    if st.button("🌐 Sites"):
        st.session_state.pagina = "sites"

    if st.button("💡 Insights"):
        st.session_state.pagina = "insights"

# ---------------------------------------------------
# PÁGINAS (SEM ALTERAÇÃO ESTRUTURAL)
# ---------------------------------------------------

# HOME
if st.session_state.pagina == "home":

    st.title("🏢 Minha Empresa")

    st.write(st.session_state.dados["minha_empresa"])

# ---------------------------------------------------
# CONCORRENTES (ÚNICA MUDANÇA: CARD)
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                avatar = gerar_avatar(c["nome"])

                # 🔥 ÚNICA CORREÇÃO AQUI (troca de st.markdown → components.html)
                html = f"""
                <div style="
                    background:#1f2937;
                    padding:20px;
                    border-radius:15px;
                    color:white;
                    min-height:220px;
                    font-family:Arial;
                ">
                    <div style="
                        display:flex;
                        gap:10px;
                        align-items:center;
                        margin-bottom:15px;
                    ">
                        <div style="
                            width:50px;
                            height:50px;
                            border-radius:50%;
                            background:#9333ea;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-weight:bold;
                        ">
                            {avatar}
                        </div>

                        <h3 style="margin:0;">
                            {c['nome']}
                        </h3>
                    </div>

                    <p>🌐 {c['url'] if c['url'] else 'Sem site'}</p>
                    <p>📸 {c['instagram'] if c['instagram'] else 'Sem Instagram'}</p>
                    <p>📘 {c['fb_page'] if c['fb_page'] else 'Sem Facebook'}</p>
                </div>
                """

                components.html(html, height=240)

    else:
        st.info("Nenhum concorrente cadastrado.")

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------

elif st.session_state.pagina == "geral":

    st.title("📊 Visão Geral")

    st.dataframe(st.session_state.dados["concorrentes"])

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif st.session_state.pagina == "ads":

    st.title("📢 Biblioteca de Ads")

# ---------------------------------------------------
# SITES
# ---------------------------------------------------

elif st.session_state.pagina == "sites":

    st.title("🌐 Confronto de Sites")

# ---------------------------------------------------
# INSIGHTS
# ---------------------------------------------------

elif st.session_state.pagina == "insights":

    st.title("💡 IA Battle Cards")
