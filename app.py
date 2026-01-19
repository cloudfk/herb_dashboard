import streamlit as st
from data_loader import load_data
from analysis import PrescriptionAnalyzer
import pandas as pd

st.set_page_config(layout="wide", page_title="Herbal Dashboard")

def render_comparison_page(df_pres, df_herb, df_path):
    st.title("🌿 Herbal Prescription Mechanism Comparison")
    
    # Selectors
    if not df_pres.empty:
        pres_col = df_pres.columns[0]
        presoptions = sorted(df_pres[pres_col].unique().tolist())
        
        c1, c2 = st.sidebar.columns(2)
        with c1:
            pres_a = st.selectbox("Prescription A", presoptions, index=0 if len(presoptions)>0 else 0)
        with c2:
            pres_b = st.selectbox("Prescription B", presoptions, index=1 if len(presoptions)>1 else 0)

        if pres_a and pres_b:
            analyzer = PrescriptionAnalyzer(df_pres, df_herb, df_path, pres_a, pres_b)
            st.header(f"Comparing: {pres_a} vs {pres_b}")
            
            # Sankey
            st.subheader("Flow Analysis (Sankey Diagram)")
            st.caption("Flow: Prescription -> Herb -> Ingredient -> Pathway")
            fig = analyzer.generate_sankey()
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            st.divider()
            st.subheader("🧬 Biochemical Insights")
            common_targets, common_loops = analyzer.get_common_insights()
            
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.info(f"**Common Target Proteins ({len(common_targets)})**")
                if common_targets:
                    st.write(", ".join(sorted(common_targets)))
                else:
                    st.write("No common targets found.")
            with col_i2:
                st.success(f"**Common Pathology Loops ({len(common_loops)})**")
                if common_loops:
                    st.write(", ".join(sorted(common_loops)))
                else:
                    st.write("No common loops found.")

def render_inference_page(df_pres, df_herb, df_path):
    st.title("🔍 Pathology Situation Inference")
    st.info("이 페이지는 선정된 처방의 약재와 그 타겟 단백질, 경로(Pathway) 및 작용(Action)을 분석하여 어떠한 병리적 상황을 해결하려 하는지 유추합니다.")
    
    if not df_pres.empty:
        pres_col = df_pres.columns[0]
        presoptions = sorted(df_pres[pres_col].unique().tolist())
        
        target_pres = st.sidebar.selectbox("Select Prescription", presoptions)
        
        if target_pres:
            # We can use PrescriptionAnalyzer with dummy values for B
            analyzer = PrescriptionAnalyzer(df_pres, df_herb, df_path, target_pres, target_pres)
            df_inf = analyzer.get_inference_data(target_pres)
            
            st.header(f"Prescription: {target_pres}")
            
            st.subheader("🎨 Physiological Interaction Palette")
            st.info("Visualizing the flow: [Center: Herb] -> [Middle: Action] -> [Outer: Pathology Loop]")
            fig_palette = analyzer.generate_interaction_sunburst(target_pres)
            st.plotly_chart(fig_palette, use_container_width=True)
            
            # 2. Detailed View
            st.divider()
            st.subheader("🧪 Detailed Mechanism")
            
            # Group by Herb for better readability
            herbs = df_inf['Herb_Name'].unique()
            for herb in herbs:
                with st.expander(f"🌿 Herb: {herb}"):
                    herb_data = df_inf[df_inf['Herb_Name'] == herb]
                    # Show unique combinations of Compound, Target, Pathway, Action
                    display_cols = ['Compound_Name (성분)', 'Target_Protein', 'Pathway', 'Action', 'Loop_Node']
                    # Keep only existing columns
                    existing_cols = [c for c in display_cols if c in herb_data.columns]
                    st.table(herb_data[existing_cols].drop_duplicates())

# --- App Loading ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Prescription Comparison", "Pathology Inference"])

# Reload Button
if st.sidebar.button("🔄 Real-time Data Refresh"):
    st.cache_data.clear()
    st.rerun()

# Load Data
with st.spinner("Loading data..."):
    df_pres, df_herb, df_path = load_data()

if df_pres.empty:
    st.error("Failed to load data. Please check the Google Sheet connection.")
    st.stop()

if page == "Prescription Comparison":
    render_comparison_page(df_pres, df_herb, df_path)
else:
    render_inference_page(df_pres, df_herb, df_path)
