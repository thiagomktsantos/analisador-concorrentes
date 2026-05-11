import streamlit as st
from components.headers import cabecalho_simples


def render_sites():

    cabecalho_simples(
        "🌐 Confronto de Sites",
        "Análise comparativa de posicionamento"
    )

    concorrentes = st.session_state.get("concorrentes", [])

    if not concorrentes:
        st.info("Nenhum concorrente cadastrado")
        return

    for c in concorrentes:

        st.markdown(f"### {c['nome']}")

        st.code(c["site"])

        st.markdown("""
        - Posicionamento
        - SEO
        - Copy
        - CTA
        - Oferta
        """)

        st.divider()
