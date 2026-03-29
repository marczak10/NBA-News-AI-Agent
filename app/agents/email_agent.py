from datetime import datetime
import os

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.constants.prompts import EMAIL_PROMPT
from app.services.env_config import load_project_env
from app.constants.user_profile import USER_PROFILE

load_project_env()


class EmailIntroduction(BaseModel):
    greeting: str = Field(description="Personalized greeting with user's name and date")
    introduction: str = Field(
        description="2-3 sentence overview of what's in the top 10 ranked articles"
    )


class EmailAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-5.4-nano",
            api_key=os.getenv("OPENAI_KEY"),
            temperature=0.7,
        )

    def _initialize_agent(self):
        agent = create_agent(
            model=self.llm,
            system_prompt=EMAIL_PROMPT,
            response_format=EmailIntroduction,
        )
        return agent

    def generate_email_introduction(
        self, top_ranked_summaries: list[dict]
    ) -> EmailIntroduction:
        agent = self._initialize_agent()
        current_date = datetime.now().strftime("%B %d, %Y")
        user_name = USER_PROFILE.get("name", "there") if USER_PROFILE else "there"
        article_summaries = "\n".join(
            [
                f"{item['rank']}. {item['title']}: {item['summary']}"
                for item in top_ranked_summaries
            ]
        )
        user_prompt = f"""Create an email introduction for {user_name} for {current_date}.

        Top 10 ranked articles:
        {article_summaries}

        Generate a greeting and introduction that previews these articles."""

        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_prompt}]}
        )

        structured_response = response.get("structured_response")

        if isinstance(structured_response, EmailIntroduction):
            return structured_response
        if structured_response is not None:
            return EmailIntroduction.model_validate(structured_response)
        raise ValueError("Email agent did not return a structured response.")
