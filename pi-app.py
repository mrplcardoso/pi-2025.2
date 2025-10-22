import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns  # <<< necessário
sns.set_theme(style="whitegrid")

def flatten_multilevel_columns(df):
    """Se df.columns for MultiIndex, achata para strings como “Topo – Sub”."""
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for top, sub in df.columns:
            top = str(top).strip()
            sub = str(sub).strip()
            if top and sub:
                new_name = f"{top} - {sub}"
            elif sub:
                new_name = sub
            else:
                new_name = top
            new_cols.append(new_name)
        df.columns = new_cols
    return df

def read_uploaded_file(uploaded_file):
    """
    Lê o arquivo (CSV ou Excel com múltiplas planilhas),
    achata cabeçalhos multilinha e concatena as planilhas.
    Retorna um DataFrame “plano”.
    """
    _, ext = os.path.splitext(uploaded_file.name.lower())
    if ext in (".xls", ".xlsx"):
        # lê todas as planilhas
        dict_dfs = pd.read_excel(uploaded_file, sheet_name=None, header=[0,1])
        list_flat = []
        for sheet_name, df in dict_dfs.items():
            # flatten colunas multilinha
            df = flatten_multilevel_columns(df)
            # opcional: marcar de qual planilha veio
            df["PLANILHA"] = sheet_name
            list_flat.append(df)
        # concatenar todas
        df_concat = pd.concat(list_flat, ignore_index=True, sort=False)
        return df_concat.fillna(0)
    elif ext == ".csv":
        df = pd.read_csv(uploaded_file)
        return df.fillna(0)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")

def general_review(df):

    df_proc = df.copy()

    st.subheader("Visão Geral")

    # Garantir que a coluna da planilha exista
    if "PLANILHA" not in df_proc.columns:
        df_proc["PLANILHA"] = "Único"

    planilhas = ["Todos"] + sorted(df_proc["PLANILHA"].dropna().unique().tolist())
    planilha_selecionada = st.selectbox("Escolha a planilha", planilhas)

    if planilha_selecionada != "Todos":
        df_info = df_proc[df_proc["PLANILHA"] == planilha_selecionada]
    else:
        df_info = df_proc

    col_ano = "DADOS GERAIS - SERIE_ANO"
    col_turma = "DADOS GERAIS - TURMA"
    missing_cols = [c for c in (col_ano, col_turma) if c not in df_info.columns]

    if missing_cols:
        st.error(f"As seguintes colunas não foram encontradas: {missing_cols}")
    else:
        # Total
        st.markdown(f"**Total de alunos:** {len(df_info)}")

        # Quantidade de alunos por ano
        st.markdown("**Quantidade de alunos por ano do ensino médio:**")
        alunos_por_ano = df_info.groupby(col_ano).size().reset_index(name="Quantidade de alunos")
        st.dataframe(alunos_por_ano, use_container_width=True)

        # Quantidade de alunos por turma e ano
        st.markdown("**Quantidade de alunos por turma e ano:**")
        alunos_por_turma_ano = df_info.groupby([col_ano, col_turma]).size().reset_index(name="Quantidade de alunos")
        st.dataframe(alunos_por_turma_ano, use_container_width=True)

    st.markdown(f"**Total de colunas:** {len(df.columns)}")
    st.dataframe(pd.DataFrame(df.columns, columns=["Colunas"]), use_container_width=True)

def general_performance(df):
    st.subheader("Desempenho Geral")

    # Selecionar colunas de notas
    col_notas = [
        "NOTAS - LP", "NOTAS - LI", "NOTAS - BIO", "NOTAS - FÍS", "NOTAS - QUÍ",
        "NOTAS - MAT", "NOTAS - GEO", "NOTAS - HIS", "NOTAS - FIL", "NOTAS - SOC"
    ]

    # Filtrar somente linhas válidas
    df_notas = df.dropna(subset=col_notas).copy()

    # Calcular média do aluno
    df_notas["MÉDIA GERAL"] = df_notas[col_notas].mean(axis=1)

    # Agrupar por turma, série e ano
    agrupado = (
        df_notas.groupby(
            ["DADOS GERAIS - TURMA", "DADOS GERAIS - SERIE_ANO", "DADOS GERAIS - ANO"]
        )["MÉDIA GERAL"]
        .agg(["mean", "max", "min", "count"])
        .reset_index()
    )

    # Adicionar quantidade de alunos acima e abaixo da média geral
    media_global = df_notas["MÉDIA GERAL"].mean()
    acima_media = (
        df_notas[df_notas["MÉDIA GERAL"] > media_global]
        .groupby(["DADOS GERAIS - TURMA", "DADOS GERAIS - SERIE_ANO", "DADOS GERAIS - ANO"])
        .size()
        .reset_index(name="Acima da média")
    )
    abaixo_media = (
        df_notas[df_notas["MÉDIA GERAL"] <= media_global]
        .groupby(["DADOS GERAIS - TURMA", "DADOS GERAIS - SERIE_ANO", "DADOS GERAIS - ANO"])
        .size()
        .reset_index(name="Abaixo da média")
    )

    # Combinar tudo
    resumo = (
        agrupado
        .merge(acima_media, on=["DADOS GERAIS - TURMA", "DADOS GERAIS - SERIE_ANO", "DADOS GERAIS - ANO"], how="left")
        .merge(abaixo_media, on=["DADOS GERAIS - TURMA", "DADOS GERAIS - SERIE_ANO", "DADOS GERAIS - ANO"], how="left")
    )

    # Ordenar conforme solicitado: Turma → Série → Ano
    resumo = resumo.sort_values(
        by=["DADOS GERAIS - TURMA", "DADOS GERAIS - SERIE_ANO", "DADOS GERAIS - ANO"],
        ascending=[True, True, True]
    ).reset_index(drop=True)

    st.markdown("### Estatísticas por Turma / Série / Ano")
    st.dataframe(resumo, use_container_width=True)

    # --- Gráfico de linha: média por turma e série ao longo dos anos ---
    st.markdown("### Evolução da Média por Turma e Série ao Longo dos Anos")

    # Criar coluna combinando turma e série para identificar cada linha
    df_notas["TURMA_SÉRIE"] = df_notas["DADOS GERAIS - TURMA"].astype(str) + " - " + df_notas[
        "DADOS GERAIS - SERIE_ANO"].astype(str)

    serie_media = (
        df_notas.groupby(["DADOS GERAIS - ANO", "TURMA_SÉRIE"])["MÉDIA GERAL"]
        .mean()
        .reset_index()
        .sort_values(["DADOS GERAIS - ANO", "TURMA_SÉRIE"])
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    for turma_serie, dados in serie_media.groupby("TURMA_SÉRIE"):
        ax.plot(
            dados["DADOS GERAIS - ANO"],
            dados["MÉDIA GERAL"],
            marker="o",
            label=turma_serie
        )

    ax.set_xlabel("Ano do Calendário")
    ax.set_ylabel("Média Geral")
    ax.set_title("Evolução das Médias por Turma e Série")
    ax.legend(title="Turma - Série", bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig)

def subject_performance(df):
    st.subheader("Desempenho por Disciplina")

    # --- Colunas de notas ---
    col_notas = [
        "NOTAS - LP", "NOTAS - LI", "NOTAS - BIO", "NOTAS - FÍS", "NOTAS - QUÍ",
        "NOTAS - MAT", "NOTAS - GEO", "NOTAS - HIS", "NOTAS - FIL", "NOTAS - SOC"
    ]

    # --- Limpeza e preparação ---
    df_notas = df.dropna(subset=col_notas).copy()

    # Converter notas para numérico (caso venham como texto)
    for c in col_notas:
        df_notas[c] = pd.to_numeric(df_notas[c], errors="coerce")

    # --- Cálculo da média e taxa de aprovação por disciplina e série ---
    lista_series = sorted(df_notas["DADOS GERAIS - SERIE_ANO"].dropna().unique().tolist())

    for serie in lista_series:
        st.markdown(f"### 🏫 {serie}")

        df_serie = df_notas[df_notas["DADOS GERAIS - SERIE_ANO"] == serie].copy()

        estatisticas = []
        for col in col_notas:
            media = df_serie[col].mean()
            taxa_aprov = (df_serie[col] >= 5.0).mean() * 100  # percentual de alunos com nota >= 50
            estatisticas.append({"Disciplina": col.replace("NOTAS - ", ""), "Média": media, "Aprovação (%)": taxa_aprov})

        df_estat = pd.DataFrame(estatisticas).sort_values(by="Média", ascending=False)

        # --- Exibir tabela resumida ---
        st.dataframe(df_estat, use_container_width=True)

        # --- Gráfico de barras horizontais ---
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.barh(df_estat["Disciplina"], df_estat["Média"], color="steelblue")
        ax1.set_xlabel("Média das Notas")
        ax1.set_ylabel("Disciplina")
        ax1.set_title(f"Média das Notas - {serie}")
        ax1.invert_yaxis()  # maior média no topo
        st.pyplot(fig)

        # --- Gráfico extra: taxa de aprovação ---
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.barh(df_estat["Disciplina"], df_estat["Aprovação (%)"], color="seagreen")
        ax2.set_xlabel("Taxa de Aprovação (%)")
        ax2.set_ylabel("Disciplina")
        ax2.set_title(f"Taxa de Aprovação - {serie}")
        ax2.invert_yaxis()
        st.pyplot(fig2)

def dispersal(df):
    st.subheader("Dispersão de Notas e Outliers")

    # --- Colunas de notas ---
    col_notas = [
        "NOTAS - LP", "NOTAS - LI", "NOTAS - BIO", "NOTAS - FÍS", "NOTAS - QUÍ",
        "NOTAS - MAT", "NOTAS - GEO", "NOTAS - HIS", "NOTAS - FIL", "NOTAS - SOC"
    ]

    # Verificar existência das colunas de nota
    faltantes = [c for c in col_notas if c not in df.columns]
    if len(faltantes) == len(col_notas):
        st.error("Nenhuma das colunas de NOTAS foi encontrada no DataFrame. Verifique os nomes das colunas.")
        return
    # manter apenas colunas existentes
    col_notas = [c for c in col_notas if c in df.columns]

    # --- Identificador do aluno (coluna potencial) ---
    possible_id_cols = [
        "DADOS GERAIS - CD_ALUNO_ANONIMIZADO",
        "DADOS GERAIS - Nº CHAMADA",
        "DADOS GERAIS - NÚMERO CHAMADA",
        "CD_ALUNO_ANONIMIZADO",
        "Nº CHAMADA",
        "N_CHAMADA",
        "ALUNO",
        "DADOS GERAIS - ALUNO"
    ]
    id_col = None
    for c in possible_id_cols:
        if c in df.columns:
            id_col = c
            break
    if id_col is None:
        # criar coluna de id a partir do índice
        df = df.reset_index(drop=True)
        df["ALUNO_ID"] = df.index.astype(str)
        id_col = "ALUNO_ID"

    # --- Conversão das notas para numérico ---
    df_notas = df.copy()
    for c in col_notas:
        df_notas[c] = pd.to_numeric(df_notas[c], errors="coerce")

    # Seletores (defensivos: verificar existência das colunas de agrupamento)
    col_serie = "DADOS GERAIS - SERIE_ANO"
    col_ano = "DADOS GERAIS - ANO"
    col_turma = "DADOS GERAIS - TURMA"

    for col in (col_serie, col_ano, col_turma):
        if col not in df_notas.columns:
            st.error(f"Coluna obrigatória ausente: {col}. Não é possível gerar dispersão.")
            return

    # Opcional: permitir seleção (ou usar todos)
    serie_sel = st.selectbox("Selecione a série (ou Todos)",
                             ["Todos"] + sorted(df_notas[col_serie].dropna().unique().tolist()))
    ano_sel = st.selectbox("Selecione o ano (ou Todos)",
                           ["Todos"] + sorted(df_notas[col_ano].dropna().unique().tolist()))
    turma_sel = st.selectbox("Selecione a turma (ou Todos)",
                             ["Todos"] + sorted(df_notas[col_turma].dropna().unique().tolist()))

    # Aplicar filtros de seleção
    df_filtro = df_notas.copy()
    if serie_sel != "Todos":
        df_filtro = df_filtro[df_filtro[col_serie] == serie_sel]
    if ano_sel != "Todos":
        df_filtro = df_filtro[df_filtro[col_ano] == ano_sel]
    if turma_sel != "Todos":
        df_filtro = df_filtro[df_filtro[col_turma] == turma_sel]

    if df_filtro.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # --- Boxplot por disciplina (mostra outliers) ---
    st.markdown("### 📘 Boxplots por Disciplina (outliers mostrados)")

    # melt para long format
    melted = df_filtro.melt(
        id_vars=[id_col, col_turma, col_serie, col_ano],
        value_vars=col_notas,
        var_name="Disciplina",
        value_name="Nota"
    )

    # limpar nome da disciplina para exibir
    melted["Disciplina"] = melted["Disciplina"].str.replace("NOTAS - ", "").str.strip()

    # plot: um boxplot por disciplina (horizontal)
    fig, ax = plt.subplots(figsize=(12, max(4, len(col_notas) * 0.6)))
    sns.boxplot(data=melted, x="Nota", y="Disciplina", orient="h", ax=ax, showfliers=True)
    ax.set_title(f"Dispersão das Notas por Disciplina — Série: {serie_sel} | Turma: {turma_sel} | Ano: {ano_sel}")
    ax.set_xlabel("Nota")
    ax.set_ylabel("Disciplina")
    st.pyplot(fig)

    # --- Identificar outliers por disciplina (Q1/Q3 rule) ---
    st.markdown("#### 🔎 Alunos identificados como outliers (por disciplina)")

    outlier_rows = []
    for disc in melted["Disciplina"].unique():
        sub = melted[melted["Disciplina"] == disc].dropna(subset=["Nota"])
        if sub.empty:
            continue
        q1 = sub["Nota"].quantile(0.25)
        q3 = sub["Nota"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        out = sub[(sub["Nota"] < lower) | (sub["Nota"] > upper)]
        if not out.empty:
            # pegar algumas colunas úteis para identificar
            for _, r in out.iterrows():
                outlier_rows.append({
                    "Disciplina": disc,
                    id_col: r[id_col],
                    col_turma: r[col_turma],
                    col_serie: r[col_serie],
                    col_ano: r[col_ano],
                    "Nota": r["Nota"],
                    "Tipo": "Acima" if r["Nota"] > upper else "Abaixo"
                })

    if outlier_rows:
        df_outliers = pd.DataFrame(outlier_rows).sort_values([col_turma, col_serie, col_ano])
        st.dataframe(df_outliers, use_container_width=True)
    else:
        st.info("Nenhum outlier detectado nas disciplinas com base na regra IQR (1.5 * IQR).")

    # --- Boxplot final: médias por aluno (por turma) ---
    st.markdown("### 📗 Boxplot das Médias por Aluno (por Turma)")

    # calcular média por aluno usando as colunas de nota
    df_filtro["MÉDIA_GERAL_ALUNO"] = df_filtro[col_notas].mean(axis=1)

    # boxplot das médias, agrupado por turma (horizontal)
    fig2, ax2 = plt.subplots(figsize=(12, max(4, len(df_filtro[col_turma].unique()) * 0.6)))
    sns.boxplot(data=df_filtro, x="MÉDIA_GERAL_ALUNO", y=col_turma, orient="h", ax=ax2, showfliers=True)
    ax2.set_title(f"Dispersão das Médias por Turma — Série: {serie_sel} | Ano: {ano_sel}")
    ax2.set_xlabel("Média Geral do Aluno")
    ax2.set_ylabel("Turma")
    st.pyplot(fig2)

    st.markdown("""
        **Interpretação**:
        - Pontos fora das caixas são outliers (muito acima ou muito abaixo do intervalo interquartil).
        - A caixa mostra Q1–Q3; a linha dentro da caixa é a mediana.
        - Use a tabela de outliers para identificar os alunos e verificar se há problemas/erros de entrada.
        """)

def main():
    st.title("Visualizador Didático")

    uploaded_file = st.file_uploader("Carregue sua planilha", type=["csv", "xlsx"])
    if uploaded_file is None:
        st.info("Por favor, carregue uma planilha para começar.")
        return

    df = read_uploaded_file(uploaded_file)

    # Criação das abas principais
    (tab_general_review, tab_general_performance,
     tab_subject_performance, tab_dispersal, tab_filter) = st.tabs(
        ["Visão Geral", "Desempenho Geral", "Desempenho por Disciplina", "Dispersão", "Filtragem e Ordenação"])

    # ======================================================
    # Aba 1: Visão Geral
    # ======================================================
    with tab_general_review:
        general_review(df)

    # ======================================================
    # Aba 2: Desempenho Geral
    # ======================================================

    with tab_general_performance:
        general_performance(df)

    # ======================================================
    # Aba 3: Desempenho por Disciplina
    # ======================================================

    with tab_subject_performance:
        subject_performance(df)

    # ======================================================
    # Aba 4: Dispersão
    # ======================================================

    with tab_dispersal:
        dispersal(df)

    # ======================================================
    # Aba 5: Filtragem e Ordenação
    # ======================================================

    with tab_filter:
        st.subheader("Filtragem e ordenação de dados")

        # Sidebar alternativa dentro da aba (mais limpo)
        cols_para_filtrar = st.multiselect("Colunas para filtrar (várias)", df.columns.tolist())
        filtros = {}
        for col in cols_para_filtrar:
            if pd.api.types.is_numeric_dtype(df[col]):
                minv = float(df[col].min())
                maxv = float(df[col].max())
                filtros[col] = st.slider(f"Intervalo para {col}", minv, maxv, (minv, maxv))
            else:
                opcoes = df[col].dropna().unique().tolist()
                filtros[col] = st.multiselect(f"Valores para {col}", options=opcoes, default=opcoes)

        col_ord = st.selectbox("Ordenar por", df.columns)
        ordem = st.radio("Ordem", ["Crescente", "Decrescente"])
        aplicar = st.button("Aplicar filtros e ordenação")
        mostrar_colunas_filtradas = st.checkbox("Mostrar somente colunas usadas", value=False)

        df_proc = df.copy()
        if aplicar:
            for col, criterio in filtros.items():
                if pd.api.types.is_numeric_dtype(df[col]):
                    lo, hi = criterio
                    df_proc = df_proc[df_proc[col].between(lo, hi)]
                else:
                    if criterio:
                        df_proc = df_proc[df_proc[col].isin(criterio)]
            asc = (ordem == "Crescente")
            df_proc = df_proc.sort_values(by=col_ord, ascending=asc)

        st.subheader("Resultado filtrado")
        if mostrar_colunas_filtradas and (aplicar or not filtros):
            colunas_usadas = set(cols_para_filtrar)
            colunas_usadas.add(col_ord)
            cols_para_mostrar = [c for c in df_proc.columns if c in colunas_usadas]
            if not cols_para_mostrar:
                cols_para_mostrar = df_proc.columns.tolist()
            st.dataframe(df_proc[cols_para_mostrar], use_container_width=True)
        else:
            st.dataframe(df_proc, use_container_width=True)



if __name__ == "__main__":
    main()
