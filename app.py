import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix

# Configuració de la pàgina
st.set_page_config(page_title="Laboratori Espacial - Tesi", layout="wide")
st.title("🔬 Laboratori Espacial: Xarxes de Codificació Masculina")

@st.cache_data
def carregar_dades():
    try:
        df = pd.read_csv("Dades_Tesi.csv", sep=";")
    except:
        df = pd.read_csv("Dades_Tesi.csv", sep=",")
        
    df['X'] = df['X'].astype(str).str.strip().str.replace(',', '.')
    df['Y'] = df['Y'].astype(str).str.strip().str.replace(',', '.')
    df['X'] = pd.to_numeric(df['X'], errors='coerce')
    df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        
    df = df.dropna(subset=['X', 'Y', 'GENERE', 'Tipologia'])
    return df.reset_index(drop=True)

df = carregar_dades()

# --- BARRA LATERAL ---
st.sidebar.header("🕹️ Controls de l'Entorn")
radi = st.sidebar.slider("Radi d'interacció (metres):", min_value=10, max_value=300, value=100, step=10)

st.write(f"S'han carregat correctament **{len(df)}** establiments comercials.")

# --- SECCIÓ DIDÀCTICA I FÓRMULES ---
with st.expander("📘 Quins càlculs fa aquesta aplicació i per què? (Metodologia)"):
    st.markdown("""
    Aquest laboratori aplica anàlisi de xarxes espacials (*Spatial Network Analysis*) per entendre l'organització urbana. Analitzem específicament les interaccions entre dos espais de codificació masculina (registrats operativament a la base de dades amb les etiquetes FEM i MASC per diferenciar les seves tipologies):
    
    **1. Matriu de Distàncies Espacials:** Calcula la distància euclidiana en línia recta entre tots els punts de la ciutat.
    """)
    st.latex(r"d(P_1, P_2) = \sqrt{(X_2 - X_1)^2 + (Y_2 - Y_1)^2}")
    
    st.markdown("""
    **2. Homofília (Assortativitat de Newman):** Compara les interaccions reals entre locals del mateix tipus amb la probabilitat que s'ajuntin per atzar. Un resultat proper a 0 indica barreja total; proper a 1 indica segregació.
    """)
    st.latex(r"r = \frac{\sum e_{ii} - \sum a_i^2}{1 - \sum a_i^2}")
    
    st.markdown("""
    **3. Coocurrència:** Comptabilitza les afinitats espacials pures per descobrir quines activitats formen "clústers".
    
    **4. Centralitat d'Intermediació (Nodes Pont):** Identifica els establiments que actuen com a "Frontisses Urbanes", mantenint la cohesió entre les diferents xarxes. Es calcula multiplicant les connexions de les dues categories en un mateix radi.
    """)
    st.latex(r"Score_{pont} = K_{grupA} \times K_{grupB}")

# --- MOTOR DE CÀLCUL ---
if st.button("🚀 Executar Super-Càlcul Espacial"):
    with st.spinner("Creuant matriu espacial. Això pot trigar uns segons..."):
        coords = df[['X', 'Y']].values
        dist_mat = distance_matrix(coords, coords)
        
        adj_matrix = (dist_mat <= radi) & (dist_mat > 0)
        total_connexions = int(np.sum(adj_matrix) / 2)
        
        if total_connexions == 0:
            st.warning("No hi ha interaccions a aquesta distància. Prova d'ampliar el radi.")
            st.stop()
            
        df_gen = df['GENERE'].values
        df_tipo = df['Tipologia'].values
        df_id = df['fid'].values
        
        fem_fem, masc_masc, creuades = 0, 0, 0
        cooc_dict = {}
        ponts_data = []
        
        for i in range(len(df)):
            veins = np.where(adj_matrix[i])[0]
            gen_i = df_gen[i]
            tipo_i = df_tipo[i]
            
            links_fem, links_masc = 0, 0
            
            for v in veins:
                gen_v = df_gen[v]
                tipo_v = df_tipo[v]
                
                if gen_v == 'FEM': links_fem += 1
                else: links_masc += 1
                    
                if v > i:
                    if gen_i == 'FEM' and gen_v == 'FEM': fem_fem += 1
                    elif gen_i == 'MASC' and gen_v == 'MASC': masc_masc += 1
                    else: creuades += 1
                        
                    par = tuple(sorted([f"{tipo_i} ({gen_i})", f"{tipo_v} ({gen_v})"]))
                    cooc_dict[par] = cooc_dict.get(par, 0) + 1
                    
            score_pont = links_fem * links_masc
            ponts_data.append({
                'ID': df_id[i],
                'Tipologia': tipo_i,
                'Gènere': gen_i,
                'Conn. Grup A': links_fem,
                'Conn. Grup B': links_masc,
                'Score Pont': score_pont
            })
            
        st.success("Càlcul completat amb èxit!")
        
        # --- 1. MATRIU DE DISTÀNCIES ---
        st.subheader("1. Matriu de Distàncies i Interaccions Globals")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Connexions Totals", total_connexions)
        c2.metric("Connexions A-A", fem_fem)
        c3.metric("Connexions B-B", masc_masc)
        c4.metric("Connexions Creuades", creuades)
        
        st.divider()
        
        # --- 2. HOMOFÍLIA ---
        st.subheader("2. Hibridació Espacial (Índex d'Homofília de Newman)")
        frac_iguals = (fem_fem + masc_masc) / total_connexions
        
        conn_totals_fem = (fem_fem * 2) + creuades
        conn_totals_masc = (masc_masc * 2) + creuades
        punts_totals = conn_totals_fem + conn_totals_masc
        
        prob_fem = conn_totals_fem / punts_totals if punts_totals > 0 else 0
        prob_masc = conn_totals_masc / punts_totals if punts_totals > 0 else 0
        prob_atzar = (prob_fem**2) + (prob_masc**2)
        
        r_index = (frac_iguals - prob_atzar) / (1 - prob_atzar) if prob_atzar < 1 else 0
        
        st.info(f"**Índex d'Assortativitat (r): {round(r_index, 4)}**")
        st.caption("Un índex proper a 0 confirma que els dos espais de codificació masculina conviuen perfectament a la trama urbana sense formar clústers aïllats per categoria.")
        
        st.divider()
        
        # --- 3 i 4. RÀNQUINGS ---
        col_A, col_B = st.columns(2)
        
        with col_A:
            st.subheader("3. Rànquing de Coocurrència")
            cooc_list = [{'Parella Espacial': f"{p[0]} ↔ {p[1]}", 'Connexions': count} for p, count in cooc_dict.items()]
            df_cooc = pd.DataFrame(cooc_list).sort_values(by='Connexions', ascending=False).head(15)
            st.dataframe(df_cooc, hide_index=True, use_container_width=True)
            
        with col_B:
            st.subheader("4. Centralitat d'Intermediació (Nodes Pont)")
            df_ponts = pd.DataFrame(ponts_data)
            df_ponts = df_ponts[df_ponts['Score Pont'] > 0] 
            df_ponts = df_ponts.sort_values(by='Score Pont', ascending=False).head(15)
            st.dataframe(df_ponts, hide_index=True, use_container_width=True)