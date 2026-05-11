import streamlit as st
from components.headers import cabecalho_analise


def render_redes():

    cabecalho_analise(
        "📱 Redes Sociais",
        "Métricas de engajamento"
    )

    concorrentes = st.session_state.get("concorrentes", [])

    if not concorrentes:
        st.info("Nenhum concorrente cadastrado")
        return

    for c in concorrentes:

        st.subheader(c["nome"])

        col1, col2, col3 = st.columns(3)

        col1.metric("Seguidores", "12.3K")
        col2.metric("Posts", "342")
        col3.metric("Engajamento", "4.2%")

        st.divider()
