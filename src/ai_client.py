from __future__ import annotations

from google import genai
from google.genai import errors, types
import httpx


RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]


class IncompleteGeneration(RuntimeError):
    def __init__(self, reason) -> None:
        self.reason = str(reason) if reason is not None else "UNKNOWN"
        super().__init__(f"A geração não terminou normalmente (motivo: {self.reason}). Tente novamente.")


class GeminiClient:
    """Adapter around Gemini generation and embedding APIs with transient-error resilience."""

    def __init__(
        self,
        api_key: str,
        llm_model: str,
        embedding_model: str,
        embedding_dimensions: int,
        llm_fallback_model: str = "gemini-3.5-flash-lite",
    ) -> None:
        if not api_key:
            raise ValueError("A chave da API Gemini é obrigatória.")

        retry_options = types.HttpRetryOptions(
            attempts=3,
            initial_delay=1.0,
            max_delay=4.0,
            exp_base=2.0,
            jitter=1.0,
            http_status_codes=RETRYABLE_STATUS_CODES,
        )
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(retry_options=retry_options),
        )
        self._llm_model = llm_model
        self._llm_fallback_model = llm_fallback_model
        self._embedding_model = embedding_model
        self._embedding_dimensions = embedding_dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.models.embed_content(
            model=self._embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self._embedding_dimensions,
            ),
        )
        return [embedding.values for embedding in response.embeddings or []]

    def embed_query(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model=self._embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="QUESTION_ANSWERING",
                output_dimensionality=self._embedding_dimensions,
            ),
        )
        if not response.embeddings:
            raise RuntimeError("A API Gemini não retornou embedding para a consulta.")
        return response.embeddings[0].values

    def generate(self, prompt: str) -> str:
        try:
            return self._generate_with_model(self._llm_model, prompt)
        except errors.ServerError as exc:
            should_fallback = (
                exc.code == 503
                and self._llm_fallback_model
                and self._llm_fallback_model != self._llm_model
            )
            if not should_fallback:
                raise

            return self._generate_with_model(self._llm_fallback_model, prompt)

    def _generate_with_model(self, model: str, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=700),
        )
        candidates = response.candidates or []
        reason = candidates[0].finish_reason if candidates else None
        if reason != types.FinishReason.STOP:
            raise IncompleteGeneration(reason)
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("A API Gemini retornou uma resposta vazia.")
        return text


class GroqGenerationClient(GeminiClient):
    """Use Gemini for embeddings and Groq for answer generation."""

    def __init__(self, *args, groq_api_key: str, groq_model: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not groq_api_key or not groq_model:
            raise ValueError("Chave e modelo Groq são obrigatórios.")
        self._groq_api_key = groq_api_key
        self._groq_model = groq_model

    def generate(self, prompt: str) -> str:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._groq_api_key}"},
            json={"model": self._groq_model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2, "max_completion_tokens": 2048},
            timeout=60.0,
        )
        if response.is_error:
            raise RuntimeError(f"A API Groq retornou erro HTTP {response.status_code}.")
        choices = response.json().get("choices") or []
        if not choices:
            raise RuntimeError("A API Groq não retornou resposta.")
        choice = choices[0]
        if choice.get("finish_reason") != "stop":
            raise IncompleteGeneration(choice.get("finish_reason"))
        text = (choice.get("message", {}).get("content") or "").strip()
        if not text:
            raise RuntimeError("A API Groq retornou uma resposta vazia.")
        return text
