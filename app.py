import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix

# Configuració de la pàgina
st.set_page_config(page_title="Laboratori Espacial - Tesi", layout="wide")
st.title("🔬 Laboratori Espacial: Xarxes de Gènere urbà")

@st.cache_data
def carregar_dades():
    try:
        df = pd.read_csv("Dades_Tesi.csv", sep=";")
    except:
        df = pd.read_csv("Dades_Tesi.csv", sep=",")
        
    # Netejar coordenades
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

# --- SECCIÓ DIDÀCTICA ---
with st.expander("📘 Quins càlculs fa aquesta aplicació i per què? (Metodologia)"):
    st.markdown("""
    Aquest laboratori no només dibuixa punts, sinó que aplica anàlisi de xarxes espacials (*Spatial Network Analysis*) per entendre com s'organitza la ciutat segons el gènere:
    * **1. Matriu de Distàncies:** L'algoritme aplica el Teorema de Pitàgores sobre les coordenades UTM (X, Y) per calcular la distància en línia recta de cada establiment a tots els altres, ignorant els que superin el radi establert.
    * **2. Homofília (Newman):** Compara les interaccions reals entre espais del mateix gènere amb la probabilitat que s'ajuntin per pur atzar. Si el resultat s'acosta a 0, la ciutat està altament barrejada.
    * **3. Coocurrència:** Comptabilitza les afinitats espacials per descobrir quines activitats econòmiques formen "clústers" de proximitat.
    * **4. Centralitat d'Intermediació (Ponts):** Multiplica les connexions femenines per les masculines de cada local. Els establiments amb puntuacions altes actuen com a "Frontisses Urbanes", indispensables per evitar la fragmentació de l'ecosistema comercial.
    """)

# --- MOTOR DE CÀLCUL ---
if st.button("🚀 Executar Super-Càlcul Espacial"):
    with st.spinner("Creuant matriu espacial. Això pot trigar uns segons..."):
        # 1. Preparar vectors matemàtics
        coords = df[['X', 'Y']].values
        dist_mat = distance_matrix(coords, coords)
        
        # 2. Filtrar pel radi seleccionat pel control lliscant
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
        
        # 3. L'escombrat node a node
        for i in range(len(df)):
            veins = np.where(adj_matrix[i])[0]
            gen_i = df_gen[i]
            tipo_i = df_tipo[i]
            
            links_fem, links_masc = 0, 0
            
            for v in veins:
                gen_v = df_gen[v]
                tipo_v = df_tipo[v]
                
                # Comptar per a la centralitat d'aquest node
                if gen_v == 'FEM':
                    links_fem += 1
                else:
                    links_masc += 1
                    
                # Comptar coocurrència i fraccions (només en una direcció per no duplicar)
                if v > i:
                    if gen_i == 'FEM' and gen_v == 'FEM':
                        fem_fem += 1
                    elif gen_i == 'MASC' and gen_v == 'MASC':
                        masc_masc += 1
                    else:
                        creuades += 1
                        
                    # Agrupem la parella ordenant alfabèticament per evitar Bar-Forn i Forn-Bar separats
                    par = tuple(sorted([f"{tipo_i} ({gen_i})", f"{tipo_v} ({gen_v})"]))
                    cooc_dict[par] = cooc_dict.get(par, 0) + 1
                    
            # Guardem la centralitat d'aquest local concret
            score_pont = links_fem * links_masc
            ponts_data.append({
                'ID': df_id[i],
                'Tipologia': tipo_i,
                'Gènere': gen_i,
                'Conn. FEM': links_fem,
                'Conn. MASC': links_masc,
                'Score Pont': score_pont
            })
            
        st.success(f"Càlcul completat! A {radi} metres hi ha **{total_connexions}** connexions actives a la xarxa.")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Clúster FEM-FEM", fem_fem)
        c2.metric("Clúster MASC-MASC", masc_masc)
        c3.metric("Connexions Creuades", creuades)
        
        st.divider()
        
        # --- HOMOFÍLIA ---
        st.subheader("1. Hibridació Espacial (Índex d'Homofília)")
        frac_iguals = (fem_fem + masc_masc) / total_connexions
        
        conn_totals_fem = (fem_fem * 2) + creuades
        conn_totals_masc = (masc_masc * 2) + creuades
        punts_totals = conn_totals_fem + conn_totals_masc
        
        prob_fem = conn_totals_fem / punts_totals if punts_totals > 0 else 0
        prob_masc = conn_totals_masc / punts_totals if punts_totals > 0 else 0
        prob_atzar = (prob_fem**2) + (prob_masc**2)
        
        r_index = (frac_iguals - prob_atzar) / (1 - prob_atzar) if prob_atzar < 1 else 0
        
        st.info(f"**Índex d'Assortativitat (r): {round(r_index, 4)}**")
        st.caption("*(Interpretació: 0 = Barreja urbana perfecta i estructurada a l'atzar / 1 = Segregació total en 'guetos' de gènere).*")
        
        st.divider()
        
        col_A, col_B = st.columns(2)
        
        with col_A:
            st.subheader("2. Rànquing de Coocurrència")
            cooc_list = [{'Parella Espacial': f"{p[0]} ↔ {p[1]}", 'Vegades': count} for p, count in cooc_dict.items()]
            df_cooc = pd.DataFrame(cooc_list).sort_values(by='Vegades', ascending=False).head(15)
            st.dataframe(df_cooc, hide_index=True)
            
        with col_B:
            st.subheader("3. Ancoratges de Ciutat (Nodes Pont)")
            df_ponts = pd.DataFrame(ponts_data)
            df_ponts = df_ponts[df_ponts['Score Pont'] > 0] 
            df_ponts = df_ponts.sort_values(by='Score Pont', ascending=False).head(15)
            st.dataframe(df_ponts, hide_index=True)