# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
from pandas.core.base import PandasObject
from pandas.core.interchange.dataframe_protocol import DataFrame
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

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

def read_uploaded_file(uploaded_file: str):
    """
    Lê o arquivo (CSV ou Excel com múltiplas planilhas),
    achata cabeçalhos multilinha e concatena as planilhas.
    Retorna um DataFrame “plano”.
    """
    _, ext = os.path.splitext(uploaded_file.lower())
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

# =========================================
# 1. Leitura dos dados
# =========================================
# Substitua o caminho abaixo pelo seu arquivo
# df = pd.read_excel("Dados da Escola.xlsx")
df = read_uploaded_file("Dados da Escola.xlsx")

# Exibe as 5 primeiras linhas para conferir
#print("Prévia dos dados:")
#print(df.head())

# =========================================
# 2. Seleção das colunas numéricas relevantes
# =========================================
# Vamos considerar apenas notas e idade para os clusters
colunas_notas = ['DADOS GERAIS - IDADE', 'NOTAS - LP', 'NOTAS - LI', 'NOTAS - BIO', 'NOTAS - FÍS',
                 'NOTAS - QUÍ', 'NOTAS - MAT', 'NOTAS - GEO', 'NOTAS - HIS', 'NOTAS - FIL', 'NOTAS - SOC']
df_numerico = df[colunas_notas].dropna()

# =========================================
# 3. Padronização dos dados (muito importante)
# =========================================
scaler = StandardScaler()
dados_padronizados = scaler.fit_transform(df_numerico)

# =========================================
# 4. Determinar número ideal de clusters (metodo do cotovelo)
# =========================================
inercia = []
for k in range(1, 10):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(dados_padronizados)
    inercia.append(kmeans.inertia_)

plt.plot(range(1, 10), inercia, marker='o')
plt.title('Método do Cotovelo')
plt.xlabel('Número de Clusters (k)')
plt.ylabel('Inércia')
plt.grid(True)
#plt.show()
plt.savefig("grafico_inercia.png", dpi=300, bbox_inches='tight')
print("Gráfico salvo como grafico_clusters.png")

# =========================================
# 5. Treinar o modelo K-Means
# =========================================
# Supondo que você observou o gráfico e escolheu, por exemplo, k=3
k = 3
modelo = KMeans(n_clusters=k, random_state=42)
df['Cluster'] = modelo.fit_predict(dados_padronizados)

# =========================================
# 6. Redução de dimensão para visualização (PCA)
# =========================================
pca = PCA(n_components=2)
componentes = pca.fit_transform(dados_padronizados)

plt.figure(figsize=(8, 6))
plt.scatter(componentes[:, 0], componentes[:, 1], c=df['Cluster'], cmap='viridis')
plt.title('Clusters de alunos (reduzido a 2D pelo PCA)')
plt.xlabel('Componente Principal 1')
plt.ylabel('Componente Principal 2')
plt.colorbar(label='Cluster')
#plt.show()
plt.savefig("grafico_clusters.png", dpi=300, bbox_inches='tight')
print("Gráfico salvo como grafico_clusters.png")

# =========================================
# 7. Análise dos clusters
# =========================================
media_clusters = df.groupby('Cluster')[colunas_notas].mean()
print("\nMédias por cluster:")
print(media_clusters)

# =========================================
# 8. Gráfico de barras das médias
# =========================================
plt.figure(figsize=(10, 6))
media_clusters.T.plot(kind='bar')
plt.title('Médias das disciplinas por cluster')
plt.xlabel('Disciplinas')
plt.ylabel('Média das notas')
plt.legend(title='Cluster')
plt.tight_layout()
plt.savefig("grafico_medias_por_cluster.png", dpi=300, bbox_inches='tight')
print("Gráfico de médias por cluster salvo como grafico_medias_por_cluster.png")

# =========================================
# 9. Distribuição de alunos por PERÍODO e Cluster
# =========================================
if 'DADOS GERAIS - PERIODO' in df.columns:
    dist_periodo = pd.crosstab(df['DADOS GERAIS - PERIODO'], df['Cluster'])
    print("\nDistribuição de alunos por período e cluster:")
    print(dist_periodo)

    plt.figure(figsize=(8, 6))
    dist_periodo.plot(kind='bar')
    plt.title('Número de alunos por período em cada cluster')
    plt.xlabel('Período')
    plt.ylabel('Número de alunos')
    plt.legend(title='Cluster')
    plt.tight_layout()
    plt.savefig("grafico_periodo_por_cluster.png", dpi=300, bbox_inches='tight')
    print("Gráfico de distribuição por período salvo como grafico_periodo_por_cluster.png")
else:
    print("\n⚠️ Coluna 'PERIODO' não encontrada no arquivo. Gráfico não gerado.")

# Salvar o resultado
df.to_csv("dados_com_clusters.csv", index=False)
print("\nArquivo salvo como dados_com_clusters.csv")
