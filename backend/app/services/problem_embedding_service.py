import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.problem import Problem
from app.models.problem_embedding import ProblemEmbedding

logger = logging.getLogger("problem_embedding_service")

# Lazy model loading to optimize startup time
_model = None

def get_embedding_model():
    """
    Lazily loads the SentenceTransformer model.
    """
    global _model
    if _model is None:
        logger.info("Initializing SentenceTransformer 'all-MiniLM-L6-v2' model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer model loaded successfully.")
    return _model

def build_problem_text(problem: Problem) -> str:
    """
    Constructs the text representation of a problem for semantic embedding.
    Format: "{title} | Tags: {tag1,tag2} | Rating: {rating}"
    """
    tags_str = ",".join([t.name.lower() for t in problem.topics])
    rating_str = str(problem.difficulty) if problem.difficulty is not None else "None"
    return f"{problem.title} | Tags: {tags_str} | Rating: {rating_str}"

def generate_embeddings_for_new_problems(db: Session) -> int:
    """
    Finds all problems without embeddings, encodes their text, and saves vectors to the DB.
    Returns the count of generated embeddings.
    """
    # Get existing problem IDs with embeddings
    existing_ids = db.query(ProblemEmbedding.problem_id).all()
    existing_ids_set = {r[0] for r in existing_ids}

    # Fetch all problems and filter for missing embeddings
    all_problems = db.query(Problem).all()
    problems_to_encode = [p for p in all_problems if p.id not in existing_ids_set]

    if not problems_to_encode:
        logger.info("All problems already have embeddings in the database.")
        return 0

    logger.info(f"Generating embeddings for {len(problems_to_encode)} problems...")
    model = get_embedding_model()

    # Create text and encode in batches
    texts = [build_problem_text(p) for p in problems_to_encode]
    start_time = time.time()
    embeddings = model.encode(texts, batch_size=128, show_progress_bar=False)
    logger.info(f"Encoding complete in {time.time() - start_time:.2f} seconds.")

    # Save to database
    for p, emb in zip(problems_to_encode, embeddings):
        prob_emb = ProblemEmbedding(
            problem_id=p.id,
            embedding=emb.tolist()  # Convert numpy array to float list for pgvector
        )
        db.add(prob_emb)

    db.commit()
    logger.info(f"Successfully saved {len(problems_to_encode)} problem embeddings.")
    return len(problems_to_encode)

def find_similar_problems(db: Session, problem_id: Any, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches the top N most similar problems for a given problem ID.
    Performs native SQL distance queries on PostgreSQL and numpy fallback on SQLite.
    """
    import uuid
    if isinstance(problem_id, str):
        try:
            problem_id = uuid.UUID(problem_id)
        except ValueError:
            pass

    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise ValueError(f"Problem with ID '{problem_id}' not found.")

    # Get or generate embedding on-the-fly if missing
    prob_emb = db.query(ProblemEmbedding).filter(ProblemEmbedding.problem_id == problem_id).first()
    if not prob_emb:
        logger.info(f"Embedding missing for problem '{problem.title}'. Generating on-the-fly...")
        model = get_embedding_model()
        text_content = build_problem_text(problem)
        vector = model.encode(text_content).tolist()
        prob_emb = ProblemEmbedding(problem_id=problem.id, embedding=vector)
        db.add(prob_emb)
        db.commit()
        db.refresh(prob_emb)

    target_embedding = prob_emb.embedding

    dialect_name = db.bind.dialect.name
    if dialect_name == "postgresql":
        # pgvector cosine_distance (0 = identical, 2 = opposite)
        distance = ProblemEmbedding.embedding.cosine_distance(target_embedding)
        results = (
            db.query(Problem, distance)
            .join(ProblemEmbedding)
            .filter(Problem.id != problem_id)
            .order_by(distance)
            .limit(limit)
            .all()
        )

        similar_problems = []
        for p, dist in results:
            similarity = round(1.0 - float(dist), 4)  # Convert cosine distance to cosine similarity
            similar_problems.append({
                "problem_id": str(p.id),
                "name": p.title,
                "similarity": similarity,
                "rating": p.difficulty
            })
        return similar_problems
    else:
        # SQLite fallback: fetch all embeddings and calculate similarity using numpy
        import numpy as np
        all_embeddings = (
            db.query(ProblemEmbedding)
            .filter(ProblemEmbedding.problem_id != problem_id)
            .all()
        )

        target_vec = np.array(target_embedding, dtype=np.float32)
        target_norm = np.linalg.norm(target_vec)
        if target_norm == 0:
            target_norm = 1e-9

        scored_problems = []
        for pe in all_embeddings:
            p = pe.problem
            vec = np.array(pe.embedding, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm == 0:
                norm = 1e-9
            sim = np.dot(target_vec, vec) / (target_norm * norm)
            scored_problems.append((p, float(sim)))

        # Sort descending by similarity
        scored_problems.sort(key=lambda x: x[1], reverse=True)

        similar_problems = []
        for p, sim in scored_problems[:limit]:
            similar_problems.append({
                "problem_id": str(p.id),
                "name": p.title,
                "similarity": round(sim, 4),
                "rating": p.difficulty
            })
        return similar_problems
