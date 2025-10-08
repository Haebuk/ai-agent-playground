from typing import Optional
from crewai.crew import CrewOutput
from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel


class FundManagerState(BaseModel):
    # 사용자 input
    investment_goal: str = ""  # 사용자의 투자 목표
    risk_preference: str = ""  # 사용자의 투자 성향 (보수적, 공격적)
    budget: float = 0.0  # 사용자의 예산

    # 라우터의 의사결정
    strategy_type: str = ""

    # 분석 결과들
    tech_trends: Optional[CrewOutput] = None
    growth_scores: Optional[CrewOutput] = None
    stability_scores: Optional[CrewOutput] = None
    divide_scores: Optional[CrewOutput] = None
    portfolio: Optional[CrewOutput] = None


class FundManagerFlow(Flow[FundManagerState]):
    @start()
    def init_fund_analysis(self):
        if not self.state.investment_goal:
            raise ValueError("투자 목표를 입력해주세요")
        if not self.state.risk_preference:
            raise ValueError("투자 성향을 입력해주세요")
        if not self.state.budget:
            raise ValueError("예산을 입력해주세요")

    @listen(init_fund_analysis)
    def analyze_investment_strategy(self):
        pass

    @router(analyze_investment_strategy)
    def strategy_router(self):
        if self.state.strategy_type == "growth":
            return "growth_analysis"
        elif self.state.strategy_type == "value":
            return "value_analysis"

    @listen("growth_analysis")
    def analyze_tech_trends(self):
        pass

    @listen(analyze_tech_trends)
    def evaludate_growth_potential(self):
        pass

    @listen("value_analysis")
    def screen_stable_companies(self):
        pass

    @listen(screen_stable_companies)
    def evaluate_value_potential(self):
        pass

    @listen(or_(evaludate_growth_potential, evaluate_value_potential))
    def synthesize_portfolio(self):
        pass

    @listen(synthesize_portfolio)
    def finalize_investment_recommendation(self):
        pass


flow = FundManagerFlow()
flow.kickoff(
    inputs={
        "investment_goal": "AI 같은 첨단 기술주에 투자하고 싶습니다.",
        "risk_preference": "공격적",
        "budget": 20000.0,
    }
)

flow.kickoff(
    inputs={
        "investment_goal": "은퇴 자금을 위해 안정적인 배당을 원합니다/",
        "risk_preference": "보수적",
        "budget": 50000.0,
    }
)
# flow.plot()
