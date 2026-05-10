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


def empresa_tem_dados(emp):
    """Retorna True se a empresa já tem pelo menos o nome preenchido."""
    return bool(emp.get("nome", "").strip())

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

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"] {
    background-color: #1e2327 !important;
}

.sidebar-header {
    color: #afb1b3;
    font-size: 11px;
    font-weight: 700;
    padding: 10px 20px 4px 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: block;
    width: 100%;
    border-top: 1px solid #2c3338;
    margin-top: 2px;
}

[data-testid="stSidebar"] div.stButton {
    margin-bottom: 0px !important;
}

[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    border-radius: 8px !important;
    background-color: transparent !important;
    color: #eee !important;
    border: none !important;
    text-align: left !important;
    padding: 6px 20px !important;
    min-height: auto !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    white-space: normal !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease !important;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #2c3338 !important;
    color: #ffffff !important;
}

/* ============ CARDS CONCORRENTES — força fundo escuro ============ */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1a2235 !important;
    border: 1px solid #2d3f5e !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
    min-height: 260px !important;
    display: flex !important;
    flex-direction: column !important;
}

/* garante que texto dentro dos cards fique visível */
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] span,
[data-testid="stVerticalBlockBorderWrapper"] div {
    color: inherit;
}

[data-testid="stVerticalBlockBorderWrapper"] > div {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
}

.card-inner { flex: 1; }

.card-avatar {
    width: 52px;
    height: 52px;
    min-width: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #9333ea, #ec4899);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: bold;
    color: white !important;
    line-height: 1;
    flex-shrink: 0;
}

.card-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 14px;
}

.card-name {
    margin: 0;
    padding: 0;
    font-size: 18px;
    color: #f1f5f9 !important;
    line-height: 1.3;
    word-break: break-word;
}

.card-info p {
    margin: 5px 0;
    color: #94a3b8 !important;
    font-size: 14px;
}

/* ============ BOTÃO EDITAR (estilo neutro, não-primary) ============ */

.btn-editar-empresa > button {
    background-color: #334155 !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease !important;
}

.btn-editar-empresa > button:hover {
    background-color: #475569 !important;
    border-color: #64748b !important;
    color: #ffffff !important;
}

/* ============ CARD MINHA EMPRESA ============ */

.empresa-card {
    background: #1a2235;
    border: 1px solid #2d3f5e;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    max-width: 860px;
}

.empresa-top {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid #2d3f5e;
}

.empresa-avatar {
    width: 64px;
    height: 64px;
    min-width: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: bold;
    color: white;
    flex-shrink: 0;
}

.empresa-nome {
    margin: 0 0 4px 0;
    padding: 0;
    font-size: 22px;
    font-weight: 700;
    color: #f1f5f9;
}

.empresa-subtitulo {
    margin: 0;
    font-size: 13px;
    color: #94a3b8;
}

.empresa-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 40px;
}

.empresa-grupo {
    margin-bottom: 0;
}

.empresa-grupo-titulo {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748b;
    margin: 0 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #1e3a5f;
}

.empresa-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 8px;
}

.empresa-row-icon {
    font-size: 15px;
    width: 20px;
    flex-shrink: 0;
    margin-top: 1px;
}

.empresa-row-content {}

.empresa-row-label {
    font-size: 11px;
    color: #64748b;
    display: block;
    margin-bottom: 1px;
}

.empresa-row-value {
    font-size: 14px;
    color: #cbd5e1;
}

.empresa-servicos {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #2d3f5e;
}

.empresa-servicos-titulo {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748b;
    margin: 0 0 10px 0;
}

.service-tag {
    background-color: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2d5a8e;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    margin-right: 6px;
    display: inline-block;
    margin-bottom: 6px;
}

/* ============ POPUP ============ */

.popup-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    z-index: 999999;
}

.popup-box {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #1f2937;
    width: 500px;
    border-radius: 16px;
    padding: 30px;
    z-index: 9999999;
    border: 1px solid #374151;
    color: white;
}

.popup-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 15px;
}

.popup-text {
    color: #cbd5e1;
    margin-bottom: 25px;
    line-height: 1.5;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.markdown(
        '<hr style="border:none;border-top:1px solid #2c3338;margin:8px 0 0 0"/>'
        '<div class="sidebar-header">Dados Principais</div>',
        unsafe_allow_html=True
    )

    if st.button("🏠 Minha Empresa"):
        trocar_pagina("home")

    if st.button("👥 Concorrentes"):
        trocar_pagina("cad")

    st.markdown(
        '<hr style="border:none;border-top:1px solid #2c3338;margin:8px 0 0 0"/>'
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
# POPUP ALERTA
# ---------------------------------------------------

if st.session_state.mostrar_alerta_saida:

    st.markdown("""
    <div class="popup-overlay"></div>

    <div class="popup-box">

        <div class="popup-title">
            ⚠️ Cancelar edição?
        </div>

        <div class="popup-text">
            Você possui uma edição aberta de concorrente.
            Se sair agora as alterações não salvas serão perdidas.
        </div>

    </div>
    """, unsafe_allow_html=True)

    p1, p2, p3 = st.columns([1, 1, 1])

    with p2:

        if st.button(
            "✅ Sair e cancelar edição",
            use_container_width=True
        ):

            st.session_state.mostrar_form_concorrente = False
            st.session_state.editando_concorrente = None
            st.session_state.mostrar_alerta_saida = False

            st.session_state.pagina = (
                st.session_state.pagina_destino
            )

            st.rerun()

        if st.button(
            "❌ Continuar editando",
            use_container_width=True
        ):

            st.session_state.mostrar_alerta_saida = False
            st.rerun()

# ---------------------------------------------------
# HOME — Minha Empresa
# ---------------------------------------------------

if st.session_state.pagina == "home":

    emp = st.session_state.dados["minha_empresa"]
    tem_dados = empresa_tem_dados(emp)

    # Se não tem dados OU está em modo edição → mostra formulário
    if not tem_dados or st.session_state.editar_empresa:

        # Título com botão cancelar ao lado (só se já tinha dados)
        h1, h2 = st.columns([8, 2])
        with h1:
            st.title("🏢 Minha Empresa")
        with h2:
            if tem_dados:
                st.markdown("<div style='padding-top:18px'/>", unsafe_allow_html=True)
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.editar_empresa = False
                    st.rerun()

        st.markdown("---")

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

        site_digitado = st.text_input(
            "Site",
            emp["site"]
        )

        emp["site"] = limpar_site(site_digitado)

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

        if st.button(
            "💾 Salvar Empresa",
            type="primary"
        ):

            if emp["nome"].strip():
                st.session_state.editar_empresa = False
                st.success("Empresa salva com sucesso!")
                st.rerun()
            else:
                st.error("Informe pelo menos o nome da empresa.")

    else:
        # Tem dados e não está editando → exibe card reorganizado
        h1, h2 = st.columns([8, 2])
        with h1:
            st.title("🏢 Minha Empresa")
        with h2:
            st.markdown("<div style='padding-top:18px'/>", unsafe_allow_html=True)
            # Botão com classe CSS neutra (sem type="primary")
            st.markdown('<div class="btn-editar-empresa">', unsafe_allow_html=True)
            if st.button("✏️ Editar Empresa", use_container_width=True):
                st.session_state.editar_empresa = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        avatar = gerar_avatar(emp["nome"])

        servicos_html = ""
        if emp["servicos"]:
            tags = "".join([
                f"<span class='service-tag'>{s}</span>"
                for s in emp["servicos"]
            ])
            servicos_html = f"""
            <div class="empresa-servicos">
                <div class="empresa-servicos-titulo">🛠️ Serviços</div>
                {tags}
            </div>
            """

        loc = emp['cidade'] or ''
        if emp['estado']:
            loc += (', ' if loc else '') + emp['estado']

        st.markdown(
            f"""
            <div class="empresa-card">

                <div class="empresa-top">
                    <div class="empresa-avatar">{avatar}</div>
                    <div>
                        <h2 class="empresa-nome">{emp['nome']}</h2>
                        <p class="empresa-subtitulo">{emp['setor']}{' · ' + emp['tipo'] if emp['tipo'] else ''}</p>
                    </div>
                </div>

                <div class="empresa-grid">

                    <div class="empresa-grupo">
                        <div class="empresa-grupo-titulo">📍 Localização</div>
                        <div class="empresa-row">
                            <span class="empresa-row-icon">🗺️</span>
                            <div class="empresa-row-content">
                                <span class="empresa-row-label">Cidade / Estado</span>
                                <span class="empresa-row-value">{loc or '—'}</span>
                            </div>
                        </div>
                    </div>

                    <div class="empresa-grupo">
                        <div class="empresa-grupo-titulo">🌐 Presença Digital</div>
                        <div class="empresa-row">
                            <span class="empresa-row-icon">📸</span>
                            <div class="empresa-row-content">
                                <span class="empresa-row-label">Instagram</span>
                                <span class="empresa-row-value">{emp['instagram'] or '—'}</span>
                            </div>
                        </div>
                        <div class="empresa-row">
                            <span class="empresa-row-icon">📘</span>
                            <div class="empresa-row-content">
                                <span class="empresa-row-label">Facebook</span>
                                <span class="empresa-row-value">{emp['fb_page'] or '—'}</span>
                            </div>
                        </div>
                        <div class="empresa-row">
                            <span class="empresa-row-icon">🔗</span>
                            <div class="empresa-row-content">
                                <span class="empresa-row-label">Site</span>
                                <span class="empresa-row-value">{emp['site'] or '—'}</span>
                            </div>
                        </div>
                    </div>

                </div>

                {servicos_html}

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
        if st.button("➕ Adicionar", use_container_width=True):
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

                with st.container(border=True):

                    st.markdown(
                        f"""
                        <div class="card-inner">
                            <div class="card-header">
                                <div class="card-avatar">{avatar}</div>
                                <h3 class="card-name">{c['nome']}</h3>
                            </div>
                            <div class="card-info">
                                <p>🌐 {c['url'] or '—'}</p>
                                <p>📸 {c['instagram'] or '—'}</p>
                                <p>📘 {c['fb_page'] or '—'}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✏️ Editar", key=f"editar_{i}", use_container_width=True):
                            st.session_state.editando_concorrente = i
                            st.session_state.mostrar_form_concorrente = False
                            st.rerun()
                    with b2:
                        if st.button("🗑️ Remover", key=f"remove_{i}", use_container_width=True):
                            st.session_state.dados["concorrentes"].pop(i)
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
