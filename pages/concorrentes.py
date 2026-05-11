import streamlit as st
from components.headers import cabecalho_simples


def render_concorrentes():

    cabecalho_simples(
        "🎯 Concorrentes",
        "Gerencie seus concorrentes"
    )

    if "concorrentes" not in st.session_state:
        st.session_state.concorrentes = []

    with st.form("concorrente"):

        nome = st.text_input("Nome")
        site = st.text_input("Site")
        instagram = st.text_input("Instagram")
        facebook = st.text_input("Facebook")

        salvar = st.form_submit_button("Salvar")

        if salvar:
            st.session_state.concorrentes.append({
                "nome": nome,
                "site": site,
                "instagram": instagram,
                "facebook": facebook
            })

            st.success("Concorrente adicionado")

    st.divider()

    for c in st.session_state.concorrentes:

        st.markdown(f"### {c['nome']}")
        st.write(c["site"])
        st.write(c["instagram"])
        st.write(c["facebook"])

        st.divider()
