import streamlit as st
import google.generativeai as genai
import pandas as pd

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
    border-radius: 0px;
    background-color: transparent;
    color: #eee;
    border: none;
    border-bottom: 1px solid #2c3338;
    text-align: left;
    padding: 15px 20px;
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

.card-concorrente {
    background: #1f2937;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #2d3748;
    margin-bottom: 15px;
    transition: 0.2s;
}

.card-concorrente:hover {
    border-color: #2271b1;
    transform: translateY(-2px);
}

.nome-card {
    font-size: 20px;
    font-weight: 700;
    color: white;
    margin-bottom: 10px;
}

.info-card {
    color: #cbd5e1;
    margin-bottom: 5px;
    font-size: 14px;
}

/* CARD ADICIONAR */

div[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(34,113,177,0.12);
    border: 2px dashed #2271b1;
    border-radius: 14px;
    padding: 35px 20px;
    min-height: 140px;
    font-size: 22px;
    font-weight: 700;
    color: white;
    transition: 0.2s;
    white-space: pre-line;
}

div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: #3b82f6;
    background: rgba(34,113,177,0.22);
    transform: translateY(-2px);
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

    if st.button("📢 Biblioteca de Ads"):
        st.session_state.pagina = "ads"

    if st.button("💡 IA Battle Cards"):
        st.session_state.pagina = "insights"

# ---------------------------------------------------
# PÁGINA: HOME
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

    st.subheader("📱 Redes Sociais")

    col_a, col_b = st.columns(2)

    insta_val = (
        emp["instagram"]
        if emp["instagram"].startswith("@")
        else "@" + emp["instagram"]
    )

    emp["instagram"] = col_a.text_input(
        "Instagram",
        value=insta_val
    )

    emp["fb_page"] = col_b.text_input(
        "Facebook",
        emp["fb_page"]
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
# PÁGINA: CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    # CARD ADICIONAR

    add_clicked = st.button(
        "➕ Adicionar Concorrente\n\nCadastre empresas para monitorar",
        key="card_add_concorrente",
        use_container_width=True
    )

    if add_clicked:

        st.session_state.mostrar_form_concorrente = True

        st.rerun()

    st.markdown("---")

    # FORMULÁRIO

    if st.session_state.mostrar_form_concorrente:

        with st.form(
            "cad_concorrente",
            clear_on_submit=True
        ):

            st.subheader("📄 Identificação")

            c1, c2 = st.columns(2)

            n = c1.text_input(
                "Nome do Concorrente"
            )

            u = c2.text_input(
                "URL do Site"
            )

            st.markdown("---")

            st.subheader("📱 Redes Sociais")

            c3, c4 = st.columns(2)

            insta_handle = c3.text_input(
                "Instagram (@empresa)",
                value="@"
            )

            fb_p = c4.text_input(
                "Facebook"
            )

            ads_manual = st.text_input(
                "ID Manual Ads (Opcional)"
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

                st.rerun()

            if salvar:

                if n:

                    clean_handle = insta_handle.strip()

                    if clean_handle == "@":
                        clean_handle = ""

                    elif not clean_handle.startswith("@"):
                        clean_handle = "@" + clean_handle

                    search_term = (
                        ads_manual
                        or fb_p
                        or clean_handle.replace("@", "")
                        or n
                    )

                    st.session_state.dados[
                        "concorrentes"
                    ].append({
                        "nome": n,
                        "url": u,
                        "instagram": clean_handle,
                        "fb_page": fb_p,
                        "ads_id": search_term
                    })

                    st.session_state.mostrar_form_concorrente = False

                    st.success(
                        f"{n} cadastrado com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error("Nome obrigatório.")

    # GRID DE CARDS

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        st.subheader("📌 Concorrentes Cadastrados")

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                st.markdown(f"""
                <div class="card-concorrente">

                    <div class="nome-card">
                        {c['nome']}
                    </div>

                    <div class="info-card">
                        🌐 {c['url'] or 'Sem site'}
                    </div>

                    <div class="info-card">
                        📸 {c['instagram'] or 'Sem Instagram'}
                    </div>

                    <div class="info-card">
                        👍 {c['fb_page'] or 'Sem Facebook'}
                    </div>

                </div>
                """, unsafe_allow_html=True)

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
# PÁGINA: ADS
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
# PÁGINA: VISÃO GERAL
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
# PÁGINA: IA BATTLE CARDS
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
