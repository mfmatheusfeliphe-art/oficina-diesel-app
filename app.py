import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão & Diagnóstico Diesel",
    page_icon="⚙️",
    layout="wide"
)
# --- OCULTAR MENU PADRÃO E APLICAR ASSINATURA ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
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
""", unsafe_allow_key=True)

# --- ASSINATURA NA BARRA LATERAL (SIDEBAR) ---
st.sidebar.markdown("""
    <div class="marca-registrada">
        ⚡ <b>Desenvolvido por:</b><br>
        <b>Matheus Feliphe</b><br>
        <i>Engenharia Mecânica</i><br>
        <span style="font-size:11px; color:#a0a0a0;">© 2026 - Todos os direitos reservados</span>
    </div>
""", unsafe_allow_key=True)
# --- CONEXÃO COM O BANCO DE DADOS (ESTOQUE) ---
def conectar_bd():
    conn = sqlite3.connect("estoque_diesel.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pecas (
            codigo TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            aplicacao TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            estoque_minimo INTEGER NOT NULL,
            preco_custo REAL NOT NULL
        )
    """)
    conn.commit()
    return conn

conn = conectar_bd()

def listar_pecas():
    return pd.read_sql_query("SELECT * FROM pecas", conn)

def cadastrar_peca(codigo, nome, aplicacao, quantidade, estoque_minimo, preco_custo):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pecas (codigo, nome, aplicacao, quantidade, estoque_minimo, preco_custo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (codigo.upper(), nome, aplicacao, quantidade, estoque_minimo, preco_custo))
        conn.commit()
        return True, "Peça cadastrada com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"O código '{codigo}' já existe no estoque!"

def atualizar_quantidade(codigo, qtd_mudanca, tipo="saida"):
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, nome, estoque_minimo FROM pecas WHERE codigo = ?", (codigo,))
    res = cursor.fetchone()
    if not res:
        return False, "Peça não encontrada."
    
    qtd_atual, nome, est_min = res
    if tipo == "saida":
        if qtd_mudanca > qtd_atual:
            return False, f"Estoque insuficiente! Atual: {qtd_atual}"
        nova_qtd = qtd_atual - qtd_mudanca
    else:
        nova_qtd = qtd_atual + qtd_mudanca

    cursor.execute("UPDATE pecas SET quantidade = ? WHERE codigo = ?", (nova_qtd, codigo))
    conn.commit()
    
    msg = f"Estoque atualizado! Nova quantidade de '{nome}': {nova_qtd} un."
    if tipo == "saida" and nova_qtd <= est_min:
        msg += f" ⚠️ ALERTA: Atingiu o estoque mínimo ({est_min})!"
    return True, msg

# --- BANCO DE DADOS DE DIAGNÓSTICOS ---
DIAGNOSTICOS = {
    "P0299 - Pressão de Sobrealimentação do Turbo Insuficiente": {
        "sistema": "Admissão / Ar",
        "sintomas": ["Falta de potência", "Fumaça preta em aceleração", "Veículo em modo de emergência"],
        "causas_comuns": [
            "Vazamento em mangueiras do intercooler ou mangote rasgado",
            "Atuador da geometria variável (VGT) travado ou com falha vácuo/elétrica",
            "Sensor de pressão do coletor (MAP) sujo com fuligem ou defeituoso",
            "Obstrução no filtro de ar ou catalisador/DPF entupido"
        ],
        "passos_teste": [
            {"passo": 1, "acao": "Inspeção Visual / Estanqueidade", "detalhe": "Verifique mangotes do intercooler e braçadeiras quanto a vazamentos de ar ou trincas."},
            {"passo": 2, "acao": "Teste do Sensor MAP", "detalhe": "Com a chave ligada (motor desligado), a leitura da pressão atmosférica no scanner deve ser de ~1.0 bar (100 kPa). Com o multímetro, cheque o sinal de 0.5V a 4.5V no pino de resposta."},
            {"passo": 3, "acao": "Atuador da Geometria (VGT)", "detalhe": "Execute o teste de atuadores via scanner. Verifique se a haste da geometria se move livremente sem travamentos mecânicos."},
            {"passo": 4, "acao": "Contrapressão de Escape", "detalhe": "Meça a contrapressão antes do DPF/Catalisador. Valores acima de 0.2 bar em lenta indicam obstrução no pós-tratamento."}
        ]
    },
    "P204F - Sistema de Injeção de Redutor (Arla 32) - Desempenho": {
        "sistema": "Pós-Tratamento (SCR / Arla 32)",
        "sintomas": ["Luz da injeção acesa", "Alerta de limitação de torque (Limp Mode)", "Mensagem no painel de contagem regressiva de km"],
        "causas_comuns": [
            "Cristalização do Arla 32 no dosador ou na tubulação",
            "Baixa pressão da bomba de Arla 32 (deve estabilizar em ~5.0 a 6.0 bar)",
            "Filtro da unidade de bombeamento entupido",
            "Sensor de temperatura de escape com leitura incorreta (simulando motor frio)"
        ],
        "passos_teste": [
            {"passo": 1, "acao": "Teste de Dosagem e Cristalização", "detalhe": "Remova o injetor de Arla 32 do escape sem desligar a tubulação e faça o teste de dosagem via scanner. Observe o padrão do spray e o volume injetado."},
            {"passo": 2, "acao": "Pressão de Linha", "detalhe": "Acompanhe pelo scanner se a pressão do Arla atinge ~5.0 a 6.0 bar no ciclo de purga/estabilização."},
            {"passo": 3, "acao": "Qualidade do Arla 32", "detalhe": "Utilize um refratômetro para medir a concentração do líquido. O valor correto deve ser rigorosamente 32.5% (variação tolerada: 31.8% a 33.2%)."},
            {"passo": 4, "acao": "Alimentação Elétrica da Unidade", "detalhe": "Verifique fusíveis, relés e tensão de alimentação (12V/24V) na bomba de Arla e no aquecedor da mangueira."}
        ]
    },
    "P0087 - Pressão da Linha de Combustível/Sistema Muito Baixa": {
        "sistema": "Injeção Common Rail",
        "sintomas": ["Motor apaga em carga/aceleração", "Dificuldade de partida a quente", "Falha de combustão (misfire)"],
        "causas_comuns": [
            "Filtro de combustível/separador (Racor) obstruído ou com entrada de ar",
            "Válvula reguladora de pressão (DRV / M-Prop) travada ou com anel de vedação danificado",
            "Retorno excessivo dos injetores (injetores 'lavando')",
            "Bomba de alta pressão com desgaste interno ou falha na bomba pré-alimentadora"
        ],
        "passos_teste": [
            {"passo": 1, "acao": "Linha de Baixa Pressão", "detalhe": "Instale um manômetro no filtro primário. Verifique se a pressão de alimentação (linha de baixa) está dentro do especificado pelo fabricante."},
            {"passo": 2, "acao": "Teste de Retorno dos Injetores", "detalhe": "Execute o teste das provetas na linha de retorno dos injetores em marcha lenta e sob partida. Diferenças discrepantes entre cilindros indicam retorno excessivo."},
            {"passo": 3, "acao": "Válvula de Alívio do Rail", "detalhe": "Verifique se há vazamento no tubo de retorno da válvula mecânica de limitação de pressão do tubo Rail enquanto o motor funciona."},
            {"passo": 4, "acao": "Válvula Dosadora (M-Prop)", "detalhe": "Meça a resistência da solenoide (geralmente entre 2.0 e 3.5 Ohms) e inspecione micro-almas de sujeira nas vedações O-ring."}
        ]
    }
}

# --- MENU PRINCIPAL DA APLICAÇÃO ---
st.sidebar.title("🛠️ Oficina Diesel Pro")
modulo = st.sidebar.radio(
    "Selecione o Módulo:",
    ["📋 Controle de Estoque", "🔍 Assistente de Diagnóstico", "⚡ Calculadora de Sensores"]
)

df_estoque = listar_pecas()

# ==========================================
# MÓDULO 1: CONTROLE DE ESTOQUE
# ==========================================
if modulo == "📋 Controle de Estoque":
    st.title("📦 Controle de Estoque Inteligente")
    
    aba_estoque, aba_mov, aba_cad, aba_alerta = st.tabs([
        "📋 Consultar Estoque", "📦 Dar Entrada/Saída", "➕ Cadastrar Peça", "🚨 Alertas de Reposição"
    ])

    with aba_estoque:
        busca = st.text_input("🔍 Buscar por nome, código ou aplicação (ex: Iveco, Filtro, Sensor):")
        if not df_estoque.empty:
            if busca:
                df_filtrado = df_estoque[
                    df_estoque['nome'].str.contains(busca, case=False) |
                    df_estoque['codigo'].str.contains(busca, case=False) |
                    df_estoque['aplicacao'].str.contains(busca, case=False)
                ]
            else:
                df_filtrado = df_estoque
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.info("Nenhuma peça cadastrada ainda.")

    with aba_mov:
        if df_estoque.empty:
            st.warning("Cadastre peças primeiro.")
        else:
            lista_codigos = df_estoque['codigo'].tolist()
            peca_sel = st.selectbox("Selecione a Peça:", options=lista_codigos, 
                                    format_func=lambda x: f"{x} - {df_estoque[df_estoque['codigo'] == x]['nome'].values[0]}")
            tipo_mov = st.radio("Operação:", ["Saída (Uso em OS)", "Entrada (Compra)"])
            qtd = st.number_input("Quantidade:", min_value=1, value=1, step=1)
            
            if st.button("Confirmar Movimentação"):
                tipo_str = "saida" if "Saída" in tipo_mov else "entrada"
                sucesso, msg = atualizar_quantidade(peca_sel, qtd, tipo=tipo_str)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

    with aba_cad:
        with st.form("form_cad"):
            c1, c2 = st.columns(2)
            with c1:
                codigo = st.text_input("Código da Peça (ex: FIL-001):")
                nome = st.text_input("Nome da Peça:")
                aplicacao = st.text_input("Aplicação (ex: Iveco Daily 3.0):")
            with c2:
                quantidade = st.number_input("Qtd Inicial:", min_value=0, value=5)
                est_min = st.number_input("Estoque Mínimo:", min_value=1, value=2)
                preco = st.number_input("Preço de Custo (R$):", min_value=0.0, value=100.0)
            if st.form_submit_button("Salvar Peça"):
                if codigo and nome:
                    suc, msg = cadastrar_peca(codigo, nome, aplicacao, quantidade, est_min, preco)
                    if suc:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Preencha Código e Nome.")

    with aba_alerta:
        if not df_estoque.empty:
            df_critico = df_estoque[df_estoque['quantidade'] <= df_estoque['estoque_minimo']]
            if df_critico.empty:
                st.success("🎉 Todas as peças estão em nível seguro de estoque!")
            else:
                st.warning("Peças que precisam de reposição imediata:")
                st.dataframe(df_critico, use_container_width=True)

# ==========================================
# MÓDULO 2: ASSISTENTE DE DIAGNÓSTICO
# ==========================================
elif modulo == "🔍 Assistente de Diagnóstico":
    st.title("🔍 Assistente de Diagnóstico Diesel")
    st.caption("Roteiro sequencial de testes de campo para diagnóstico preciso.")

    opcao_busca = st.radio("Modo de Busca:", ["Por Código DTC", "Por Sintoma"])

    if opcao_busca == "Por Código DTC":
        codigo_sel = st.selectbox("Selecione o Código de Falha:", list(DIAGNOSTICOS.keys()))
        dados = DIAGNOSTICOS[codigo_sel]

        st.markdown(f"### 📌 {codigo_sel}")
        st.text(f"Sistema: {dados['sistema']}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ⚠️ Sintomas")
            for s in dados["sintomas"]:
                st.markdown(f"- {s}")
        with col2:
            st.markdown("#### 🛠️ Causas Prováveis")
            for c in dados["causas_comuns"]:
                st.markdown(f"- {c}")

        st.markdown("#### 📋 Passos de Teste")
        for passo in dados["passos_teste"]:
            with st.expander(f"Passo {passo['passo']}: {passo['acao']}"):
                st.write(passo["detalhe"])
                st.checkbox("Concluído", key=f"dtc_{codigo_sel}_{passo['passo']}")
    else:
        sintoma_input = st.text_input("Digite o sintoma (ex: fumaça, Arla, sem potência):")
        if sintoma_input:
            for dtc, dados in DIAGNOSTICOS.items():
                texto = dtc + " " + dados["sistema"] + " " + " ".join(dados["sintomas"])
                if sintoma_input.lower() in texto.lower():
                    with st.expander(f"🔴 {dtc}"):
                        st.write("**Sintomas:**", ", ".join(dados["sintomas"]))
                        st.write("**Causas:**", ", ".join(dados["causas_comuns"]))

# ==========================================
# MÓDULO 3: CALCULADORA DE SENSORES
# ==========================================
elif modulo == "⚡ Calculadora de Sensores":
    st.title("⚡ Calculadora de Sinais e Sensores")
    st.caption("Validação de leituras de multímetro e osciloscópio no pátio.")

    tipo_sensor = st.selectbox("Selecione o Componente:", [
        "1. Sensor de Pressão Analógico (MAP, Rail, Arla)",
        "2. Sensor de Temperatura NTC (Escape/DPF, Água)",
        "3. Teste de Injetor Common Rail (Solenoide/Piezo)",
        "4. Sinal PWM de Atuadores (M-Prop, VGT)"
    ])

    if "1. Sensor de Pressão" in tipo_sensor:
        st.subheader("📊 Resposta Tensão vs. Pressão")
        col1, col2 = st.columns(2)
        with col1:
            p_min = st.number_input("Pressão Mínima (Bar):", value=0.0)
            p_max = st.number_input("Pressão Máxima (Bar):", value=2000.0)
        with col2:
            p_medida = st.number_input("Pressão Lida no Scanner (Bar):", value=1350.0)
            v_ref = st.number_input("Tensão de Alimentação Medida (V):", value=5.0)

        if p_max > p_min:
            prop = (p_medida - p_min) / (p_max - p_min)
            prop = max(0.0, min(1.0, prop))
            tensao_esp = 0.5 + (prop * 4.0) * (v_ref / 5.0)
            st.success(f"🎯 **Sinal Esperado no Multímetro:** `{tensao_esp:.2f} V` no pino de resposta.")

    elif "2. Sensor de Temperatura" in tipo_sensor:
        st.subheader("🌡️ Tabela Dinâmica NTC")
        temp = st.slider("Temperatura Estimada (°C):", min_value=-10, max_value=600, value=25)
        if temp <= 25:
            r, v = "2.20 kΩ a 2.80 kΩ", "3.2 V a 3.8 V"
        elif temp <= 80:
            r, v = "300 Ω a 400 Ω", "1.0 V a 1.4 V"
        else:
            r, v = "30 Ω a 100 Ω", "0.1 V a 0.4 V"
        c1, c2 = st.columns(2)
        c1.metric("Resistência Esperada", r)
        c2.metric("Tensão no Conector", v)

    elif "3. Teste de Injetor" in tipo_sensor:
        st.subheader("💉 Parâmetros de Resistência")
        tech = st.radio("Tecnologia:", ["Solenoide Indutivo", "Piezoelétrico"])
        if "Solenoide" in tech:
            st.success("✅ **Resistência da Bobina:** `0.2 Ω a 0.8 Ω`")
            st.info("O isolamento para a carcaça metálica deve ser Infinito (O.L).")
        else:
            st.success("✅ **Resistência Esperada:** `150 kΩ a 200 kΩ`")

    elif "4. Sinal PWM" in tipo_sensor:
        st.subheader("🔄 Duty Cycle vs. Tensão Média")
        duty = st.slider("Duty Cycle (%):", 0, 100, 35)
        v_bat = st.number_input("Tensão de Bateria (V):", value=24.0)
        v_medio = v_bat * (duty / 100.0)
        st.success(f"🎯 **Tensão Média Estimada no Multímetro (DC):** `{v_medio:.2f} V`")