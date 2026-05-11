import streamlit as st


def trocar_pagina(nome):
    st.session_state.pagina = nome


def render_sidebar():

    with st.sidebar:

        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #0f1117 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("## CI Dashboard")
        st.caption("Competitive Intelligence")

        st.markdown("---")

        st.markdown("### Dados")

        if st.button("🏛️ Minha Empresa"):
            trocar_pagina("home")

        if st.button("🎯 Concorrentes"):
            trocar_pagina("cad")

        st.markdown("### Análise")

        if st.button("📈 Visão Geral"):
            trocar_pagina("geral")

        if st.button("📱 Redes Sociais"):
            trocar_pagina("redes")

        if st.button("🔍 Confronto de Sites"):
            trocar_pagina("sites")

        if st.button("🎬 Biblioteca de Ads"):
            trocar_pagina("ads")

        if st.button("💡 Insights"):
            trocar_pagina("insights")
