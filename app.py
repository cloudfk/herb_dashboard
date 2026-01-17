import streamlit as st
from data_loader import load_data
from analysis import PrescriptionAnalyzer
import pandas as pd

st.set_page_config(layout="wide", page_title="Herbal Prescription Comparison")

st.title("🌿 Herbal Prescription Mechanism Comparison")

# Sidebar
st.sidebar.header("Configuration")

# Reload Button
if st.sidebar.button("🔄 Real-time Data Refresh"):
    st.cache_data.clear()
    st.rerun()

# Load Data
with st.spinner("Loading data from Google Sheets..."):
    df_pres, df_herb, df_path = load_data()

if df_pres.empty:
    st.stop()

# Selectors
if not df_pres.empty:
    # Assuming first column is Prescription Name
    pres_col = df_pres.columns[0]
    presoptions = sorted(df_pres[pres_col].unique().tolist())
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        pres_a = st.selectbox("Prescription A", presoptions, index=0 if len(presoptions)>0 else 0)
    with col2:
        # Default second one
        pres_b = st.selectbox("Prescription B", presoptions, index=1 if len(presoptions)>1 else 0)

# Main Logic
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

    # Debug / Raw Data View (Optional)
    with st.expander("View Raw Data Segments"):
        st.write("Filtered Data for Selection:")
        st.dataframe(analyzer.get_filtered_data().head(20))

else:
    st.warning("Please select prescriptions.")
