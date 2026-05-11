import streamlit as st

def trocar_pagina(nome):
    st.session_state.pagina = nome

def render_sidebar():
    with st.sidebar:
        st.title("CI Dashboard")

        if st.button("Minha Empresa"):
            trocar_pagina("home")
