import pandas as pd
import plotly.graph_objects as go

class PrescriptionAnalyzer:
    def __init__(self, df_pres, df_herb, pres_a, pres_b):
        self.raw_pres = df_pres
        self.raw_herb = df_herb
        self.pres_a = pres_a
        self.pres_b = pres_b
        
        # Column mapping based on actual data inspection (User confirmed English headers)
        self.col_pres_name = 'Prescription_Name'
        self.col_pres_herb = 'Herb_Name'
        self.col_pres_amount = 'Amount'
        
        # Shared Logic (Merging integrated columns)
        self.col_herb_name = 'Herb_Name'
        self.col_herb_ing = 'Compound_Name'
        self.col_herb_target = 'Target_Protein'
        self.col_herb_loop = 'Core_Action'
        self.col_herb_desc = 'KM_Efficacy'

    def get_filtered_data(self):
        # Filter for A and B
        df = self.raw_pres[self.raw_pres[self.col_pres_name].isin([self.pres_a, self.pres_b])].copy()
        
        # Integrated structure: everything is already in df_herb
        df = pd.merge(df, self.raw_herb, left_on=self.col_pres_herb, right_on=self.col_herb_name, how='left')
        
        return df

    def get_structure(self):
        # We need nodes and links
        # Levels: Prescription -> Herb -> Ingredient -> Loop/Pathway (using Loop as final node for now, or Target)
        # User asked: [Prescription] -> [Herb] -> [Ingredient] -> [Pathway/Loop Node]
        
        df = self.get_filtered_data()
        
        # Determine unique sets for coloring
        # For each Herb, Ingredient, Loop: Is it in A? Is it in B?
        
        # Helpers to get sets
        def get_items(pres_name, col):
            return set(df[df[self.col_pres_name] == pres_name][col].dropna())
        
        herbs_a = get_items(self.pres_a, self.col_pres_herb)
        herbs_b = get_items(self.pres_b, self.col_pres_herb)
        
        ings_a = get_items(self.pres_a, self.col_herb_ing)
        ings_b = get_items(self.pres_b, self.col_herb_ing)
        
        loops_a = get_items(self.pres_a, self.col_herb_loop)
        loops_b = get_items(self.pres_b, self.col_herb_loop)
        
        # Assign colors
        def get_color(item, set_a, set_b):
            in_a = item in set_a
            in_b = item in set_b
            if in_a and in_b:
                return "purple"
            elif in_a:
                return "red"
            elif in_b:
                return "blue"
            else:
                return "grey"
        
        # Build Node List
        # We need unique nodes with indices
        
        # Prescriptions
        nodes = []
        nodes.append({'label': self.pres_a, 'color': 'red', 'type': 'Prescription'})
        nodes.append({'label': self.pres_b, 'color': 'blue', 'type': 'Prescription'})
        
        # Map keys: (Level, Name) -> Index
        node_map = {('Prescription', self.pres_a): 0, ('Prescription', self.pres_b): 1}
        
        def add_nodes(items, set_a, set_b, n_type):
            sorted_items = sorted(list(set_a | set_b))
            start_idx = len(nodes)
            for i, item in enumerate(sorted_items):
                 nodes.append({
                     'label': item,
                     'color': get_color(item, set_a, set_b),
                     'type': n_type
                 })
                 node_map[(n_type, item)] = start_idx + i
        
        add_nodes(herbs_a | herbs_b, herbs_a, herbs_b, 'Herb')
        add_nodes(ings_a | ings_b, ings_a, ings_b, 'Ingredient')
        add_nodes(loops_a | loops_b, loops_a, loops_b, 'Pathway')
        
        # Build Links
        links = []
        
        # 1. Pres -> Herb
        # Group by Pres, Herb to get summed Amount
        grp1 = df.groupby([self.col_pres_name, self.col_pres_herb])[self.col_pres_amount].sum().reset_index()
        for _, row in grp1.iterrows():
            src_name = row[self.col_pres_name]
            tgt_name = row[self.col_pres_herb]
            val = row[self.col_pres_amount]
            
            src_key = ('Prescription', src_name)
            tgt_key = ('Herb', tgt_name)
            
            if pd.notna(src_name) and pd.notna(tgt_name) and val > 0:
                # Link color based on Source (Prescription) is easiest, or relationship.
                # Requirement: "Prescription A related paths are Red..."
                # Link color usually matches source for flow clarity in this case.
                c = 'red' if src_name == self.pres_a else 'blue'
                if src_key in node_map and tgt_key in node_map:
                    links.append({'source': node_map[src_key], 'target': node_map[tgt_key], 'value': val, 'color': c})

        # 2. Herb -> Ingredient
        # Problem: Amounts are definitions. We should propagate the "Flow" from the specific prescription.
        # But Sankey in Plotly sums incoming. 
        # If we just link Herb(Purple) -> Ing(Purple), what color?
        # The prompt says: "Two prescription shared path -> Purple".
        # So strictly, we should have separate links if we want to show the 'Red flow' vs 'Blue flow' through a shared node.
        # However, standard Sankey merges flows at nodes. 
        # To strictly show separate Red/Blue paths, we'd need to duplicate nodes (Herb_A, Herb_B), but that defeats the purpose of "Shared Node".
        # So we stick to standard Sankey: Shared Node = Purple. 
        # Links: If the node is Shared, the outgoing link color is tricky.
        # usually we make the link color semi-transparent grey or purple if both contribute.
        # Simply: 
        # If Link connects (Red -> Red) -> Red
        # (Blue -> Blue) -> Blue
        # (Purple -> Purple) -> Purple?
        # (Red -> Purple) -> Red
        # (Purple -> Red) -> Red (Shouldn't happen)
        # (Purple -> Purple) -> Purple.
        
        # Let's aggregate flows.
        # Actually, best way to calculate flow volume for (Herb -> Ing) is to sum the Amounts of that Herb from A and B.
        # But wait, Herb X has Amount 10 in A, 20 in B. Total 30.
        # Herb X contains Ing Y, Ing Z.
        # We flow 30 to Y and 30 to Z? Or split?
        # I will just default to count or sum. 
        # Let's just create defined links based on existence.
        # Weight/Value: The user said "Line thickness reflects Amount".
        # So for Herb -> Ing, use Sum(Amount of Herb).
        
        # Iterate over all Unique (Herb, Ing) pairs in the library (that are in our subset)
        # Value = Sum of Amounts of this Herb in our filtered DF.
        
        grp2 = df.groupby([self.col_pres_herb, self.col_herb_ing])[self.col_pres_amount].sum().reset_index()
        for _, row in grp2.iterrows():
            src_name = row[self.col_pres_herb]
            tgt_name = row[self.col_herb_ing]
            val = row[self.col_pres_amount]
            
            src_key = ('Herb', src_name)
            tgt_key = ('Ingredient', tgt_name)
            
            if pd.notna(src_name) and pd.notna(tgt_name) and val > 0:
                # Color logic for link
                # If src is Red (only A), link is Red.
                # If src is Blue (only B), link is Blue.
                # If src is Purple (Both), check Target.
                # Actually simpler: check if this specific (Herb->Ing) connection exists in A-chain? 
                # Yes, if Herb is present in A.
                # Is it in B-chain? Yes, if Herb is present in B.
                # Herb is the determinant because Ingredient is intrinsic to Herb.
                src_color = get_color(src_name, herbs_a, herbs_b)
                # If src is purple, the link carries both flows. Color it purple? 
                # Or maybe gradient? Plotly supports 'scales'.
                # Let's use src color.
                if src_key in node_map and tgt_key in node_map:
                    links.append({'source': node_map[src_key], 'target': node_map[tgt_key], 'value': val, 'color': src_color.replace('grey', 'silver')})

        # 3. Ingredient -> Core Action (Pathology Loop)
        # Grouped by 핵심작용 to reduce target-protein level clutter
        grp3 = df.groupby([self.col_herb_ing, self.col_herb_loop])[self.col_pres_amount].sum().reset_index()
        for _, row in grp3.iterrows():
            src_name = row[self.col_herb_ing]
            tgt_name = row[self.col_herb_loop]
            val = row[self.col_pres_amount]
            
            src_key = ('Ingredient', src_name)
            tgt_key = ('Pathway', tgt_name)
            
            if pd.notna(src_name) and pd.notna(tgt_name) and val > 0:
                src_color = get_color(src_name, ings_a, ings_b)
                if src_key in node_map and tgt_key in node_map:
                    links.append({'source': node_map[src_key], 'target': node_map[tgt_key], 'value': val, 'color': src_color.replace('grey', 'silver')})
                
        return nodes, links

    def generate_sankey(self):
        nodes, links = self.get_structure()
        
        # Plotly format
        # node = dict(label=[...], color=[...])
        # link = dict(source=[...], target=[...], value=[...], color=[...])
        
        node_dict = {
            'label': [n['label'] for n in nodes],
            'color': [n['color'] for n in nodes],
            'pad': 40,  # Further increased padding
            'thickness': 12, # Even slimmer nodes to give more room for labels
            'line': dict(color="black", width=0.5)
        }
        
        link_dict = {
            'source': [l['source'] for l in links],
            'target': [l['target'] for l in links],
            'value': [l['value'] for l in links],
            'color': [l['color'].replace('red', 'rgba(255,0,0,0.4)').replace('blue', 'rgba(0,0,255,0.4)').replace('purple', 'rgba(128,0,128,0.4)') for l in links] # Add transparency
        }
        
        fig = go.Figure(data=[go.Sankey(
            node=node_dict,
            link=link_dict
        )])
        
        fig.update_layout(
            title_text=f"{self.pres_a} vs {self.pres_b} Comparison",
            font_size=14, # Larger font
            height=1200, # Taller diagram
            margin=dict(l=40, r=40, t=80, b=40)
        )
        return fig

    def get_common_insights(self):
        df = self.get_filtered_data()
        
        # Filter for Prescription A and B separately
        df_a = df[df[self.col_pres_name] == self.pres_a]
        df_b = df[df[self.col_pres_name] == self.pres_b]
        
        # Common Loops
        loops_a = set(df_a[self.col_herb_loop].dropna())
        loops_b = set(df_b[self.col_herb_loop].dropna())
        common_loops = list(loops_a.intersection(loops_b))
        
        # Common Targets
        targets_a = set(df_a[self.col_herb_target].dropna())
        targets_b = set(df_b[self.col_herb_target].dropna())
        common_targets = list(targets_a.intersection(targets_b))
        
        return common_targets, common_loops

    def get_inference_data(self, target_pres):
        # Filter raw prescription data
        df = self.raw_pres[self.raw_pres[self.col_pres_name] == target_pres].copy()
        
        # Merge with integrated Herb Library
        df = pd.merge(df, self.raw_herb, left_on=self.col_pres_herb, right_on=self.col_herb_name, how='left')
        
        return df
    def get_comparison_profiles(self):
        df = self.get_filtered_data()
        
        # 1. Herb Sets
        df_a = df[df[self.col_pres_name] == self.pres_a]
        df_b = df[df[self.col_pres_name] == self.pres_b]
        
        herbs_a = set(df_a[self.col_pres_herb].dropna().unique())
        herbs_b = set(df_b[self.col_pres_herb].dropna().unique())
        
        shared_herbs = sorted(list(herbs_a & herbs_b))
        only_a_herbs = sorted(list(herbs_a - herbs_b))
        only_b_herbs = sorted(list(herbs_b - herbs_a))
        
        # 2. Functional Profile (Herb Names on X-axis, Amount on Y-axis)
        # We need to know which actions are associated with each herb
        def get_formatted_actions(df_herb):
            return df_herb.groupby(self.col_pres_herb)[self.col_herb_loop].apply(
                lambda x: "<br>• " + "<br>• ".join(sorted(set(x.dropna())))
            ).to_dict()

        herb_actions_a = get_formatted_actions(df_a)
        herb_actions_b = get_formatted_actions(df_b)
        
        amounts_a = df_a.groupby(self.col_pres_herb)[self.col_pres_amount].max().to_dict()
        amounts_b = df_b.groupby(self.col_pres_herb)[self.col_pres_amount].max().to_dict()
        
        all_herbs = sorted(list(herbs_a | herbs_b))
        
        comparison_data = []
        for herb in all_herbs:
            category = "Shared" if herb in shared_herbs else (self.pres_a if herb in only_a_herbs else self.pres_b)
            actions = herb_actions_a.get(herb) or herb_actions_b.get(herb) or "N/A"
            
            comparison_data.append({
                'Herb': herb,
                self.pres_a: amounts_a.get(herb, 0),
                self.pres_b: amounts_b.get(herb, 0),
                'Actions': actions,
                'Category': category
            })
            
        return {
            'herbs': {
                'shared': shared_herbs,
                'only_a': only_a_herbs,
                'only_b': only_b_herbs
            },
            'actions': comparison_data
        }

    def get_single_structure(self, target_pres, mode='deep'):
        # mode: 'deep' (5 levels) or 'condensed' (3 levels: Pres -> Herb -> Core Action)
        df = self.raw_pres[self.raw_pres[self.col_pres_name] == target_pres].copy()
        df = pd.merge(df, self.raw_herb, left_on=self.col_pres_herb, right_on=self.col_herb_name, how='left')
        
        nodes = []
        node_map = {} # (Type, Name) -> Index
        
        # 1. Prescription Node
        nodes.append({'label': target_pres, 'color': '#2E2E2E', 'type': 'Prescription'})
        node_map[('Prescription', target_pres)] = 0
        
        # Helper to add layer nodes
        def add_layer_nodes(items, n_type, color):
            start_idx = len(nodes)
            unique_items = sorted(list(set(items.dropna())))
            for i, item in enumerate(unique_items):
                nodes.append({'label': item, 'color': color, 'type': n_type})
                node_map[(n_type, item)] = start_idx + i

        add_layer_nodes(df[self.col_pres_herb], 'Herb', '#2ECC71') # Green
        
        if mode == 'deep':
            add_layer_nodes(df[self.col_herb_ing], 'Ingredient', '#F39C12') # Orange
            add_layer_nodes(df[self.col_herb_target], 'Target', '#E74C3C') # Red
        
        add_layer_nodes(df[self.col_herb_loop], 'Action', '#9B59B6') # Purple
        
        links = []
        
        # 1. Pres -> Herb
        grp1 = df.groupby(self.col_pres_herb)[self.col_pres_amount].sum().reset_index()
        for _, row in grp1.iterrows():
            src, tgt, val = target_pres, row[self.col_pres_herb], row[self.col_pres_amount]
            if (('Prescription', src) in node_map) and (('Herb', tgt) in node_map) and val > 0:
                links.append({'source': node_map[('Prescription', src)], 'target': node_map[('Herb', tgt)], 'value': val, 'color': 'rgba(46, 204, 113, 0.2)'})
        
        if mode == 'deep':
            # 2. Herb -> Ingredient
            grp2 = df.groupby([self.col_pres_herb, self.col_herb_ing])[self.col_pres_amount].sum().reset_index()
            for _, row in grp2.iterrows():
                src, tgt, val = row[self.col_pres_herb], row[self.col_herb_ing], row[self.col_pres_amount]
                if (('Herb', src) in node_map) and (('Ingredient', tgt) in node_map) and val > 0:
                    links.append({'source': node_map[('Herb', src)], 'target': node_map[('Ingredient', tgt)], 'value': val, 'color': 'rgba(243, 156, 18, 0.1)'})
            
            # 3. Ingredient -> Target
            grp3 = df.groupby([self.col_herb_ing, self.col_herb_target])[self.col_pres_amount].sum().reset_index()
            for _, row in grp3.iterrows():
                src, tgt, val = row[self.col_herb_ing], row[self.col_herb_target], row[self.col_pres_amount]
                if (('Ingredient', src) in node_map) and (('Target', tgt) in node_map) and val > 0:
                    links.append({'source': node_map[('Ingredient', src)], 'target': node_map[('Target', tgt)], 'value': val, 'color': 'rgba(231, 76, 60, 0.05)'})
            
            # 4. Target -> Action
            grp4 = df.groupby([self.col_herb_target, self.col_herb_loop])[self.col_pres_amount].sum().reset_index()
            for _, row in grp4.iterrows():
                src, tgt, val = row[self.col_herb_target], row[self.col_herb_loop], row[self.col_pres_amount]
                if (('Target', src) in node_map) and (('Action', tgt) in node_map) and val > 0:
                    links.append({'source': node_map[('Target', src)], 'target': node_map[('Action', tgt)], 'value': val, 'color': 'rgba(155, 89, 182, 0.1)'})
        else:
            # Condensed Mode: Herb -> Action directly
            # Group by Herb and Action, use max amount for sizing
            grp_condensed = df.groupby([self.col_pres_herb, self.col_herb_loop])[self.col_pres_amount].max().reset_index()
            
            # Count actions per herb to distribute flow evenly
            herb_action_counts = df.groupby(self.col_pres_herb)[self.col_herb_loop].nunique().to_dict()

            for _, row in grp_condensed.iterrows():
                h_name, a_name, h_amt = row[self.col_pres_herb], row[self.col_herb_loop], row[self.col_pres_amount]
                
                # Distribute amount across actions to keep flow consistent and visually balanced
                div = herb_action_counts.get(h_name, 1)
                val = h_amt / div
                
                if (('Herb', h_name) in node_map) and (('Action', a_name) in node_map) and val > 0:
                    # Use a more vibrant color for condensed links
                    links.append({
                        'source': node_map[('Herb', h_name)], 
                        'target': node_map[('Action', a_name)], 
                        'value': val, 
                        'color': 'rgba(155, 89, 182, 0.4)' 
                    })

                    
        return nodes, links

    def generate_single_sankey(self, target_pres, mode='deep'):
        nodes, links = self.get_single_structure(target_pres, mode)
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                label=[n['label'] for n in nodes],
                color=[n['color'] for n in nodes],
                pad=20 if mode=='condensed' else 15,
                thickness=20 if mode=='condensed' else 15,
                line=dict(color="rgba(0,0,0,0.2)", width=0.5)
            ),
            link=dict(
                source=[l['source'] for l in links],
                target=[l['target'] for l in links],
                value=[l['value'] for l in links],
                color=[l['color'] for l in links],
                hovertemplate="Flow Volume: %{value:.1f}<extra></extra>"
            )
        )])
        
        title = f"Mechanism Narrative: {target_pres} (Overview)" if mode=='condensed' else f"Detailed Bio-Pathway: {target_pres}"
        
        fig.update_layout(
            title_text=title,
            font_size=14 if mode=='condensed' else 12,
            height=700 if mode=='condensed' else (800 if len(nodes) < 50 else 1200),
            margin=dict(l=40, r=40, t=80, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    def generate_sunburst(self, target_pres):
        import plotly.express as px
        df = self.get_inference_data(target_pres)
        
        # Prepare data for Sunburst: Prescription -> Herb -> Core Action
        # We need to aggregate amounts correctly
        sun_df = df.groupby([self.col_pres_name, self.col_pres_herb, self.col_herb_loop])[self.col_pres_amount].max().reset_index()
        
        # To make it look good, we can add a 'Total' root
        fig = px.sunburst(
            sun_df,
            path=[self.col_pres_herb, self.col_herb_loop],
            values=self.col_pres_amount,
            color=self.col_pres_herb,
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title=f"Hierarchical Mechanism: {target_pres}"
        )
        
        fig.update_layout(
            height=700,
            margin=dict(l=0, r=0, b=0, t=80),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig


