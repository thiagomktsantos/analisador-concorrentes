import streamlit as st
import google.generativeai as genai
import trafilatura
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IA Competitive Intelligence", layout="wide")

# --- 2. CONFIGURAÇÃO DA IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

# --- 3. ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        "minha_empresa": {
            "nome": "", "setor": "Marketing", "tipo": "", 
            "instagram": "@", "fb_page": "", "servicos": [] 
        },
        "concorrentes": [],
    }

if 'logado' not in st.session_state: st.session_state.logado = False
if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'show_form' not in st.session_state: st.session_state.show_form = False

# --- 4. FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    if model is None: return "Erro: Chave API não configurada."
    try:
        emp = st.session_state.dados['minha_empresa']
        contexto = f"Empresa: {emp['nome']} | Setor: {emp['setor']}\n---\n"
        return model.generate_content(contexto + prompt).text
    except Exception as e: return f"Erro: {str(e)}"

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Dashboard")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
