"""
Reciprocal Rank Fusion (RRF) Re-ranking Utility.

Combines multiple retrieval rankings (e.g. Dense Vector Similarity + Sparse Keyword Search)
into a single fused, high-precision ranking without needing score normalization.
"""
from typing import Any, Dict, List, Tuple


def reciprocal_rank_fusion(
    ranked_lists: List[List[Any]],
    k: int = 60,
    id_getter=lambda x: x.id,
) -> List[Tuple[Any, float]]:
    """
    Executes Reciprocal Rank Fusion on multiple ranked result lists.

    Formula:
        RRF_Score(doc) = SUM( 1.0 / (k + rank_i(doc)) )

    :param ranked_lists: List of ranked result lists from different search algorithms.
    :param k: Smoothing constant (industry standard is 60).
    :param id_getter: Function to extract unique identifier from each result item.
    :return: List of tuples (item, fused_score) sorted descending by fused_score.
    """
    scores: Dict[Any, float] = {}
    item_map: Dict[Any, Any] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list):
            item_id = id_getter(item)
            item_map[item_id] = item

            # rank starts at 0, so rank + 1 represents 1st place
            rrf_contribution = 1.0 / (k + (rank + 1))
            scores[item_id] = scores.get(item_id, 0.0) + rrf_contribution

    # Sort items by accumulated RRF score descending
    sorted_items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    return [(item_map[item_id], score) for item_id, score in sorted_items]

