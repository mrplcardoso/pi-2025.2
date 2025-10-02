import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def show_header_info(df):
    st.subheader("Estrutura dos Dados")
    # criar um DataFrame auxiliar com nome de coluna e tipo
    info = {
        "Coluna": df.columns,
        "Tipo": [str(df[col].dtype) for col in df.columns]
    }
    df_info = pd.DataFrame(info)
    st.table(df_info)

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

    # Filtro numérico por intervalo
    col_num_choices = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    col_num = st.sidebar.selectbox("Coluna numérica para filtrar intervalo (opcional)", ["---"] + col_num_choices)
    intervalo = None
    if col_num != "---":
        vmin = float(df[col_num].min())
        vmax = float(df[col_num].max())
        intervalo = st.sidebar.slider(f"Intervalo para {col_num}", vmin, vmax, (vmin, vmax))

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

        # aplicar filtro de intervalo numérico
        if intervalo and col_num != "---":
            df_proc = df_proc[df_proc[col_num].between(intervalo[0], intervalo[1])]

        # ordenar
        asc = (ordem == "Crescente")
        df_proc = df_proc.sort_values(by=col_ord, ascending=asc)

    # Segundo bloco: mostrar resultados após ações
    st.subheader("Resultados")

    # Mostrar tabela processada
    st.dataframe(df_proc, use_container_width=True)

    # Mostrar gráfico (exemplo simples)
    if aplicar:
        st.subheader("Gráfico")
        # exemplo de gráfico: contagem por disciplina ou coluna categórica
        # aqui escolho a coluna de ordenação como exemplo
        try:
            counts = df_proc[col_ord].value_counts()
            fig, ax = plt.subplots()
            counts.plot(kind="bar", ax=ax)
            st.pyplot(fig)
        except Exception as e:
            st.write("Não foi possível gerar gráfico:", e)

if __name__ == "__main__":
    main()
