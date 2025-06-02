import asyncio
import json

from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from resume_service.domain.exceptions.format import ResumeParsingError
from resume_service.domain.models.resume_info import ResumeInfo

json_schema = ResumeInfo.model_json_schema()


class LLMAdapter:
    def __init__(self, llm_client: AsyncOpenAI) -> None:
        self._client = llm_client
        self._max_retries = 3

    async def format_resume(self, resume: str, attempt: int = 1) -> ResumeInfo:
        """Get resume as structured output."""
        chat_response = await self._client.chat.completions.create(
            model="Qwen/Qwen2.5-14B-Instruct",
            messages=[
                {"role": "system", "content": "Ты полезный ассистент."},
                {
                    "role": "user",
                    "content": f"Преобразуй резюме: {resume} в JSON.",
                },
            ],
            extra_body={"guided_json": json_schema},
            temperature=0.0,
            top_p=1.0,
        )

        json_res = chat_response.choices[0].message.content
        data = json.loads(json_res)

        try:
            ResumeInfo.model_validate(data)
        except:
            if attempt <= self._max_retries:
                return await self.format_resume(resume, attempt + 1)
            raise ResumeParsingError

        return ResumeInfo(**data)

    async def answer(self, question: str, resume: dict) -> StreamingResponse:
        async def event_stream():
            response = await self._client.chat.completions.create(
                model="Qwen/Qwen2.5-14B-Instruct",
                messages=[{"role": "user", "content": f"Дано резюме: {resume}\n{question}"}],
                max_tokens=2000,
                stream=True,
            )
            async for chunk in response:
                print("CHUNK:", chunk)
                delta = chunk.choices[0].delta.content
                print("DELTA", delta)
                if delta:
                    yield delta
            await asyncio.sleep(0)  # Yield control

        return StreamingResponse(event_stream(), media_type="text/plain")
