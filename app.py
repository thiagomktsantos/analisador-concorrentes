import streamlit as st
import google.generativeai as genai
import pandas as pd
import trafilatura

# =====================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================
st.set_page_config(
    page_title="Analisador de Concorrentes",
    page_icon="📊",
    layout="wide"
)

# =====================================
# CONFIGURAÇÃO GEMINI
# =====================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# =====================================
# ESTADO GLOBAL
# =====================================
if "dados" not in st.session_state:
    st.session_state.dados = {
        "concorrentes": []
    }

# =====================================
# CSS GLOBAL (CARD CORRIGIDO)
# =====================================
st.markdown("""
<style>

body {
    background-color: #0f172a;
}

.card-concorrente {
    background: linear-gradient(180deg, #1f2937, #111827);
    padding: 24px;
    border-radius: 20px;
    border: 1px solid #2d3748;
    margin-bottom: 20px;
}

.nome-card {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 18px;
}

.info-card {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #e5e7eb;
    font-size: 15px;
    margin-bottom: 12px;
}

.info-icon {
    width: 22px;
    text-align: center;
}

.info-text {
    word-break: break-word;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# FUNÇÕES
# =====================================
def extrair_texto_site(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except:
        return ""
    return ""

# =====================================
# TÍTULO
# =====================================
st.title("📊 Analisador de Concorrentes")

# =====================================
# FORMULÁRIO
# =====================================
with st.form("form_concorrente"):
    nome = st.text_input("Nome do concorrente")
    url = st.text_input("Site")
    instagram = st.text_input("Instagram")
    facebook = st.text_input("Facebook")

    submitted = st.form_submit_button("Adicionar concorrente")

    if submitted and nome:
        st.session_state.dados["concorrentes"].append({
            "nome": nome,
            "url": url,
            "instagram": instagram,
            "facebook": facebook
        })

# =====================================
# EXIBIÇÃO DOS CARDS (AQUI ESTAVA O ERRO)
# =====================================
st.markdown("## Concorrentes")

cols = st.columns(3)

for i, c in enumerate(st.session_state.dados["concorrentes"]):
    with cols[i % 3]:
        st.markdown(f"""
        <div class="card-concorrente">

            <div class="nome-card">
                {c.get('nome', '')}
            </div>

            <div class="info-card">
                <span class="info-icon">🌐</span>
                <span class="info-text">{c.get('url') or 'Sem site'}</span>
            </div>

            <div class="info-card">
                <span class="info-icon">📸</span>
                <span class="info-text">{c.get('instagram') or 'Sem Instagram'}</span>
            </div>

            <div class="info-card">
                <span class="info-icon">👍</span>
                <span class="info-text">{c.get('facebook') or 'Sem Facebook'}</span>
            </div>

        </div>
        """, unsafe_allow_html=True)

# =====================================
# DEBUG OPCIONAL
# =====================================
with st.expander("📦 Dados em memória"):
    st.json(st.session_state.dados)
