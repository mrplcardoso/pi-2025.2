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
            df["__sheet_name"] = sheet_name
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

    # Sidebar: ações que usuário pode executar
    st.sidebar.header("Filtragem")

    # Escolha colunas para filtrar
    cols_para_filtrar = st.sidebar.multiselect("Colunas para filtrar (várias)", df.columns.tolist())

    filtros = {}
    for col in cols_para_filtrar:
        if pd.api.types.is_numeric_dtype(df[col]):
            minv = float(df[col].min())
            maxv = float(df[col].max())
            filtros[col] = st.sidebar.slider(f"Intervalo para {col}", minv, maxv, (minv, maxv))
        else:
            opcoes = df[col].dropna().unique().tolist()
            filtros[col] = st.sidebar.multiselect(f"Valores para {col}", options=opcoes, default=opcoes)

    # Ordenação
    col_ord = st.sidebar.selectbox("Ordenar por", df.columns)
    ordem = st.sidebar.radio("Ordem", ["Crescente", "Decrescente"])

    # Botões para aplicar e para mostrar só colunas filtradas
    aplicar = st.sidebar.button("Aplicar")
    mostrar_colunas_filtradas = st.sidebar.checkbox("Mostrar somente colunas usadas", value=False)

    # Copiar o DataFrame original para aplicar filtros/ordenar
    df_proc = df.copy()

    if aplicar:
        # aplicar filtros
        for col, criterio in filtros.items():
            if pd.api.types.is_numeric_dtype(df[col]):
                lo, hi = criterio
                df_proc = df_proc[df_proc[col].between(lo, hi)]
            else:
                if criterio:
                    df_proc = df_proc[df_proc[col].isin(criterio)]
        # ordenar
        asc = (ordem == "Crescente")
        df_proc = df_proc.sort_values(by=col_ord, ascending=asc)

    # Segundo bloco: mostrar resultados após ações
    st.subheader("Resultado")

    # Preparar colunas para exibição
    if mostrar_colunas_filtradas and aplicar:
        # montar lista de colunas usadas nos filtros + coluna de ordenação
        colunas_usadas = set(cols_para_filtrar)
        colunas_usadas.add(col_ord)
        # opcional: garantir que colunas obrigatórias (por exemplo identidades do aluno) sempre apareçam
        # colunas_usadas.update(["Aluno", "Disciplina", "Ano"])  # ajuste conforme seu dataset

        # filtrar DataFrame para exibir somente essas colunas
        cols_para_mostrar = [c for c in df_proc.columns if c in colunas_usadas]
        # se por acaso não restar nenhuma, fallback para todas as colunas
        if not cols_para_mostrar:
            cols_para_mostrar = df_proc.columns.tolist()
        st.dataframe(df_proc[cols_para_mostrar], use_container_width=True)
    else:
        # mostrar todas as colunas
        st.dataframe(df_proc, use_container_width=True)


    # ======================================================
    # 🔍 SEÇÃO: ANÁLISE EXPLORATÓRIA AUTOMÁTICA
    # ======================================================
    st.header("📈 Análise Exploratória dos Dados")

    # 1. Informações gerais
    st.subheader("📋 Informações gerais")
    st.write(f"**Total de linhas:** {len(df_proc)}")
    st.write(f"**Total de colunas:** {len(df_proc.columns)}")
    st.write("**Tipos de dados:**")
    st.dataframe(df_proc.dtypes.rename("Tipo").reset_index(names=["Coluna"]))

    # 3. Estatísticas descritivas
    st.subheader("📊 Estatísticas descritivas (numéricas)")
    st.dataframe(df_proc.describe().T)

    # 4. Distribuições automáticas
    st.subheader("📉 Distribuições de colunas numéricas")
    numeric_cols = df_proc.select_dtypes(include="number").columns
    for col in numeric_cols:
        fig, ax = plt.subplots()
        df_proc[col].plot(kind="hist", bins=20, ax=ax)
        ax.set_title(f"Distribuição: {col}")
        st.pyplot(fig)

    # 5. Distribuições de colunas categóricas
    st.subheader("📦 Distribuições de colunas categóricas")
    cat_cols = df_proc.select_dtypes(exclude="number").columns
    for col in cat_cols:
        if df_proc[col].nunique() <= 20:  # evitar gráficos muito longos
            fig, ax = plt.subplots()
            df_proc[col].value_counts().plot(kind="bar", ax=ax)
            ax.set_title(f"Contagem por categoria: {col}")
            st.pyplot(fig)

    # 6. Correlação entre variáveis numéricas
    if len(numeric_cols) > 1:
        st.subheader("📊 Correlação entre variáveis numéricas")
        corr = df_proc[numeric_cols].corr()
        st.dataframe(corr)
        fig, ax = plt.subplots()
        im = ax.imshow(corr, cmap="coolwarm")
        ax.set_xticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(corr.columns)))
        ax.set_yticklabels(corr.columns)
        fig.colorbar(im)
        st.pyplot(fig)

if __name__ == "__main__":
    main()
