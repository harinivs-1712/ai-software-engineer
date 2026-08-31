
from collections.abc import Iterator

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME

from services.prompt_manager import (
    get_system_prompt
)


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def build_contents(history, message):

    contents = []


    for item in history:

        role = (
            "model"
            if item.role == "assistant"
            else "user"
        )

        contents.append(
            types.Content(
                role=role,
                parts=[
                    types.Part(
                        text=item.content
                    )
                ],
            )
        )


    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=message
                )
            ],
        )
    )


    return contents


def generate_response_stream(
    message: str,
    history,
    mode: str,
) -> Iterator[str]:

    contents = build_contents(
        history,
        message
    )


    system_prompt = get_system_prompt(
        mode
    )


    response_stream = (
        client.models.generate_content_stream(
            model=MODEL_NAME,

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )
    )


    for chunk in response_stream:

        if chunk.text:
            yield chunk.text

