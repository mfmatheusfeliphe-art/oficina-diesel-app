import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

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

# --- CONEXÃO COM BANCO DE DADOS EM NUVEM (SUPABASE) ---
@st.cache_resource
def get_db_engine():
    db_url = st.secrets["postgres"]["url"]
    # Garante suporte a SSL no PostgreSQL do Supabase
    return create_engine(
        db_url,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True
    )

engine = get_db_engine()

def init_db():
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS estoque (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(100) UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                categoria VARCHAR(100) DEFAULT 'Outros',
                quantidade INTEGER NOT NULL DEFAULT 0,
                qtd_minima INTEGER NOT NULL DEFAULT 1,
                preco NUMERIC(10, 2) NOT NULL DEFAULT 0.0
            );
        '''))
        conn.commit()

init_db()

# --- TÍTULO PRINCIPAL ---
st.markdown('<div class="empresa-header">🚛 FLP TRUCK DIESEL</div>', unsafe_allow_html=True)
st.title("📦 Sistema de Controle de Estoque")
st.caption("Gestão de peças, componentes de injeção Common Rail e Arla 32")

# --- NAVEGAÇÃO DA BARRA LATERAL ---
st.sidebar.title("🔍 Menu")
menu = st.sidebar.radio("Selecione uma opção:", ["Visão Geral & Consulta", "Cadastrar Peça", "Movimentação (Entrada/Saída)"])

# --- LEITURA DE DADOS DA NUVEM ---
df = pd.read_sql("SELECT * FROM estoque ORDER BY id DESC", engine)

# --- OPÇÃO 1: VISÃO GERAL & CONSULTA ---
if menu == "Visão Geral & Consulta":
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

    busca = st.text_input("🔍 Buscar por Código, Nome ou Categoria:")
    
    if not df.empty:
        df_exibicao = df.copy()
        if busca:
            df_exibicao = df_exibicao[
                df_exibicao['codigo'].str.contains(busca, case=False, na=False) |
                df_exibicao['nome'].str.contains(busca, case=False, na=False) |
                df_exibicao['categoria'].str.contains(busca, case=False, na=False)
            ]
        
        df_exibicao['preco'] = df_exibicao['preco'].astype(float).map("R$ {:,.2f}".format)
        
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
                    with engine.connect() as conn:
                        query = text("""
                            INSERT INTO estoque (codigo, nome, categoria, quantidade, qtd_minima, preco)
                            VALUES (:codigo, :nome, :categoria, :quantidade, :qtd_minima, :preco)
                        """)
                        conn.execute(query, {
                            "codigo": codigo,
                            "nome": nome,
                            "categoria": categoria,
                            "quantidade": quantidade,
                            "qtd_minima": qtd_minima,
                            "preco": preco
                        })
                        conn.commit()
                    st.success(f"Peça '{nome}' cadastrada com sucesso na nuvem!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: O código '{codigo}' já pode estar cadastrado.")
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
            with engine.connect() as conn:
                res = conn.execute(text("SELECT quantidade FROM estoque WHERE codigo = :codigo"), {"codigo": cod_peca}).fetchone()
                qtd_atual = res[0]

                if "Entrada" in tipo_mov:
                    nova_qtd = qtd_atual + qtd_mov
                else:
                    nova_qtd = qtd_atual - qtd_mov

                if nova_qtd < 0:
                    st.error("Erro: A quantidade em estoque não pode ficar negativa.")
                else:
                    conn.execute(text("UPDATE estoque SET quantidade = :nova_qtd WHERE codigo = :codigo"), {
                        "nova_qtd": nova_qtd,
                        "codigo": cod_peca
                    })
                    conn.commit()
                    st.success("Estoque atualizado com sucesso na nuvem!")
                    st.rerun()
    else:
        st.info("Cadastre peças primeiro para poder realizar movimentações de entrada ou saída.")
