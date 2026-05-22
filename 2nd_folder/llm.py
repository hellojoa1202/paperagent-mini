import os

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"


def ask_llm(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set OPENAI_API_KEY before running.")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
