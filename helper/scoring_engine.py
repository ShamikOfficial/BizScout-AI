import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_cluster_profiles(df: pd.DataFrame, target_category: str = None) -> pd.DataFrame:
    """
    Analyze cluster profiles for restaurants.
    
    Args:
        df (pd.DataFrame): Restaurant data with cluster information
        target_category (str, optional): Category to analyze. If None, analyzes all restaurants.
        
    Returns:
        pd.DataFrame: Cluster statistics
    """
    # If no target category, use all data
    if target_category is None:
        cat_df = df.copy()
    else:
        # Normalize category column for easier filtering
        df['has_target_category'] = df['categories'].apply(lambda cats: target_category in cats)
        # Filter by only relevant businesses for the target category
        cat_df = df[df['has_target_category'] == True]

    cluster_stats = cat_df.groupby('cluster_id').agg({
        'id': 'count',  # competition
        'review_count': 'sum',  # proxy for demand
        'rating': 'mean',
        'price_category': 'mean'
    }).rename(columns={
        'id': 'category_count',
        'review_count': 'total_footfall',
        'rating': 'avg_rating',
        'price_category': 'avg_price'
    })

    # Add total businesses in each cluster
    total_cluster_businesses = df.groupby('cluster_id')['id'].count().rename('business_density')
    cluster_stats = cluster_stats.join(total_cluster_businesses)

    return cluster_stats.reset_index()

from sklearn.preprocessing import MinMaxScaler

def rank_clusters(cluster_df: pd.DataFrame, capital: str = 'Low', risk: str = 'Low') -> pd.DataFrame:
    df = cluster_df.copy()

    # Normalize key features to 0–1
    features_to_normalize = ['total_footfall', 'avg_rating', 'avg_price', 'category_count']
    scaler = MinMaxScaler()
    df_norm = pd.DataFrame(scaler.fit_transform(df[features_to_normalize]), columns=features_to_normalize)

    # Combine normalized features into the dataframe
    for col in features_to_normalize:
        df[f'norm_{col}'] = df_norm[col]

    # Scoring logic with normalized values
    if capital == 'Low' and risk == 'Low':
        df['score'] = (
            -3.0 * df['norm_category_count'] +
            -2.0 * df['norm_total_footfall'] +
            -1.0 * df['norm_avg_price'] +
            1.0 * df['norm_avg_rating']
        )

    elif capital == 'Low' and risk == 'High':
        df['score'] = (
            2.0 * df['norm_total_footfall'] +
            -2.5 * df['norm_avg_rating'] +
            -1.5 * df['norm_category_count'] +
            -1.0 * df['norm_avg_price']
        )


    elif capital == 'High' and risk == 'High':
        df['score'] = (
            3.0 * df['norm_total_footfall'] +
            2.5 * df['norm_avg_rating'] +
            1.5 * df['norm_category_count'] +
            1.0 * df['norm_avg_price']
        )

    elif capital == 'High' and risk == 'Low':
        df['score'] = (
            2.5 * df['norm_total_footfall'] +
            -3.0 * df['norm_category_count'] +
            1.5 * df['norm_avg_rating'] +
            0.5 * df['norm_avg_price']
        )


    return df.sort_values(by='score', ascending=False)






def analyze_clusters(combined_data: pd.DataFrame, output_dir: Path, target_category: str = None) -> None:
    """
    Analyze and rank clusters for different business strategies.
    
    Args:
        combined_data (pd.DataFrame): Combined restaurant data
        output_dir (Path): Directory to save analysis results
        target_category (str, optional): Restaurant category to analyze. If None, analyzes all restaurants.
    """
    logger.info("Analyzing cluster profiles...")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    category_msg = f"for {target_category} restaurants" if target_category else "for all restaurants"
    logger.info(f"Analyzing clusters {category_msg}...")
    
    # Get cluster profiles
    cluster_df = get_cluster_profiles(combined_data, target_category)
    
    # Analyze for different business strategies
    strategies = [
        ('Low_Capital_Low_Risk', 'Low', 'Low'),
        ('High_Capital_High_Risk', 'High', 'High'),
        ('Low_Capital_High_Risk', 'Low', 'High'),
        ('High_Capital_Low_Risk', 'High', 'Low')
    ]
    
    for strategy_name, capital, risk in strategies:
        logger.info(f"\nAnalyzing {strategy_name} strategy:")
        ranked = rank_clusters(cluster_df, capital, risk)
        logger.info(f"Top 5 clusters for {strategy_name}:")
        logger.info(ranked.head().to_string())
        
        # Save results with simplified naming
        output_file = output_dir / f'cluster_analysis_{strategy_name}.csv'
        ranked.to_csv(output_file, index=False)
        logger.info(f"Saved analysis to {output_file}") 