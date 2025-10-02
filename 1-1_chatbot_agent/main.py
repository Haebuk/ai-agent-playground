import os
from pprint import pprint
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from env import OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


class AgentState(TypedDict):
    user_query: str
    messages: list


def generate_workflow():
    """
    start -> analyze_query -> generate_response -> end
    """

    # 1. LLM
    model = ChatOpenAI(model="gpt-4o-mini")

    # 2. 노드 함수들 정의 (각 노드는 State를 입력받아 업데이트된 State 반환)
    def analyze_query(state: AgentState) -> AgentState:
        user_query = state["user_query"]

        system_msg = SystemMessage(
            content="""
            당신은 전문 AI 어시스턴트입니다.
            사용자의 질문에 대해 정확하고 친절한 한국어 답변을 제공하세요.
            """
        )
        return {
            "messages": [system_msg, HumanMessage(content=user_query)],
            "user_query": user_query,
        }

    def generate_response(state: AgentState) -> AgentState:
        messages = state["messages"]
        response = model.invoke(messages)

        return {"messages": [response], "user_query": state["user_query"]}

    # 3. 그래프 생성 및 구성
    workflow = StateGraph(AgentState)

    # 4. 노드 추가
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("generate_response", generate_response)

    # 5. 엣지 추가
    workflow.add_edge(START, "analyze_query")
    workflow.add_edge("analyze_query", "generate_response")
    workflow.add_edge("generate_response", END)

    # 6. 그래프 컴파일
    return workflow.compile()


class ChatBot:
    def __init__(self):
        self.workflow = generate_workflow()

    def process_message(self, user_message: str) -> str:
        initial_state: AgentState = {
            "messages": [],
            "user_query": user_message,
        }

        result = self.workflow.invoke(initial_state)

        messages = result["messages"]

        ai_message = messages[0].content

        return ai_message


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if update.message is None or update.message.text is None:
        return

    user_message = update.message.text

    result = ChatBot().process_message(user_message)

    await update.message.reply_text(result)


app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, handler))

app.run_polling()
