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
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)
    btn_home = st.button("🏠 Minha Empresa")
    btn_cad = st.button("👥 Concorrentes")
    
    st.markdown('<div class="sidebar-header">Análise Comparativa</div>', unsafe_allow_html=True)
    btn_geral = st.button("📊 Visão Geral")
    btn_sites = st.button("🌐 Confronto de Sites")
    btn_social = st.button("📱 Social & Copy")
    btn_ads = st.button("📢 Biblioteca de Ads")
    
    st.markdown('<div class="sidebar-header">Estratégia</div>', unsafe_allow_html=True)
    btn_insights = st.button("💡 IA Battle Cards")

    if btn_home: st.session_state.pagina = "home"
    if btn_cad: st.session_state.pagina = "cad"
    if btn_geral: st.session_state.pagina = "geral"
    if btn_sites: st.session_state.pagina = "sites"
    if btn_social: st.session_state.pagina = "social"
    if btn_ads: st.session_state.pagina = "ads"
    if btn_insights: st.session_state.pagina = "insights"

if 'pagina' not in st.session_state: st.session_state.pagina = "home"

# --- 8. LÓGICA DAS PÁGINAS ---

if st.session_state.pagina == "home":
    st.title("🏢 Minha Empresa")
    emp = st.session_state.dados["minha_empresa"]
    
    col1, col2 = st.columns(2)
    with col1:
        emp["nome"] = st.text_input("Nome da Empresa", emp["nome"])
        emp["setor"] = st.selectbox("Setor", ["Marketing", "Tecnologia", "Varejo", "Saúde", "Educação", "Indústria"], index=0)
    with col2:
        emp["tipo"] = st.text_input("Sub-nicho (ex: SaaS, Agência local)", emp["tipo"])

    st.write("### 🛠️ Nossos Serviços/Produtos")
    with st.form("form_servico", clear_on_submit=True):
        novo_servico = st.text_input("Adicionar Serviço")
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
    with st.form("cad_concorrente"):
        col1, col2 = st.columns(2)
        n = col1.text_input("Nome do Concorrente (Interno)")
        u = col1.text_input("URL do Site")
        
        # Campo Instagram com o prefixo sugerido
        i = col2.text_input("Instagram", placeholder="instagram.com/usuario_da_empresa")
        
        # Novo campo Nome da Página
        f = col2.text_input("Nome da Página no Facebook (Exato)")
        
        # Campo de Identificador Automático/Manual
        a = st.text_input(
            "Identificador Manual para Ads (Opcional)", 
            help="O sistema tentará usar o Nome da Página ou Instagram. Se a busca na [Biblioteca de Anúncios](https://www.facebook.com/ads/library/) não funcionar, coloque aqui o ID numérico ou nome exato."
        )
        
        if st.form_submit_button("Salvar Concorrente"):
            # Lógica de auto-preenchimento para o termo de busca dos Ads
            # Limpa o instagram se o usuário colou o link completo
            insta_clean = i.replace("https://", "").replace("www.", "").replace("instagram.com/", "").replace("@", "")
            
            search_term = a or f or insta_clean or n
            
            st.session_state.dados["concorrentes"].append({
                "nome": n, 
                "url": u, 
                "instagram": f"instagram.com/{insta_clean}" if insta_clean else "", 
                "fb_page": f,
                "ads_id": search_term, 
                "analise_site": ""
            })
            st.success("Concorrente salvo!")

# --- PÁGINA: VISÃO GERAL ---
elif st.session_state.pagina == "geral":
    st.title("📊 Painel de Comparação")
    if not st.session_state.dados["concorrentes"]:
        st.warning("Cadastre concorrentes primeiro.")
    else:
        df = pd.DataFrame(st.session_state.dados["concorrentes"])
        st.dataframe(df[["nome", "url", "instagram", "fb_page"]], use_container_width=True)

# --- PÁGINA: ADS ---
elif st.session_state.pagina == "ads":
    st.title("📢 Espionagem de Anúncios")
    if not st.session_state.dados["concorrentes"]:
        st.info("Nenhum concorrente cadastrado.")
    else:
        for c in st.session_state.dados["concorrentes"]:
            with st.expander(f"🔍 Anúncios de: {c['nome']}", expanded=True):
                search_term = c['ads_id']
                url_ads = f"https://www.facebook.com/ads/library/?q={search_term}&country=BR&media_type=all"
                
                st.write(f"**Termo de busca atual:** `{search_term}`")
                st.link_button(f"Abrir Biblioteca de Anúncios para {c['nome']}", url_ads)
                
                st.caption("ℹ️ *Se a página abrir vazia ou com erro, tente editar o concorrente e usar o 'Identificador Manual' com o ID numérico da página do Facebook.*")

# --- PÁGINA: CONFRONTO DE SITES ---
elif st.session_state.pagina == "sites":
    st.title("🌐 Confronto de Proposta de Valor")
    concs = st.session_state.dados["concorrentes"]
    if concs:
        escolha = st.selectbox("Selecione o concorrente", [c["nome"] for c in concs])
        c_obj = next(c for c in concs if c["nome"] == escolha)
        if st.button(f"Analisar {escolha} vs Minha Empresa"):
            with st.spinner("Analisando..."):
                downloaded = trafilatura.fetch_url(c_obj["url"])
                texto = trafilatura.extract(downloaded)
                prompt = f"Compare o site {c_obj['url']} (Conteúdo: {texto[:2000]}) com minha empresa."
                st.markdown(consultar_ia(prompt))

# --- OUTRAS PÁGINAS (SOCIAL / INSIGHTS) ---
elif st.session_state.pagina == "social":
    st.title("📱 Análise de Copy")
    copy = st.text_area("Cole a copy aqui")
    if st.button("Analisar"):
        st.markdown(consultar_ia(f"Analise e sugira melhorias: {copy}"))

elif st.session_state.pagina == "insights":
    st.title("💡 Battle Cards")
    if st.session_state.dados["concorrentes"]:
        target = st.selectbox("Contra quem?", [c["nome"] for c in st.session_state.dados["concorrentes"]])
        if st.button("Gerar Card"):
            st.markdown(consultar_ia(f"Gere um Battle Card de vendas contra o concorrente {target}"))
