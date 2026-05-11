import streamlit as st
from components.headers import cabecalho_analise


def render_ads():

    cabecalho_analise(
        "📣 Biblioteca de Ads",
        "Anúncios ativos dos concorrentes"
    )

    concorrentes = st.session_state.get("concorrentes", [])

    if not concorrentes:
        st.info("Nenhum concorrente cadastrado")
        return

    for c in concorrentes:

        st.markdown(f"### {c['nome']}")

        st.link_button(
            "Abrir Biblioteca de Ads",
            f"https://facebook.com/ads/library/?q={c['nome']}"
        )

        st.divider()
