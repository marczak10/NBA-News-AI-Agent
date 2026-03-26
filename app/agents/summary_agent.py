import os

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI

from app.constants.prompts import SUMMARY_AGENT_PROMPT

load_dotenv()


class SummaryOutput(BaseModel):
    title: str = Field(description="A 5 to 10 word headline for the source item.")
    summary: str = Field(description="A concise 2 to 3 sentence summary of the source item.")
    
    
class SummaryAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-5.4-nano",
            api_key=os.getenv("OPENAI_KEY"),
            temperature=0.2,
        )
        
    def _initialize_agent(self):
        agent = create_agent(
            model=self.llm,
            system_prompt=SUMMARY_AGENT_PROMPT,
            response_format=ToolStrategy(SummaryOutput),
    
        )
        return agent
    
    def summarize_article(self, article_type: str, title: str, content: str) -> SummaryOutput:
        agent = self._initialize_agent()
        prompt = (
            f"Summarize the following NBA {article_type} source.\n\n"
            f"Title: {title}\n\n"
            f"Content:\n{content}"
        )
        response = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )

        structured_response = response.get("structured_response")
        if isinstance(structured_response, SummaryOutput):
            return structured_response
        if structured_response is not None:
            return SummaryOutput.model_validate(structured_response)

        raise ValueError("Summary agent did not return a structured response.")
