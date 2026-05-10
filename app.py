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

# ---------------------------------------------------
# FUNÇÕES AUXILIARES (mantidas iguais)
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
# CSS
# ---------------------------------------------------

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #1e2327 !important;
}

.card-concorrente {
    background: #1f2937;
    border: 1px solid #2d3748;
    border-radius: 18px;
    padding: 22px;
    color: white;
    min-height: 260px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# NAVEGAÇÃO SEGURA (CORREÇÃO DO ERRO)
# ---------------------------------------------------

pagina = st.session_state.pagina

# ---------------------------------------------------
# HOME
# ---------------------------------------------------

if pagina == "home":

    st.title("🏢 Minha Empresa")
    st.write(st.session_state.dados["minha_empresa"])

# ---------------------------------------------------
# CONCORRENTES (CORRIGIDO)
# ---------------------------------------------------

elif pagina == "cad":

    st.title("👥 Concorrentes")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                avatar = gerar_avatar(c["nome"])

                html = f"""
                <div class="card-concorrente">
                    <div style="display:flex;gap:10px;align-items:center;">
                        <div style="background:#9333ea;width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;">
                            {avatar}
                        </div>
                        <h3>{c['nome']}</h3>
                    </div>
                    <p>🌐 {c['url']}</p>
                    <p>📸 {c['instagram']}</p>
                    <p>📘 {c['fb_page']}</p>
                </div>
                """

                components.html(html, height=250)

    else:
        st.info("Nenhum concorrente cadastrado.")

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------

elif pagina == "geral":

    st.title("📊 Visão Geral")
    st.write(st.session_state.dados["concorrentes"])

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif pagina == "ads":

    st.title("📢 Biblioteca de Ads")

# ---------------------------------------------------
# SITES
# ---------------------------------------------------

elif pagina == "sites":

    st.title("🌐 Confronto de Sites")

# ---------------------------------------------------
# INSIGHTS
# ---------------------------------------------------

elif pagina == "insights":

    st.title("💡 IA Battle Cards")
