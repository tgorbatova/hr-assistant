import json

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
