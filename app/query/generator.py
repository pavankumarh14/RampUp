from __future__ import annotations

from typing import Literal

import structlog
from openai import AsyncAzureOpenAI, AsyncOpenAI

from app.config.settings import settings

logger = structlog.get_logger(__name__)

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

Confidence = Literal["high", "partial", "not_found"]

_SYSTEM_PROMPT = """\
You are RampUp, an AI assistant that helps new employees find answers \
from their company's internal knowledge base.

Rules:
1. Answer ONLY using the provided context passages. Do not use prior knowledge.
2. If the context does not contain enough information to answer, reply with
   exactly: "I could not find a confident answer in the knowledge base."
3. Always cite the source title and URL for every fact you use.
4. Be concise and structured. Use bullet points for multi-step answers.

# TODO: tune system prompt for better grounding and confidence classification
#   - Add few-shot examples demonstrating high / partial / not_found responses.
#   - Consider asking the model to output structured JSON (answer + confidence)
#     instead of parsing confidence heuristically.
#   - Experiment with chain-of-thought to reduce hallucinations on edge cases.
"""


class AnswerGenerator:
    """Generates grounded answers from retrieved context using GPT-4o."""

    def __init__(self) -> None:
        self._client: AsyncAzureOpenAI | AsyncOpenAI | None = None

    def _get_client(self) -> AsyncAzureOpenAI | AsyncOpenAI:
        if self._client is None:
            provider = settings.LLM_PROVIDER.lower()
            if provider == "openai":
                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            elif provider == "gemini":
                self._client = AsyncOpenAI(
                    base_url=_GEMINI_BASE_URL,
                    api_key=settings.GEMINI_API_KEY,
                )
            elif provider == "groq":
                self._client = AsyncOpenAI(
                    base_url=_GROQ_BASE_URL,
                    api_key=settings.GROQ_API_KEY,
                )
            else:
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                )
        return self._client

    def _get_chat_model(self) -> str:
        provider = settings.LLM_PROVIDER.lower()
        if provider == "openai":
            return settings.OPENAI_CHAT_MODEL
        if provider == "gemini":
            return settings.GEMINI_CHAT_MODEL
        if provider == "groq":
            return settings.GROQ_CHAT_MODEL
        return settings.AZURE_OPENAI_CHAT_DEPLOYMENT

    @staticmethod
    def _build_context_block(chunks: list[dict]) -> str:
        """Format retrieved chunks into a numbered context block for the prompt."""
        lines: list[str] = ["## Retrieved Context\n"]
        for i, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[{i}] Source: {chunk['title']} ({chunk['source_url']})\n"
                f"    Score: {chunk['similarity_score']}\n"
                f"    Text: {chunk['text']}\n"
            )
        return "\n".join(lines)

    @staticmethod
    def _classify_confidence(answer: str, num_chunks: int) -> Confidence:
        """
        Heuristically classify confidence based on answer content and chunk count.

        # TODO: replace with a structured JSON output from the model so confidence
        #   is self-reported rather than inferred from answer text.
        """
        not_found_phrase = "could not find a confident answer"
        if not_found_phrase in answer.lower():
            return "not_found"
        if num_chunks == 0:
            return "not_found"
        if num_chunks < 2:
            return "partial"
        return "high"

    async def generate(
        self,
        query: str,
        context_chunks: list[dict],
    ) -> dict:
        """
        Generate a grounded answer from *context_chunks* for the given *query*.

        Returns:
            answer            – natural language answer string
            sources           – deduplicated list of source URLs cited
            confidence        – "high" | "partial" | "not_found"
        """
        client = self._get_client()

        logger.info("generator.generate.start", query=query, num_chunks=len(context_chunks))

        if not context_chunks:
            logger.info("generator.generate.no_chunks")
            return {
                "answer": "I could not find a confident answer in the knowledge base.",
                "sources": [],
                "confidence": "not_found",
            }

        context_block = self._build_context_block(context_chunks)
        user_message = f"{context_block}\n\n## Question\n{query}"
        
        logger.info("generator.generate.context", context_block=context_block)

        response = await client.chat.completions.create(
            model=self._get_chat_model(),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        answer = (response.choices[0].message.content or "").strip()
        sources = list({c["source_url"] for c in context_chunks})
        confidence = self._classify_confidence(answer, len(context_chunks))

        logger.info(
            "generator.generate.done",
            query=query[:80],
            confidence=confidence,
            num_sources=len(sources),
        )

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
        }


generator = AnswerGenerator()
