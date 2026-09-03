import { useEffect, useRef, useState } from "react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import InputBox from "../components/InputBox";
import ModeSelector from "../components/ModeSelector";
import FilePreview from "../components/FilePreview";
import FileUpload from "../components/FileUpload";

import {
  streamMessage,
  uploadFile,
} from "../services/api";

import { getErrorMessage } from "../utils/errorHandler";

import {
  loadConversations,
  saveConversations,
} from "../services/conversationStorage";

import {
  createConversation,
} from "../utils/conversations";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";


function ChatPage() {

  /* -------------------------------------------------
     CONVERSATIONS
  ------------------------------------------------- */
  const [projectId, setProjectId] = useState(null);
  const [conversations, setConversations] =
    useState(() => {

      const stored =
        loadConversations();

      return stored.length > 0
        ? stored
        : [createConversation()];
    });


  const [activeConversationId, setActiveConversationId] =
    useState(() =>
      conversations[0]?.id ?? null
    );


  const activeConversation =
    conversations.find(
      (conversation) =>
        conversation.id ===
        activeConversationId
    );


  const messages =
    activeConversation?.messages ?? [];


  /* -------------------------------------------------
     CHAT STATE
  ------------------------------------------------- */

  const [selectedMode, setSelectedMode] =
    useState("generate");


  const [input, setInput] =
    useState("");


  const [loading, setLoading] =
    useState(false);


  const [error, setError] =
    useState(null);


  /* -------------------------------------------------
     FILE STATE
  ------------------------------------------------- */

  const [uploadedFile, setUploadedFile] =
    useState(null);


  const [uploading, setUploading] =
    useState(false);


  const projectInputRef =
    useRef(null);


  /* -------------------------------------------------
     ABORT CONTROLLER
  ------------------------------------------------- */

  const abortControllerRef =
    useRef(null);


  /* -------------------------------------------------
     SAVE CONVERSATIONS
  ------------------------------------------------- */

  useEffect(() => {

    saveConversations(
      conversations
    );

  }, [conversations]);


  /* -------------------------------------------------
     ENSURE ACTIVE CONVERSATION
  ------------------------------------------------- */

  useEffect(() => {

    if (conversations.length === 0) {

      const conversation =
        createConversation();


      setConversations([
        conversation,
      ]);


      setActiveConversationId(
        conversation.id
      );

      return;
    }


    if (
      !activeConversationId ||
      !conversations.some(
        (conversation) =>
          conversation.id ===
          activeConversationId
      )
    ) {

      setActiveConversationId(
        conversations[0].id
      );
    }

  }, [
    conversations,
    activeConversationId,
  ]);


  /* -------------------------------------------------
     UPDATE CONVERSATION
  ------------------------------------------------- */

  const updateConversation = (
    conversationId,
    updates
  ) => {

    setConversations(
      (previousConversations) => {

        const updated =
          previousConversations.map(
            (conversation) => {

              if (
                conversation.id !==
                conversationId
              ) {

                return conversation;
              }


              return {
                ...conversation,
                ...updates,
                updatedAt:
                  new Date().toISOString(),
              };
            }
          );


        return updated.sort(
          (a, b) =>
            new Date(b.updatedAt) -
            new Date(a.updatedAt)
        );
      }
    );
  };


  /* -------------------------------------------------
     SUGGESTIONS
  ------------------------------------------------- */

  const handleSuggestion = (
    suggestion
  ) => {

    setInput(suggestion);
  };


  /* -------------------------------------------------
     FILE UPLOAD
  ------------------------------------------------- */

  const handleFileSelected = async (
    file
  ) => {

    if (!file) {
      return;
    }


    setUploading(true);
    setError(null);


    try {

      const result =
        await uploadFile(file);
        setProjectId(result.project_id);


      setUploadedFile(result);

    } catch (error) {

      setError(
        error.message ||
        "Failed to upload file."
      );

    } finally {

      setUploading(false);
    }
  };


  /* -------------------------------------------------
     REMOVE FILE
  ------------------------------------------------- */

  const handleRemoveFile = () => {

    setUploadedFile(null);
    setProjectId(null);
    if (projectInputRef.current) {
      projectInputRef.current.value = "";
    }
    setError(null);
  };


  /* -------------------------------------------------
     PROJECT ZIP UPLOAD
  ------------------------------------------------- */

  const handleProjectButtonClick = () => {

    if (
      loading ||
      uploading
    ) {
      return;
    }


    projectInputRef.current?.click();
  };


  const handleProjectSelected = async (
    event
  ) => {

    const file =
      event.target.files?.[0];


    if (!file) {
      return;
    }


    setUploading(true);
    setError(null);


    try {

      const formData =
        new FormData();


      formData.append(
        "file",
        file
      );


      const response =
        await fetch(
          `${API_BASE_URL}/upload/project`,
          {
            method: "POST",
            body: formData,
          }
        );


      if (!response.ok) {

        let message =
          "Project upload failed.";


        try {

          const error =
            await response.json();


          message =
            error.detail ||
            message;

        } catch {
          // Ignore JSON parsing errors.
        }


        throw new Error(
          message
        );
      }


      const result =
        await response.json();


      setProjectId(result.project_id);
      setUploadedFile({
        filename: file.name,
        name: file.name,
        extension: ".zip",
        size: file.size,
        content: `📦 Project ZIP archive containing ${result.file_count} files.\nReady for codebase context and analysis.`,
        project_id: result.project_id,
        file_count: result.file_count,
      });

      setError(null);

    } catch (error) {

      setError(
        error.message ||
        "Project upload failed."
      );

    } finally {

      setUploading(false);

      /*
        Allow the user to select
        the same ZIP file again.
      */

      event.target.value = "";
    }
  };


  /* -------------------------------------------------
     SUBMIT MESSAGE
  ------------------------------------------------- */

  const handleSubmit = async (
    event
  ) => {

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
        .map(
          (message) => ({
            role: message.role,
            content: message.content,
          })
        );


    /* ---------------------------------------------
       GENERATE CONVERSATION TITLE
    --------------------------------------------- */

    const generateConversationTitle = (
      message
    ) => {

      const cleaned =
        message
          .replace(/\s+/g, " ")
          .trim();


      if (
        cleaned.length <= 35
      ) {

        return cleaned;
      }


      return (
        cleaned.substring(0, 35) +
        "..."
      );
    };


    const isFirstMessage =
      activeConversation.messages.length === 0;


    /* ---------------------------------------------
       USER MESSAGE
    --------------------------------------------- */

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: currentMessage,
      mode: selectedMode,
    };


    /* ---------------------------------------------
       ASSISTANT MESSAGE
    --------------------------------------------- */

    const assistantMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      mode: selectedMode,
    };


    const updatedMessages = [
      ...activeConversation.messages,
      userMessage,
      assistantMessage,
    ];


    /* ---------------------------------------------
       SAVE MESSAGE
    --------------------------------------------- */

    if (isFirstMessage) {

      updateConversation(
        activeConversation.id,
        {
          title:
            generateConversationTitle(
              currentMessage
            ),
          messages:
            updatedMessages,
        }
      );

    } else {

      updateConversation(
        activeConversation.id,
        {
          messages:
            updatedMessages,
        }
      );
    }


    setInput("");
    setLoading(true);


    const controller =
      new AbortController();


    abortControllerRef.current =
      controller;


    /* ---------------------------------------------
       STREAM RESPONSE
    --------------------------------------------- */

    try {

      await streamMessage(
        activeConversation.id,
        currentMessage,
        history,
        selectedMode,
        projectId,

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


  /* -------------------------------------------------
     STOP GENERATION
  ------------------------------------------------- */

  const handleStop = () => {

    if (
      abortControllerRef.current
    ) {

      abortControllerRef.current.abort();
    }
  };


  /* -------------------------------------------------
     CLEAR CURRENT CHAT
  ------------------------------------------------- */

  const clearChat = () => {

    if (!activeConversation) {
      return;
    }


    handleStop();


    updateConversation(
      activeConversation.id,
      {
        messages: [],
      }
    );


    setInput("");
    setError(null);
    setUploadedFile(null);
  };


  /* -------------------------------------------------
     NEW CHAT
  ------------------------------------------------- */

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
    setUploadedFile(null);
  };


  /* -------------------------------------------------
     SELECT CONVERSATION
  ------------------------------------------------- */

  const handleSelectConversation = (
    conversationId
  ) => {

    handleStop();


    setActiveConversationId(
      conversationId
    );


    setInput("");
    setError(null);
    setUploadedFile(null);
  };


  /* -------------------------------------------------
     DELETE CONVERSATION
  ------------------------------------------------- */

  const handleDeleteConversation = (
    conversationId
  ) => {

    handleStop();


    const remaining =
      conversations.filter(
        (conversation) =>
          conversation.id !==
          conversationId
      );


    if (
      conversationId ===
      activeConversationId
    ) {

      if (
        remaining.length > 0
      ) {

        setActiveConversationId(
          remaining[0].id
        );

      } else {

        const newConversation =
          createConversation();


        setConversations([
          newConversation,
        ]);


        setActiveConversationId(
          newConversation.id
        );
      }

    } else {

      setConversations(
        remaining
      );
    }


    setInput("");
    setError(null);
    setUploadedFile(null);
  };


  /* -------------------------------------------------
     RENAME CONVERSATION
  ------------------------------------------------- */

  const handleRenameConversation = (
    conversationId,
    newTitle
  ) => {

    const title =
      newTitle.trim();


    if (!title) {
      return;
    }


    updateConversation(
      conversationId,
      {
        title,
      }
    );
  };


  /* -------------------------------------------------
     RETRY
  ------------------------------------------------- */

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


  /* -------------------------------------------------
     RENDER
  ------------------------------------------------- */

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950 text-white">

      {/* SIDEBAR */}

      <Sidebar
        conversations={
          conversations
        }
        activeConversationId={
          activeConversationId
        }
        onNewChat={
          handleNewChat
        }
        onSelectConversation={
          handleSelectConversation
        }
        onDeleteConversation={
          handleDeleteConversation
        }
        onRenameConversation={
          handleRenameConversation
        }
      />


      {/* MAIN AREA */}

      <div className="flex min-w-0 flex-1 flex-col">

        {/* NAVBAR */}

        <Navbar />


        {/* CHAT */}

        <ChatWindow
          messages={messages}
          loading={loading}
          onSuggestion={
            handleSuggestion
          }
        />


        {/* ERROR */}

        {error && (

          <div className="mx-auto w-full max-w-4xl px-4 pb-2">

            <div className="flex items-center justify-between gap-3 rounded-lg border border-red-900 bg-red-950/40 px-4 py-3">

              <p className="min-w-0 text-sm text-red-300">
                {error}
              </p>


              <button
                type="button"
                onClick={
                  handleRetry
                }
                disabled={
                  loading
                }
                className="shrink-0 rounded-md border border-red-800 px-3 py-1.5 text-xs font-medium text-red-200 transition hover:bg-red-900 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Retry
              </button>

            </div>

          </div>
        )}


        {/* -----------------------------------------
            UPLOADED FILE PREVIEW
        ----------------------------------------- */}

        {uploadedFile && (

          <div className="mx-auto w-full max-w-4xl px-4 pb-2">

            <FilePreview
              file={
                uploadedFile
              }
              onRemove={
                handleRemoveFile
              }
            />

          </div>
        )}


        {/* -----------------------------------------
            TOOLBAR
        ----------------------------------------- */}

        <div className="mx-auto w-full max-w-4xl px-4 pb-2">

          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-gray-800 bg-gray-900/60 p-2">

            {/* MODE */}

            <div className="shrink-0">

              <ModeSelector
                selectedMode={
                  selectedMode
                }
                onModeChange={
                  setSelectedMode
                }
              />

            </div>


            {/* DIVIDER */}

            <div className="hidden h-6 w-px bg-gray-800 sm:block" />


            {/* FILE UPLOAD */}

            <div className="shrink-0">

              <FileUpload
                onFileSelected={
                  handleFileSelected
                }
                disabled={
                  loading ||
                  uploading
                }
              />

            </div>


            {/* PROJECT BUTTON */}

            <button
              type="button"
              onClick={
                handleProjectButtonClick
              }
              disabled={
                loading ||
                uploading
              }
              className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm font-medium text-gray-300 transition hover:border-gray-600 hover:bg-gray-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >

              <span>
                📁
              </span>

              <span>
                {uploading
                  ? "Uploading..."
                  : "Project"}
              </span>

            </button>


            {/* HIDDEN ZIP INPUT */}

            <input
              ref={
                projectInputRef
              }
              type="file"
              accept=".zip"
              onChange={
                handleProjectSelected
              }
              className="hidden"
              disabled={
                loading ||
                uploading
              }
            />


            {/* REMOVE FILE */}

            {uploadedFile && (

              <button
                type="button"
                onClick={
                  handleRemoveFile
                }
                disabled={
                  loading ||
                  uploading
                }
                className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-gray-700 px-3 py-2 text-sm text-gray-400 transition hover:border-gray-600 hover:bg-gray-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
              >

                <span>
                  ×
                </span>

                <span>
                  Remove
                </span>

              </button>

            )}

          </div>

        </div>


        {/* -----------------------------------------
            INPUT BOX
        ----------------------------------------- */}

        <InputBox
          value={input}
          onChange={
            setInput
          }
          onSubmit={
            handleSubmit
          }
          onStop={
            handleStop
          }
          disabled={
            loading
          }
          loading={
            loading
          }
        />

      </div>

    </div>
  );
}


export default ChatPage;