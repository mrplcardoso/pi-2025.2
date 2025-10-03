import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

def read_uploaded_file(uploaded_file):
    # uploaded_file.name é o nome do arquivo com extensão, ex: “dados.xlsx” ou “alunos.csv”
    _, ext = os.path.splitext(uploaded_file.name.lower())
    if ext in (".xls", ".xlsx"):
        df = pd.read_excel(uploaded_file)
    elif ext == ".csv":
        df = pd.read_csv(uploaded_file)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")
    return df

def main():
    st.title("Visualizador Didático")

    uploaded_file = st.file_uploader("Carregue sua planilha", type=["csv", "xlsx"])
    if uploaded_file is None:
        st.info("Por favor, carregue uma planilha para começar.")
        return

    df = read_uploaded_file(uploaded_file)

    # Sidebar: ações que usuário pode executar
    st.sidebar.header("Filtragem")

    # Filtro por texto em coluna de string (se aplicável)
    col_str_choices = [c for c in df.columns if df[c].dtype == object]
    col_str = st.sidebar.selectbox("Coluna de texto para filtrar (opcional)", ["---"] + col_str_choices)
    filtro_texto = None
    if col_str != "---":
        filtro_texto = st.sidebar.text_input(f"Filtrar '{col_str}' que contêm:")

    # Ordenação
    col_ord = st.sidebar.selectbox("Ordenar por coluna", df.columns)
    ordem = st.sidebar.radio("Ordem", ["Crescente", "Decrescente"])

    # Botão para aplicar ações
    aplicar = st.sidebar.button("Aplicar")

    # Copiar o DataFrame original para aplicar filtros/ordenar
    df_proc = df.copy()

    if aplicar:
        # aplicar filtro de texto
        if filtro_texto and col_str != "---":
            df_proc = df_proc[df_proc[col_str].str.contains(filtro_texto, na=False, case=False)]

        # ordenar
        asc = (ordem == "Crescente")
        df_proc = df_proc.sort_values(by=col_ord, ascending=asc)

    # Segundo bloco: mostrar resultados após ações
    st.subheader("Resultado")

    # Mostrar tabela processada
    st.dataframe(df_proc, use_container_width=True)

if __name__ == "__main__":
    main()
