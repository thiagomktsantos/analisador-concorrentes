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

    url = re.sub(
        r"^https?:\/\/",
        "",
        url,
        flags=re.IGNORECASE
    )

    url = re.sub(
        r"^www\.",
        "",
        url,
        flags=re.IGNORECASE
    )

    url = remover_acentos(url)

    url = re.sub(
        r"[^a-z0-9\.\-]",
        "",
        url
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

    return valor


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

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
    background: #f3f4f6;
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #161b22 0%,
        #111827 100%
    ) !important;
    border-right: 1px solid #1f2937;
}

/* MENU */

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #d1d5db !important;
    text-align: left !important;
    padding: 14px 18px !important;
    border-radius: 12px !important;
    font-size: 16px !important;
    transition: 0.2s;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #1f2937 !important;
    color: white !important;
}

[data-testid="stSidebar"] .stButton > button:focus {
    box-shadow: none !important;
    outline: none !important;
}

.sidebar-header {
    color: #9ca3af;
    font-size: 11px;
    font-weight: 700;
    padding: 24px 18px 10px 18px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* CARD */

.conc-card {
    background: white;
    border-radius: 24px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    margin-bottom: 25px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
}

.conc-banner {
    height: 180px;
    background: linear-gradient(
        135deg,
        #0f172a,
        #1e293b
    );
}

.conc-content {
    padding: 24px;
    margin-top: -50px;
}

.conc-avatar {
    width: 78px;
    height: 78px;
    border-radius: 50%;
    background: linear-gradient(
        135deg,
        #9333ea,
        #ec4899
    );
    border: 5px solid white;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 26px;
    font-weight: 700;
}

.conc-title {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
    margin-top: 16px;
    margin-bottom: 20px;
}

.conc-info {
    color: #4b5563;
    font-size: 15px;
    margin-bottom: 12px;
    word-break: break-word;
}

.card-box {
    background: white;
    border-radius: 18px;
    padding: 25px;
    border: 1px solid #e5e7eb;
    margin-bottom: 20px;
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

    st.markdown(
        f"""
        <div class="card-box">

            <h2>{emp['nome'] or 'Minha Empresa'}</h2>

            <p><b>Setor:</b> {emp['setor']}</p>

            <p><b>Sub-nicho:</b> {emp['tipo']}</p>

            <p><b>Estado:</b> {emp['estado']}</p>

            <p><b>Cidade:</b> {emp['cidade']}</p>

            <p><b>Instagram:</b> {emp['instagram']}</p>

            <p><b>Facebook:</b> {emp['fb_page']}</p>

            <p><b>Site:</b> {emp['site']}</p>

        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    top1, top2 = st.columns([8, 2])

    with top1:
        st.title("👥 Concorrentes")

    with top2:

        if st.button(
            "➕ Adicionar",
            use_container_width=True
        ):

            st.session_state.mostrar_form_concorrente = True
            st.session_state.editando_concorrente = None

            st.rerun()

    st.markdown("---")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(2)

        for i, c in enumerate(concorrentes):

            with cols[i % 2]:

                avatar = gerar_avatar(c["nome"])

                st.markdown(
                    f"""
                    <div class="conc-card">

                        <div class="conc-banner"></div>

                        <div class="conc-content">

                            <div class="conc-avatar">
                                {avatar}
                            </div>

                            <div class="conc-title">
                                {c['nome']}
                            </div>

                            <div class="conc-info">
                                🌐 {c['url'] if c['url'] else 'Sem site'}
                            </div>

                            <div class="conc-info">
                                📸 {c['instagram'] if c['instagram'] else 'Sem Instagram'}
                            </div>

                            <div class="conc-info">
                                📘 {c['fb_page'] if c['fb_page'] else 'Sem Facebook'}
                            </div>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "✏️ Editar",
                        key=f"editar_{i}",
                        use_container_width=True
                    ):

                        st.session_state.editando_concorrente = i
                        st.rerun()

                with c2:

                    if st.button(
                        "🗑️ Remover",
                        key=f"remove_{i}",
                        use_container_width=True
                    ):

                        st.session_state.dados[
                            "concorrentes"
                        ].pop(i)

                        st.rerun()

    else:

        st.info("Nenhum concorrente cadastrado.")

# ---------------------------------------------------
# VISÃO GERAL
# ---------------------------------------------------

elif st.session_state.pagina == "geral":

    st.title("📊 Visão Geral")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        df = pd.DataFrame(concorrentes)

        st.dataframe(
            df[
                [
                    "nome",
                    "url",
                    "instagram",
                    "fb_page"
                ]
            ],
            use_container_width=True
        )

    else:

        st.warning("Sem dados.")

# ---------------------------------------------------
# ADS
# ---------------------------------------------------

elif st.session_state.pagina == "ads":

    st.title("📢 Biblioteca de Ads")

    concs = st.session_state.dados["concorrentes"]

    if not concs:

        st.info("Cadastre concorrentes.")

    else:

        for c in concs:

            with st.expander(
                f"🔍 {c['nome']}",
                expanded=True
            ):

                term = c["ads_id"]

                url = f"https://www.facebook.com/ads/library/?q={term}&country=BR&media_type=all"

                st.write(f"Buscando por: {term}")

                st.link_button(
                    "Abrir Biblioteca de Ads",
                    url
                )

# ---------------------------------------------------
# CONFRONTO DE SITES
# ---------------------------------------------------

elif st.session_state.pagina == "sites":

    st.title("🌐 Confronto de Sites")

    st.info("Módulo em desenvolvimento.")

# ---------------------------------------------------
# IA BATTLE CARDS
# ---------------------------------------------------

elif st.session_state.pagina == "insights":

    st.title("💡 IA Battle Cards")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        target = st.selectbox(
            "Gerar estratégia contra:",
            [c["nome"] for c in concorrentes]
        )

        if st.button(
            "Gerar Estratégia",
            type="primary"
        ):

            with st.spinner(
                "Criando Battle Card..."
            ):

                resposta = consultar_ia(
                    f"""
                    Gere um battle card
                    focado em vencer o
                    concorrente {target}.
                    """
                )

                st.markdown(resposta)

    else:

        st.info("Adicione concorrentes.")
