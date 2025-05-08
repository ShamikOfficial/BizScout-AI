import streamlit as st
import pandas as pd
import json
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import os
import glob
import subprocess
from pathlib import Path
import plotly.express as px

# Set page config for better aesthetics
st.set_page_config(
    page_title="BizScout AI - Restaurant Analysis",
    page_icon="🍽️",
    layout="wide"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #2196F3;  /* Changed to blue */
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1.1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(33, 150, 243, 0.2);
        position: relative;
    }
    .stButton>button:hover {
        background-color: #1976D2;  /* Darker blue on hover */
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(33, 150, 243, 0.3);
    }
    .stButton>button:disabled {
        background-color: #BDBDBD;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    .stButton>button:disabled:hover {
        background-color: #BDBDBD;
        transform: none;
        box-shadow: none;
    }
    .stButton>button:disabled:hover::after {
        content: "⚠️ Please select a category first";
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #FFEBEE;
        color: #C62828;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
        white-space: nowrap;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    .stButton>button:disabled:hover::before {
        content: "";
        position: absolute;
        bottom: calc(100% - 5px);
        left: 50%;
        transform: translateX(-50%);
        border-width: 5px;
        border-style: solid;
        border-color: #FFEBEE transparent transparent transparent;
        z-index: 1000;
    }
    .input-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .error-message {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #C62828;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# Automatically detect latest 4 files based on timestamp in name
def get_latest_files(base_path='data/final_output/', pattern='cluster_analysis_*.csv'):
    files = glob.glob(os.path.join(base_path, pattern))
    return files

# Title and description
st.title("🍽️ BizScout AI - Restaurant Analysis")
st.markdown("""
    Welcome to BizScout AI! This tool helps you analyze restaurant data and identify optimal locations
    for your business based on various risk-capital strategies.
""")

# Initialize session state for analysis results
if 'analysis_completed' not in st.session_state:
    st.session_state.analysis_completed = False
if 'merged_df' not in st.session_state:
    st.session_state.merged_df = None
if 'top_clusters' not in st.session_state:
    st.session_state.top_clusters = None

# Input section with aesthetic design
with st.container():
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    
    # Operation Mode Selection
    st.subheader("📊 Analysis Configuration")
    operation_mode = st.radio(
        "Select Operation Mode",
        ["Analyze Data", "Process Data", "Process & Analyze"],
        horizontal=True,
        index=0  # Set Analyze Data as default
    )
    
    # Category Input
    st.subheader("🏪 Restaurant Category")
    
    # Standardized categories based on the data
    standard_categories = [
        "Mexican",
        "Italian",
        "Chinese",
        "Japanese",
        "Korean",
        "Indian",
        "Thai",
        "Mediterranean",
        "American",
        "Fast Food",
        "Pizza",
        "Burgers",
        "Seafood",
        "Barbeque",
        "Food Trucks",
        "Cafes",
        "Coffee & Tea",
        "Desserts",
        "Bakeries",
        "Breakfast & Brunch"
    ]
    
    category = st.selectbox(
        "Select Restaurant Category",
        options=[""] + standard_categories,
        help="Choose a restaurant category from the standardized list"
    )
    
    # Load latest files and create option mapping for strategy selection
    latest_files = get_latest_files()
    options = {}
    for file_path in latest_files:
        name_part = os.path.basename(file_path).replace('cluster_analysis_', '').replace('.csv', '')
        strategy_key = name_part.split('_2025')[0].replace('_', ' ').title()
        options[strategy_key] = file_path

    # Strategy Selection with separate Risk and Capital toggles
    st.subheader("💰 Risk-Capital Strategy")
    
    # Create two columns for Risk and Capital toggles
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Risk Level")
        risk_level = st.radio(
            "Select Risk Level",
            ["Low Risk", "High Risk"],
            horizontal=True,
            help="Choose the risk level for your investment strategy"
        )
    
    with col2:
        st.markdown("#### 💵 Capital Level")
        capital_level = st.radio(
            "Select Capital Level",
            ["Low Capital", "High Capital"],
            horizontal=True,
            help="Choose the capital investment level for your strategy"
        )
    
    # Combine selections to match file naming pattern
    strategy_key = f"{capital_level} {risk_level}"
    
    # Show selected strategy
    st.markdown(f"""
        <div style="
            background-color: #4CAF50;
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1rem 0;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #45a049;
        ">
            <p style="
                color: #ffffff;
                margin: 0;
                font-size: 1.1rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">Selected Strategy</p>
            <h3 style="
                color: #ffffff;
                margin: 0.5rem 0 0 0;
                font-size: 1.5rem;
                font-weight: 600;
            ">{strategy_key}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Run Analysis Button with warning message
    if st.button("🚀 Run Analysis", key="run_analysis", disabled=not category, 
                 help="Select a restaurant category before running the analysis"):
        if not category:
            st.markdown("""
                <div class="error-message">
                    ⚠️ Please select a restaurant category before running the analysis.
                </div>
            """, unsafe_allow_html=True)
        else:
            # Convert operation mode to main.py format
            mode_map = {
                "Process Data": "process",
                "Analyze Data": "analyze",
                "Process & Analyze": "both"
            }
            
            # Construct command
            cmd = ["python", "main.py", "--mode", mode_map[operation_mode]]
            if category:
                cmd.extend(["--category", category])
                
            try:
                with st.spinner("Running analysis... This may take a few minutes."):
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("Analysis completed successfully!")
                        
                        # Load centroids
                        with open('data/semi_processed/cluster_centroids.json', 'r') as f:
                            centroids = json.load(f)

                        centroid_df = pd.DataFrame([
                            {
                                'cluster_id': int(cid),
                                'lat': coords['latitude'],
                                'long': coords['longitude']
                            } for cid, coords in centroids.items()
                        ])

                        # Find the matching strategy file
                        matching_file = None
                        strategy_pattern = f"cluster_analysis_{capital_level}_{risk_level}.csv".replace(' ', '_')
                        
                        # Debug information
                        st.write("Available files:", [os.path.basename(f) for f in latest_files])
                        st.write("Looking for file:", strategy_pattern)
                        
                        for file_path in latest_files:
                            file_name = os.path.basename(file_path).lower()
                            if strategy_pattern.lower() in file_name:
                                matching_file = file_path
                                break
                        
                        if matching_file:
                            # Read and prepare selected file
                            df = pd.read_csv(matching_file)
                            df['cluster_id'] = df['cluster_id'].astype(int)
                            merged_df = pd.merge(df, centroid_df, on='cluster_id', how='left')
                            
                            # Store results in session state
                            st.session_state.merged_df = merged_df
                            st.session_state.top_clusters = merged_df.sort_values(by='score', ascending=False).head(6)
                            st.session_state.analysis_completed = True
                        else:
                            st.error(f"""
                                No analysis file found for strategy: {strategy_key}
                                
                                Please ensure that:
                                1. The analysis has been run for this strategy combination
                                2. The file exists with name: {strategy_pattern}
                            """)
                        
                    else:
                        st.error(f"Error running analysis: {result.stderr}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Only show visualizations if analysis is completed
if st.session_state.analysis_completed and st.session_state.merged_df is not None:
    # Create a full-width map
    st.subheader("🗺️ Location Analysis Map")
    m = folium.Map(location=[34.05, -118.25], zoom_start=10, control_scale=True)

    # Heatmap based on score
    heat_data = [
        [row['lat'], row['long'], row['score']] for _, row in st.session_state.merged_df.iterrows()
    ]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=12).add_to(m)

    # Top clusters with different colors based on rank
    colors = ['red', 'orange', 'green', 'blue', 'purple', 'darkred']
    for idx, (_, row) in enumerate(st.session_state.top_clusters.iterrows()):
        # Create custom HTML for numbered marker
        rank = idx + 1
        html = f"""
            <div style="
                background-color: {colors[idx]};
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid white;
                box-shadow: 0 0 5px rgba(0,0,0,0.3);
            ">
                {rank}
            </div>
        """
        
        # Create custom icon
        icon = folium.DivIcon(
            html=html,
            class_name='custom-marker'
        )
        
        folium.Marker(
            location=[row['lat'], row['long']],
            popup=f"Rank: {rank}<br>Cluster ID: {row['cluster_id']}<br>Score: {row['score']:.2f}",
            icon=icon
        ).add_to(m)

    # Add custom CSS for markers
    st.markdown("""
        <style>
        .custom-marker {
            background: none;
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render map with full width
    st_folium(m, width=None, height=380)  # Further reduced height

    # Create tabs for different visualizations with minimal spacing
    tab1, tab2, tab3 = st.tabs(["📊 Top Locations", "📈 Score Distribution", "🎯 Category Analysis"])

    with tab1:
        # Create a styled table for top locations
        top_locations = st.session_state.top_clusters[['cluster_id', 'score', 'lat', 'long']].copy()
        top_locations['Rank'] = range(1, len(top_locations) + 1)
        top_locations['Score'] = top_locations['score'].round(2)
        top_locations['Latitude'] = top_locations['lat'].round(6)
        top_locations['Longitude'] = top_locations['long'].round(6)
        
        # Count locations in each cluster from the full dataset
        cluster_counts = st.session_state.merged_df['cluster_id'].value_counts()
        top_locations['Location Count'] = top_locations['cluster_id'].map(cluster_counts)
        
        # Reorder columns and drop unnecessary ones
        top_locations = top_locations[['Rank', 'cluster_id', 'Score', 'Location Count', 'Latitude', 'Longitude']]
        
        # Display the table with custom styling
        st.markdown("""
            <style>
            .dataframe {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
                font-size: 0.9em;
                font-family: sans-serif;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
            }
            .dataframe thead tr {
                background-color: #4CAF50;
                color: #ffffff;
                text-align: left;
            }
            .dataframe th,
            .dataframe td {
                padding: 6px 10px;
            }
            .dataframe tbody tr {
                border-bottom: 1px solid #dddddd;
            }
            .dataframe tbody tr:nth-of-type(even) {
                background-color: #f3f3f3;
            }
            .dataframe tbody tr:last-of-type {
                border-bottom: 2px solid #4CAF50;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(top_locations, use_container_width=True)
        
        # Add statistics in columns with minimal spacing
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Score", f"{top_locations['Score'].mean():.2f}")
        with col2:
            st.metric("Highest Score", f"{top_locations['Score'].max():.2f}")
        with col3:
            st.metric("Total Locations", f"{top_locations['Location Count'].sum():,}")
        with col4:
            st.metric("Avg. Locations/Cluster", f"{top_locations['Location Count'].mean():.1f}")
        
        # Add a bar chart showing location distribution
        fig_locations = px.bar(
            top_locations,
            x='Rank',
            y='Location Count',
            title='Location Distribution in Top Clusters',
            color='Score',
            color_continuous_scale='Plasma',
            labels={'Location Count': 'Number of Locations', 'Rank': 'Cluster Rank'}
        )
        fig_locations.update_layout(
            plot_bgcolor='white',
            title_x=0.5,
            margin=dict(t=15, b=5, l=5, r=5),
            height=300,
            xaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                title_font=dict(size=12, color='#424242')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                title_font=dict(size=12, color='#424242')
            ),
            title_font=dict(size=14, color='#212121'),
            coloraxis_colorbar=dict(
                title="Score",
                thickness=15,
                len=0.5,
                yanchor="middle",
                y=0.5,
                xanchor="right",
                x=1.1
            )
        )
        st.plotly_chart(fig_locations, use_container_width=True)

    with tab2:
        # Score distribution plot
        st.subheader("Score Distribution Analysis")
        
        # Create histogram of scores
        fig = px.histogram(
            st.session_state.merged_df,
            x='score',
            nbins=30,
            title='Distribution of Location Scores',
            labels={'score': 'Score', 'count': 'Number of Locations'},
            color_discrete_sequence=['#2196F3'],  # Blue color
            opacity=0.8
        )
        
        fig.update_layout(
            showlegend=True,
            plot_bgcolor='white',
            title_x=0.5,
            margin=dict(t=15, b=5, l=5, r=5),
            height=320,
            xaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                title_font=dict(size=12, color='#424242')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                title_font=dict(size=12, color='#424242')
            ),
            title_font=dict(size=14, color='#212121'),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        fig.update_traces(
            marker=dict(
                line=dict(width=1, color='#FFFFFF')
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Box plot of scores with enhanced styling
        fig2 = px.box(
            st.session_state.merged_df,
            y='score',
            title='Score Distribution Box Plot',
            labels={'score': 'Score'},
            color_discrete_sequence=['#2196F3'],  # Changed to blue to match button
            points='all'  # Show all points
        )
        fig2.update_layout(
            showlegend=True,
            plot_bgcolor='white',
            title_x=0.5,
            margin=dict(t=15, b=5, l=5, r=5),
            height=280,
            xaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                title_font=dict(size=12, color='#424242')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                title_font=dict(size=12, color='#424242')
            ),
            title_font=dict(size=14, color='#212121'),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        fig2.update_traces(
            boxmean=True,  # Show mean
            marker=dict(
                size=4,
                color='#2196F3',  # Changed to blue
                line=dict(width=1, color='#1976D2')  # Darker blue outline
            ),
            line=dict(
                color='#1976D2',  # Darker blue
                width=2
            ),
            fillcolor='#BBDEFB'  # Light blue fill
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("Category-based Analysis")
        
        # Load and process category data from combined restaurants
        try:
            # Get the latest combined restaurants file
            combined_files = glob.glob('data/processed/combined_restaurants_*.csv')
            if combined_files:
                latest_file = max(combined_files, key=os.path.getctime)
                df_combined = pd.read_csv(latest_file)
                
                # Process categories
                all_categories = []
                for cats in df_combined['categories']:
                    if isinstance(cats, str):
                        # Convert string representation of list to actual list
                        cats = eval(cats)
                        all_categories.extend(cats)
                
                # Count categories
                category_counts = pd.Series(all_categories).value_counts().head(10)
                
                # Create color palette with blue tones
                colors = px.colors.sequential.Blues[2:12]  # Blue color sequence
                
                # Create pie chart with enhanced styling
                fig_categories = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title='Top 10 Restaurant Categories',
                    color_discrete_sequence=colors,
                    hole=0.4  # Create a donut chart
                )
                
                # Update layout
                fig_categories.update_layout(
                    plot_bgcolor='white',
                    title_x=0.5,
                    margin=dict(t=15, b=5, l=5, r=5),
                    height=350,
                    title_font=dict(size=14, color='#212121'),
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=1.05,
                        bgcolor='rgba(255, 255, 255, 0.8)'
                    )
                )
                
                # Update traces for better appearance
                fig_categories.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    insidetextorientation='radial',
                    marker=dict(
                        line=dict(width=1, color='#FFFFFF')
                    )
                )
                
                st.plotly_chart(fig_categories, use_container_width=True)
                
                # Display category statistics with minimal spacing
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Categories", len(category_counts))
                with col2:
                    st.metric("Most Common Category", f"{category_counts.index[0]} ({category_counts.iloc[0]})")
                
            else:
                st.info("No combined restaurant data found.")
        except Exception as e:
            st.error(f"Error loading category data: {str(e)}")
