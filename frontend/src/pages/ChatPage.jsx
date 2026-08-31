import { useEffect, useRef, useState } from "react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import InputBox from "../components/InputBox";

import { streamMessage } from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import {
  loadConversations,
  saveConversations,
} from "../services/conversationStorage";

import {
  createConversation,
  initializeConversations,
} from "../utils/conversation";


function ChatPage() {

  const [messages, setMessages] =
    useState([]);

  const [conversations, setConversations] =
    useState(() => {

      const stored =
        loadConversations();

      return stored.length > 0
        ? stored
        : [createConversation()];
    });


  const [activeConversationId, setActiveConversationId] =
    useState(null);


  useEffect(() => {

    setActiveConversationId(
      conversations[0]?.id ?? null
    );

  }, []);

  useEffect(() => {

    saveConversations(
      conversations
    );

  }, [conversations]);

  const activeConversation =
    conversations.find(
      (conversation) =>
        conversation.id ===
        activeConversationId
    );

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);


  const abortControllerRef =
    useRef(null);

  const isFirstMessage =
    activeConversation.messages.length === 0;


  const handleSuggestion = (suggestion) => {
    setInput(suggestion);
  };


  const handleSubmit = async (event) => {

    event.preventDefault();


    if (
      !input.trim() ||
      loading ||
      !activeConversation
    ) {
      return;
    }


    setError(null);


    const currentMessage =
      input.trim();


    const history =
      activeConversation.messages
        .filter(
          (message) =>
            message.content.trim() !== ""
        )
        .map((message) => ({
          role: message.role,
          content: message.content,
        }));

    const generateConversationTitle = (
      message
    ) => {

      const cleaned =
        message
          .replace(/\s+/g, " ")
          .trim();


      if (cleaned.length <= 35) {
        return cleaned;
      }


      return (
        cleaned.substring(0, 35) +
        "..."
      );
    };

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: currentMessage,
    };


    const assistantMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
    };


    const updatedMessages = [
      ...activeConversation.messages,
      userMessage,
      assistantMessage,
    ];


    updateConversation(
      activeConversation.id,
      {
        messages: updatedMessages,
      }
    );


    setInput("");

    setLoading(true);


    const controller =
      new AbortController();


    abortControllerRef.current =
      controller;


    if (isFirstMessage) {

      updateConversation(
        activeConversation.id,
        {
          title:
            generateConversationTitle(
              currentMessage
            ),
          messages: updatedMessages,
        }
      );

    } else {

      updateConversation(
        activeConversation.id,
        {
          messages: updatedMessages,
        }
      );

    }


    try {

      await streamMessage(
        activeConversation.id,
        currentMessage,
        history,

        (chunk) => {

          setConversations(
            (previousConversations) =>
              previousConversations.map(
                (conversation) => {

                  if (
                    conversation.id !==
                    activeConversation.id
                  ) {
                    return conversation;
                  }


                  return {
                    ...conversation,

                    messages:
                      conversation.messages.map(
                        (message) => {

                          if (
                            message.id !==
                            assistantMessage.id
                          ) {
                            return message;
                          }


                          return {
                            ...message,

                            content:
                              message.content +
                              chunk,
                          };

                        }
                      ),

                    updatedAt:
                      new Date().toISOString(),
                  };

                }
              )
          );

        },

        controller.signal
      );


    } catch (error) {

      if (
        error.name ===
        "AbortError"
      ) {

        console.log(
          "Generation stopped."
        );

      } else {

        const message =
          getErrorMessage(error);


        setError(message);

      }

    } finally {

      setLoading(false);

      abortControllerRef.current =
        null;

    }
  };



  const handleStop = () => {

    if (
      abortControllerRef.current
    ) {

      abortControllerRef.current.abort();

    }

  };

  const clearChat = () => {

    setMessages([]);

    setInput("");

    setError(null);
  };


  const handleNewChat = () => {

  handleStop();


  const conversation =
    createConversation();


  setConversations(
    (previousConversations) => [
      conversation,
      ...previousConversations,
    ]
  );


  setActiveConversationId(
    conversation.id
  );


  setInput("");

  setError(null);

};

const handleSelectConversation = (
  conversationId
) => {

  handleStop();


  setActiveConversationId(
    conversationId
  );


  setInput("");

  setError(null);

};

const handleDeleteConversation = (
  conversationId
) => {

  handleStop();


  setConversations(
    (previousConversations) =>
      previousConversations.filter(
        (conversation) =>
          conversation.id !==
          conversationId
      )
  );


  if (
    conversationId ===
    activeConversationId
  ) {

    const remaining =
      conversations.filter(
        (conversation) =>
          conversation.id !==
          conversationId
      );


    if (remaining.length > 0) {

      setActiveConversationId(
        remaining[0].id
      );

    } else {

      const newConversation =
        createConversation();


      setConversations([
        newConversation
      ]);


      setActiveConversationId(
        newConversation.id
      );

    }

  }

};


  const handleRetry = () => {

    if (!messages.length) {
      return;
    }


    const lastUserMessage =
      [...messages]
        .reverse()
        .find(
          (message) =>
            message.role === "user"
        );


    if (!lastUserMessage) {
      return;
    }


    setInput(
      lastUserMessage.content
    );

    setError(null);

  };


  return (
    <div className="flex h-screen overflow-hidden bg-gray-950 text-white">

      <Sidebar
        onNewChat={handleNewChat}
      />


      <div className="flex min-w-0 flex-1 flex-col">

        <Navbar />


        <ChatWindow
          messages={messages}
          loading={loading}
          onSuggestion={handleSuggestion}
        />


        {error && (

          <div className="mx-auto w-full max-w-4xl px-4 pb-2">

            <div className="flex items-center justify-between gap-3 rounded-lg border border-red-900 bg-red-950/40 px-4 py-3">

              <p className="text-sm text-red-300">
                {error}
              </p>


              <button
                onClick={handleRetry}
                className="shrink-0 rounded-md px-3 py-1.5 text-xs font-medium text-red-200 hover:bg-red-900"
              >
                Retry
              </button>

            </div>

          </div>

        )}


        <InputBox
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          onStop={handleStop}
          disabled={loading}
          loading={loading}
        />

      </div>

    </div>
  );
}


export default ChatPage;