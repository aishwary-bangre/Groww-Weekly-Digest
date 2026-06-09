import logging
from typing import Dict, List
import numpy as np

from sentence_transformers import SentenceTransformer
import umap
import hdbscan

from ingestion.models import ProcessedReview

logger = logging.getLogger("groww_pulse.reasoning.clusterer")

class Clusterer:
    """Handles embedding generation and density-based clustering."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        logger.info(f"Initializing SentenceTransformer with model: {model_name}")
        # Loads locally, no API cost
        self.encoder = SentenceTransformer(model_name)
    
    def cluster(self, reviews: List[ProcessedReview]) -> Dict[int, List[ProcessedReview]]:
        """
        Takes scrubbed reviews, embeds them, reduces dimensionality with UMAP, 
        and clusters with HDBSCAN.
        """
        if not reviews:
            logger.warning("No reviews provided to cluster.")
            return {}
            
        logger.info(f"Generating embeddings for {len(reviews)} reviews...")
        texts = [r.scrubbed_text for r in reviews]
        embeddings = self.encoder.encode(texts, show_progress_bar=False)
        
        # UMAP for dimensionality reduction
        # This makes HDBSCAN much more effective
        logger.info("Reducing dimensionality with UMAP...")
        # using arbitrary reasonable defaults for NLP
        n_neighbors = min(15, len(embeddings) - 1) if len(embeddings) > 2 else 2
        umap_embeddings = umap.UMAP(
            n_neighbors=n_neighbors, 
            n_components=5, 
            metric='cosine',
            random_state=42 # for reproducibility in testing
        ).fit_transform(embeddings)
        
        # HDBSCAN for density-based clustering
        logger.info("Clustering with HDBSCAN...")
        min_cluster_size = max(5, len(reviews) // 50) # dynamic scaling based on volume
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        cluster_labels = clusterer.fit_predict(umap_embeddings)
        
        # Group reviews by cluster
        clusters: Dict[int, List[ProcessedReview]] = {}
        for review, label in zip(reviews, cluster_labels):
            review.cluster_id = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(review)
            
        noise_count = len(clusters.get(-1, []))
        cluster_count = len(clusters) - (1 if -1 in clusters else 0)
        logger.info(f"Clustering complete. Found {cluster_count} distinct topics. {noise_count} reviews classified as noise.")
        
        return clusters
