# ---------------------------------------------------
# PÁGINA: CONCORRENTES
# ---------------------------------------------------

elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    if "mostrar_form_concorrente" not in st.session_state:
        st.session_state.mostrar_form_concorrente = False

    # ---------------------------------------------------
    # CSS EXTRA
    # ---------------------------------------------------

    st.markdown("""
    <style>

    .card-concorrente {
        background: #1f2937;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #2d3748;
        margin-bottom: 15px;
        transition: 0.2s;
    }

    .card-concorrente:hover {
        border-color: #2271b1;
        transform: translateY(-2px);
    }

    .nome-card {
        font-size: 20px;
        font-weight: 700;
        color: white;
        margin-bottom: 10px;
    }

    .info-card {
        color: #cbd5e1;
        margin-bottom: 5px;
        font-size: 14px;
    }

    /* CARD ADICIONAR */

    div[data-testid="stButton"] > button[kind="secondary"] {
        background: rgba(34,113,177,0.12);
        border: 2px dashed #2271b1;
        border-radius: 14px;
        padding: 35px 20px;
        min-height: 140px;
        font-size: 22px;
        font-weight: 700;
        color: white;
        transition: 0.2s;
    }

    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        border-color: #3b82f6;
        background: rgba(34,113,177,0.22);
        transform: translateY(-2px);
    }

    </style>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------
    # CARD ADICIONAR CLICÁVEL
    # ---------------------------------------------------

    add_clicked = st.button(
        "➕ Adicionar Concorrente\n\nCadastre empresas para monitorar",
        key="card_add_concorrente",
        use_container_width=True
    )

    if add_clicked:
        st.session_state.mostrar_form_concorrente = True

    st.markdown("---")

    # ---------------------------------------------------
    # FORMULÁRIO
    # ---------------------------------------------------

    if st.session_state.mostrar_form_concorrente:

        with st.form("cad_concorrente", clear_on_submit=True):

            st.subheader("📄 Identificação")

            c1, c2 = st.columns(2)

            n = c1.text_input("Nome do Concorrente")

            u = c2.text_input("URL do Site")

            st.markdown("---")

            st.subheader("📱 Redes Sociais")

            c3, c4 = st.columns(2)

            insta_handle = c3.text_input(
                "Instagram (@empresa)",
                value="@"
            )

            fb_p = c4.text_input(
                "Facebook"
            )

            ads_manual = st.text_input(
                "ID Manual Ads (Opcional)"
            )

            col_salvar, col_cancelar = st.columns(2)

            salvar = col_salvar.form_submit_button(
                "Salvar Concorrente",
                type="primary"
            )

            cancelar = col_cancelar.form_submit_button(
                "Cancelar"
            )

            # CANCELAR

            if cancelar:

                st.session_state.mostrar_form_concorrente = False

                st.rerun()

            # SALVAR

            if salvar:

                if n:

                    clean_handle = insta_handle.strip()

                    if clean_handle == "@":
                        clean_handle = ""

                    elif not clean_handle.startswith("@"):
                        clean_handle = "@" + clean_handle

                    search_term = (
                        ads_manual
                        or fb_p
                        or clean_handle.replace("@", "")
                        or n
                    )

                    st.session_state.dados["concorrentes"].append({
                        "nome": n,
                        "url": u,
                        "instagram": clean_handle,
                        "fb_page": fb_p,
                        "ads_id": search_term
                    })

                    st.session_state.mostrar_form_concorrente = False

                    st.success(
                        f"{n} cadastrado com sucesso!"
                    )

                    st.rerun()

                else:
                    st.error("Nome obrigatório.")

    # ---------------------------------------------------
    # GRID DE CARDS
    # ---------------------------------------------------

    concorrentes = st.session_state.dados["concorrentes"]

    if concorrentes:

        st.subheader("📌 Concorrentes Cadastrados")

        cols = st.columns(3)

        for i, c in enumerate(concorrentes):

            with cols[i % 3]:

                st.markdown(f"""
                <div class="card-concorrente">

                    <div class="nome-card">
                        {c['nome']}
                    </div>

                    <div class="info-card">
                        🌐 {c['url'] or 'Sem site'}
                    </div>

                    <div class="info-card">
                        📸 {c['instagram'] or 'Sem Instagram'}
                    </div>

                    <div class="info-card">
                        👍 {c['fb_page'] or 'Sem Facebook'}
                    </div>

                </div>
                """, unsafe_allow_html=True)

                if st.button(
                    "🗑️ Remover",
                    key=f"remove_{i}",
                    use_container_width=True
                ):

                    st.session_state.dados["concorrentes"].pop(i)

                    st.rerun()

    else:

        st.info("Nenhum concorrente cadastrado.")
