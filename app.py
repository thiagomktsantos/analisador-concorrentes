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
            width: 100%; 
            border-radius: 0px; 
            background-color: transparent; 
            color: #eee; 
            border: none; 
            border-bottom: 1px solid #2c3338; 
            text-align: left; 
            padding: 15px 20px; 
        }
        [data-testid="stSidebar"] div.stButton > button:hover { 
            background-color: #2c3338; 
            color: #72aee6; 
        }
        
        .service-tag { 
            background-color: #2271b1; 
            color: white; 
            padding: 4px 10px; 
            border-radius: 4px; 
            font-size: 12px; 
            margin-right: 5px; 
            display: inline-block;
            margin-bottom: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 7. MENU LATERAL ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Dados Principais</div>', unsafe_allow_html=True)
    btn_home = st.button("🏠 Minha Empresa")
    # ALTERADO: Nome simplificado para "Concorrentes"
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
        btn_adicionar = st.form_submit_button("Adicionar", type="primary")
        
        if btn_adicionar and novo_servico:
            emp["servicos"].append(novo_servico)
            st.rerun()
    
    if emp["servicos"]:
        tags_html = "".join([f"<span class='service-tag'>{s}</span>" for s in emp["servicos"]])
        st.markdown(tags_html, unsafe_allow_html=True)

# --- PÁGINA: CONCORRENTES (CADASTRO) ---
elif st.session_state.pagina == "cad":
    # ALTERADO: Nome simplificado
    st.title("👥 Concorrentes")
    with st.form("cad_concorrente"):
        col1, col2 = st.columns(2)
        n = col1.text_input("Nome do Concorrente")
        u = col1.text_input("URL do Site")
        i = col2.text_input("Instagram (arroba)")
        
        # ALTERADO: Adicionado parâmetro 'help' para a bolinha de interrogação com explicação
        a = col2.text_input(
            "ID/Nome na Ads Library", 
            help="Para obter esse dado, acesse a Biblioteca de Anúncios do Facebook, pesquise pelo concorrente e copie o nome exato da página ou o ID numérico que aparece nos filtros da URL."
        )
        
        if st.form_submit_button("Salvar Concorrente"):
            st.session_state.dados["concorrentes"].append({
                "nome": n, "url": u, "instagram": i, "ads_id": a, "analise_site": ""
            })
            st.success("Cadastrado com sucesso!")

# --- PÁGINA: VISÃO GERAL ---
elif st.session_state.pagina == "geral":
    st.title("📊 Painel de Comparação")
    if not st.session_state.dados["concorrentes"]:
        st.warning("Cadastre concorrentes primeiro na aba 'Concorrentes'.")
    else:
        df = pd.DataFrame(st.session_state.dados["concorrentes"])
        st.dataframe(df[["nome", "url", "instagram"]], use_container_width=True)

# --- PÁGINA: CONFRONTO DE SITES ---
elif st.session_state.pagina == "sites":
    st.title("🌐 Confronto de Proposta de Valor")
    concs = st.session_state.dados["concorrentes"]
    if concs:
        escolha = st.selectbox("Selecione o concorrente para comparar", [c["nome"] for c in concs])
        c_obj = next(c for c in concs if c["nome"] == escolha)
        
        if st.button(f"Analisar {escolha} vs Minha Empresa"):
            with st.spinner("Extraindo dados do site e comparando..."):
                downloaded = trafilatura.fetch_url(c_obj["url"])
                texto_concorrente = trafilatura.extract(downloaded)
                
                prompt = f"""
                Compare o site do concorrente abaixo com os serviços da minha empresa.
                Site do Concorrente ({c_obj['nome']}): {c_obj['url']}
                Conteúdo extraído: {texto_concorrente[:2500]}
                
                Responda em tópicos:
                1. O que eles oferecem que nós não oferecemos?
                2. Qual o tom de voz deles?
                3. Onde nossa empresa ganha deles tecnicamente?
                4. Sugestão de melhoria no nosso site para converter mais que eles.
                """
                resultado = consultar_ia(prompt)
                st.markdown(resultado)

# --- PÁGINA: SOCIAL ---
elif st.session_state.pagina == "social":
    st.title("📱 Análise de Presença e Copy")
    copy_concorrente = st.text_area("Cole aqui uma legenda ou anúncio do concorrente para análise")
    if st.button("Analisar Copy"):
        res = consultar_ia(f"Analise esta copy de um concorrente e me diga como posso criar uma versão superior para a minha empresa: {copy_concorrente}")
        st.markdown(res)

# --- PÁGINA: ADS ---
elif st.session_state.pagina == "ads":
    st.title("📢 Espionagem de Anúncios")
    for c in st.session_state.dados["concorrentes"]:
        st.subheader(f"🔍 {c['nome']}")
        url_ads = f"https://www.facebook.com/ads/library/?q={c['ads_id'] or c['nome']}&country=BR&media_type=all"
        st.link_button(f"Ver anúncios de {c['nome']} no Facebook", url_ads)

# --- PÁGINA: INSIGHTS (BATTLE CARDS) ---
elif st.session_state.pagina == "insights":
    st.title("💡 IA Battle Cards (Estratégia de Vendas)")
    if st.session_state.dados["concorrentes"]:
        conc_alvo = st.selectbox("Gerar Battle Card contra:", [c["nome"] for c in st.session_state.dados["concorrentes"]])
        
        if st.button("Gerar Card"):
            prompt = f"""
            Crie um 'Battle Card' de vendas para o meu time comercial.
            O objetivo é fechar contrato quando o cliente está em dúvida entre a minha empresa e o concorrente {conc_alvo}.
            
            Inclua:
            - Argumentos matadores (Why us?)
            - Como desqualificar o concorrente de forma ética.
            - Perguntas de implicação para fazer ao cliente.
            """
            st.markdown(consultar_ia(prompt))
    else:
        st.info("Adicione concorrentes para gerar cards estratégicos.")
