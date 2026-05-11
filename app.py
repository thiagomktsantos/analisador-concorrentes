import streamlit as st
from components.sidebar import render_sidebar
from pages.home import render_home
from pages.concorrentes import render_concorrentes
from pages.geral import render_geral
from pages.redes import render_redes
from pages.sites import render_sites
from pages.ads import render_ads
from pages.insights import render_insights

st.set_page_config(
    page_title="CI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

render_sidebar()

pagina = st.session_state.pagina

if pagina == "home":
    render_home()

elif pagina == "cad":
    render_concorrentes()

elif pagina == "geral":
    render_geral()

elif pagina == "redes":
    render_redes()

elif pagina == "sites":
    render_sites()

elif pagina == "ads":
    render_ads()

elif pagina == "insights":
    render_insights()
