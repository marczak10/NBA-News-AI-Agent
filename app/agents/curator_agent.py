import json
import os
from datetime import datetime
from typing import Any

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.constants.prompts import CURATOR_AGENT_PROMPT
from app.services.env_config import load_project_env
from app.constants.user_profile import USER_PROFILE

load_project_env()


class RankedArticle(BaseModel):
    summary_id: str = Field(description="The ID of the ranked article summary")
    relevance_score: float = Field(
        description="Relevance score from 0.0 to 10.0",
        ge=0.0,
        le=10.0,
    )
    rank: int = Field(description="Rank position (1 = most relevant)", ge=1)
    reasoning: str = Field(
        description="Brief explanation of why this article is ranked here"
    )


class RankedArticleList(BaseModel):
    articles: list[RankedArticle] = Field(description="List of ranked articles")


class CuratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-5.4-nano",
            api_key=os.getenv("OPENAI_KEY"),
            temperature=0.3,
        )

    def _inject_user_profile(self, prompt: str) -> str:
        if USER_PROFILE:
            profile_info = json.dumps(USER_PROFILE, ensure_ascii=True, indent=2)
        else:
            profile_info = (
                "No explicit user profile provided.\n"
                "Use the ranking request and general NBA news importance as the primary signals."
            )
        return f"{prompt}\n\nUser Profile:\n{profile_info}"

    def _initialize_agent(self):
        agent = create_agent(
            model=self.llm,
            system_prompt=self._inject_user_profile(CURATOR_AGENT_PROMPT),
            response_format=ToolStrategy(RankedArticleList),
        )
        return agent

    def _serialize_field(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _serialize_summary(self, summary: Any) -> dict[str, str | None]:
        if isinstance(summary, dict):
            return {
                "id": self._serialize_field(
                    summary.get("id") or summary.get("summary_id")
                ),
                "title": self._serialize_field(summary.get("title")),
                "source_id": self._serialize_field(summary.get("source_id")),
                "source_type": self._serialize_field(summary.get("source_type")),
                "summary": self._serialize_field(
                    summary.get("summary") or summary.get("summary_text")
                ),
                "article_created_at": self._serialize_field(
                    summary.get("article_created_at")
                ),
            }

        return {
            "id": self._serialize_field(getattr(summary, "id", None)),
            "title": self._serialize_field(getattr(summary, "title", None)),
            "source_id": self._serialize_field(getattr(summary, "source_id", None)),
            "source_type": self._serialize_field(getattr(summary, "source_type", None)),
            "summary": self._serialize_field(getattr(summary, "summary_text", None)),
            "article_created_at": self._serialize_field(
                getattr(summary, "article_created_at", None)
            ),
        }

    def rank_summaries(self, summaries: list[Any]) -> RankedArticleList:
        if not summaries:
            return RankedArticleList(articles=[])

        agent = self._initialize_agent()
        serialized_summaries = [
            self._serialize_summary(summary) for summary in summaries
        ]
        user_prompt = f"""
        Rank these {len(summaries)} NBA news article summaries based on the user profile:
        {json.dumps(serialized_summaries, ensure_ascii=True, indent=2)}
        Provide a relevance score (0.0-10.0) and rank (1-{len(summaries)}) for each article, ordered from most to least relevant."""

        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_prompt}]}
        )

        structured_response = response.get("structured_response")
        if isinstance(structured_response, RankedArticleList):
            ranked_summaries = structured_response
        elif structured_response is not None:
            ranked_summaries = RankedArticleList.model_validate(structured_response)
        else:
            raise ValueError("Curator agent did not return a structured response.")

        ranked_summaries.articles.sort(key=lambda article: article.rank)
        return ranked_summaries
