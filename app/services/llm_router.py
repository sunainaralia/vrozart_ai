import openai
import httpx
import os
from typing import AsyncGenerator
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("CHATGPT_API_KEY"))
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")

async def stream_chat_response(model: str, prompt: str) -> AsyncGenerator[str, None]:
    if model.startswith("gpt"):
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    elif model.startswith("claude"):
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        async with httpx.AsyncClient(timeout=None) as http_client:
            async with http_client.stream("POST", url="https://api.anthropic.com/v1/messages", headers=headers, json=body) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        yield line.replace("data: ", "")


# 2️⃣ NON-STREAMING Function
async def get_full_chat_response(model: str, prompt: str) -> str:
    if model.startswith("gpt"):
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    elif model.startswith("claude"):
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        async with httpx.AsyncClient() as http_client:
            r = await http_client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
            res = r.json()
            return res["content"][0]["text"]