"""
OpenRouter AI Client Utility.

Provides unified interface for:
- Text Embeddings generation (1536-dim vector representation)
- Chat Completion generation (Streaming & Non-Streaming)
"""
import json
from typing import AsyncGenerator, Generator, List
from fastapi import HTTPException, status
import httpx

from app.config import settings


class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.chat_model = settings.OPENROUTER_CHAT_MODEL
        self.embedding_model = settings.OPENROUTER_EMBEDDING_MODEL

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://fastapi-rag.local",
            "X-Title": "FastAPI Production RAG",
            "Content-Type": "application/json",
        }

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a batch of text strings.

        :param texts: List of text chunks or query strings.
        :return: List of 1536-dimensional float vectors.
        """
        if not texts:
            return []

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.embedding_model,
            "input": texts,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"OpenRouter Embeddings API failed [{response.status_code}]: {response.text}",
                )

            data = response.json()
            # Sort embeddings by original input index to ensure exact order
            items = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in items]

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to communicate with OpenRouter API: {str(exc)}",
            )

    def generate_single_embedding(self, text: str) -> List[float]:
        """Convenience method for a single string embedding (e.g. user search query)."""
        vectors = self.generate_embeddings([text])
        if not vectors:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Embedding generation returned empty vector list",
            )
        return vectors[0]

    def generate_chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> str:
        """
        Generates a non-streaming grounded response from the LLM.
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"OpenRouter Chat API failed [{response.status_code}]: {response.text}",
                )

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to communicate with OpenRouter API: {str(exc)}",
            )

    def stream_chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> Generator[str, None, None]:
        """
        Yields tokens in real-time as Server-Sent Events (SSE) from OpenRouter.
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'error': f'OpenRouter returned {response.status_code}'})}\n\n"
                        return

                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break
                            try:
                                chunk_json = json.loads(raw_data)
                                delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield f"data: {json.dumps({'token': content})}\n\n"
                            except json.JSONDecodeError:
                                continue
        except httpx.RequestError as exc:
            yield f"data: {json.dumps({'error': f'Streaming connection failed: {str(exc)}'})}\n\n"


openrouter_client = OpenRouterClient()

