import streamlit as st
import datetime


def cabecalho_simples(titulo, subtitulo=""):

    st.title(titulo)

    if subtitulo:
        st.caption(subtitulo)

    st.divider()



def cabecalho_analise(titulo, subtitulo=""):

    h1, h2 = st.columns([6, 2])

    with h1:
        st.title(titulo)
        st.caption(subtitulo)

    with h2:
        periodo = st.selectbox(
            "Período",
            [
                "Últimos 7 dias",
                "Últimos 30 dias",
                "Últimos 90 dias",
                "Últimos 12 meses",
                "Todo o período"
            ]
        )

    st.divider()

    periodo_map = {
        "Últimos 7 dias": 7,
        "Últimos 30 dias": 30,
        "Últimos 90 dias": 90,
        "Últimos 12 meses": 365,
        "Todo o período": None,
    }

    dias = periodo_map[periodo]

    if dias:
        data_inicio = (
            datetime.date.today() - datetime.timedelta(days=dias)
        ).strftime("%Y-%m-%d")
    else:
        data_inicio = None

    return periodo, data_inicio
