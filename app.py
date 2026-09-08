import streamlit as st
import pandas as pd
import sqlite3

# Configuração da página
st.set_page_config(
    page_title="FLP TRUCK DIESEL - Controle de Estoque",
    page_icon="🚛",
    layout="wide"
)

# --- ESTILO CSS E ASSINATURA ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Ajuste de cor dos cartões de métricas para alta legibilidade */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00a8e8;
        border-top: 1px solid #e0e0e0;
        border-right: 1px solid #e0e0e0;
        border-bottom: 1px solid #e0e0e0;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    [data-testid="stMetricLabel"] {
        color: #31333F !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: #00a8e8 !important;
        font-weight: bold !important;
    }
    
    .empresa-header {
        font-size: 28px;
        font-weight: 800;
        color: #00a8e8;
        letter-spacing: 1.5px;
        margin-bottom: 0px;
    }
    
    .marca-registrada {
        padding: 12px;
        background-color: #1e222d;
        border-radius: 8px;
        border-left: 4px solid #00a8e8;
        color: #ffffff;
        font-size: 13px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
    <div style="font-size: 18px; font-weight: bold; color: #00a8e8; text-align: center; margin-bottom: 15px;">
        🚛 FLP TRUCK DIESEL
    </div>
    <div class="marca-registrada">
        ⚡ <b>Desenvolvido por:</b><br>
        <b>Matheus Feliphe</b><br>
        <i>Engenharia Mecânica</i><br>
        <span style="font-size:11px; color:#a0a0a0;">© 2026 - Todos os direitos reservados</span>
    </div>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO BANCO DE DADOS LOCAL ---
DB_NAME = 'estoque_diesel.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT DEFAULT 'Outros',
            quantidade INTEGER NOT NULL DEFAULT 0,
            qtd_minima INTEGER NOT NULL DEFAULT 1,
            preco REAL NOT NULL DEFAULT 0.0
        )
    ''')
    
    c.execute("PRAGMA table_info(estoque)")
    colunas = [coluna[1] for coluna in c.fetchall()]
    
    if 'categoria' not in colunas:
        c.execute("ALTER TABLE estoque ADD COLUMN categoria TEXT DEFAULT 'Outros'")
    if 'qtd_minima' not in colunas:
        c.execute("ALTER TABLE estoque ADD COLUMN qtd_minima INTEGER DEFAULT 1")
        
    conn.commit()
    conn.close()

init_db()

# --- TÍTULO PRINCIPAL ---
st.markdown('<div class="empresa-header">🚛 FLP TRUCK DIESEL</div>', unsafe_allow_html=True)
st.title("📦 Sistema de Controle de Estoque")
st.caption("Gestão de peças, componentes de injeção Common Rail e Arla 32")

# --- NAVEGAÇÃO DA BARRA LATERAL ---
st.sidebar.title("🔍 Menu")
menu = st.sidebar.radio("Selecione uma opção:", ["Visão Geral & Consulta", "Cadastrar Peça", "Movimentação (Entrada/Saída)"])

# --- BANCO DE DADOS: LEITURA DE DADOS ---
conn = get_connection()
df = pd.read_sql_query("SELECT * FROM estoque", conn)
conn.close()

# --- OPÇÃO 1: VISÃO GERAL & CONSULTA ---
if menu == "Visão Geral & Consulta":
    # Métricas de topo
    if not df.empty:
        total_itens = len(df)
        total_pecas = df['quantidade'].sum()
        valor_total = (df['quantidade'] * df['preco']).sum()
        alertas = df[df['quantidade'] <= df['qtd_minima']]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tipos de Peças", total_itens)
        col2.metric("Total em Estoque (Un)", total_pecas)
        col3.metric("Valor em Estoque", f"R$ {valor_total:,.2f}")
        col4.metric("Itens com Estoque Baixo", len(alertas))

        if len(alertas) > 0:
            st.warning(f"⚠️ **Atenção:** Existem {len(alertas)} item(ns) com estoque no limite crítico ou zerado!")
    
    st.markdown("---")
    st.subheader("📋 Tabela de Peças Cadastradas")

    # Filtro de busca
    busca = st.text_input("🔍 Buscar por Código, Nome ou Categoria:")
    
    if not df.empty:
        df_exibicao = df.copy()
        if busca:
            df_exibicao = df_exibicao[
                df_exibicao['codigo'].str.contains(busca, case=False, na=False) |
                df_exibicao['nome'].str.contains(busca, case=False, na=False) |
                df_exibicao['categoria'].str.contains(busca, case=False, na=False)
            ]
        
        # Formatação de preços
        df_exibicao['preco'] = df_exibicao['preco'].map("R$ {:,.2f}".format)
        
        st.dataframe(
            df_exibicao.rename(columns={
                'codigo': 'Código',
                'nome': 'Descrição da Peça',
                'categoria': 'Categoria',
                'quantidade': 'Qtd Atual',
                'qtd_minima': 'Qtd Mínima',
                'preco': 'Preço Un.'
            }),
            use_container_width=True
        )
    else:
        st.info("Nenhuma peça cadastrada até o momento. Utilize o menu lateral para cadastrar novos itens.")

# --- OPÇÃO 2: CADASTRAR PEÇA ---
elif menu == "Cadastrar Peça":
    st.subheader("➕ Cadastrar Nova Peça no Estoque")

    with st.form("form_cadastro_peca"):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código do Fabricante / Referência *")
            nome = st.text_input("Nome / Descrição da Peça *")
            categoria = st.selectbox("Categoria *", [
                "Injeção Common Rail",
                "Arla 32 / SCR / DPF",
                "Filtros & Lubrificantes",
                "Sensores & Atuadores",
                "Reparos & Juntas",
                "Outros"
            ])
        
        with col2:
            quantidade = st.number_input("Quantidade Inicial em Estoque", min_value=0, step=1, value=0)
            qtd_minima = st.number_input("Estoque Mínimo (Alerta de Compra)", min_value=1, step=1, value=2)
            preco = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f", value=0.0)

        submitted = st.form_submit_button("Salvar Peça")

        if submitted:
            if codigo and nome:
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO estoque (codigo, nome, categoria, quantidade, qtd_minima, preco)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (codigo, nome, categoria, quantidade, qtd_minima, preco))
                    conn.commit()
                    conn.close()
                    st.success(f"Peça '{nome}' cadastrada com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"Erro: O código '{codigo}' já está cadastrado em outra peça.")
            else:
                st.warning("Preencha os campos obrigatórios (Código e Descrição).")

# --- OPÇÃO 3: MOVIMENTAÇÃO (ENTRADA/SAÍDA) ---
elif menu == "Movimentação (Entrada/Saída)":
    st.subheader("🔄 Atualizar Quantidade em Estoque")

    if not df.empty:
        pecas_dict = {f"{row['codigo']} - {row['nome']} (Atual: {row['quantidade']} un)": row['codigo'] for _, row in df.iterrows()}
        peca_selecionada = st.selectbox("Selecione a Peça:", list(pecas_dict.keys()))
        cod_peca = pecas_dict[peca_selecionada]

        col1, col2 = st.columns(2)
        with col1:
            tipo_mov = st.radio("Tipo de Movimentação:", ["Entrada (Adicionar ao estoque)", "Saída (Baixa por aplicação/venda)"])
        with col2:
            qtd_mov = st.number_input("Quantidade da Movimentação", min_value=1, step=1, value=1)

        if st.button("Confirmar Movimentação"):
            conn = get_connection()
            c = conn.cursor()
            
            c.execute("SELECT quantidade FROM estoque WHERE codigo = ?", (cod_peca,))
            qtd_atual = c.fetchone()[0]

            if "Entrada" in tipo_mov:
                nova_qtd = qtd_atual + qtd_mov
            else:
                nova_qtd = qtd_atual - qtd_mov

            if nova_qtd < 0:
                st.error("Erro: A quantidade em estoque não pode ficar negativa.")
            else:
                c.execute("UPDATE estoque SET quantidade = ? WHERE codigo = ?", (nova_qtd, cod_peca))
                conn.commit()
                conn.close()
                st.success("Estoque atualizado com sucesso!")
                st.rerun()
    else:
        st.info("Cadastre peças primeiro para poder realizar movimentações de entrada ou saída.")