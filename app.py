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
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
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

    url = url.strip()

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

/* MENU */

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

/* BOTÃO */

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

/* TAG */

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

    estado_index = (
        estados.index(emp["estado"])
        if emp["estado"] in estados
        else 0
    )

    emp["estado"] = loc1.selectbox(
        "Estado",
        estados,
        index=estado_index
    )

    cidades = ESTADOS_CIDADES.get(
        emp["estado"],
        []
    )

    cidade_index = (
        cidades.index(emp["cidade"])
        if emp["cidade"] in cidades
        else 0
    )

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

    emp["site"] = st.text_input(
        "Site",
        emp["site"]
    )

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

# ---------------------------------------------------
# CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    top1, top2 = st.columns([8, 2])

    with top1:
        st.title("👥 Concorrentes")

    with top2:

        st.markdown(
            '<div class="add-button">',
            unsafe_allow_html=True
        )

        add_clicked = st.button(
            "➕ Adicionar",
            use_container_width=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    if add_clicked:

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

            col1, col2 = st.columns(2)

            salvar = col1.form_submit_button(
                "Salvar",
                type="primary"
            )

            cancelar = col2.form_submit_button(
                "Cancelar"
            )

            if cancelar:

                st.session_state.mostrar_form_concorrente = False
                st.session_state.editando_concorrente = None

                st.rerun()

            if salvar:

                if n:

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

                        st.success(
                            f"{n} atualizado com sucesso!"
                        )

                    else:

                        st.session_state.dados[
                            "concorrentes"
                        ].append(dados_novos)

                        st.success(
                            f"{n} cadastrado com sucesso!"
                        )

                    st.session_state.mostrar_form_concorrente = False
                    st.session_state.editando_concorrente = None

                    st.rerun()

                else:

                    st.error("Nome obrigatório.")

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                avatar = gerar_avatar(c["nome"])

                card_html = f"""
                <html>
                <head>

                <style>

                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: Arial, sans-serif;
                }}

                .card {{
                    background: #1f2937;
                    border: 1px solid #2d3748;
                    border-radius: 18px;
                    padding: 22px;
                    color: white;
                    min-height: 300px;
                    box-sizing: border-box;
                }}

                .topo {{
                    display: flex;
                    align-items: center;
                    gap: 14px;
                    margin-bottom: 24px;
                }}

                .avatar {{
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: linear-gradient(
                        135deg,
                        #9333ea,
                        #ec4899
                    );
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 22px;
                    font-weight: bold;
                    color: white;
                    flex-shrink: 0;
                }}

                .nome {{
                    font-size: 22px;
                    font-weight: 700;
                    color: white;
                    line-height: 1.2;
                }}

                .info {{
                    font-size: 15px;
                    color: #cbd5e1;
                    margin-bottom: 14px;
                    word-break: break-word;
                    line-height: 1.5;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}

                .logo {{
                    width: 20px;
                    height: 20px;
                    object-fit: contain;
                    flex-shrink: 0;
                }}

                </style>
                </head>

                <body>

                    <div class="card">

                        <div class="topo">

                            <div class="avatar">
                                {avatar}
                            </div>

                            <div class="nome">
                                {c['nome']}
                            </div>

                        </div>

                        <div class="info">
                            🌐
                            <span>{c['url'] if c['url'] else 'Sem site'}</span>
                        </div>

                        <div class="info">

                            <img
                                class="logo"
                                src="https://cdn-icons-png.flaticon.com/512/2111/2111463.png"
                            >

                            <span>
                                {c['instagram'] if c['instagram'] else 'Sem Instagram'}
                            </span>

                        </div>

                        <div class="info">

                            <img
                                class="logo"
                                src="https://cdn-icons-png.flaticon.com/512/733/733547.png"
                            >

                            <span>
                                {c['fb_page'] if c['fb_page'] else 'Sem Facebook'}
                            </span>

                        </div>

                    </div>

                </body>
                </html>
                """

                components.html(
                    card_html,
                    height=320
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
