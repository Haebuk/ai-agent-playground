import os

from crewai.flow.flow import Flow, listen, or_, router, start
from crewai.agent import LiteAgentOutput
from pydantic import BaseModel
from env import OPENAI_API_KEY


os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


class Post(BaseModel):
    title: str
    content: str
    hashtag: list[str]


class ScoreManager(BaseModel):
    score: int = 0
    reason: str = ""


class BlogContentMakerState(BaseModel):
    topic: str = ""
    max_length: int = 1000
    research_data: LiteAgentOutput | None = None
    score_manager: ScoreManager | None = None
    post: Post | None = None


class BlogContentMakerFlow(Flow[BlogContentMakerState]):
    @start()
    def init_make_blog_content(self):
        pass

    @listen(init_make_blog_content)
    def research_by_topic(self):
        pass

    @listen(or_(research_by_topic, "remake"))
    def handle_make_blog(self):
        pass

    @listen(handle_make_blog)
    def manage_seo(self):
        pass

    @router(manage_seo)
    def manage_score_router(self):
        if self.state.score_manager.score >= 70:
            return None
        else:
            return "remake"


flow = BlogContentMakerFlow()
# flow.kickoff({"topic": "AI 로보틱스"})
flow.plot()
