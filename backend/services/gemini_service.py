from collections.abc import Iterator

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, MODEL_NAME

from prompts.software_engineer import SYSTEM_PROMPT


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
) -> Iterator[str]:

    contents = build_contents(
        history,
        message
    )


    response_stream = (
        client.models.generate_content_stream(
            model=MODEL_NAME,

            contents=contents,

            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
    )


    for chunk in response_stream:

        if chunk.text:
            yield chunk.text