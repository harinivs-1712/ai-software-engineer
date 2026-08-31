import { useEffect, useRef } from "react";

function InputBox({
  value,
  onChange,
  onSubmit,
  onStop,
  disabled,
  loading,
}) {

  const handleKeyDown = (event) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      if (
        !disabled &&
        value.trim()
      ) {
        onSubmit(event);
      }

    }

  };
  const inputRef = useRef(null);

  useEffect(() => {

  inputRef.current?.focus();

}, []);



  return (
    <div className="border-t border-gray-800 bg-gray-950 px-4 pb-4 pt-3">

      <form
        onSubmit={onSubmit}
        className="mx-auto max-w-4xl"
      >

        <div className="rounded-2xl border border-gray-700 bg-gray-900 shadow-lg shadow-black/10 transition focus-within:border-gray-600">

          <textarea
          ref={inputRef}
            value={value}
            onChange={(event) =>
              onChange(event.target.value)
            }
            onKeyDown={handleKeyDown}
            placeholder={
              loading
                ? "AI is generating..."
                : "Ask your AI Software Engineer..."
            }
            disabled={disabled}
            rows={2}
            className="max-h-40 min-h-12 w-full resize-none bg-transparent px-4 pt-3 text-sm leading-6 text-white outline-none placeholder:text-gray-600 disabled:cursor-not-allowed"
          />


          <div className="flex items-center justify-between px-3 pb-2">

            <span className="hidden text-[11px] text-gray-600 sm:block">
              Enter to send · Shift + Enter for new line
            </span>


            <div className="ml-auto">

              {loading ? (

                <button
                  type="button"
                  onClick={onStop}
                  className="rounded-xl bg-gray-700 px-4 py-2 text-xs font-medium text-white transition hover:bg-gray-600"
                >
                  Stop
                </button>

              ) : (

                <button
                  type="submit"
                  disabled={!value.trim()}
                  className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-30"
                >
                  ↑
                </button>

              )}

            </div>

          </div>

        </div>


        <p className="mt-2 text-center text-[10px] text-gray-700">
          AI can make mistakes. Review generated code before using it.
        </p>

      </form>

    </div>
  );
}


export default InputBox;
