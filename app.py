import streamlit as st

from pages.dashboard import render_dashboard
from pages.redes_sociais import render_redes_sociais
from pages.concorrentes import render_concorrentes
from pages.insights import render_insights

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

st.sidebar.title("Marketylics")

if st.sidebar.button("Dashboard"):
    st.session_state.pagina = "dashboard"

if st.sidebar.button("Redes Sociais"):
    st.session_state.pagina = "redes"

if st.sidebar.button("Concorrentes"):
    st.session_state.pagina = "concorrentes"

if st.sidebar.button("Insights"):
    st.session_state.pagina = "insights"

if st.session_state.pagina == "dashboard":
    render_dashboard()

elif st.session_state.pagina == "redes":
    render_redes_sociais()

elif st.session_state.pagina == "concorrentes":
    render_concorrentes()

elif st.session_state.pagina == "insights":
    render_insights()
