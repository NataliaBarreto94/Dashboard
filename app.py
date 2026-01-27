import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Dashboard - AVP - Manutenção - Processo",
    layout="wide"
)

# =====================================================
# PALETA
# =====================================================
AMARELO = "#f1c40f"
PRETO = "#0e1117"
CINZA_ESCURO = "#1c1f26"
VERDE = "#1dd268"

CORES_STATUS = {
    "Confirmada": VERDE,
    "Em aberto": AMARELO
}

# =====================================================
# CSS
# =====================================================
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    background-color: {PRETO};
    color: white;
}}
[data-testid="metric-container"] {{
    background-color: {CINZA_ESCURO};
    padding: 15px;
    border-radius: 10px;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# CAMINHOS
# =====================================================
BASE = r"C:\\Users\\Forno\\Desktop\\IW28"
CAMINHO_IW28 = os.path.join(BASE, "IW28.xlsx")
CAMINHO_IW47 = os.path.join(BASE, "IW47.xlsx")
CAMINHO_SPLAN = os.path.join(BASE, "SPLAN.xlsx")
CAMINHO_IW38 = os.path.join(BASE, "IW38.xlsx")
PASTA_FOTOS = BASE

# =====================================================
# LOADERS
# =====================================================
@st.cache_data(ttl=300)
def carregar_iw28():
    df = pd.read_excel(CAMINHO_IW28)
    df.columns = [c.strip() for c in df.columns]
    df["Conclusão desejada"] = pd.to_datetime(df["Conclusão desejada"], errors="coerce")
    df["Criado em"] = pd.to_datetime(df["Criado em"], errors="coerce")
    df["Encerram.por data"] = pd.to_datetime(df["Encerram.por data"], errors="coerce")
    return df

@st.cache_data(ttl=300)
def carregar_iw47():
    df = pd.read_excel(CAMINHO_IW47)
    df.columns = [c.strip() for c in df.columns]
    df["Data de lançamento"] = pd.to_datetime(df["Data de lançamento"], errors="coerce")
    df["Minutos"] = pd.to_numeric(df["Trabalho real"], errors="coerce")
    df["Horas"] = df["Minutos"] / 60
    return df.dropna(subset=["Nome do empregado", "Horas", "Data de lançamento"])

@st.cache_data(ttl=300)
def carregar_splan():
    df = pd.read_excel(CAMINHO_SPLAN)
    df.columns = [c.strip() for c in df.columns]
    df["Data da Investigação"] = pd.to_datetime(df["Data da Investigação"], errors="coerce")
    df["Mês"] = df["Data da Investigação"].dt.to_period("M").astype(str)
    return df

@st.cache_data(ttl=300)
def carregar_iw38():
    df = pd.read_excel(CAMINHO_IW38)
    df.columns = [c.strip() for c in df.columns]

    df["Data fim real da ordem"] = pd.to_datetime(
        df["Data fim real da ordem"], errors="coerce"
    )

    df["Custos totais plan."] = pd.to_numeric(
        df["Custos totais plan."], errors="coerce"
    )

    return df

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================
def ajustar_status(df):
    df["Status do sistema"] = df["Encerram.por data"].apply(
        lambda x: "Confirmada" if pd.notna(x) else "Em aberto"
    )
    return df

def manter_codigo_macro(txt):
    if pd.isna(txt):
        return None
    m = re.search(r"[A-Z]{2}-\d{5}", str(txt))
    return m.group() if m else None



def obter_foto(nome):
    if not isinstance(nome, str):
        return None
    primeiro_nome = nome.split()[0]
    for ext in [".jpg", ".jpeg", ".png", ".PNG"]:
        caminho = os.path.join(PASTA_FOTOS, f"{primeiro_nome}{ext}")
        if os.path.exists(caminho):
            return caminho
    return None

# =====================================================
# LEITURA DOS DADOS
# =====================================================
df_iw28 = ajustar_status(carregar_iw28())
df_iw47 = carregar_iw47()
df_splan = carregar_splan()
df_iw38 = carregar_iw38()

df_iw28["Código Macro"] = df_iw28["Local de instalação"].apply(manter_codigo_macro)


def manter_codigo_macro(txt):
    if pd.isna(txt):
        return None
    m = re.search(r"(VP-\d{5})", str(txt))
    return m.group(1) if m else None

df_iw28["Ano"] = df_iw28["Criado em"].dt.isocalendar().year
df_iw28["Semana"] = df_iw28["Criado em"].dt.isocalendar().week
df_iw28["Ano-Semana"] = df_iw28["Ano"].astype(str) + "-W" + df_iw28["Semana"].astype(str).str.zfill(2)

# =====================================================
# ABAS
# =====================================================
aba_iw28, aba_iw47, aba_splan, aba_iw38 = st.tabs(
    [
        "📋 Programação – IW28",
        "⏱️ IW47 – Apropriação",
        "🕵️ Splan",
        "🗂️ IW38 – Planos de Manutenção"
    ]
)

# =====================================================
# ================= IW28 ===============================
# =====================================================
with aba_iw28:
    st.title("Dashboard — AVP | Manutenção | Processo")
    st.caption("Fonte: SAP - IW28")

    c1, c2, c3, c4 = st.columns(4)
    f_macro = c1.multiselect("Código Macro", sorted(df_iw28["Código Macro"].dropna().unique()))
    f_status = c2.multiselect("Status", sorted(df_iw28["Status do sistema"].unique()))
    f_centro = c3.multiselect("Centro de Trabalho", sorted(df_iw28["CenTrab.principal"].dropna().unique()))
    f_tipo = c4.multiselect("Tipo de Nota", sorted(df_iw28["Tipo de nota"].dropna().unique()))

    df_f = df_iw28.copy()
    if f_macro: df_f = df_f[df_f["Código Macro"].isin(f_macro)]
    if f_status: df_f = df_f[df_f["Status do sistema"].isin(f_status)]
    if f_centro: df_f = df_f[df_f["CenTrab.principal"].isin(f_centro)]
    if f_tipo: df_f = df_f[df_f["Tipo de nota"].isin(f_tipo)]

    hoje = pd.Timestamp(datetime.today().date())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de Ordens", len(df_f))
    k2.metric("Confirmadas", (df_f["Status do sistema"] == "Confirmada").sum())
    k3.metric("Em aberto", (df_f["Status do sistema"] == "Em aberto").sum())
    k4.metric(
        "Atrasadas",
        ((df_f["Conclusão desejada"] < hoje) &
         (df_f["Status do sistema"] != "Confirmada")).sum()
    )

    st.divider()

    aba_vis = st.radio(
        "Visualização",
        ["Por Status", "Backlog Semanal (IW)", "Por Código Macro", "Por Centro de Trabalho", "Por Tipo de Nota"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if aba_vis == "Por Status":
        fig = px.histogram(df_f, x="Status do sistema", color="Status do sistema",
                           color_discrete_map=CORES_STATUS, text_auto=True)

    elif aba_vis == "Backlog Semanal (IW)":
        base = (df_f[df_f["Status do sistema"] == "Em aberto"]
                .groupby("Ano-Semana").size().reset_index(name="Backlog"))
        fig = px.bar(base, x="Ano-Semana", y="Backlog", text="Backlog")

    elif aba_vis == "Por Código Macro":
        base = df_f.groupby(["Local de instalação", "Status do sistema"]).size().reset_index(name="Qtd")
        fig = px.bar(base, x="Local de instalação", y="Qtd",
                     color="Status do sistema", color_discrete_map=CORES_STATUS, text="Qtd")

    elif aba_vis == "Por Centro de Trabalho":
        base = df_f.groupby(["CenTrab.principal", "Status do sistema"]).size().reset_index(name="Qtd")
        fig = px.bar(base, x="CenTrab.principal", y="Qtd",
                     color="Status do sistema", color_discrete_map=CORES_STATUS, text="Qtd")

    else:
        base = df_f.groupby(["Tipo de nota", "Status do sistema"]).size().reset_index(name="Qtd")
        fig = px.bar(base, x="Tipo de nota", y="Qtd",
                     color="Status do sistema", color_discrete_map=CORES_STATUS, text="Qtd")

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_f, use_container_width=True)

# =====================================================
# ================= IW47 ===============================
# =====================================================
with aba_iw47:
    st.title("IW47 — Apropriação de Horas (Individual)")

    c1, c2, c3 = st.columns(3)
    with c1:
        f_colab = st.multiselect(
            "Colaborador",
            sorted(df_iw47["Nome do empregado"].unique())
        )
    with c2:
        f_mes = st.selectbox(
            "Mês",
            ["Todos"] + sorted(
                df_iw47["Data de lançamento"]
                .dt.to_period("M")
                .astype(str)
                .unique()
            ),
            key="mes_iw47"
        )
    with c3:
        f_periodo = st.date_input(
            "Período",
            (
                df_iw47["Data de lançamento"].min().date(),
                df_iw47["Data de lançamento"].max().date()
            )
        )

    # ---------------- FILTROS ----------------
    df47 = df_iw47.copy()

    if f_colab:
        df47 = df47[df47["Nome do empregado"].isin(f_colab)]

    if f_mes != "Todos":
        df47 = df47[
            df47["Data de lançamento"]
            .dt.to_period("M")
            .astype(str) == f_mes
        ]

    df47 = df47[
        (df47["Data de lançamento"].dt.date >= f_periodo[0]) &
        (df47["Data de lançamento"].dt.date <= f_periodo[1])
    ]

    # ---------------- RESUMO ----------------
    resumo = (
        df47
        .groupby("Nome do empregado", as_index=False)["Horas"]
        .sum()
    )

    fig = px.bar(
        resumo,
        x="Nome do empregado",
        y="Horas",
        text="Horas"
    )
    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- DETALHAMENTO ----------------
    st.subheader("Detalhamento Diário")
    st.dataframe(
        df47[
            [
                "Data de lançamento",
                "Nome do empregado",
                "Minutos",
                "Horas",
                "Texto de confirmação"
            ]
        ],
        use_container_width=True
    )

    # ---------------- METAS ----------------
    PREVENTIVA_120H = [
        "ANDRE SAVIO NADAL", "CARLOS DANIEL ANTUNES",
        "DEJAIR JOSE SANTOS LIVRAMENTO", "JEAN WILLIAN SANTOS",
        "RODRIGO PINHEIRO", "NATALIA BARRETO"
    ]

    CORRETIVA_90H = [
        "EZEQUIEL ALEIXO", "RODRIGO CHARLES VIEIRA",
        "RONALDO CORREA DA ROCHA", "ALISSON PAULO GASTAO",
        "ROMARIO KASPCHAK", "THIAGO MAURICIO AZEVEDO",
        "CRISTIANO IATCZAKI", "EVANDRO LOPES SANTANA",
        "VICTOR EMANUEL PAES DE MELLO"
    ]

    def definir_meta(nome):
        if nome in PREVENTIVA_120H:
            return 120
        if nome in CORRETIVA_90H:
            return 90
        return None  # evita erro para nomes fora da lista

    st.subheader("Indicador de Meta Mensal por Colaborador")

    if f_mes == "Todos":
        st.warning("Selecione um mês para validar a meta mensal.")
    else:
        resumo["Meta (h)"] = resumo["Nome do empregado"].apply(definir_meta)
        resumo = resumo.dropna(subset=["Meta (h)"])

        resumo["Ating (%)"] = (
            resumo["Horas"] / resumo["Meta (h)"] * 100
        ).round(1)

        resumo["Status"] = resumo.apply(
            lambda x: "🟢 Atingida"
            if x["Horas"] >= x["Meta (h)"]
            else "🔴 Abaixo",
            axis=1
        )

        for _, row in resumo.iterrows():
            col_foto, col_info = st.columns([1, 6])

            with col_foto:
                foto = obter_foto(row["Nome do empregado"])
                if foto:
                    st.image(foto, width=70)
                else:
                    st.markdown("👤")

            with col_info:
                st.markdown(f"""
                <div style="background-color:#1c1f26;
                            padding:12px;
                            border-radius:10px;
                            margin-bottom:8px;">
                    <b>{row['Nome do empregado']}</b><br>
                    Horas: <b>{row['Horas']:.1f}h</b> |
                    Meta: <b>{row['Meta (h)']}h</b> |
                    Atingimento: <b>{row['Ating (%)']}%</b><br>
                    <span style="font-size:18px">{row['Status']}</span>
                </div>
                """, unsafe_allow_html=True)


# =====================================================
# ================= SPLAN ==============================
# =====================================================
with aba_splan:
    st.title("Splan — Investigações por Colaborador")

    c1, c2, c3 = st.columns(3)
    with c1:
        f_colab = st.multiselect(
            "Criador da Investigação",
            sorted(df_splan["Criador da Investigação"].unique())
        )
    with c2:
        f_mes = st.selectbox(
            "Mês",
            ["Todos"] + sorted(df_splan["Mês"].unique()),
            key="mes_splan"
        )
    with c3:
        f_metodo = st.multiselect(
            "Método de Investigação",
            sorted(df_splan["Método de Investigação"].dropna().unique())
        )

    df_sp = df_splan.copy()
    if f_colab:
        df_sp = df_sp[df_sp["Criador da Investigação"].isin(f_colab)]
    if f_mes != "Todos":
        df_sp = df_sp[df_sp["Mês"] == f_mes]
    if f_metodo:
        df_sp = df_sp[df_sp["Método de Investigação"].isin(f_metodo)]

    resumo = df_sp.groupby("Criador da Investigação").size().reset_index(name="Qtd Investigações")

    fig = px.bar(resumo, x="Criador da Investigação", y="Qtd Investigações", text="Qtd Investigações")
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalhamento")
    st.dataframe(
        df_sp[["Data da Investigação", "Criador da Investigação", "Método de Investigação"]],
        use_container_width=True
    )

# =====================================================
# ================= IW38 ===============================
# =====================================================
with aba_iw38:
    st.title("IW38 — Planos de Manutenção")
    st.caption("Fonte: SAP - IW38")

    # ---------------- FILTROS ----------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_plano = st.multiselect(
            "Plano de Manutenção",
            sorted(df_iw38["Plano de manutenção"].dropna().unique())
        )
    with c2:
        f_local = st.multiselect(
            "Local de Instalação",
            sorted(df_iw38["Local de instalação"].dropna().unique())
        )
    with c3:
        f_tp = st.multiselect(
            "Tipo Atividade Manutenção",
            sorted(df_iw38["Tp.atvd.manut."].dropna().unique())
        )
    with c4:
        f_centro = st.multiselect(
            "Centro de Trabalho",
            sorted(df_iw38["CenTrab.principal"].dropna().unique())
        )

    df38 = df_iw38.copy()

    if f_plano:
        df38 = df38[df38["Plano de manutenção"].isin(f_plano)]
    if f_local:
        df38 = df38[df38["Local de instalação"].isin(f_local)]
    if f_tp:
        df38 = df38[df38["Tp.atvd.manut."].isin(f_tp)]
    if f_centro:
        df38 = df38[df38["CenTrab.principal"].isin(f_centro)]

    # ---------------- KPIs ----------------
    k1, k2, k3 = st.columns(3)

    k1.metric("Total de Ordens", len(df38))
    k2.metric(
        "Ordens Encerradas",
        df38["Data fim real da ordem"].notna().sum()
    )
    k3.metric(
        "Custo Total Planejado",
        f"R$ {df38['Custos totais plan.'].sum():,.2f}"
    )

    st.divider()

    # ---------------- VISUALIZAÇÃO ----------------
    vis = st.radio(
        "Visualização",
        [
            "Por Plano de Manutenção",
            "Por Centro de Trabalho",
            "Custos por Plano"
        ],
        horizontal=True,
        label_visibility="collapsed"
    )

    if vis == "Por Plano de Manutenção":
        base = (
            df38
            .groupby("Plano de manutenção")
            .size()
            .reset_index(name="Qtd Ordens")
        )
        fig = px.bar(
            base,
            x="Plano de manutenção",
            y="Qtd Ordens",
            text="Qtd Ordens"
        )

    elif vis == "Por Centro de Trabalho":
        base = (
            df38
            .groupby("CenTrab.principal")
            .size()
            .reset_index(name="Qtd Ordens")
        )
        fig = px.bar(
            base,
            x="CenTrab.principal",
            y="Qtd Ordens",
            text="Qtd Ordens"
        )

    else:
        base = (
            df38
            .groupby("Plano de manutenção", as_index=False)
            ["Custos totais plan."]
            .sum()
        )
        fig = px.bar(
            base,
            x="Plano de manutenção",
            y="Custos totais plan.",
            text="Custos totais plan."
        )
        fig.update_traces(
            texttemplate="R$ %{text:,.0f}",
            textposition="outside"
        )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- TABELA ----------------
    st.subheader("Detalhamento das Ordens")
    st.dataframe(
        df38[
            [
                "Ordem",
                "Local de instalação",
                "Texto breve",
                "Tp.atvd.manut.",
                "CenTrab.principal",
                "Plano de manutenção",
                "Custos totais plan.",
                "Data fim real da ordem"
            ]
        ],
        use_container_width=True
    )
