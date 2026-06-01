import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix

st.set_page_config(page_title="Laboratori Espacial - Tesi", layout="wide")
st.title("🔬 Laboratori Espacial: Xarxes de Gènere")

@st.cache_data
def carregar_dades():
    # Provem de llegir amb punt i coma (el format habitual del teu Excel)
    try:
        df = pd.read_csv("Dades_Tesi.csv", sep=";")
    except:
        df = pd.read_csv("Dades_Tesi.csv", sep=",")
        
    df = df.dropna(subset=['X', 'Y', 'GENERE', 'Tipologia'])
    return df

df = carregar_dades()

st.sidebar.header("🕹️ Controls")
radi = st.sidebar.slider("Radi d'anàlisi (metres):", 10, 300, 100, 10)

st.write(f"Base de dades activa: **{len(df)}** establiments.")

if st.button("🚀 Executar Càlcul Espacial"):
    with st.spinner("Calculant distàncies (Teorema de Pitàgores per a tots els punts)..."):
        coords = df[['X', 'Y']].values
        dist_mat = distance_matrix(coords, coords)
        
        # Filtrem els que estan a menys del radi (i que no siguin el mateix punt, distància > 0)
        adj_matrix = (dist_mat <= radi) & (dist_mat > 0)
        total_connexions = int(np.sum(adj_matrix) / 2)
        
        st.success(f"A {radi} metres hi ha **{total_connexions}** connexions actives a la ciutat.")
        
        # Recompte ràpid de clústers
        df_genere = df['GENERE'].values
        fem_fem, masc_masc, creuades = 0, 0, 0
        
        for i in range(len(df)):
            veins = np.where(adj_matrix[i])[0]
            gen_i = df_genere[i]
            for v in veins:
                if v > i: # Per no comptar la mateixa parella dues vegades
                    gen_v = df_genere[v]
                    if gen_i == 'FEM' and gen_v == 'FEM':
                        fem_fem += 1
                    elif gen_i == 'MASC' and gen_v == 'MASC':
                        masc_masc += 1
                    else:
                        creuades += 1
                        
        col1, col2, col3 = st.columns(3)
        col1.metric("Clúster FEM-FEM", fem_fem)
        col2.metric("Clúster MASC-MASC", masc_masc)
        col3.metric("Connexions Creuades", creuades)
        
        st.info("💡 Prova de canviar el radi a l'esquerra i torna a calcular per veure com l'agrupació d'oci (MASC) o de cures (FEM) varia amb la distància.")