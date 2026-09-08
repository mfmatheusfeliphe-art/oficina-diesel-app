import streamlit as st
import pandas as pd
import sqlite3

# Configuração da página
st.set_page_config(
    page_title="Gestão & Diagnóstico Diesel",
    page_icon="⚙️",
    layout="wide"
)

# --- ESTILO E ASSINATURA ---
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
""", unsafe_allow_html=True)

st.sidebar.markdown("""
    <div class="marca-registrada">
        ⚡ <b>Desenvolvido por:</b><br>
        <b>Matheus Feliphe</b><br>
        <i>Engenharia Mecânica</i><br>
        <span style="font-size:11px; color:#a0a0a0;">© 2026 - Todos os direitos reservados</span>
    </div>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS DE DIAGNÓSTICOS COMPLETO ---
DIAGNOSTICOS = {
    # -------------------------------------------------------------------------
    # VW 24.280 (MOTOR MAN D08 36)
    # -------------------------------------------------------------------------
    "VW 24.280 - Sensor de Pressão do Rail (MAN D08)": {
        "veiculo": "VW Constellation 24.280",
        "motor": "MAN D08 36 (6 Cilindros - EGR)",
        "modulo_ecu": "Bosch EDC17 C55",
        "sistema": "Injeção Common Rail",
        "sintomas": [
            "Motor corta em aceleração (falta de potência)",
            "Dificuldade ou não pega na partida",
            "Código de falha P0087 (Pressão Baixa) ou P0088 (Pressão Alta)"
        ],
        "pinout": {
            "Pino 1": "Massa de Sensores (GND) -> Conecta ao Pino A58 da ECU",
            "Pino 2": "Sinal de Tensão (0.5V a 4.5V) -> Conecta ao Pino A41 da ECU",
            "Pino 3": "Alimentação +5V VCC -> Conecta ao Pino A42 da ECU"
        },
        "valores_referencia": {
            "Tensão com Chave Ligada (Motor Parado)": "0.50V ± 0.05V (Pressão 0 bar)",
            "Tensão em Marcha Lenta (~600 RPM)": "1.30V a 1.50V (~350 a 400 bar)",
            "Tensão em Carga Máxima": "Até 4.20V (~1600 bar)",
            "Resistência de Isolamento": "OL (Infinita) para a carcaça/massa do motor"
        ],
        "passos_teste": [
            {
                "passo": 1,
                "acao": "Teste de Alimentação e Massa",
                "detalhe": "Chave ligada. Meça com multímetro entre Pino 3 (+5V) e Pino 1 (Massa). Deve indicar 5.0V cravados. Se não houver 5V, verifique chicote ou linha de 5V da ECU.",
                "verificacao": "O multímetro deve indicar exatamente 5.0V com a chave ligada."
            },
            {
                "passo": 2,
                "acao": "Teste de Sinal em Repouso",
                "detalhe": "Com o conector plugado no sensor (use agulhas de teste), meça entre Pino 2 (Sinal) e Pino 1 (Massa). Com a chave ligada e motor parado, a leitura OBRIGATORIAMENTE deve ser 0.50V.",
                "verificacao": "Sinal estável em 0.50V confirma sensor zerado e calibrado."
            },
            {
                "passo": 3,
                "acao": "Teste Dinâmico na Partida/Marcha Lenta",
                "detalhe": "Dê partida no motor. O sinal deve subir para aproximadamente 1.3V a 1.5V. Se o sinal não passar de 0.8V na partida, a pressão mecânica do Rail está insuficiente para liberar a partida na ECU.",
                "verificacao": "Tensão deve acompanhar a elevação da rotação sem quedas bruscas."
            }
        ]
    },
    "VW 24.280 - Válvula Dosadora M-Prop / ZME (Bomba CP3.4)": {
        "veiculo": "VW Constellation 24.280",
        "motor": "MAN D08 36",
        "modulo_ecu": "Bosch EDC17 C55",
        "sistema": "Injeção Common Rail - Alimentação de Alta",
        "sintomas": [
            "Motor oscila marcha lenta (oscilação de RPM)",
            "Pressão do Rail desgovernada",
            "Entra em Modo de Emergência (Limp Mode) sob carga"
        ],
        "pinout": {
            "Pino 1": "Alimentação / Sinal PWM (ECU Pino A09)",
            "Pino 2": "Sinal PWM / Retorno (ECU Pino A10)"
        ],
        "valores_referencia": {
            "Resistência Elétrica da Bobina": "2.8 Ω a 3.5 Ω a 20°C",
            "Isolamento para Carcaça": "OL (Infinita)",
            "Sinal de Controle (Osciloscópio)": "Sinal PWM em frequência de ~180 Hz a 200 Hz",
            "Duty Cycle (Marcha Lenta)": "Aproximadamente 38% a 45% (Normalmente Aberta)"
        ],
        "passos_teste": [
            {
                "passo": 1,
                "acao": "Medição de Resistência Ôhmica",
                "detalhe": "Desconecte a M-Prop. Meça a resistência entre os Pinos 1 e 2 do componente. Valor esperado: 2.8 Ω a 3.5 Ω. Valores abaixo indicam curto interno; acima indicam bobina interrompida.",
                "verificacao": "Leitura entre 2.8 Ω e 3.5 Ω confirma integridade da bobina."
            },
            {
                "passo": 2,
                "acao": "Teste de Curto para Massa",
                "detalhe": "Meça a resistência entre qualquer pino do conector da M-Prop e o corpo metálico da bomba de alta. Deve marcar OL (sem continuidade).",
                "verificacao": "Leitura OL confirma ausência de curto com a massa."
            },
            {
                "passo": 3,
                "acao": "Análise Mecânica (Limalha)",
                "detalhe": "Remova a M-Prop (2 parafusos Torx) e inspecione a micro-peneira na ponta da válvula. Se houver partículas prateadas/douradas (limalha), a bomba de alta está em processo de destruição mecânica.",
                "verificacao": "Peneira limpa e sem resíduos metálicos."
            }
        ]
    },
    "VW 24.280 - Válvula EGR (Atuador Elétrico e Sensor de Posição)": {
        "veiculo": "VW Constellation 24.280",
        "motor": "MAN D08 36 (Sistema EGR)",
        "modulo_ecu": "Bosch EDC17 C55",
        "sistema": "Gestão de Emissões / Controle de Oxigênio",
        "sintomas": [
            "Fumaça preta excessiva no escape",
            "Perda brusca de potência e alto consumo",
            "Códigos P0401 (Fluxo Insuficiente) ou P0402 (Fluxo Excessivo)"
        ],
        "pinout": {
            "Pino 1": "Massa do Sensor de Posição",
            "Pino 2": "Sinal do Sensor de Posição (Potenciômetro)",
            "Pino 3": "Alimentação +5V do Sensor de Posição",
            "Pino 4": "Motor DC / Atuador EGR (+)",
            "Pino 5": "Motor DC / Atuador EGR (-)"
        ],
        "valores_referencia": {
            "Resistência do Motor do Atuador (Pinos 4 e 5)": "2.0 Ω a 6.0 Ω",
            "Sinal de Posição com EGR Fechada (Repouso)": "~0.8V a 1.0V",
            "Sinal de Posição com EGR Totalmente Aberta": "~4.0V a 4.5V"
        ],
        "passos_teste": [
            {
                "passo": 1,
                "acao": "Teste de Trancamento Mecânico / Carbonização",
                "detalhe": "Em veículos com alta quilometragem, a crosta de fuligem/óleo trava a borboleta interna da EGR. Remova o duto e confirme manualmente se a borboleta retorna suavemente pela força da mola.",
                "verificacao": "Movimento livre com retorno automático completo."
            },
            {
                "passo": 2,
                "acao": "Medição do Motor do Atuador",
                "detalhe": "Desconecte o soquete de 5 pinos. Meça com multímetro a resistência entre Pinos 4 e 5. Se estiver em curto (< 0.5 Ω) ou aberta (OL), o motor interno queimou a bobina.",
                "verificacao": "Resistência entre 2.0 Ω e 6.0 Ω indica motor elétrico saudável."
            },
            {
                "passo": 3,
                "acao": "Teste de Resposta do Potenciômetro de Posição",
                "detalhe": "Com chave ligada, monitore a tensão do Pino 2 (Sinal). Mova a haste manualmente (ou via scanner na função de atuadores): a voltagem deve subir de forma contínua sem saltos ou interrupções.",
                "verificacao": "Variação linear de tensão entre 0.8V e 4.5V."
            }
        ]
    }
}

# --- FUNÇÃO DE BANCO DE DADOS LOCAL (ESTOQUE) ---
def init_db():
    conn = sqlite3.connect('estoque_diesel.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nome TEXT,
            quantidade INTEGER,
            preco REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- NAVEGAÇÃO DO APLICATIVO ---
st.sidebar.title("🔍 Navegação")
menu = st.sidebar.radio("Ir para:", ["Assistente de Diagnóstico", "Controle de Estoque"])

# --- ABA 1: ASSISTENTE DE DIAGNÓSTICO ---
if menu == "Assistente de Diagnóstico":
    st.title("🛠️ Assistente de Diagnóstico Técnico Diesel")
    st.subheader("Base de Conhecimento e Parâmetros de Pátio")

    opcao_selecionada = st.selectbox(
        "Selecione o Diagnóstico / Componente:",
        list(DIAGNOSTICOS.keys())
    )

    dados = DIAGNOSTICOS[opcao_selecionada]

    st.markdown("---")
    st.header(f"📌 {opcao_selecionada}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Veículo:** {dados.get('veiculo', 'N/A')}")
        st.markdown(f"**Motor:** {dados.get('motor', 'N/A')}")
    with col2:
        st.markdown(f"**Módulo ECU:** {dados.get('modulo_ecu', 'N/A')}")
        st.markdown(f"**Sistema:** {dados.get('sistema', 'N/A')}")

    st.markdown("### ⚠️ Sintomas Comuns")
    for sintoma in dados.get("sintomas", []):
        st.write(f"- {sintoma}")

    st.markdown("### 🔌 Pinout / Conectores")
    for pino, desc in dados.get("pinout", {}).items():
        st.write(f"- **{pino}:** {desc}")

    st.markdown("### 📊 Valores de Referência")
    for param, val in dados.get("valores_referencia", {}).items():
        st.write(f"- **{param}:** `{val}`")

    st.markdown("### 🛠️ Roteiro de Testes Passo a Passo")
    for passo in dados.get("passos_teste", []):
        with st.expander(f"Passo {passo['passo']}: {passo['acao']}"):
            st.write(passo['detalhe'])
            st.info(f"**Como verificar se deu certo:** {passo['verificacao']}")

# --- ABA 2: CONTROLE DE ESTOQUE ---
elif menu == "Controle de Estoque":
    st.title("📦 Controle de Estoque da Oficina")
    
    conn = sqlite3.connect('estoque_diesel.db')
    df = pd.read_sql_query("SELECT * FROM estoque", conn)
    conn.close()

    st.dataframe(df, use_container_width=True)

    st.markdown("### Cadastrar Nova Peça")
    with st.form("form_estoque"):
        cod = st.text_input("Código da Peça")
        nome = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade", min_value=0, step=1)
        preco = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Salvar Peça")

        if submitted:
            if cod and nome:
                try:
                    conn = sqlite3.connect('estoque_diesel.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO estoque (codigo, nome, quantidade, preco) VALUES (?, ?, ?, ?)",
                              (cod, nome, qtd, preco))
                    conn.commit()
                    conn.close()
                    st.success("Peça cadastrada com sucesso!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Erro: Código de peça já existe no sistema.")
            else:
                st.warning("Preencha todos os campos obrigatórios.")