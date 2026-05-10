# --- PÁGINA: CONCORRENTES ---
elif st.session_state.pagina == "cad":

    st.title("👥 Concorrentes")

    # Estado do modal/form
    if "mostrar_form_concorrente" not in st.session_state:
        st.session_state.mostrar_form_concorrente = False

    # CSS dos cards
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

    .card-add {
        background: rgba(34,113,177,0.12);
        border: 2px dashed #2271b1;
        border-radius: 14px;
        padding: 30px;
        text-align: center;
        cursor: pointer;
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
    </style>
    """, unsafe_allow_html=True)

    # CARD ADICIONAR
    st.markdown("""
    <div class="card-add">
        <h3>➕ Adicionar Concorrente</h3>
        <p>Clique no botão abaixo para cadastrar</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Novo Concorrente", type="primary"):
        st.session_state.mostrar_form_concorrente = True

    st.markdown("---")

    # FORMULÁRIO
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
                "Nome da Página no Facebook"
            )

            ads_manual = st.text_input(
                "ID Manual para Ads (Opcional)",
                help="Use se a busca automática falhar."
            )

            salvar = st.form_submit_button(
                "Salvar Concorrente",
                type="primary"
            )

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

                    st.success(f"{n} cadastrado com sucesso!")

                    st.rerun()

                else:
                    st.error("O nome é obrigatório.")

    # LISTA DE CARDS
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
                    f"🗑️ Remover",
                    key=f"remover_{i}"
                ):
                    st.session_state.dados["concorrentes"].pop(i)
                    st.rerun()

    else:
        st.info("Nenhum concorrente cadastrado.")
