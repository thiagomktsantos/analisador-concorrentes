import streamlit as st
from components.headers import cabecalho_analise


def render_insights():

    cabecalho_analise(
        "✨ Insights",
        "Estratégias geradas por IA"
    )

    concorrentes = st.session_state.get("concorrentes", [])

    if not concorrentes:
        st.info("Nenhum concorrente cadastrado")
        return

    nomes = [c["nome"] for c in concorrentes]

    alvo = st.selectbox(
        "Gerar estratégia contra",
        nomes
    )

    if st.button("⚡ Gerar Insight"):

        st.markdown(f"""
        ## Estratégia contra {alvo}

        - Melhorar posicionamento
        - Criar diferenciação
        - Aumentar prova social
        - Escalar tráfego pago
        - Reforçar branding
        """)
