import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import unicodedata

# ---------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------

st.set_page_config(
    page_title="IA Competitive Intelligence",
    layout="wide"
)

# ---------------------------------------------------
# GEMINI
# ---------------------------------------------------

if "GEMINI_API_KEY" in st.secrets:

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")

else:
    model = None

# ---------------------------------------------------
# DADOS
# ---------------------------------------------------

ESTADOS_CIDADES = {
    "São Paulo": ["São Paulo", "Campinas", "Santos"],
    "Rio de Janeiro": ["Rio de Janeiro", "Niterói"],
    "Minas Gerais": ["Belo Horizonte", "Uberlândia"]
}

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

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

if "logado" not in st.session_state:
    st.session_state.logado = True

if "editar_empresa" not in st.session_state:
    st.session_state.editar_empresa = False

# ---------------------------------------------------
# FUNÇÕES
# ---------------------------------------------------

def limpar_site(url):
    if not url:
        return ""
    url = url.lower()
    url = re.sub(r"https?://", "", url)
    url = re.sub(r"www\.", "", url)
    return url.strip()

def avatar(nome):
    if not nome:
        return "?"
    p = nome.split()
    return (p[0][0] + (p[1][0] if len(p) > 1 else "")).upper()

# ---------------------------------------------------
# CSS (MENU LIMPO)
# ---------------------------------------------------

st.markdown("""
<style>

[data-testid="stSidebar"] {
    background: #111827;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: transparent;
    border: none;
    color: #d1d5db;
    text-align: left;
    padding: 12px;
    font-size: 15px;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #1f2937;
    color: white;
    border-radius: 10px;
}

/* CARD LIMPO SEM ESCAPE HTML */

.card {
    background: white;
    border-radius: 18px;
    padding: 20px;
    border: 1px solid #e5e7eb;
    margin-bottom: 15px;
}

.badge {
    background: #2563eb;
    color: white;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# MENU
# ---------------------------------------------------

with st.sidebar:

    st.title("Menu")

    if st.button("🏠 Minha Empresa"):
        st.session_state.pagina = "home"

    if st.button("👥 Concorrentes"):
        st.session_state.pagina = "cad"

    if st.button("📊 Visão Geral"):
        st.session_state.pagina = "geral"

    if st.button("🌐 Confronto de Sites"):
        st.session_state.pagina = "sites"

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

    emp["nome"] = st.text_input("Nome", emp["nome"])
    emp["instagram"] = st.text_input("Instagram", emp["instagram"])
    emp["site"] = st.text_input("Site", emp["site"])

# ---------------------------------------------------
# CONCORRENTES (CORRIGIDO SEM HTML QUEBRA)
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    nome = st.text_input("Nome concorrente")
    site = st.text_input("Site")

    if st.button("Adicionar"):

        st.session_state.dados["concorrentes"].append({
            "nome": nome,
            "url": limpar_site(site),
            "instagram": "",
            "fb_page": ""
        })

        st.rerun()

    st.divider()

    concorrentes = st.session_state.dados["concorrentes"]

    if not concorrentes:
        st.info("Nenhum concorrente cadastrado.")

    else:

        cols = st.columns(2)

        for i, c in enumerate(concorrentes):

            with cols[i % 2]:

                # CARD NATIVO (SEM HTML)
                with st.container():

                    st.markdown("### " + c["nome"])
                    st.write("🌐", c["url"] or "Sem site")
                    st.write("📸", c["instagram"] or "Sem Instagram")
                    st.write("📘", c["fb_page"] or "Sem Facebook")

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("Editar", key=f"edit_{i}"):
                            st.session_state.editando_concorrente = i

                    with c2:
                        if st.button("Remover", key=f"del_{i}"):
                            st.session_state.dados["concorrentes"].pop(i)
                            st.rerun()

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------

elif st.session_state.pagina == "geral":

    st.title("📊 Visão Geral")

    df = pd.DataFrame(st.session_state.dados["concorrentes"])

    st.dataframe(df)

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif st.session_state.pagina == "ads":

    st.title("📢 Biblioteca de Ads")

    for c in st.session_state.dados["concorrentes"]:

        with st.expander(c["nome"]):

            st.write("Busca:", c["nome"])

            st.link_button(
                "Abrir Ads Library",
                "https://www.facebook.com/ads/library/"
            )

# ---------------------------------------------------
# SITES
# ---------------------------------------------------

elif st.session_state.pagina == "sites":

    st.title("🌐 Confronto de Sites")

    st.info("Em desenvolvimento")

# ---------------------------------------------------
# INSIGHTS
# ---------------------------------------------------

elif st.session_state.pagina == "insights":

    st.title("💡 IA Battle Cards")

    concs = st.session_state.dados["concorrentes"]

    if concs:

        alvo = st.selectbox("Concorrente", [c["nome"] for c in concs])

        if st.button("Gerar"):

            st.success(f"Estratégia gerada contra {alvo}")

    else:
        st.info("Adicione concorrentes.")
