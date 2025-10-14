import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

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
            df["Planilha"] = sheet_name
            list_flat.append(df)
        # concatenar todas
        df_concat = pd.concat(list_flat, ignore_index=True, sort=False)
        return df_concat.fillna(0)
    elif ext == ".csv":
        df = pd.read_csv(uploaded_file)
        return df.fillna(0)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")

def main():
    st.title("Visualizador Didático")

    uploaded_file = st.file_uploader("Carregue sua planilha", type=["csv", "xlsx"])
    if uploaded_file is None:
        st.info("Por favor, carregue uma planilha para começar.")
        return

    df = read_uploaded_file(uploaded_file)

    # Criação das abas principais
    tab_dados, tab_filtros, tab_analise = st.tabs(
        ["📋 Dados brutos", "🎛️ Filtragem e ordenação", "📈 Análise exploratória"])

    # ======================================================
    # 🗂️ Aba 1: Dados brutos
    # ======================================================
    with tab_dados:

        df_proc = df.copy()

        st.subheader("Visualização inicial dos dados")

        # Garantir que a coluna da planilha exista
        if "Planilha" not in df_proc.columns:
            df_proc["Planilha"] = "Único"

        planilhas = ["Todos"] + sorted(df_proc["Planilha"].dropna().unique().tolist())
        planilha_selecionada = st.selectbox("Escolha a planilha", planilhas)

        if planilha_selecionada != "Todos":
            df_info = df_proc[df_proc["Planilha"] == planilha_selecionada]
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

    # ======================================================
    # 🎛️ Aba 2: Filtros e ordenação
    # ======================================================
    with tab_filtros:
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

    # ======================================================
    # 📈 Aba 3: Análise exploratória
    # ======================================================
    with tab_analise:
        st.subheader("Análise exploratória dos dados")



if __name__ == "__main__":
    main()
