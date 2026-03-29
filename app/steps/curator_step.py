import json
import logging
import time
from datetime import datetime, timedelta, timezone

import numpy as np

from app.agents.curator_agent import CuratorAgent, RankedArticle, RankedArticleList
from app.database.connection import get_session
from app.database.table_models import ESPNArticle, NBAArticle, Summary, YoutubeVideo
from app.steps.base import RankedSummary, State

logger = logging.getLogger(__name__)


def _get_cutoff_reference_time(state: State) -> datetime:
    start_time = state.get("start_time")
    if start_time is None:
        return datetime.utcnow()
    if start_time.tzinfo is None:
        return start_time
    return start_time.astimezone(timezone.utc).replace(tzinfo=None)


def _get_top_ranked_summaries(
    ranked_summaries: RankedArticleList, top_n: int = 10
) -> list[RankedArticle]:
    return ranked_summaries.articles[:top_n]


def _serialize_ranked_summary(
    summary: Summary, ranked_summary: RankedArticle, url: str
) -> RankedSummary:
    return {
        "id": summary.id,
        "title": summary.title,
        "summary": summary.summary_text,
        "url": url,
        "source_id": summary.source_id,
        "source_type": summary.source_type,
        "article_created_at": summary.article_created_at,
        "rank": ranked_summary.rank,
        "relevance_score": ranked_summary.relevance_score,
        "reasoning": ranked_summary.reasoning,
    }


def _get_source_urls(session, summaries: list[Summary]) -> dict[tuple[str, str], str]:
    source_ids_by_type = {
        "nba_article": [
            summary.source_id
            for summary in summaries
            if summary.source_type == "nba_article"
        ],
        "espn_article": [
            summary.source_id
            for summary in summaries
            if summary.source_type == "espn_article"
        ],
        "youtube_video": [
            summary.source_id
            for summary in summaries
            if summary.source_type == "youtube_video"
        ],
    }

    source_urls: dict[tuple[str, str], str] = {}
    for source_type, model in (
        ("nba_article", NBAArticle),
        ("espn_article", ESPNArticle),
        ("youtube_video", YoutubeVideo),
    ):
        source_ids = source_ids_by_type[source_type]
        if not source_ids:
            continue

        rows = session.query(model).filter(model.id.in_(source_ids)).all()
        for row in rows:
            source_urls[(source_type, row.id)] = row.url

    return source_urls


def _dedupe_summaries_by_source(summaries: list[Summary]) -> list[Summary]:
    deduped_by_source: dict[tuple[str, str], Summary] = {}

    for summary in sorted(
        summaries,
        key=lambda item: (item.created_at, item.id),
        reverse=True,
    ):
        source_key = (summary.source_type, summary.source_id)
        if source_key not in deduped_by_source:
            deduped_by_source[source_key] = summary

    return list(deduped_by_source.values())


def _parse_summary_vector(summary: Summary) -> np.ndarray | None:
    raw_vector = getattr(summary, "summary_vector", None)
    if not raw_vector:
        return None

    try:
        if isinstance(raw_vector, str):
            parsed_vector = json.loads(raw_vector)
        else:
            parsed_vector = raw_vector
    except (TypeError, json.JSONDecodeError):
        logger.warning(
            "Skipping summary %s during clustering because summary_vector is invalid.",
            getattr(summary, "id", "<unknown>"),
        )
        return None

    vector = np.asarray(parsed_vector, dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        logger.warning(
            "Skipping summary %s during clustering because summary_vector is empty or malformed.",
            getattr(summary, "id", "<unknown>"),
        )
        return None

    return vector


def _cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    if embeddings.size == 0:
        return np.empty((0, 0))

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    safe_norms = np.where(norms == 0, 1.0, norms)
    normalized_embeddings = embeddings / safe_norms
    return normalized_embeddings @ normalized_embeddings.T


def _cluster_summaries_by_embedding(
    summaries: list[Summary], threshold: float = 0.8
) -> list[Summary]:
    if not summaries:
        return []

    summaries_by_dimension: dict[int, list[tuple[Summary, np.ndarray]]] = {}
    summaries_without_vectors: list[Summary] = []

    for summary in summaries:
        vector = _parse_summary_vector(summary)
        if vector is None:
            summaries_without_vectors.append(summary)
            continue

        summaries_by_dimension.setdefault(int(vector.shape[0]), []).append(
            (summary, vector)
        )

    kept_summary_objects: set[int] = {
        id(summary) for summary in summaries_without_vectors
    }

    for summaries_with_vectors in summaries_by_dimension.values():
        group_summaries = [summary for summary, _ in summaries_with_vectors]
        embeddings = np.vstack([vector for _, vector in summaries_with_vectors])
        similarity_matrix = _cosine_similarity_matrix(embeddings)

        clustered_indices: set[int] = set()
        clusters: list[list[Summary]] = []
        for i in range(len(group_summaries)):
            if i in clustered_indices:
                continue
            cluster = [group_summaries[i]]
            clustered_indices.add(i)
            for j in range(i + 1, len(group_summaries)):
                if j in clustered_indices:
                    continue
                if similarity_matrix[i][j] >= threshold:
                    cluster.append(group_summaries[j])
                    clustered_indices.add(j)
            clusters.append(cluster)

        for cluster in clusters:
            most_recent_summary = max(cluster, key=lambda summary: summary.created_at)
            kept_summary_objects.add(id(most_recent_summary))

    return [summary for summary in summaries if id(summary) in kept_summary_objects]


def curate(state: State) -> State:
    logger.info("Starting curator step.")
    curate_start_time = time.time()
    cutoff = _get_cutoff_reference_time(state) - timedelta(hours=24)
    curator_agent = CuratorAgent()

    with get_session() as session:
        recent_summaries = (
            session.query(Summary).filter(Summary.article_created_at >= cutoff).all()
        )
        logger.info("Loaded %s recent summaries.", len(recent_summaries))

        deduped_summaries = _dedupe_summaries_by_source(recent_summaries)
        logger.info(
            "Keeping %s unique summaries after deduping.",
            len(deduped_summaries),
        )

        clustered_ranked_summaries = _cluster_summaries_by_embedding(deduped_summaries)
        logger.info(
            "Keeping %s summaries after clustering by embedding similarity.",
            len(clustered_ranked_summaries),
        )

        ranked_summaries = curator_agent.rank_summaries(clustered_ranked_summaries)
        logger.info("Ranked summaries: %s", ranked_summaries)

        top_10_ranked_summaries = _get_top_ranked_summaries(ranked_summaries)
        logger.info("Top 10 ranked summaries: %s", top_10_ranked_summaries)

        logger.debug(
            "Got %s ranked summaries from the curator agent.",
            len(ranked_summaries.articles),
        )

        summaries_by_id = {summary.id: summary for summary in deduped_summaries}
        source_urls = _get_source_urls(session, deduped_summaries)
        top_summaries: list[RankedSummary] = []
        for ranked_summary in top_10_ranked_summaries:
            original_summary = summaries_by_id.get(ranked_summary.summary_id)
            if original_summary:
                source_url = source_urls.get(
                    (original_summary.source_type, original_summary.source_id),
                    "",
                )
                top_summaries.append(
                    _serialize_ranked_summary(
                        original_summary,
                        ranked_summary,
                        source_url,
                    )
                )

    curate_end_time = time.time()
    logger.info(
        "Finished curator step in %.2f seconds. Picked %s top summaries.",
        curate_end_time - curate_start_time,
        len(top_summaries),
    )
    return {"top_summaries": top_summaries}
