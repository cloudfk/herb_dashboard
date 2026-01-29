import streamlit as st
from data_loader import load_data
from analysis import PrescriptionAnalyzer
import pandas as pd

st.set_page_config(layout="wide", page_title="Herbal Dashboard")

def render_mechanism_page(df_pres, df_herb, sankey_mode='condensed'):
    st.title("🔬 Deep Mechanism Analysis")
    st.info("이 페이지는 선택된 처방의 [약재 -> 성분 -> 타켓 단백질 -> 핵심작용]으로 이어지는 생물학적 기전을 시각화합니다.")


    # Selector
    if not df_pres.empty:
        pres_col = df_pres.columns[0]
        presoptions = sorted(df_pres[pres_col].unique().tolist())
        
        target_pres = st.sidebar.selectbox("Select Prescription", presoptions, key="mech_pres")

        if target_pres:
            analyzer = PrescriptionAnalyzer(df_pres, df_herb, target_pres, target_pres)
            st.header(f"Prescription Mechanism: {target_pres}")
            
            # Visualization Options
            viz_type = "Sankey (Flow)"
            if sankey_mode == 'condensed':
                st.sidebar.divider()
                st.sidebar.subheader("Visualization Type")
                viz_type = st.sidebar.radio(
                    "Select Visual Form",
                    ["Sankey (Flow)", "Sunburst (Hierarchy)"],
                    index=0,
                    help="연결성을 강조하려면 Sankey, 계층 구조와 비중을 강조하려면 Sunburst를 선택하세요."
                )

            # Visualization
            st.subheader(f"Mechanism Visualization ({viz_type})")
            if sankey_mode == 'deep':
                st.caption("Flow: Prescription -> Herb -> Ingredient -> Target -> Core Action")
            else:
                st.caption("Flow: Prescription -> Herb -> Core Action (Summarized)")
                
            if "Sunburst" in viz_type:
                fig = analyzer.generate_sunburst(target_pres)
            else:
                fig = analyzer.generate_single_sankey(target_pres, mode=sankey_mode)
            
            st.plotly_chart(fig, use_container_width=True)

            
            # Insights
            st.divider()
            _, active_loops = analyzer.get_common_insights()
            
            if active_loops:
                st.success(f"**Identified Core Actions ({len(active_loops)})**")
                st.write(", ".join(sorted(active_loops)))

def render_intuitive_comparison_page(df_pres, df_herb):
    # Custom CSS for glassmorphism and card styling
    st.markdown("""
    <style>
    .pres-card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        transition: transform 0.3s ease;
    }
    .pres-card:hover {
        transform: translateY(-5px);
    }
    .card-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .herb-item {
        font-size: 0.9em;
        padding: 4px 8px;
        border-radius: 5px;
        margin: 2px 0;
        display: inline-block;
        background: rgba(255, 255, 255, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎯 Intuitive Comparative Analysis")
    st.info("이 페이지는 두 처방의 공통 성분과 독자적 성분, 그리고 핵심 효능의 분포를 직관적으로 비교합니다.")

    if not df_pres.empty:
        pres_col = df_pres.columns[0]
        presoptions = sorted(df_pres[pres_col].unique().tolist())
        
        c1, c2 = st.sidebar.columns(2)
        with c1:
            pres_a = st.selectbox("Prescription A", presoptions, index=0 if len(presoptions)>0 else 0, key="int_a")
        with c2:
            pres_b = st.selectbox("Prescription B", presoptions, index=1 if len(presoptions)>1 else 0, key="int_b")

        if pres_a and pres_b:
            analyzer = PrescriptionAnalyzer(df_pres, df_herb, pres_a, pres_b)
            profiles = analyzer.get_comparison_profiles()
            
            st.header(f"⚖️ {pres_a} vs {pres_b}")
            
            # 1. Herb Overlap (Styled Cards)
            st.subheader("🌿 Herb Composition Comparison")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="pres-card" style="background: rgba(255, 75, 75, 0.05); border-left: 5px solid #FF4B4B;">
                    <div class="card-title"><span style='color:#FF4B4B'>🔴</span> Only {pres_a}</div>
                    {"".join([f'<div class="herb-item">{h}</div>' for h in profiles['herbs']['only_a']])}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="pres-card" style="background: rgba(128, 0, 128, 0.05); border-left: 5px solid #800080;">
                    <div class="card-title"><span style='color:#800080'>🟣</span> Shared Herbs</div>
                    {"".join([f'<div class="herb-item" style="font-weight:bold; color:#800080;">{h}</div>' for h in profiles['herbs']['shared']])}
                </div>
                """, unsafe_allow_html=True)
                    
            with col3:
                st.markdown(f"""
                <div class="pres-card" style="background: rgba(0, 102, 204, 0.05); border-left: 5px solid #0066CC;">
                    <div class="card-title"><span style='color:#0066CC'>🔵</span> Only {pres_b}</div>
                    {"".join([f'<div class="herb-item">{h}</div>' for h in profiles['herbs']['only_b']])}
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # 2. Functional Profile (Grouped Bar Chart)
            st.subheader("📈 Herb Composition & Action Comparison")
            st.caption("차트 막대의 높이는 처방 내 약재 용량(Amount)을 나타내며, 툴팁에서 해당 약재의 핵심작용(Core Action)을 확인할 수 있습니다.")
            
            df_plot = pd.DataFrame(profiles['actions'])
            if not df_plot.empty:
                import plotly.express as px
                
                # Sort by amount and category for better visualization
                df_plot['Total_Amount'] = df_plot[pres_a] + df_plot[pres_b]
                df_plot = df_plot.sort_values(by=['Category', 'Total_Amount'], ascending=[True, False])

                fig = px.bar(
                    df_plot, 
                    x="Herb", 
                    y=[pres_a, pres_b], 
                    barmode="group",
                    hover_data={"Herb": True, "Category": True, "Actions": True, "value": ":.1f", "variable": False},
                    labels={"value": "Amount", "variable": "Prescription", "Herb": "Herb Name"},
                    color_discrete_map={pres_a: "#FF4B4B", pres_b: "#0066CC"}
                )
                
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>Amount: %{y}<br>Category: %{customdata[1]}<br>Core Actions:<br>%{customdata[2]}"
                )

                fig.update_layout(
                    height=600, 
                    font_size=12,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis={'categoryorder':'array', 'categoryarray':df_plot['Herb'], 'tickangle':45},
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=50, b=100)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Action Distribution (Donut Chart)
                st.subheader("📊 Action Theme Distribution")
                st.caption("두 처방에서 나타나는 핵심작용(Core Action) 테마들의 비중을 비교합니다.")
                
                # Flatten the 'Actions' list and count frequencies
                def get_action_counts(pres_name):
                    actions = []
                    for _, row in df_plot.iterrows():
                        if row[pres_name] > 0:
                            for a in row['Actions'].split(', '):
                                actions.append(a.strip())
                    return pd.Series(actions).value_counts()

                counts_a = get_action_counts(pres_a)
                counts_b = get_action_counts(pres_b)
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    fig_a = px.pie(values=counts_a.values, names=counts_a.index, title=f"Action Themes: {pres_a}", hole=0.4)
                    fig_a.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_a, use_container_width=True)
                with col_c2:
                    fig_b = px.pie(values=counts_b.values, names=counts_b.index, title=f"Action Themes: {pres_b}", hole=0.4)
                    fig_b.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_b, use_container_width=True)
            else:
                st.warning("No functional mapping available for these prescriptions.")


def render_inference_page(df_pres, df_herb, df_script):
    st.title("🔍 Pathology Situation Inference")
    st.info("이 페이지는 선정된 처방의 약재와 그 타겟 단백질, 경로(Pathway) 및 작용(Action)을 분석하여 어떠한 병리적 상황을 해결하려 하는지 유추합니다.")
    
    if not df_pres.empty:
        pres_col = df_pres.columns[0]
        presoptions = sorted(df_pres[pres_col].unique().tolist())
        
        target_pres = st.sidebar.selectbox("Select Prescription", presoptions)
        
        if target_pres:
            # Display Clinical Script if available
            if df_script is not None and not df_script.empty:
                relevant_script = df_script[df_script['Prescription_Name'] == target_pres]
                if not relevant_script.empty:
                    st.subheader("📋 Clinical Context (Traditional Indications)")
                    st.info("이 처방이 전통적으로 어떤 증상을 해결하기 위해 사용되는지 설명합니다.")
                    for _, row in relevant_script.iterrows():
                        with st.expander(f"📌 {row['Symptom_Status']}"):
                            st.write(row['Explanation'])
                    st.divider()

            # We can use PrescriptionAnalyzer with dummy values for B
            analyzer = PrescriptionAnalyzer(df_pres, df_herb, target_pres, target_pres)
            df_inf = analyzer.get_inference_data(target_pres)
            
            st.header(f"Prescription: {target_pres}")
            
            # 1. Summary of Evidence
            st.subheader("💡 Key Pathological Themes")
            st.info("이 처방이 집중하고 있는 주요 병리적 통제 포인트입니다.")
            
            # Group by Core Action to show common themes
            pathway_summary = df_inf.groupby([analyzer.col_herb_loop]).size().reset_index(name='Target_Interaction_Count')
            pathway_summary = pathway_summary.sort_values(by='Target_Interaction_Count', ascending=False)
            
            # Show top themes as tags
            top_themes = pathway_summary.head(10)
            theme_html = "".join([f'<span style="background-color: #f0f2f6; color: #1f77b4; padding: 5px 10px; border-radius: 15px; margin: 5px; display: inline-block; font-weight: bold; border: 1px solid #1f77b4;">#{row[analyzer.col_herb_loop]} ({row["Target_Interaction_Count"]})</span>' for _, row in top_themes.iterrows()])
            st.markdown(theme_html, unsafe_allow_html=True)
            st.divider()
            
            # 2. Detailed View
            st.subheader("🧪 Detailed Mechanism Evidence")
            st.caption("각 약재가 어떤 성분을 통해 어떤 단백질을 조절하여 핵심작용을 수행하는지 상세 데이터를 제공합니다.")
            
            # Group by Herb for better readability
            herbs = sorted(df_inf['Herb_Name'].unique())
            for herb in herbs:
                with st.expander(f"🌿 Herb: {herb}"):
                    herb_data = df_inf[df_inf['Herb_Name'] == herb]
                    # Show unique combinations of Compound, Target, Action
                    display_cols = ['Compound_Name', 'Target_Protein', analyzer.col_herb_loop, analyzer.col_herb_desc]
                    # Keep only existing columns
                    existing_cols = [c for c in display_cols if c in herb_data.columns]
                    st.dataframe(herb_data[existing_cols].drop_duplicates(), use_container_width=True, hide_index=True)


def main():
    # --- App Loading ---
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Mechanism Analysis", "Intuitive Comparison", "Pathology Inference"])
    
    # Reload Button
    if st.sidebar.button("🔄 Real-time Data Refresh"):
        st.cache_data.clear()
        st.rerun()
    
    # Load Data
    with st.spinner("Loading data..."):
        df_pres, df_herb, df_script = load_data()
    
    if df_pres.empty:
        st.error("Failed to load data. Please check the Google Sheet connection.")
        st.stop()
    
    view_mode = "Condensed (Herb-Action)"
    if page == "Mechanism Analysis":
        st.sidebar.divider()
        st.sidebar.subheader("Analysis Depth")
        view_mode = st.sidebar.radio(
            "Select Detail Level",
            ["Condensed (Herb-Action)", "Detailed (Molecular)"],
            index=0,
            help="성분(Ingredient)과 타겟 단백질(Target) 수준의 복잡한 생물학적 기전을 보려면 'Detailed'를 선택하세요."
        )
    
    sankey_mode = 'deep' if "Detailed" in view_mode else 'condensed'
    
    if page == "Mechanism Analysis":
        render_mechanism_page(df_pres, df_herb, sankey_mode)
    elif page == "Intuitive Comparison":
        render_intuitive_comparison_page(df_pres, df_herb)
    else:
        render_inference_page(df_pres, df_herb, df_script)


if __name__ == "__main__":
    main()
