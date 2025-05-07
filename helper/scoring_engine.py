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

def rank_clusters(cluster_df: pd.DataFrame, capital: str = 'Low', risk: str = 'Low') -> pd.DataFrame:
    """
    Rank clusters based on capital and risk profile.

    Args:
        cluster_df (pd.DataFrame): Cluster statistics
        capital (str): 'Low' or 'High'
        risk (str): 'Low' or 'High'

    Returns:
        pd.DataFrame: Scored and ranked clusters
    """
    df = cluster_df.copy()

    if capital == 'Low' and risk == 'Low':
        # Low capital, low risk: Avoid high traffic, competition, and expensive areas
        df['score'] = (
            -3.0 * df['category_count'] +  # Strong penalty for competition
            -1.5 * df['total_footfall'] +  # Avoid crowded areas
            -0.5 * df['avg_price']        # Avoid expensive locations
        )

    elif capital == 'Low' and risk == 'High':
        # Low capital, high risk: Look for high traffic but avoid expensive, competitive areas
        df['score'] = (
            +3.0 * df['total_footfall'] +    # High footfall
            -2.5 * df['category_count'] +    # Avoid competition
            -1.0 * df['avg_price'] +         # Avoid expensive areas
            -1.5 * df['avg_rating']          # Compete with lower-rated businesses
        )

    elif capital == 'High' and risk == 'Low':
        # High capital, low risk: Focus on moderate footfall, low competition, and manageable prices
        df['score'] = (
            -2.0 * df['category_count'] +    # Avoid high competition
            +2.0 * df['total_footfall'] +    # Moderate footfall
            -1.0 * df['avg_price'] +         # Prefer non-expensive
            -0.5 * df['avg_rating']          # Less importance on high ratings
        )

    elif capital == 'High' and risk == 'High':
        # High capital, high risk: Focus on high footfall, high ratings, and tolerate competition
        df['score'] = (
            +3.5 * df['total_footfall'] +    # Maximize footfall
            +2.5 * df['avg_rating'] +        # Maximize ratings
            +1.5 * df['category_count'] +    # Tolerate competition
            +1.0 * df['avg_price']           # Premium areas are ok
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
        ('Low Capital, Low Risk', 'Low', 'Low'),
        ('High Capital, High Risk', 'High', 'High'),
        ('Low Capital, High Risk', 'Low', 'High'),
        ('High Capital, Low Risk', 'High', 'Low')
    ]
    
    for strategy_name, capital, risk in strategies:
        logger.info(f"\nAnalyzing {strategy_name} strategy:")
        ranked = rank_clusters(cluster_df, capital, risk)
        logger.info(f"Top 5 clusters for {strategy_name}:")
        logger.info(ranked.head().to_string())
        
        # Save results to final_output directory with category in filename
        category_suffix = f"_{target_category.lower()}" if target_category else "_all"
        output_file = output_dir / f'cluster_analysis{category_suffix}_{strategy_name.lower().replace(", ", "_")}_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv'
        ranked.to_csv(output_file, index=False)
        logger.info(f"Saved analysis to {output_file}") 