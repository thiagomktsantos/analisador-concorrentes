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
    "Acre": ["Rio Branco", "Cruzeiro do Sul"],
    "Alagoas": ["Maceió", "Arapiraca"],
    "Amapá": ["Macapá", "Santana"],
    "Amazonas": ["Manaus", "Parintins"],
    "Bahia": ["Salvador", "Feira de Santana"],
    "Ceará": ["Fortaleza", "Juazeiro do Norte", "Sobral"],
    "Distrito Federal": ["Brasília"],
    "Espírito Santo": ["Vitória", "Vila Velha"],
    "Goiás": ["Goiânia", "Anápolis"],
    "Maranhão": ["São Luís", "Imperatriz"],
    "Mato Grosso": ["Cuiabá", "Rondonópolis"],
    "Mato Grosso do Sul": ["Campo Grande", "Dourados"],
    "Minas Gerais": ["Belo Horizonte", "Uberlândia"],
    "Pará": ["Belém", "Santarém"],
    "Paraíba": ["João Pessoa", "Campina Grande"],
    "Paraná": ["Curitiba", "Londrina"],
    "Pernambuco": ["Recife", "Caruaru"],
    "Piauí": ["Teresina", "Parnaíba"],
    "Rio de Janeiro": ["Rio de Janeiro", "Niterói"],
    "Rio Grande do Norte": ["Natal", "Mossoró"],
    "Rio Grande do Sul": ["Porto Alegre", "Caxias do Sul"],
    "Rondônia": ["Porto Velho", "Ji-Paraná"],
    "Roraima": ["Boa Vista"],
    "Santa Catarina": ["Florianópolis", "Joinville"],
    "São Paulo": ["São Paulo", "Campinas", "Santos"],
    "Sergipe": ["Aracaju"],
    "Tocantins": ["Palmas"]
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

empresa = st.session_state.dados["minha_empresa"]

campos_padrao = {
    "estado": "",
    "cidade": "",
    "instagram": "@",
    "fb_page": "",
    "site": "",
    "servicos": []
}

for campo, valor in campos_padrao.items():
    if campo not in empresa:
        empresa[campo] = valor

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

if "mostrar_alerta_saida" not in st.session_state:
    st.session_state.mostrar_alerta_saida = False

if "pagina_destino" not in st.session_state:
    st.session_state.pagina_destino = None

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def limpar_site(url):
    if not url:
        return ""

    url = url.strip().lower()

    url = re.sub(r"^https?:\/\/", "", url, flags=re.IGNORECASE)
    url = re.sub(r"^www\.", "", url, flags=re.IGNORECASE)

    url = remover_acentos(url)

    url = re.sub(r"[^a-z0-9\.\-]", "", url)

    return url

def gerar_avatar(nome):
    nome = nome.strip().upper()
    if not nome:
        return "?"

    partes = nome.split()

    if len(partes) == 1:
        return partes[0][0]

    return partes[0][0] + partes[1][0]

def obter_instagram_handle(valor):
    if not valor:
        return ""

    valor = re.sub(r"^https?:\/\/(www\.)?instagram\.com\/", "", valor, flags=re.IGNORECASE)
    return valor.strip("/")

def obter_facebook_handle(valor):
    if not valor:
        return ""

    valor = re.sub(r"^https?:\/\/(www\.)?facebook\.com\/", "", valor, flags=re.IGNORECASE)
    return valor.strip("/")

# ---------------------------------------------------
# CONTROLE NAVEGAÇÃO
# ---------------------------------------------------

def trocar_pagina(destino):

    editando = (
        st.session_state.mostrar_form_concorrente
        or st.session_state.editando_concorrente is not None
    )

    if (
        st.session_state.pagina == "cad"
        and destino != "cad"
        and editando
    ):
        st.session_state.mostrar_alerta_saida = True
        st.session_state.pagina_destino = destino
    else:
        st.session_state.pagina = destino
        st.session_state.mostrar_form_concorrente = False
        st.session_state.editando_concorrente = None
        st.session_state.editar_empresa = False

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

        resposta = model.generate_content(
            contexto + "\n" + prompt
        )

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
    border-radius: 0px !important;
    background-color: transparent !important;
    color: #eee !important;
    border: none !important;
    border-bottom: 1px solid #2c3338 !important;
    text-align: left !important;
    padding: 15px 20px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)

    if st.button("🏠 Minha Empresa"):
        trocar_pagina("home")

    if st.button("👥 Concorrentes"):
        trocar_pagina("cad")

# ---------------------------------------------------
# CONCORRENTES (CORRIGIDO AQUI)
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                avatar = gerar_avatar(c["nome"])

                html_card = f"""
                <div class="card-concorrente">
                    <div style="display:flex;align-items:center;gap:15px;margin-bottom:20px;">
                        <div class="avatar-concorrente">{avatar}</div>
                        <div><h3 style="margin:0;color:white;">{c['nome']}</h3></div>
                    </div>

                    <div class="info-concorrente">🌐 {c.get('url','')}</div>
                    <div class="info-concorrente">📸 {c.get('instagram','')}</div>
                    <div class="info-concorrente">📘 {c.get('fb_page','')}</div>
                </div>
                """

                st.markdown(html_card, unsafe_allow_html=True)

    else:
        st.info("Nenhum concorrente cadastrado.")
