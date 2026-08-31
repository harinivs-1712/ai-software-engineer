import { useState, Children, isValidElement } from "react";


// Helper to recursively get text content from React nodes
const getRawText = (children) => {
  return Children.toArray(children).reduce((text, child) => {
    let newText = "";
    if (typeof child === "string" || typeof child === "number") {
      newText = child.toString();
    } else if (isValidElement(child) && child.props.children) {
      newText = getRawText(child.props.children);
    }
    return text + newText;
  }, "");
};


function CodeBlock({
  language,
  children,
}) {

  const [copied, setCopied] =
    useState(false);


  const rawCode = getRawText(children).replace(
    /\n$/,
    ""
  );


  const handleCopy = async () => {

    try {

      await navigator.clipboard.writeText(
        rawCode
      );

      setCopied(true);


      setTimeout(() => {
        setCopied(false);
      }, 2000);

    } catch (error) {

      console.error(
        "Failed to copy code:",
        error
      );

    }
  };


  return (
    <div className="my-4 overflow-hidden rounded-xl border border-gray-800 bg-gray-950 shadow-lg shadow-black/10">

      <div className="flex items-center justify-between border-b border-gray-800 bg-gray-900 px-4 py-2">

        <span className="text-xs font-medium text-gray-500">
          {language || "code"}
        </span>


        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-gray-500 transition hover:bg-gray-800 hover:text-gray-200 font-medium"
        >
          {copied ? (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-500">
                <path d="M20 6 9 17l-5-5"/>
              </svg>
              <span className="text-green-400">Copied!</span>
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
                <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
              </svg>
              <span>Copy</span>
            </>
          )}
        </button>

      </div>


      <pre className="max-h-[500px] overflow-auto p-4 text-[13px] leading-6">

        <code>
          {children}
        </code>

      </pre>

    </div>
  );
}


export default CodeBlock;