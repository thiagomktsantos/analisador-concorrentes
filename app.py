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
            "instagram": "", "fb_page": "", "servicos": [] 
        },
        "concorrentes": [],
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- 4. FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    if model is None: return "Erro: Chave API não configurada."
    try:
        emp = st.session_state.dados['minha_empresa']
        contexto = f"Empresa: {emp['nome']} | Setor: {emp['setor']} | Serviços: {', '.join(emp['servicos'])}\n---\n"
        return model.generate_content(contexto + prompt).text
    except Exception as e: return f"Erro: {str(e)}"

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Dashboard")
        if st.button("Acessar Painel"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 6. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1e2327 !important; }
        .sidebar-header { color: #afb1b3; font-size: 11px; font-weight: 700; padding: 20px; text-transform: uppercase; letter-spacing: 1px; }
        [data-testid="stSidebar"] div.stButton > button { 
            width: 100%; border-radius: 0px; background-color: transparent; 
            color: #eee; border: none; border-bottom: 1px solid #2c3338; 
            text-align: left; padding: 15px 20px; 
        }
        .service-tag { 
            background-color: #2271b1; color: white; padding: 4px 10px; 
            border-radius: 4px; font-size: 12px; margin-right: 5px; 
            display: inline-block; margin-bottom: 5px;
        }
        /* Estilo para o @ travado ao lado do input */
        .at-symbol {
            display: flex; align-items: center; justify-content: flex-end;
            height: 100%; padding-top: 28px; font-size: 18px;
            color: #2271b1; font-weight: bold; margin-right: -15px;
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
    if st.button("🌐 Confronto de Sites"): st.session_state.pagina = "sites"
    if st.button("📢 Biblioteca de Ads"): st.session_state.pagina = "ads"
    if st.button("💡 IA Battle Cards"): st.session_state.pagina = "insights"

if 'pagina' not in st.session_state: st.session_state.pagina = "home"

# --- 8. LÓGICA DAS PÁGINAS ---

# --- PÁGINA: MINHA EMPRESA ---
if st.session_state.pagina == "home":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    
    st.subheader("📄 Informações Gerais")
    col1, col2 = st.columns(2)
    emp["nome"] = col1.text_input("Nome da Empresa", emp["nome"])
    emp["setor"] = col1.selectbox("Setor", ["Marketing", "Tecnologia", "Varejo", "Saúde", "Educação", "Indústria"], index=0)
    emp["tipo"] = col2.text_input("Sub-nicho", emp["tipo"])

    st.markdown("---")
    st.subheader("📱 Redes Sociais")
    col_a, col_b = st.columns(2)
    with col_a:
        c_at, c_in = st.columns([0.3, 4])
        c_at.markdown('<div class="at-symbol">@</div>', unsafe_allow_html=True)
        # Remove @ inicial se já existir para não duplicar na exibição
        val_i = emp["instagram"].replace("@", "")
        emp["instagram"] = "@" + c_in.text_input("Instagram (@empresa)", value=val_i, key="my_insta")
    
    emp["fb_page"] = col_b.text_input("Nome da Página no Facebook", emp["fb_page"])

    st.markdown("---")
    st.subheader("🛠️ Nossos Serviços")
    with st.form("form_servico", clear_on_submit=True):
        novo = st.text_input("Adicionar Serviço (Enter)")
        if st.form_submit_button("Adicionar", type="primary") and novo:
            emp["servicos"].append(novo)
            st.rerun()
    
    if emp["servicos"]:
        st.markdown("".join([f"<span class='service-tag'>{s}</span>" for s in emp["servicos"]]), unsafe_allow_html=True)

# --- PÁGINA: CONCORRENTES ---
elif st.session_state.pagina == "cad":
    st.title("👥 Concorrentes")
    
    with st.form("cad_concorrente", clear_on_submit=True):
        st.subheader("📄 Identificação")
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome do Concorrente")
        u = c2.text_input("URL do Site")
        
        st.markdown("---")
        st.subheader("📱 Redes Sociais")
        c3, c4 = st.columns(2)
        with c3:
            col_at, col_in = st.columns([0.3, 4])
            col_at.markdown('<div class="at-symbol">@</div>', unsafe_allow_html=True)
            insta_handle = col_in.text_input("Instagram (@empresa)", key="conc_insta")
        
        fb_p = c4.text_input("Nome da Página no Facebook")
        
        ads_manual = st.text_input("ID Manual para Ads (Opcional)", help="Use se a busca automática falhar.")
        
        if st.form_submit_button("Salvar Concorrente", type="primary"):
            if n:
                # Limpeza e definição do termo de busca para Ads
                handle = insta_handle.replace("@", "").strip()
                search_term = ads_manual or fb_p or handle or n
                
                st.session_state.dados["concorrentes"].append({
                    "nome": n, "url": u, "instagram": f"@{handle}" if handle else "",
                    "fb_page": fb_p, "ads_id": search_term
                })
                st.success(f"Concorrente {n} cadastrado!")
            else:
                st.error("O nome é obrigatório.")

# --- PÁGINA: BIBLIOTECA DE ADS ---
elif st.session_state.pagina == "ads":
    st.title("📢 Biblioteca de Ads")
    concs = st.session_state.dados["concorrentes"]
    if not concs:
        st.info("Cadastre concorrentes primeiro.")
    else:
        for c in concs:
            with st.expander(f"🔍 {c['nome']}", expanded=True):
                term = c['ads_id']
                url = f"https://www.facebook.com/ads/library/?q={term}&country=BR&media_type=all"
                st.write(f"Buscando por: **{term}**")
                st.link_button(f"Abrir Biblioteca de Ads", url)

# --- PÁGINA: VISÃO GERAL ---
elif st.session_state.pagina == "geral":
    st.title("📊 Painel Comparativo")
    if st.session_state.dados["concorrentes"]:
        df = pd.DataFrame(st.session_state.dados["concorrentes"])
        st.dataframe(df[["nome", "url", "instagram", "fb_page"]], use_container_width=True)
    else:
        st.warning("Sem dados.")

# --- PÁGINA: IA BATTLE CARDS ---
elif st.session_state.pagina == "insights":
    st.title("💡 IA Battle Cards")
    if st.session_state.dados["concorrentes"]:
        target = st.selectbox("Gerar card contra:", [c["nome"] for c in st.session_state.dados["concorrentes"]])
        if st.button("Gerar Estratégia", type="primary"):
            with st.spinner("Criando Battle Card..."):
                st.markdown(consultar_ia(f"Gere um battle card focado em vencer o concorrente {target}."))
    else:
        st.info("Adicione concorrentes.")
