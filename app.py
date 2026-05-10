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
# CSS
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

.card-concorrente {
    background: #1f2937;
    border: 1px solid #2d3748;
    border-radius: 18px;
    padding: 22px;
    color: white;
    min-height: 340px;
    margin-bottom: 20px;
}

.avatar-concorrente {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg,#9333ea,#ec4899);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:22px;
    font-weight:bold;
    color:white;
}

.info-concorrente {
    color:#cbd5e1;
    margin-bottom:12px;
    font-size:15px;
    word-break:break-word;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.markdown(
        '<div class="sidebar-header">Dados Principais</div>',
        unsafe_allow_html=True
    )

    if st.button("🏠 Minha Empresa"):
        trocar_pagina("home")

    if st.button("👥 Concorrentes"):
        trocar_pagina("cad")

    st.markdown(
        '<div class="sidebar-header">Análise</div>',
        unsafe_allow_html=True
    )

    if st.button("📊 Visão Geral"):
        trocar_pagina("geral")

    if st.button("🌐 Confronto de Sites"):
        trocar_pagina("sites")

    if st.button("📢 Biblioteca de Ads"):
        trocar_pagina("ads")

    if st.button("💡 IA Battle Cards"):
        trocar_pagina("insights")

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

if st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    if st.button(
        "➕ Adicionar Concorrente",
        type="primary"
    ):

        st.session_state.mostrar_form_concorrente = True
        st.session_state.editando_concorrente = None
        st.rerun()

    st.markdown("---")

    if (
        st.session_state.mostrar_form_concorrente
        or st.session_state.editando_concorrente is not None
    ):

        concorrente_edit = None

        if st.session_state.editando_concorrente is not None:

            concorrente_edit = st.session_state.dados[
                "concorrentes"
            ][st.session_state.editando_concorrente]

        with st.form(
            "cad_concorrente",
            clear_on_submit=False
        ):

            st.subheader("📄 Identificação")

            c1, c2 = st.columns(2)

            n = c1.text_input(
                "Nome do Concorrente",
                value=(
                    concorrente_edit["nome"]
                    if concorrente_edit else ""
                )
            )

            u = c2.text_input(
                "URL do Site",
                value=(
                    concorrente_edit["url"]
                    if concorrente_edit else ""
                )
            )

            st.markdown("---")

            st.subheader("📱 Redes Sociais")

            c3, c4 = st.columns(2)

            insta_handle = c3.text_input(
                "Instagram",
                value=(
                    concorrente_edit["instagram"]
                    if concorrente_edit else "@"
                )
            )

            fb_p = c4.text_input(
                "Facebook",
                value=(
                    concorrente_edit["fb_page"]
                    if concorrente_edit else ""
                )
            )

            ads_manual = st.text_input(
                "ID Manual Ads (Opcional)",
                value=(
                    concorrente_edit["ads_id"]
                    if concorrente_edit else ""
                )
            )

            b1, b2 = st.columns(2)

            salvar = b1.form_submit_button(
                "Salvar",
                type="primary"
            )

            cancelar = b2.form_submit_button(
                "Cancelar"
            )

            if cancelar:

                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None
                st.rerun()

            if salvar:

                clean_handle = obter_instagram_handle(
                    insta_handle
                )

                fb_clean = obter_facebook_handle(
                    fb_p
                )

                site_clean = limpar_site(u)

                search_term = (
                    ads_manual
                    or fb_clean
                    or clean_handle.replace("@", "")
                    or n
                )

                dados_novos = {
                    "nome": n,
                    "url": site_clean,
                    "instagram": clean_handle,
                    "fb_page": fb_clean,
                    "ads_id": search_term
                }

                if st.session_state.editando_concorrente is not None:

                    st.session_state.dados[
                        "concorrentes"
                    ][
                        st.session_state.editando_concorrente
                    ] = dados_novos

                else:

                    st.session_state.dados[
                        "concorrentes"
                    ].append(dados_novos)

                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None

                st.rerun()

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                avatar = gerar_avatar(c["nome"])

                st.markdown(
                    f"""
                    <div class="card-concorrente">

                        <div style="
                            display:flex;
                            align-items:center;
                            gap:15px;
                            margin-bottom:20px;
                        ">

                            <div class="avatar-concorrente">
                                {avatar}
                            </div>

                            <div>
                                <h3 style="
                                    margin:0;
                                    color:white;
                                ">
                                    {c['nome']}
                                </h3>
                            </div>

                        </div>

                        <div class="info-concorrente">
                            🌐 {c['url'] if c['url'] else 'Sem site'}
                        </div>

                        <div class="info-concorrente">
                            📸 {c['instagram'] if c['instagram'] else 'Sem Instagram'}
                        </div>

                        <div class="info-concorrente">
                            📘 {c['fb_page'] if c['fb_page'] else 'Sem Facebook'}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                b1, b2 = st.columns(2)

                with b1:

                    if st.button(
                        "✏️ Editar",
                        key=f"editar_{i}",
                        use_container_width=True
                    ):

                        st.session_state.editando_concorrente = i
                        st.session_state.mostrar_form_concorrente = False

                        st.rerun()

                with b2:

                    if st.button(
                        "🗑️ Remover",
                        key=f"remove_{i}",
                        use_container_width=True
                    ):

                        st.session_state.dados[
                            "concorrentes"
                        ].pop(i)

                        st.rerun()
