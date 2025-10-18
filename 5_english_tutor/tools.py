"""
[Note]
Indexing (pre retrieval)
- 문서 ---(분할)---> chunk1, chunk2, ... ---(임베딩)---> 행렬데이터 ---(저장)---> 벡터DB

Retrieval (post retrieval)
- 사용자 질문 ---(임베딩)---> 행렬데이터 ---(검색)---> 벡터DB ---> chunk1, chunk2, ... ---> 답변생성

벡터 DB -> Pyncone(유료), Chroma(무료) 등등

청크(Chunk) = RAG에서 문서를 나눠 임베딩하는 “정보 단위”.
"""

import os
from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from env import OPENAI_API_KEY
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


PDF_FILENAME = os.path.join("knowledge", "29ESLConversationTopic.pdf")
PERSIST_DIR = os.path.join(".chroma", "esl_topics")


def _qa(question):
    os.makedirs(PERSIST_DIR, exist_ok=True)

    embeddings = OpenAIEmbeddings()

    try:
        has_index = bool(os.listdir(PERSIST_DIR))
    except Exception:
        has_index = False

    if has_index:
        # 기존 인덱스 로드
        vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    else:
        # 새 인덱스 구축
        loader = PyPDFLoader(PDF_FILENAME)
        docs = loader.load()

        # 문서 -> 청크 분할
        # 문서를 너무 길게 넣으면 벡터 임베딩이 부정확해짐
        # 너무 짧게 나누면 문맥이 끊겨서 검색시 정보 손실 발생
        # chunk_overlap: 청크 간 중복 범위. 문맥의 흐름을 유지
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_documents(docs)

        # 임베딩
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIR,
        )

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    return RetrievalQA(llm=llm, chain_type="stuff", retriever=retriever).run(question)


class RAGToolInput(BaseModel):
    question: str = Field(..., description="ESL 주제 PDF를 사용해 답변할 질문")


class RAGTool(BaseTool):
    name: str = "ESL_Chroma_RAG"
    description: str = (
        "Retrieves from '29 ESL Conversation Topics' PDF via ChromaDB and answers the question"
    )
    args_schema: Type[BaseModel] = RAGToolInput

    def _run(self, question: str) -> str:
        try:
            return _qa(question)
        except Exception as e:
            return f"Chroma RAG 사용중 에러가 발생했습니다: {e}"


rag_tool = RAGTool()
