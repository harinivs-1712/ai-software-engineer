import { useEffect, useRef } from "react";
import Message from "./Message";


const suggestions = [
  "Explain binary search in Java",
  "Debug this Python code",
  "Explain REST APIs",
  "Solve Two Sum optimally",
];


function ChatWindow({
  messages,
  loading,
  onSuggestion,
}) {

  const bottomRef =
    useRef(null);


  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages, loading]);


  return (
    <main className="min-h-0 flex-1 overflow-y-auto">

      <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-4 py-8 sm:px-6">

        {messages.length === 0 ? (

          <div className="flex flex-1 flex-col items-center justify-center py-12 text-center">

            {/* Icon */}

            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600 text-xl font-bold shadow-lg shadow-blue-600/20">
              AI
            </div>


            {/* Heading */}

            <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              AI Software Engineer
            </h2>


            <p className="mt-3 max-w-lg text-sm leading-6 text-gray-500 sm:text-base">
              Generate code, debug errors, explain
              algorithms, review code, and solve
              software engineering problems.
            </p>


            {/* Suggestions */}

            <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">

              {suggestions.map(
                (suggestion) => (

                  <button
                    key={suggestion}
                    onClick={() =>
                      onSuggestion?.(
                        suggestion
                      )
                    }
                    className="rounded-xl border border-gray-800 bg-gray-900/60 px-4 py-3 text-left text-sm text-gray-400 transition hover:border-gray-700 hover:bg-gray-900 hover:text-gray-200"
                  >
                    {suggestion}
                  </button>

                )
              )}

            </div>


            <p className="mt-8 text-xs text-gray-700">
              Powered by Gemini
            </p>

          </div>

        ) : (

          <div className="flex flex-col gap-7">

            {messages.map(
              (message) => (

                <Message
                  key={message.id}
                  role={message.role}
                  content={message.content}
                />

              )
            )}


            {loading &&
              messages.length > 0 &&
              messages[messages.length - 1]?.role ===
                "assistant" &&
              !messages[messages.length - 1]?.content && (

                <div className="flex items-center gap-3">

                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white">
                    AI
                  </div>

                  <div className="rounded-2xl bg-gray-800 px-4 py-3">

                    <div className="flex gap-1">

                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />

                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />

                      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />

                    </div>

                  </div>

                </div>
              )}

          </div>

        )}


        <div ref={bottomRef} />

      </div>

    </main>
  );
}


export default ChatWindow;