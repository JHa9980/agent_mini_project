"""Service clients for the Edge AI Trend Lab project."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

from dotenv import load_dotenv

_DOTENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=_DOTENV_PATH, override=False)

from langchain_openai import ChatOpenAI

try:
    from langchain_tavily import TavilySearch  # type: ignore
except ImportError:  # pragma: no cover
    from langchain_community.tools.tavily_search import TavilySearchResults as TavilySearch  # type: ignore


@lru_cache(maxsize=1)
def get_settings() -> Dict[str, Any]:
    # LangSmith 환경 변수 디버깅
    print("--- LangSmith 변수 확인 ---")
    print(f"LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
    print(f"LANGCHAIN_API_KEY 설정 여부: {'설정됨' if os.environ.get('LANGCHAIN_API_KEY') else '설정 안됨'}")
    print(f"LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")
    print("--------------------------")

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    tavily_api_key = os.environ.get("TAVILY_API_KEY")

    if not openai_api_key:
        raise EnvironmentError("OPENAI_API_KEY not set. Please configure .env.")
    if not tavily_api_key:
        raise EnvironmentError("TAVILY_API_KEY not set. Please configure .env.")

    return {
        "openai_api_key": openai_api_key,
        "tavily_api_key": tavily_api_key,
    }


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        streaming=False,
        openai_api_key=settings["openai_api_key"],
    )


@lru_cache(maxsize=1)
def get_tavily_tool():
    settings = get_settings()
    try:
        return TavilySearch(
            max_results=6,
            include_answer=True,
            api_key=settings["tavily_api_key"],
        )
    except TypeError:
        return TavilySearch(
            max_results=6,
            include_answer=True,
            tavily_api_key=settings["tavily_api_key"],
        )
