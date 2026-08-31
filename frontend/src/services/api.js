const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


export async function streamMessage(
  conversationId,
  message,
  history,
  mode,
  onChunk,
  signal
) {

  const response = await fetch(
    `${API_BASE_URL}/chat/stream`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        conversation_id: conversationId,
        message,
        history,
        mode: mode || "generate",
      }),

      signal,
    }
  );


  if (!response.ok) {

    let errorMessage =
      "The AI server returned an error.";


    try {

      const errorData =
        await response.json();

      if (errorData.detail) {
        errorMessage =
          errorData.detail;
      }

    } catch {
      // Response wasn't JSON.
    }


    throw new Error(errorMessage);
  }


  if (!response.body) {

    throw new Error(
      "The server did not provide a response stream."
    );

  }


  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();


  let finished = false;


  while (!finished) {

    const {
      value,
      done
    } = await reader.read();


    finished = done;


    if (value) {

      const chunk =
        decoder.decode(
          value,
          {
            stream: !done
          }
        );


      if (chunk) {
        onChunk(chunk);
      }

    }
  }
}