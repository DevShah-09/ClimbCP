import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.problem import Problem
from app.models.problem_embedding import ProblemEmbedding
from app.models.problem_cluster import ProblemCluster
from app.models.problem_attempt import ProblemAttempt
from app.models.cf_user import CFUser
from app.models.topic import Topic
from app.models.problem_topic import ProblemTopic

logger = logging.getLogger("concept_clustering_service")

def label_cluster_problems(problems: List[Problem]) -> str:
    """
    Analyzes the topics and titles of problems in a cluster to assign
    a descriptive semantic label.
    """
    if not problems:
        return "General Algorithms"

    tags = []
    titles = []
    for p in problems:
        tags.extend([t.name.lower() for t in p.topics])
        titles.append(p.title.lower())

    all_tags_str = " ".join(tags)
    all_titles_str = " ".join(titles)

    # Label assignment based on dominant tag and title keywords
    if "dsu" in all_tags_str or "union find" in all_tags_str or "disjoint" in all_tags_str:
        return "DSU"
    elif "tree" in all_tags_str and ("dp" in all_tags_str or "dynamic programming" in all_tags_str):
        return "Tree DP"
    elif "mst" in all_tags_str or "spanning" in all_tags_str or "kruskal" in all_tags_str or "prim" in all_tags_str:
        return "MST"
    elif "shortest" in all_tags_str or "dijkstra" in all_tags_str or "bellman" in all_tags_str or "floyd" in all_titles_str:
        return "Shortest Path"
    elif "search" in all_tags_str and ("state" in all_titles_str or "space" in all_titles_str or "bitmask" in all_tags_str or "backtrack" in all_titles_str):
        return "State Space Search"
    elif "dp" in all_tags_str or "dynamic programming" in all_tags_str:
        return "Dynamic Programming"
    elif "math" in all_tags_str or "number theory" in all_tags_str or "gcd" in all_tags_str or "combinatorics" in all_tags_str:
        return "Math & Number Theory"
    elif "greedy" in all_tags_str:
        return "Greedy Algorithms"
    elif "sort" in all_tags_str or "binary search" in all_tags_str:
        return "Sorting & Searching"
    elif "string" in all_tags_str or "suffix" in all_tags_str or "kmp" in all_tags_str:
        return "String Algorithms"
    elif "graph" in all_tags_str:
        return "Graph Traversal & BFS/DFS"
    elif "tree" in all_tags_str:
        return "Tree Algorithms"
    return "General Implementation"

def cluster_problems(db: Session, n_clusters: int = 15) -> Dict[str, Any]:
    """
    Performs KMeans clustering on all problem embeddings in the database
    and stores the resulting cluster assignments in the problem_clusters table.
    """
    logger.info("Starting problem embedding clustering...")
    embeddings = db.query(ProblemEmbedding).all()

    if not embeddings:
        logger.warning("No problem embeddings found to cluster.")
        return {"status": "error", "message": "No problem embeddings found."}

    # If count is less than n_clusters, adjust
    n_samples = len(embeddings)
    actual_clusters = min(n_clusters, n_samples)

    if actual_clusters < 2:
        logger.warning("Too few embeddings for clustering.")
        return {"status": "error", "message": "Too few embeddings for clustering."}

    # Extract embedding vectors
    import numpy as np
    X = np.array([emb.embedding for emb in embeddings], dtype=np.float32)

    # Run KMeans
    try:
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
    except ImportError:
        logger.warning("scikit-learn not installed. Falling back to pure numpy KMeans.")
        # Pure numpy KMeans implementation for fallback
        centroids = X[np.random.choice(n_samples, actual_clusters, replace=False)]
        labels = np.zeros(n_samples, dtype=np.int32)
        for _ in range(15):  # Max 15 iterations
            # Distance from each sample to centroids
            distances = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)
            new_labels = np.argmin(distances, axis=1)
            if np.array_equal(labels, new_labels):
                break
            labels = new_labels
            # Update centroids
            for i in range(actual_clusters):
                centroids[i] = X[labels == i].mean(axis=0)

    # Truncate existing clusters
    db.query(ProblemCluster).delete()
    db.commit()

    # Bulk insert new clusters
    for emb, label in zip(embeddings, labels):
        pc = ProblemCluster(
            problem_id=emb.problem_id,
            cluster_id=int(label)
        )
        db.add(pc)

    db.commit()
    logger.info(f"Successfully clustered {n_samples} problems into {actual_clusters} concepts.")
    return {"status": "success", "problems_clustered": n_samples, "clusters_created": actual_clusters}

def get_cluster_labels(db: Session) -> Dict[int, str]:
    """
    Resolves a friendly string label for each cluster ID based on its member problems.
    Appends numeric suffixes if labels are duplicated.
    """
    clusters = db.query(ProblemCluster).all()
    grouped_problems = {}
    for c in clusters:
        grouped_problems.setdefault(c.cluster_id, []).append(c.problem_id)

    # Fetch problems in bulk
    all_problems = db.query(Problem).all()
    problem_map = {p.id: p for p in all_problems}

    labels = {}
    label_counts = {}
    
    # Sort cluster IDs for deterministic numbering
    for cluster_id in sorted(grouped_problems.keys()):
        prob_ids = grouped_problems[cluster_id]
        problems_in_cluster = [problem_map[pid] for pid in prob_ids if pid in problem_map]
        
        raw_label = label_cluster_problems(problems_in_cluster)
        label_counts[raw_label] = label_counts.get(raw_label, 0) + 1
        
        if label_counts[raw_label] > 1:
            labels[cluster_id] = f"{raw_label} {label_counts[raw_label]}"
        else:
            labels[cluster_id] = raw_label

    return labels

def get_user_concept_mastery(db: Session, handle: str) -> List[Dict[str, Any]]:
    """
    Computes a user's mastery levels for each semantic concept cluster.
    """
    user = db.query(CFUser).filter(CFUser.handle.ilike(handle)).first()
    if not user:
        raise ValueError(f"No profile found for handle '{handle}'")

    user_id = user.id
    user_rating = user.current_rating or 1200

    # Get user problem attempts
    attempts = db.query(ProblemAttempt).filter(ProblemAttempt.user_id == user_id).all()
    user_attempts_map = {att.problem_id: att for att in attempts}

    # Get all problem clusters
    clusters = db.query(ProblemCluster).all()
    if not clusters:
        # If no clusters exist, run clustering first
        cluster_problems(db)
        clusters = db.query(ProblemCluster).all()

    # Get cluster labels
    cluster_labels = get_cluster_labels(db)

    # Fetch all problems for recommendations
    all_problems = db.query(Problem).all()
    problem_map = {p.id: p for p in all_problems}

    # Group problems by cluster
    cluster_groups = {}
    for c in clusters:
        cluster_groups.setdefault(c.cluster_id, []).append(c.problem_id)

    concept_masteries = []

    for cluster_id, prob_ids in cluster_groups.items():
        concept_name = cluster_labels.get(cluster_id, f"Concept {cluster_id}")
        
        solved_count = 0
        attempted_count = 0
        unsolved_problems = []

        for pid in prob_ids:
            if pid not in problem_map:
                continue
            p = problem_map[pid]
            att = user_attempts_map.get(pid)
            if att:
                attempted_count += 1
                if att.solved:
                    solved_count += 1
                else:
                    unsolved_problems.append(p)
            else:
                unsolved_problems.append(p)

        # Mastery Formula: (solved / attempted) * 100.
        # If not attempted, default to 0 (to encourage learning).
        mastery = 0
        if attempted_count > 0:
            mastery = min(100, int((solved_count / attempted_count) * 100))

        # Recommend 3 problems closest to user rating
        # Filter by rating suitability
        unsolved_problems.sort(key=lambda p: abs((p.difficulty or 1200) - user_rating))
        recommendations = []
        for p in unsolved_problems[:3]:
            recommendations.append({
                "problem_id": str(p.id),
                "name": p.title,
                "rating": p.difficulty or 1200,
                "problem_code": p.problem_code
            })

        concept_masteries.append({
            "cluster_id": cluster_id,
            "concept": concept_name,
            "mastery": mastery,
            "solved": solved_count,
            "attempted": attempted_count,
            "recommendations": recommendations
        })

    # Sort descending by mastery
    concept_masteries.sort(key=lambda x: x["mastery"], reverse=True)
    return concept_masteries

def get_weak_concepts(db: Session, handle: str) -> List[Dict[str, Any]]:
    """
    Returns the user's weak concept clusters (mastery < 60) ordered ascending.
    """
    masteries = get_user_concept_mastery(db, handle)
    return [m for m in masteries if m["mastery"] < 60]
