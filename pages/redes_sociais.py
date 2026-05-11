import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

def render_redes_sociais():

    st.title("📱 Redes Sociais")
    st.caption("Posts, engajamento e inteligência competitiva")

    empresas = [
        {
            "nome": "Minha Empresa",
            "instagram": "@empresa"
        },
        {
            "nome": "Concorrente 1",
            "instagram": "@concorrente"
        }
    ]

    def gerar_posts():

        posts = []

        for _ in range(6):

            likes = random.randint(300, 15000)
            comentarios = random.randint(10, 600)
            views = random.randint(1000, 120000)

            posts.append({
                "Tipo": random.choice(["Reel", "Imagem", "Carrossel"]),
                "Curtidas": likes,
                "Comentários": comentarios,
                "Views": views,
                "Engajamento %": round(
                    (likes + comentarios) / max(views, 1) * 100,
                    2
                ),
                "Data": (
                    datetime.now() - timedelta(days=random.randint(1, 30))
                ).strftime("%d/%m/%Y")
            })

        return posts

    cols = st.columns(len(empresas))

    for idx, empresa in enumerate(empresas):

        with cols[idx]:

            st.metric(
                "Seguidores",
                f"{random.randint(5000, 500000):,}"
            )

            st.write(empresa["nome"])
            st.caption(empresa["instagram"])

    for empresa in empresas:

        st.subheader(empresa["nome"])

        df = pd.DataFrame(gerar_posts())

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    insights = [
        "Reels performam melhor.",
        "Conteúdo educacional gera mais comentários.",
        "Posts noturnos possuem mais engajamento."
    ]

    st.subheader("💡 Insights")

    for insight in insights:
        st.info(insight)
