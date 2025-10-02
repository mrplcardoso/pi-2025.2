import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def show_header_info(df):
    # Queremos duas linhas: primeira linha = nomes das colunas; segunda linha = tipos de dados
    cols = list(df.columns)
    tipos = [str(df[col].dtype) for col in cols]

    # Criar um DataFrame pequeno transposto
    # Linha 1: nomes das colunas
    # Linha 2: tipos
    df_header = pd.DataFrame([cols, tipos], index=['Coluna', 'Tipo'])

    # Transpor, para que as colunas originais virem colunas no df_header
    # Aqui df_header.T vai ter:
    #   índice = nomes das colunas originais
    #   colunas = “Coluna” e “Tipo”

    df_header_t = df_header.T

    st.subheader("Estrutura dos Dados")
    # Usar st.dataframe ou st.table
    st.table(df_header_t)

def main():
    st.title("Visualizador Didático")

    uploaded_file = st.file_uploader("Carregue seu arquivo .csv", type=["csv"])
    if uploaded_file is None:
        st.info("Por favor, carregue um arquivo .scv para começar.")
        return

    df = pd.read_csv(uploaded_file)

    # Mostrar cabeçalho + tipos de dados
    show_header_info(df)

    # Sidebar: ações que usuário pode executar
    st.sidebar.header("Ações / Filtros")

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
    st.subheader("Resultados")

    # Mostrar tabela processada
    st.dataframe(df_proc, use_container_width=True)

if __name__ == "__main__":
    main()
