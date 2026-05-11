import streamlit as st
from components.headers import cabecalho_simples


def render_home():

    cabecalho_simples(
        "🏛️ Minha Empresa",
        "Gerencie os dados da sua empresa"
    )

    if "empresa" not in st.session_state:
        st.session_state.empresa = {
            "nome": "",
            "setor": "",
            "site": "",
            "instagram": "",
            "facebook": ""
        }

    empresa = st.session_state.empresa

    col1, col2 = st.columns(2)

    with col1:
        empresa["nome"] = st.text_input(
            "Nome da Empresa",
            empresa["nome"]
        )

        empresa["setor"] = st.text_input(
            "Setor",
            empresa["setor"]
        )

    with col2:
        empresa["site"] = st.text_input(
            "Site",
            empresa["site"]
        )

        empresa["instagram"] = st.text_input(
            "Instagram",
            empresa["instagram"]
        )

    empresa["facebook"] = st.text_input(
        "Facebook",
        empresa["facebook"]
    )

    if st.button("💾 Salvar"):
        st.success("Empresa salva!")
