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
            "nome": "", 
            "setor": "Marketing", 
            "tipo": "Agência", 
            "instagram": "",
            "fb_page": "",
            "servicos": [] 
        },
        "concorrentes": [],
    }

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- 4. FUNÇÕES AUXILIARES ---
def consultar_ia(prompt):
    if model is None: return "Erro: Chave API não configurada."
    try:
        contexto = f"""
        CONTEXTO DA MINHA EMPRESA:
        Nome: {st.session_state.dados['minha_empresa']['nome']}
        Setor: {st.session_state.dados['minha_empresa']['setor']}
        Redes: {st.session_state.dados['minha_empresa']['instagram']}, {st.session_state.dados['minha_empresa']['fb_page']}
        Serviços: {', '.join(st.session_state.dados['minha_empresa']['servicos'])}
        ---
        """
        full_prompt = contexto + prompt
        return model.generate_content(full_prompt).text
    except Exception as e: return f"Erro na IA: {str(e)}"

# --- 5. TELA DE LOGIN ---
if not st.session_state.logado:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login Dashboard")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
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
        [data-testid="stSidebar"] div.stButton > button:hover { background-color: #2c3338; color: #72aee6; }
        
        .service-tag { 
            background-color: #2271b1; color: white; padding: 4px 10px; 
            border-radius: 4px; font-size: 12px; margin-right: 5px; 
            display: inline-block; margin-bottom: 5px;
        }
        .insta-prefix { 
            display: flex; align-items: center; height: 100%; 
            padding-top: 28px; color: #555; font-weight: bold; 
        }
        .section-box {
            padding: 20px;
            border: 1px solid #e6e9ef;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)
    if st.button("🏠 Minha Empresa"): st.session_state.pagina = "home"
    if st.button("👥 Concorrentes"): st.session_state.pagina = "cad"
    
    st.markdown('<div class="sidebar-header">Análise Comparativa</div>', unsafe_allow_html=True)
    if st.button("📊 Visão Geral"): st.session_state.pagina = "geral"
    if st.button("🌐 Confronto de Sites"): st.session_state.pagina = "sites"
    if st.button("📱 Social & Copy"): st.session_state.pagina = "social"
    if st.button("📢 Biblioteca de Ads"): st.session_state.pagina = "ads"
    
    st.markdown('<div class="sidebar-header">Estratégia</div>', unsafe_allow_html=True)
    if st.button("💡 IA Battle Cards"): st.session_state.pagina = "insights"

if 'pagina' not in st.session_state: st.session_state.pagina = "home"

# --- 8. LÓGICA DAS PÁGINAS ---

# --- PÁGINA: MINHA EMPRESA ---
if st.session_state.pagina == "home":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    
    st.markdown("#### 📄 Informações Gerais")
    col1, col2 = st.columns(2)
    emp["nome"] = col1.text_input("Nome da Empresa", emp["nome"])
    emp["setor"] = col1.selectbox("Setor", ["Marketing", "Tecnologia", "Varejo", "Saúde", "Educação", "Indústria"], index=0)
    emp["tipo"] = col2.text_input("Sub-nicho (ex: SaaS, Agência local)", emp["tipo"])

    st.markdown("#### 📱 Redes Sociais")
    col_a, col_b = st.columns(2)
    with col_a:
        c_pref, c_in = st.columns([1.2, 3])
        c_pref.markdown('<div class="insta-prefix">instagram.com/</div>', unsafe_allow_html=True)
        # Limpa o valor para exibição
        val_insta = emp["instagram"].replace("instagram.com/", "")
        emp["instagram"] = "instagram.com/" + c_in.text_input("Instagram", value=val_insta, key="my_insta")
    
    emp["fb_page"] = col_b.text_input("Nome da Página no Facebook", emp["fb_page"])

    st.write("### 🛠️ Nossos Serviços/Produtos")
    with st.form("form_servico", clear_on_submit=True):
        novo_servico = st.text_input("Adicionar Serviço (Aperte Enter)")
        if st.form_submit_button("Adicionar", type="primary"):
            if novo_servico:
                emp["servicos"].append(novo_servico)
                st.rerun()
    
    if emp["servicos"]:
        tags_html = "".join([f"<span class='service-tag'>{s}</span>" for s in emp["servicos"]])
        st.markdown(tags_html, unsafe_allow_html=True)

# --- PÁGINA: CONCORRENTES ---
elif st.session_state.pagina == "cad":
    st.title("👥 Concorrentes")
    
    with st.form("cad_concorrente", clear_on_submit=True):
        st.markdown("#### 📄 Informações Básicas")
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome do Concorrente (Interno)")
        u = c2.text_input("URL do Site")
        
        st.markdown("---")
        st.markdown("#### 📱 Redes Sociais")
        c3, c4 = st.columns(2)
        
        with c3:
            col_prefix, col_input = st.columns([1.2, 3])
            col_prefix.markdown('<div class="insta-prefix">instagram.com/</div>', unsafe_allow_html=True)
            insta_user = col_input.text_input("Instagram", key="conc_insta")
        
        f = c4.text_input("Nome da Página no Facebook")
        
        a = st.text_input("Identificador Manual para Ads (Opcional)", 
                         help="Use se o nome da página for muito diferente do nome da empresa.")
        
        if st.form_submit_button("Salvar Concorrente", type="primary"):
            if n:
                term_insta = insta_user.replace("@", "").strip()
                search_term = a or f or term_insta or n
                
                st.session_state.dados["concorrentes"].append({
                    "nome": n, 
                    "url": u, 
                    "instagram": f"instagram.com/{term_insta}" if term_insta else "", 
                    "fb_page": f, 
                    "ads_id": search_term
                })
                st.success(f"Concorrente '{n}' cadastrado!")
            else:
                st.error("O nome é obrigatório.")

# --- PÁGINA: VISÃO GERAL ---
elif st.session_state.pagina == "geral":
    st.title("📊 Painel de Comparação")
    if not st.session_state.dados["concorrentes"]:
        st.warning("Cadastre concorrentes primeiro.")
    else:
        df = pd.DataFrame(st.session_state.dados["concorrentes"])
        st.dataframe(df[["nome", "url", "instagram", "fb_page"]], use_container_width=True)

# --- PÁGINA: BIBLIOTECA DE ADS ---
elif st.session_state.pagina == "ads":
    st.title("📢 Biblioteca de Ads")
    concs = st.session_state.dados["concorrentes"]
    if not concs:
        st.info("Cadastre concorrentes primeiro.")
    else:
        for c in concs:
            with st.expander(f"🔍 {c['nome']}", expanded=True):
                search_term = c['ads_id']
                url_ads = f"https://www.facebook.com/ads/library/?q={search_term}&country=BR&media_type=all"
                st.write(f"**Buscando anúncios para:** `{search_term}`")
                st.link_button(f"Abrir Biblioteca de Anúncios", url_ads)

# --- PÁGINA: IA BATTLE CARDS ---
elif st.session_state.pagina == "insights":
    st.title("💡 IA Battle Cards")
    concs = st.session_state.dados["concorrentes"]
    if concs:
        target = st.selectbox("Gerar card contra:", [c["nome"] for c in concs])
        if st.button("Gerar Card Estratégico", type="primary"):
            with st.spinner("IA criando estratégia..."):
                res = consultar_ia(f"Crie um Battle Card de vendas focado em vencer o concorrente {target}. Use as redes sociais deles para comparar tom de voz.")
                st.markdown(res)
    else:
        st.info("Adicione concorrentes para gerar cards.")
