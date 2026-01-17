import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(
    page_title="Dashboard - AVP - Manutenção - Processo",
    layout="wide"
)

# ============================
# PALETA AVP
# ============================
AMARELO = "#f1c40f"
PRETO = "#0e1117"
CINZA_ESCURO = "#1c1f26"
CINZA_CLARO = "#b0b3b8"

# ============================
# CSS GLOBAL (AVP)
# ============================
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    background-color: {PRETO};
    color: white;
}}

/* RADIO = ABAS */
div[role="radiogroup"] label {{
    color: {CINZA_CLARO} !important;
    font-size: 16px;
    padding-bottom: 6px;
}}

div[role="radiogroup"] label:has(input:checked) {{
    color: {AMARELO} !important;
    font-weight: 700;
    border-bottom: 3px solid {AMARELO};
}}

/* KPIs */
[data-testid="metric-container"] {{
    background-color: {CINZA_ESCURO};
    padding: 15px;
    border-radius: 10px;
}}
</style>
""", unsafe_allow_html=True)

# ============================
# ARQUIVO
# ============================
ARQUIVO = r"C:\Users\Forno\Desktop\SAP\IW38_novo.xlsx"

# ============================
# CARREGAMENTO DOS DADOS
# ============================
@st.cache_data(ttl=300)
def carregar_dados(caminho):
    if not os.path.exists(caminho):
        st.error(f"Arquivo não encontrado:\n{caminho}")
        return pd.DataFrame()

    df = pd.read_excel(caminho)
    df.columns = [c.strip() for c in df.columns]

    if "Data-base do fim" in df.columns:
        df["Data-base do fim"] = pd.to_datetime(
            df["Data-base do fim"], errors="coerce"
        )

    return df

# ============================
# AJUSTE STATUS
# ============================
def ajustar_status(df):
    def map_status(status):
        s = str(status)

        if all(x in s for x in ["LIB", "CAPC", "MatC", "NOAP"]):
            return "Liberado"

        if all(x in s for x in ["ABER", "CAPC", "SCDM"]):
            return "Aguardando liberação"

        if all(x in s for x in ["LIB", "CONF", "CAPC", "JBFI", "NOAP", "SCDM"]):
            return "Confirmada"

        return "Outros"

    if "Status do sistema" in df.columns:
        df["Status do sistema"] = df["Status do sistema"].apply(map_status)

    return df

CORES_STATUS = {
    "Confirmada": "#1dd268",
    "Liberado": AMARELO,
    "Aguardando liberação": "#44a5e6",
    "Outros": "#ec7c40"
}

# ============================
# LEITURA
# ============================
df = carregar_dados(ARQUIVO)
df = ajustar_status(df)

if df.empty:
    st.stop()

# ============================
# CABEÇALHO
# ============================
st.title("Dashboard — AVP | Manutenção | Processo")
st.caption("Fonte: SAP")

# ============================
# FILTROS
# ============================
c1, c2, c3, c4 = st.columns(4)

with c1:
    filtro_local = st.multiselect(
        "Local de instalação",
        sorted(df["Local de instalação"].dropna().unique())
    )

with c2:
    filtro_status = st.multiselect(
        "Status do sistema",
        sorted(df["Status do sistema"].dropna().unique())
    )

with c3:
    filtro_centro = st.multiselect(
        "Centro de Trabalho",
        sorted(df["CenTrab.principal"].dropna().unique())
    )

with c4:
    filtro_ord = st.multiselect(
        "Campo de ordenação",
        sorted(df["Campo de ordenação"].dropna().unique())
    )

def aplicar_filtros(_df):
    df_f = _df.copy()

    if filtro_local:
        df_f = df_f[df_f["Local de instalação"].isin(filtro_local)]

    if filtro_status:
        df_f = df_f[df_f["Status do sistema"].isin(filtro_status)]

    if filtro_centro:
        df_f = df_f[df_f["CenTrab.principal"].isin(filtro_centro)]

    if filtro_ord:
        df_f = df_f[df_f["Campo de ordenação"].isin(filtro_ord)]

    return df_f

df_f = aplicar_filtros(df)

# ============================
# KPIs
# ============================
total = len(df_f)
confirmadas = (df_f["Status do sistema"] == "Confirmada").sum()
nao_confirmadas = total - confirmadas

hoje = pd.Timestamp(datetime.today().date())
atrasadas = (
    (df_f["Data-base do fim"] < hoje) &
    (df_f["Status do sistema"] != "Confirmada")
).sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total de Ordens", total)
k2.metric("Confirmadas", confirmadas)
k3.metric("Não confirmadas", nao_confirmadas)
k4.metric("Atrasadas", atrasadas)

st.divider()

# ============================
# NAVEGAÇÃO (SUBSTITUI ABAS)
# ============================
aba = st.radio(
    "Visualizações",
    [
        "Por Status",
        "Por Local",
        "Por Centro de Trabalho",
        "Por Campo de ordenação"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

# ============================
# GRÁFICOS
# ============================
if aba == "Por Status":
    g1 = px.histogram(
        df_f,
        x="Status do sistema",
        color="Status do sistema",
        color_discrete_map=CORES_STATUS,
        title="Distribuição por Status"
    )
    st.plotly_chart(g1, use_container_width=True)

elif aba == "Por Local":
    base = df_f.groupby(
        ["Local de instalação", "Status do sistema"]
    ).size().reset_index(name="Qtd")

    g2 = px.bar(
        base,
        x="Local de instalação",
        y="Qtd",
        color="Status do sistema",
        color_discrete_map=CORES_STATUS,
        title="Ordens por Local"
    )
    st.plotly_chart(g2, use_container_width=True)

elif aba == "Por Centro de Trabalho":
    base = df_f.groupby(
        ["CenTrab.principal", "Status do sistema"]
    ).size().reset_index(name="Qtd")

    g3 = px.bar(
        base,
        x="CenTrab.principal",
        y="Qtd",
        color="Status do sistema",
        color_discrete_map=CORES_STATUS,
        title="Ordens por Centro de Trabalho"
    )
    st.plotly_chart(g3, use_container_width=True)

elif aba == "Por Campo de ordenação":
    base = df_f.groupby(
        ["Campo de ordenação", "Status do sistema"]
    ).size().reset_index(name="Qtd")

    g4 = px.bar(
        base,
        x="Campo de ordenação",
        y="Qtd",
        color="Status do sistema",
        color_discrete_map=CORES_STATUS,
        title="Ordens por Campo de ordenação"
    )
    st.plotly_chart(g4, use_container_width=True)

st.divider()

# ============================
# BACKLOG POR SEMANA
# ============================
st.subheader("Backlog por semana")

df_backlog = df_f[
    (df_f["Status do sistema"] != "Confirmada") &
    (df_f["Data-base do fim"].notna())
]

if df_backlog.empty:
    st.info("Nenhuma ordem em backlog.")
else:
    iso = df_backlog["Data-base do fim"].dt.isocalendar()
    df_backlog["Ano-Semana"] = (
        iso.year.astype(str) + "-W" +
        iso.week.astype(str).str.zfill(2)
    )

    base_backlog = (
        df_backlog.groupby("Ano-Semana")
        .size()
        .reset_index(name="Qtd")
        .sort_values("Ano-Semana")
    )

    g_backlog = px.bar(
        base_backlog,
        x="Ano-Semana",
        y="Qtd",
        text="Qtd",
        title="Backlog semanal",
        color_discrete_sequence=[AMARELO]
    )

    g_backlog.update_traces(textposition="outside")
    g_backlog.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(g_backlog, use_container_width=True)

st.divider()

# ============================
# TABELA FINAL
# ============================
st.subheader("Programação")
st.dataframe(df_f, use_container_width=True)

