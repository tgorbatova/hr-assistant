from openai import AsyncOpenAI


class LLMAdapter:
    def __init__(self, llm_client: AsyncOpenAI) -> None:
        self._client = llm_client

    async def format_resume(self, resume: str) -> str:
        """Get resume as structured output."""
        completions = await self._client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": resume,
                },
            ],
        )

        return completions.choices[0].message.content
