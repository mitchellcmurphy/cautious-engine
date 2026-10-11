from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.exceptions import SummarizationError

T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        """Plain-text completion, used for the cheaper per-chunk map step."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # openai SDK raises several distinct exception types
            raise SummarizationError(str(exc)) from exc

        content = response.choices[0].message.content
        if not content:
            raise SummarizationError("OpenAI returned an empty response")
        return content

    async def complete_structured(
        self, system_prompt: str, user_prompt: str, schema_model: type[T]
    ) -> T:
        """Structured-output completion constrained to `schema_model`."""
        try:
            response = await self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=schema_model,
            )
        except Exception as exc:
            raise SummarizationError(str(exc)) from exc

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise SummarizationError(
                "OpenAI response did not match the expected schema"
            )
        return parsed
