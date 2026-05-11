import streamlit as st
import pandas as pd
from components.headers import cabecalho_analise


def render_geral():

    cabecalho_analise(
        "📈 Visão Geral",
        "Resumo dos concorrentes"
    )

    concorrentes = st.session_state.get("concorrentes", [])

    if not concorrentes:
        st.info("Nenhum concorrente cadastrado")
        return

    df = pd.DataFrame(concorrentes)

    st.dataframe(df, use_container_width=True)
