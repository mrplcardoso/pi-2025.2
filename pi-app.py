import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

def read_uploaded_file(uploaded_file):
    _, ext = os.path.splitext(uploaded_file.name.lower())
    if ext in (".xls", ".xlsx"):
        try:
            df = pd.read_excel(uploaded_file, header=[0,1])
            # dict_dfs é algo como {'Sheet1': df1, 'Sheet2': df2, ...}
            # Agora concatenar todos em um só df
            # manter o nome da planilha como coluna opcional (se quiser)
            list_dfs = []
            for sheet_name, df in dict_dfs.items():
                # opcional: adicionar coluna indicando a planilha de origem
                df["__sheet_name"] = sheet_name
                list_dfs.append(df)
            # concatenar (ignore_index=True para renumerar índice)
            df = pd.concat(list_dfs, ignore_index=True)
            # se MultiIndex, achatar
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
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, header=0)
    elif ext == ".csv":
        df = pd.read_csv(uploaded_file)
    else:
        raise ValueError(f"Extensão não suportada: {ext}")
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
