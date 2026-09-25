from __future__ import annotations

import hashlib
import math
import sys
import types
from typing import Any

# Workaround for upstream RAGAS bug (issues #2741, #2753)
# where langchain_community.chat_models.vertexai is imported unconditionally
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _shim = types.ModuleType("langchain_community.chat_models.vertexai")
    _shim.ChatVertexAI = type("ChatVertexAI", (), {})
    sys.modules["langchain_community.chat_models.vertexai"] = _shim

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.embeddings.base import BaseRagasEmbeddings
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from ragsentry.metrics.judge_config import JudgeConfig
from ragsentry.storage.base import RunRow


class StandaloneEmbeddings(BaseRagasEmbeddings):
    """
    Zero-dependency, deterministic embedding engine for text-only LLM providers
    (xAI, Anthropic, Groq) that do not supply an embedding endpoint.
    Prevents RAGAS from crashing when an OpenAI key is not configured.
    """

    def __init__(self, dim: int = 384) -> None:
        super().__init__()
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for word in text.lower().split():
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[h] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)


def create_judge_llm(config: JudgeConfig):
    """Instantiate the swappable LangChain chat model wrapper for RAGAS."""
    api_key = config.get_api_key()

    if config.provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model_name=config.model,
                anthropic_api_key=api_key,
                temperature=config.temperature,
                **config.extra_params,
            )
        except ImportError:
            raise ImportError(
                "Anthropic support requires 'langchain-anthropic'. "
                "Install it with: pip install langchain-anthropic"
            )

    # Standard OpenAI-compatible providers:
    # OpenAI, Gemini, Groq, xAI (Grok), Ollama, DeepSeek, OpenRouter, local servers
    kwargs: dict[str, Any] = {
        "model": config.model,
        "openai_api_key": api_key,
        "temperature": config.temperature,
        **config.extra_params,
    }
    if config.api_base:
        kwargs["openai_api_base"] = config.api_base

    return ChatOpenAI(**kwargs)


def create_judge_embeddings(config: JudgeConfig):
    """
    Resolve embeddings provider. If using OpenAI with a valid key, uses OpenAIEmbeddings;
    otherwise uses the standalone fallback so non-OpenAI providers (xAI, Groq, Anthropic)
    never crash on missing OpenAI credentials.
    """
    if config.provider == "openai":
        try:
            return OpenAIEmbeddings(openai_api_key=config.get_api_key())
        except Exception:
            pass

    return StandaloneEmbeddings()


def score_run_rows(rows: list[RunRow], config: JudgeConfig) -> tuple[list[RunRow], dict[str, float]]:
    """Score evaluated rows using RAGAS metrics and return (scored_rows, average_scores)."""
    if not rows:
        return rows, {}

    llm = create_judge_llm(config)
    embeddings = create_judge_embeddings(config)

    # Prepare dataset for Ragas
    data: dict[str, list[Any]] = {
        "question": [r.question for r in rows],
        "answer": [r.answer for r in rows],
        "contexts": [r.contexts for r in rows],
        "ground_truth": [r.ground_truth or "" for r in rows],
    }

    dataset = Dataset.from_dict(data)

    # Determine which metrics can be run
    has_ground_truth = any(bool(r.ground_truth) for r in rows)
    metrics = [faithfulness, answer_relevancy]
    if has_ground_truth:
        metrics.extend([context_precision, context_recall])

    # Run RAGAS evaluation
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,
    )

    # Convert results dataframe/dict to per-row scores
    results_df = results.to_pandas()

    for idx, row in enumerate(rows):
        row_scores: dict[str, float] = {}
        for metric in metrics:
            metric_name = metric.name
            if metric_name in results_df.columns:
                val = results_df.iloc[idx][metric_name]
                if val is not None and not str(val).lower() == "nan":
                    try:
                        row_scores[metric_name] = round(float(val), 4)
                    except (ValueError, TypeError):
                        pass
        row.scores = row_scores

    # Compute overall average scores safely
    avg_scores: dict[str, float] = {}
    for metric in metrics:
        name = metric.name
        try:
            if name in results_df.columns:
                series = results_df[name].dropna()
                if not series.empty:
                    avg_scores[name] = round(float(series.mean()), 4)
        except Exception:
            pass

    return rows, avg_scores