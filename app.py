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
        "minha_empresa": {"nome": "", "setor": "Marketing", "tipo": "Agência", "servicos": []},
        "concorrentes": [],
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- 4. FUNÇÃO CONSULTAR IA ---
def consultar_ia(prompt):
    if model is None: return "Erro: Chave API não configurada."
    try:
        contexto = f"Empresa: {st.session_state.dados['minha_empresa']['nome']}\nSetor: {st.session_state.dados['minha_empresa']['setor']}\n---"
        return model.generate_content(contexto + prompt).text
    except Exception as e: return f"Erro: {str(e)}"

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 6. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1e2327 !important; }
        .sidebar-header { color: #afb1b3; font-size: 11px; font-weight: 700; padding: 20px; text-transform: uppercase; }
        [data-testid="stSidebar"] div.stButton > button { 
            width: 100%; border-radius: 0px; background-color: transparent; 
            color: #eee; border: none; border-bottom: 1px solid #2c3338; 
            text-align: left; padding: 15px 20px; 
        }
        .insta-prefix { 
            display: flex; align-items: center; height: 100%; 
            padding-top: 28px; color: #555; font-weight: bold; 
        }
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)
    if st.button("🏠 Minha Empresa"): st.session_state.pagina = "home"
    if st.button("👥 Concorrentes"): st.session_state.pagina = "cad"
    st.markdown('<div class="sidebar-header">Análise</div>', unsafe_allow_html=True)
    if st.button("📊 Visão Geral"): st.session_state.pagina = "geral"
    if st.button("📢 Biblioteca de Ads"): st.session_state.pagina = "ads"
    if st.button("💡 IA Battle Cards"): st.session_state.pagina = "insights"

if 'pagina' not in st.session_state: st.session_state.pagina = "home"

# --- 8. LÓGICA DAS PÁGINAS ---

# PÁGINA: MINHA EMPRESA
if st.session_state.pagina == "home":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    col1, col2 = st.columns(2)
    emp["nome"] = col1.text_input("Nome da Empresa", emp["nome"])
    emp["tipo"] = col2.text_input("Sub-nicho", emp["tipo"])

# PÁGINA: CONCORRENTES
elif st.session_state.pagina == "cad":
    st.title("👥 Concorrentes")
    
    with st.form("cad_concorrente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        # Coluna 1
        nome_concorrente = col1.text_input("Nome do Concorrente (Interno)")
        url_site = col1.text_input("URL do Site")
        
        # Coluna 2: Instagram com prefixo fora do campo
        col_prefix, col_input = col2.columns([1.2, 3])
        col_prefix.markdown('<div class="insta-prefix">instagram.com/</div>', unsafe_allow_html=True)
        insta_user = col_input.text_input("Instagram")
        
        nome_fb = col2.text_input("Nome da Página no Facebook (Exato)")
        
        # Identificador Manual
        id_manual = st.text_input(
            "Identificador Manual para Ads (Opcional)", 
            help="Se deixado vazio, o sistema usará o Nome da Página ou o Instagram para buscar anúncios automaticamente."
        )
        
        if st.form_submit_button("Salvar Concorrente"):
            if not nome_concorrente:
                st.error("O nome do concorrente é obrigatório.")
            else:
                # LÓGICA DE AUTO-PREENCHIMENTO (Processada no salvamento)
                # Prioridade: ID Manual > Nome FB > Instagram > Nome Interno
                term_insta = insta_user.replace("@", "").strip()
                search_term = id_manual or nome_fb or term_insta or nome_concorrente
                
                st.session_state.dados["concorrentes"].append({
                    "nome": nome_concorrente,
                    "url": url_site,
                    "instagram": f"instagram.com/{term_insta}" if term_insta else "",
                    "fb_page": nome_fb,
                    "ads_id": search_term # Este campo agora garante o preenchimento
                })
                st.success(f"Concorrente '{nome_concorrente}' salvo com sucesso! Identificador de Ads definido como: {search_term}")

# PÁGINA: BIBLIOTECA DE ADS
elif st.session_state.pagina == "ads":
    st.title("📢 Biblioteca de Ads")
    if not st.session_state.dados["concorrentes"]:
        st.info("Cadastre concorrentes primeiro.")
    else:
        for c in st.session_state.dados["concorrentes"]:
            with st.expander(f"🔍 {c['nome']}", expanded=True):
                search_term = c['ads_id']
                url_ads = f"https://www.facebook.com/ads/library/?q={search_term}&country=BR&media_type=all"
                st.write(f"**Buscando por:** `{search_term}`")
                st.link_button(f"Abrir anúncios de {c['nome']}", url_ads)

# PÁGINA: VISÃO GERAL
elif st.session_state.pagina == "geral":
    st.title("📊 Visão Geral")
    if st.session_state.dados["concorrentes"]:
        df = pd.DataFrame(st.session_state.dados["concorrentes"])
        st.table(df[["nome", "url", "instagram", "ads_id"]])
    else:
        st.warning("Nenhum dado para exibir.")

# PÁGINA: BATTLE CARDS
elif st.session_state.pagina == "insights":
    st.title("💡 Battle Cards")
    if st.session_state.dados["concorrentes"]:
        target = st.selectbox("Selecione o concorrente", [c["nome"] for c in st.session_state.dados["concorrentes"]])
        if st.button("Gerar Card"):
            st.markdown(consultar_ia(f"Gere um battle card de vendas contra {target}"))
