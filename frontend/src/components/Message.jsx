import { Children, isValidElement } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import CodeBlock from "./CodeBlock";


function Message({
  role,
  content,
}) {

  const isUser =
    role === "user";


  return (
    <div
      className={`flex w-full gap-3 ${
        isUser
          ? "justify-end"
          : "justify-start"
      }`}
    >

      {!isUser && (

        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white shadow-lg shadow-blue-600/10">
          AI
        </div>

      )}


      <div
        className={`min-w-0 max-w-3xl ${
          isUser
            ? "order-first"
            : ""
        }`}
      >

        <div
          className={
            isUser
              ? "rounded-2xl bg-blue-600 px-4 py-3 text-sm leading-7 text-white"
              : "px-1 py-1 text-sm leading-7 text-gray-200"
          }
        >

          {isUser ? (

            <p className="whitespace-pre-wrap break-words">
              {content}
            </p>

          ) : (

            <div className="markdown-content">

              <ReactMarkdown
                remarkPlugins={[
                  remarkGfm
                ]}
                rehypePlugins={[
                  rehypeHighlight
                ]}
                components={{
                  pre({ children, ...props }) {
                    const codeElement = Children.toArray(children).find(
                      (child) =>
                        isValidElement(child) &&
                        (child.type === "code" ||
                          child.props?.node?.tagName === "code" ||
                          child.props?.className?.includes("hljs") ||
                          child.props?.className?.includes("language-"))
                    );

                    if (codeElement) {
                      const match = /language-(\w+)/.exec(
                        codeElement.props.className || ""
                      );
                      return (
                        <CodeBlock
                          language={match ? match[1] : "code"}
                        >
                          {codeElement.props.children}
                        </CodeBlock>
                      );
                    }

                    return <pre {...props}>{children}</pre>;
                  },
                  code({
                    node,
                    className,
                    children,
                    ...props
                  }) {
                    return (
                      <code
                        className="rounded-md bg-gray-900 px-1.5 py-0.5 text-sm text-blue-300"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {content}
              </ReactMarkdown>

            </div>

          )}

        </div>

      </div>


      {isUser && (

        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-800 text-xs font-bold text-gray-300">
          U
        </div>

      )}

    </div>
  );
}


export default Message;