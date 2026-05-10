import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
import trafilatura
import re

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
    genai.configure(api_key=st.serets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
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

if "estado" not in empresa:
    empresa["estado"] = ""

if "cidade" not in empresa:
    empresa["cidade"] = ""

if "site" not in empresa:
    empresa["site"] = ""

if "instagram" not in empresa:
    empresa["instagram"] = "@"

if "fb_page" not in empresa:
    empresa["fb_page"] = ""

if "servicos" not in empresa:
    empresa["servicos"] = []

if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

if "mostrar_form_concorrente" not in st.session_state:
    st.session_state.mostrar_form_concorrente = False

if "editando_concorrente" not in st.session_state:
    st.session_state.editando_concorrente = None

# ---------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------

def limpar_site(url):

    if not url:
        return ""

    url = url.strip().lower()

    # REMOVE HTTP/HTTPS
    url = re.sub(
        r"^https?:\/\/",
        "",
        url,
        flags=re.IGNORECASE
    )

    # REMOVE WWW
    url = re.sub(
        r"^www\.",
        "",
        url,
        flags=re.IGNORECASE
    )

    # REMOVE ACENTOS E CARACTERES ESPECIAIS
    url = (
        url.replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ã", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )

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

    valor = valor.strip()

    valor = re.sub(
        r"^https?:\/\/(www\.)?instagram\.com\/",
        "",
        valor,
        flags=re.IGNORECASE
    )

    valor = valor.strip("/")

    if valor.startswith("@"):
        return valor

    return f"@{valor}" if valor else ""


def obter_facebook_handle(valor):

    if not valor:
        return ""

    valor = valor.strip()

    valor = re.sub(
        r"^https?:\/\/(www\.)?facebook\.com\/",
        "",
        valor,
        flags=re.IGNORECASE
    )

    valor = valor.strip("/")

    return valor

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
    min-height: auto !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    white-space: normal !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #2c3338 !important;
    border: none !important;
    transform: none !important;
}

.add-button button {
    background: #2271b1 !important;
    border-radius: 10px !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    height: 45px !important;
}

.add-button button:hover {
    background: #2f89d1 !important;
}

.service-tag {
    background-color: #2271b1;
    color: white;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 5px;
    display: inline-block;
    margin-bottom: 5px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# MENU LATERAL
# ---------------------------------------------------

with st.sidebar:

    st.markdown(
        '<div class="sidebar-header">Dados Principais</div>',
        unsafe_allow_html=True
    )

    if st.button("🏠 Minha Empresa"):
        st.session_state.pagina = "home"

    if st.button("👥 Concorrentes"):
        st.session_state.pagina = "cad"

    st.markdown(
        '<div class="sidebar-header">Análise</div>',
        unsafe_allow_html=True
    )

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

    st.subheader("📄 Informações Gerais")

    col1, col2 = st.columns(2)

    emp["nome"] = col1.text_input(
        "Nome da Empresa",
        emp["nome"]
    )

    emp["setor"] = col1.selectbox(
        "Setor",
        [
            "Marketing",
            "Tecnologia",
            "Varejo",
            "Saúde",
            "Educação",
            "Indústria"
        ]
    )

    emp["tipo"] = col2.text_input(
        "Sub-nicho",
        emp["tipo"]
    )

    st.markdown("---")

    st.subheader("📍 Localização")

    loc1, loc2 = st.columns(2)

    estados = list(ESTADOS_CIDADES.keys())

    estado_index = 0

    if emp["estado"] in estados:
        estado_index = estados.index(emp["estado"])

    emp["estado"] = loc1.selectbox(
        "Estado",
        estados,
        index=estado_index
    )

    cidades = ESTADOS_CIDADES.get(
        emp["estado"],
        []
    )

    cidade_index = 0

    if emp["cidade"] in cidades:
        cidade_index = cidades.index(emp["cidade"])

    emp["cidade"] = loc2.selectbox(
        "Cidade",
        cidades,
        index=cidade_index
    )

    st.markdown("---")

    st.subheader("📱 Redes Sociais")

    col_a, col_b = st.columns(2)

    emp["instagram"] = col_a.text_input(
        "Instagram",
        value=emp["instagram"]
    )

    emp["fb_page"] = col_b.text_input(
        "Facebook",
        emp["fb_page"]
    )

    st.markdown("---")

    st.subheader("🌐 Website")

    site_input = st.text_input(
        "Site",
        emp["site"]
    )

    emp["site"] = limpar_site(site_input)

    st.markdown("---")

    st.subheader("🛠️ Serviços")

    with st.form("form_servico", clear_on_submit=True):

        novo = st.text_input("Adicionar Serviço")

        enviar = st.form_submit_button(
            "Adicionar",
            type="primary"
        )

        if enviar and novo:

            emp["servicos"].append(novo)

            st.rerun()

    if emp["servicos"]:

        st.markdown(
            "".join([
                f"<span class='service-tag'>{s}</span>"
                for s in emp["servicos"]
            ]),
            unsafe_allow_html=True
        )
