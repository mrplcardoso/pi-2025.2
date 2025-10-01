import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Analisador de CSV")

uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Visualização dos dados")
    st.dataframe(df)

    # Filtro por coluna de texto — opcional
    col_str = st.selectbox("Selecione coluna de texto (opcional)", 
                           [c for c in df.columns if df[c].dtype == object] + ["---"])
    if col_str and col_str != "---":
        termo = st.text_input(f"Filtrar '{col_str}' que contêm (parte do texto):")
        if termo:
            df = df[df[col_str].str.contains(termo, na=False, case=False)]

    # Filtro por intervalo para colunas numéricas
    col_num = st.selectbox("Selecione coluna numérica para filtrar intervalo (opcional)",
                           [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])] + ["---"])
    if col_num and col_num != "---":
        min_val = float(df[col_num].min())
        max_val = float(df[col_num].max())
        intervalo = st.slider(f"Intervalo de {col_num}", min_val, max_val, (min_val, max_val))
        df = df[df[col_num].between(intervalo[0], intervalo[1])]

    # Ordenação
    coluna = st.selectbox("Selecione coluna para ordenar", df.columns)
    ordem = st.radio("Ordem", ["Crescente", "Decrescente"])
    df = df.sort_values(by=coluna, ascending=(ordem == "Crescente"))

    st.subheader("Dados filtrados / ordenados")
    st.dataframe(df)

    # Gráfico — escolha tipo
    st.subheader("Gráfico")
    tipo = st.selectbox("Tipo de gráfico", ["Bar", "Histograma", "Linha"])
    if tipo == "Bar":
        # gráfico de barras para valores categóricos (contagem)
        fig, ax = plt.subplots()
        df[coluna].value_counts().plot(kind="bar", ax=ax)
        st.pyplot(fig)
    elif tipo == "Histograma":
        if pd.api.types.is_numeric_dtype(df[coluna]):
            fig, ax = plt.subplots()
            df[coluna].plot(kind="hist", ax=ax, bins=20)
            st.pyplot(fig)
        else:
            st.write("Coluna não numérica — histograma não aplicável.")
    elif tipo == "Linha":
        if pd.api.types.is_numeric_dtype(df[coluna]):
            fig, ax = plt.subplots()
            df[coluna].plot(kind="line", ax=ax)
            st.pyplot(fig)
        else:
            st.write("Coluna não numérica — gráfico de linha não aplicável.")
