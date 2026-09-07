
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
  uploadProject,
  getProjects,
  deleteProject,
  getConversations,
  getConversation,
  createConversation,
  renameConversation,
  deleteConversation,
} from "../services/api";

import { getErrorMessage } from "../utils/errorHandler";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";


function ChatPage({ user, onLogout }) {

  /* =================================================
     CONVERSATIONS
  ================================================= */

  const [conversations, setConversations] =
    useState([]);

  const [activeConversationId, setActiveConversationId] =
    useState(null);

  const [loadingConversations, setLoadingConversations] =
    useState(true);


  /* =================================================
     CHAT STATE
  ================================================= */

  const [selectedMode, setSelectedMode] =
    useState("generate");

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);


  /* =================================================
     FILE STATE
  ================================================= */

  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const projectInputRef = useRef(null);

  /* =================================================
     LOAD PROJECTS FROM DATABASE
  ================================================= */
  const reloadProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data || []);
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  };

  useEffect(() => {
    reloadProjects();
  }, []);


  /* =================================================
     ABORT CONTROLLER
  ================================================= */

  const abortControllerRef =
    useRef(null);


  /* =================================================
     ACTIVE CONVERSATION
  ================================================= */

  const activeConversation =
    conversations.find(
      (conversation) =>
        conversation.id === activeConversationId
    );

  const messages =
    activeConversation?.messages ?? [];


  /* =================================================
     LOAD CONVERSATIONS FROM DATABASE
  ================================================= */

  useEffect(() => {

    const fetchConversations = async () => {

      try {

        setLoadingConversations(true);
        setError(null);

        const data =
          await getConversations();

        /*
         * The list endpoint may only return
         * conversation metadata.
         *
         * We therefore load the first conversation
         * separately so that its messages are available.
         */

        if (!data || data.length === 0) {

          const newConversation =
            await createConversation("New Chat");

          const fullConversation =
            await getConversation(
              newConversation.id
            );

          setConversations([
            fullConversation,
          ]);

          setActiveConversationId(
            fullConversation.id
          );

          return;
        }


        /*
         * Select the newest conversation.
         */

        const firstConversation =
          await getConversation(
            data[0].id
          );


        setConversations([
          {
            ...data[0],
            ...firstConversation,
          },

          ...data.slice(1),
        ]);


        setActiveConversationId(
          data[0].id
        );

      } catch (error) {

        console.error(
          "Failed to load conversations:",
          error
        );

        setError(
          getErrorMessage(error) ||
          "Failed to load conversations."
        );

      } finally {

        setLoadingConversations(false);

      }

    };


    fetchConversations();

  }, []);


  /* =================================================
     SELECT CONVERSATION
  ================================================= */

  const handleSelectConversation = async (
    conversationId
  ) => {

    handleStop();

    try {

      setError(null);

      const conversation =
        await getConversation(
          conversationId
        );


      setConversations(
        (previousConversations) =>
          previousConversations.map(
            (item) =>
              item.id === conversation.id
                ? {
                    ...item,
                    ...conversation,
                  }
                : item
          )
      );


      setActiveConversationId(
        conversation.id
      );


      setInput("");
      setUploadedFile(null);
      setProjectId(null);

    } catch (error) {

      console.error(
        "Failed to load conversation:",
        error
      );

      setError(
        getErrorMessage(error) ||
        "Failed to load conversation."
      );
    }
  };


  /* =================================================
     CREATE NEW CHAT
  ================================================= */

  const handleNewChat = async () => {

    handleStop();

    try {

      setError(null);

      const conversation =
        await createConversation(
          "New Chat"
        );


      /*
       * Add new conversation to the
       * beginning of the sidebar.
       */

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
      setUploadedFile(null);
      setProjectId(null);

    } catch (error) {

      console.error(
        "Failed to create conversation:",
        error
      );

      setError(
        getErrorMessage(error) ||
        "Failed to create conversation."
      );
    }
  };


  /* =================================================
     UPDATE LOCAL CONVERSATION STATE
  ================================================= */

  const updateConversationState = (
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
                updated_at:
                  new Date().toISOString(),
                updatedAt:
                  new Date().toISOString(),
              };
            }
          );


        /*
         * Keep most recently updated conversation
         * at the top.
         */

        return updated.sort(
          (a, b) => {

            const dateA =
              new Date(
                a.updated_at ||
                a.updatedAt ||
                0
              );

            const dateB =
              new Date(
                b.updated_at ||
                b.updatedAt ||
                0
              );

            return dateB - dateA;
          }
        );
      }
    );
  };


  /* =================================================
     GENERATE CONVERSATION TITLE
  ================================================= */

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


  /* =================================================
     SUGGESTIONS
  ================================================= */

  const handleSuggestion = (
    suggestion
  ) => {

    setInput(suggestion);

  };


  /* =================================================
     FILE UPLOAD
  ================================================= */

  const handleFileSelected = async (file) => {
    if (!file) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      let result;
      if (file.name.toLowerCase().endsWith(".zip")) {
        result = await uploadProject(file);
      } else {
        result = await uploadFile(file);
      }

      const activeId = result.id || result.project_id;
      setProjectId(activeId);
      setUploadedFile(result);

      await reloadProjects();
    } catch (error) {
      console.error("File upload failed:", error);
      setError(error.message || "Failed to upload file.");
    } finally {
      setUploading(false);
    }
  };

  const handleSelectProject = (id) => {
    if (projectId === id) {
      setProjectId(null);
    } else {
      setProjectId(id);
    }
  };

  const handleDeleteProject = async (id) => {
    try {
      await deleteProject(id);
      if (projectId === id) {
        setProjectId(null);
      }
      await reloadProjects();
    } catch (err) {
      console.error("Failed to delete project:", err);
      setError(err.message || "Failed to delete project.");
    }
  };


  /* =================================================
     REMOVE FILE
  ================================================= */

  const handleRemoveFile = () => {

    setUploadedFile(null);
    setProjectId(null);

    if (projectInputRef.current) {

      projectInputRef.current.value = "";

    }

    setError(null);
  };


  /* =================================================
     PROJECT ZIP BUTTON
  ================================================= */

  const handleProjectButtonClick = () => {

    if (
      loading ||
      uploading
    ) {
      return;
    }


    projectInputRef.current?.click();
  };


  /* =================================================
     PROJECT ZIP UPLOAD
  ================================================= */

  const handleProjectSelected = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await uploadProject(file);
      const newId = result.id || result.project_id;

      setProjectId(newId);
      setUploadedFile({
        filename: file.name,
        name: file.name,
        extension: ".zip",
        size: file.size,
        content: `📦 Project ZIP archive containing ${result.file_count} files.\nReady for codebase context and analysis.`,
        project_id: newId,
        file_count: result.file_count,
      });

      await reloadProjects();
      setError(null);
    } catch (error) {
      console.error("Project upload failed:", error);
      setError(error.message || "Project upload failed.");
    } finally {
      setUploading(false);
      event.target.value = "";

    }
  };


  /* =================================================
     SUBMIT MESSAGE
  ================================================= */

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


    const conversationId =
      activeConversation.id;


    /*
     * Save the history that existed BEFORE
     * the new user message.
     *
     * This keeps the request compatible with
     * the current streamMessage implementation.
     */

    const history =
      (activeConversation.messages || [])
        .filter(
          (message) =>
            message.content &&
            message.content.trim() !== ""
        )
        .map(
          (message) => ({
            role: message.role,
            content: message.content,
          })
        );


    const isFirstMessage =
      (activeConversation.messages || [])
        .length === 0;


    /* =================================================
       USER MESSAGE
    ================================================= */

    const userMessage = {

      id:
        crypto.randomUUID(),

      role:
        "user",

      content:
        currentMessage,

      mode:
        selectedMode,
    };


    /* =================================================
       ASSISTANT MESSAGE
    ================================================= */

    const assistantMessage = {

      id:
        crypto.randomUUID(),

      role:
        "assistant",

      content:
        "",

      mode:
        selectedMode,
    };


    /*
     * Immediately update the UI.
     */

    const updatedMessages = [

      ...(activeConversation.messages || []),

      userMessage,

      assistantMessage,

    ];


    updateConversationState(
      conversationId,
      {
        messages:
          updatedMessages,
      }
    );


    setInput("");
    setLoading(true);


    /* =================================================
       USER & ASSISTANT MESSAGES AUTO-SAVED BY BACKEND
    ================================================= */
    // Note: /chat/stream automatically saves user_message before streaming 
    // and saves assistant_message when stream completes.


    /* =================================================
       RENAME FIRST CONVERSATION
    ================================================= */

    if (isFirstMessage) {

      const newTitle =
        generateConversationTitle(
          currentMessage
        );


      try {

        await renameConversation(
          conversationId,
          newTitle
        );


        updateConversationState(
          conversationId,
          {
            title:
              newTitle,
          }
        );

      } catch (error) {

        console.error(
          "Failed to rename conversation:",
          error
        );

        /*
         * Title failure should not stop
         * the AI response.
         */

        updateConversationState(
          conversationId,
          {
            title:
              newTitle,
          }
        );
      }
    }


    /* =================================================
       STREAM RESPONSE
    ================================================= */

    const controller =
      new AbortController();


    abortControllerRef.current =
      controller;


    let completeResponse = "";


    try {

      await streamMessage(
        conversationId,
        currentMessage,
        selectedMode,
        projectId,
        (chunk) => {

          /*
           * Accumulate the complete
           * assistant response.
           */

          completeResponse += chunk;


          /*
           * Update the UI while streaming.
           */

          setConversations(
            (previousConversations) =>
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

                    messages:
                      (conversation.messages || [])
                        .map(
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
                                completeResponse,

                            };
                          }
                        ),

                    updated_at:
                      new Date().toISOString(),

                    updatedAt:
                      new Date().toISOString(),

                  };

                }
              )
          );

        },

        controller.signal

      );


      // Backend /chat/stream automatically saves assistant_message on completion


    } catch (error) {

      if (
        error.name ===
        "AbortError"
      ) {

        console.log(
          "Generation stopped by user."
        );

      } else {

        console.error(
          "Streaming failed:",
          error
        );


        setError(
          getErrorMessage(error)
        );

      }

    } finally {

      setLoading(false);

      abortControllerRef.current =
        null;

    }
  };


  /* =================================================
     STOP GENERATION
  ================================================= */

  const handleStop = () => {

    if (
      abortControllerRef.current
    ) {

      abortControllerRef.current.abort();

    }
  };


  /* =================================================
     CLEAR CURRENT CHAT
  ================================================= */

  const clearChat = async () => {

    if (!activeConversation) {
      return;
    }


    handleStop();


    /*
     * IMPORTANT:
     *
     * Step 5C does not have a "clear messages"
     * endpoint yet.
     *
     * Therefore we only clear the local UI here.
     *
     * The database still contains the messages.
     *
     * We will handle permanent message clearing
     * when the conversation/message API is expanded.
     */

    updateConversationState(
      activeConversation.id,
      {
        messages: [],
      }
    );


    setInput("");
    setError(null);
    setUploadedFile(null);
    setProjectId(null);
  };


  /* =================================================
     DELETE CONVERSATION
  ================================================= */

  const handleDeleteConversation = async (
    conversationId
  ) => {

    handleStop();


    try {

      setError(null);


      /*
       * Delete from database.
       */

      await deleteConversation(
        conversationId
      );


      /*
       * Remove from local React state.
       */

      const remaining =
        conversations.filter(
          (conversation) =>
            conversation.id !==
            conversationId
        );


      setConversations(
        remaining
      );


      /*
       * If the deleted conversation
       * was active, select another one.
       */

      if (
        conversationId ===
        activeConversationId
      ) {

        if (
          remaining.length > 0
        ) {

          /*
           * Load the newest remaining
           * conversation completely.
           */

          const nextConversation =
            await getConversation(
              remaining[0].id
            );


          setConversations(
            (previousConversations) =>
              previousConversations.map(
                (conversation) =>
                  conversation.id ===
                  nextConversation.id
                    ? {
                        ...conversation,
                        ...nextConversation,
                      }
                    : conversation
              )
          );


          setActiveConversationId(
            nextConversation.id
          );

        } else {

          /*
           * If there are no conversations left,
           * create a new one in the database.
           */

          const newConversation =
            await createConversation(
              "New Chat"
            );


          setConversations([
            newConversation,
          ]);


          setActiveConversationId(
            newConversation.id
          );

        }

      }


      setInput("");
      setUploadedFile(null);
      setProjectId(null);

    } catch (error) {

      console.error(
        "Failed to delete conversation:",
        error
      );

      setError(
        getErrorMessage(error) ||
        "Failed to delete conversation."
      );
    }
  };


  /* =================================================
     RENAME CONVERSATION
  ================================================= */

  const handleRenameConversation = async (
    conversationId,
    newTitle
  ) => {

    const title =
      newTitle.trim();


    if (!title) {
      return;
    }


    try {

      setError(null);


      await renameConversation(
        conversationId,
        title
      );


      updateConversationState(
        conversationId,
        {
          title,
        }
      );

    } catch (error) {

      console.error(
        "Failed to rename conversation:",
        error
      );

      setError(
        getErrorMessage(error) ||
        "Failed to rename conversation."
      );
    }
  };

  const handleProjectUpload = async (
    event
  ) => {

    const file =
      event.target.files?.[0];

    if (!file) return;

    try {

      setUploading(true);
      setError(null);

      const project =
        await uploadProject(file);

      const newId = project.id || project.project_id;

      if (newId) {
        setProjectId(newId);
      }

      setUploadedFile({
        filename: file.name,
        name: file.name,
        extension: ".zip",
        size: file.size,
        content: `📦 Project ZIP archive containing ${project.file_count || 0} files.\nReady for codebase context and analysis.`,
        project_id: newId,
        file_count: project.file_count,
      });

      await reloadProjects();

    } catch (error) {

      console.error(
        "Project upload failed:",
        error
      );

      setError(
        error.message ||
        "Project upload failed."
      );

    } finally {

      setUploading(false);

      if (event.target) {
        event.target.value = "";
      }
    }
  };
  /* =================================================
     RETRY
  ================================================= */

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


  /* =================================================
     RENDER
  ================================================= */

  return (

    <div className="flex h-screen overflow-hidden bg-gray-950 text-white">

      {/* =================================================
          SIDEBAR
      ================================================= */}

      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
        projects={projects}
        activeProjectId={projectId}
        onSelectProject={handleSelectProject}
        onDeleteProject={handleDeleteProject}
      />


      {/* =================================================
          MAIN AREA
      ================================================= */}

      <div className="flex min-w-0 flex-1 flex-col">


        {/* =================================================
            NAVBAR
        ================================================= */}

        <Navbar user={user} onLogout={onLogout} />


        {/* =================================================
            CHAT WINDOW
        ================================================= */}

        <ChatWindow

          messages={
            messages
          }

          loading={
            loading ||
            loadingConversations
          }

          onSuggestion={
            handleSuggestion
          }

        />


        {/* =================================================
            ERROR
        ================================================= */}

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


        {/* =================================================
            UPLOADED FILE PREVIEW
        ================================================= */}

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


        {/* =================================================
            TOOLBAR
        ================================================= */}

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

                {
                  uploading
                    ? "Uploading..."
                    : "Project"
                }

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
                handleProjectUpload
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


        {/* =================================================
            INPUT BOX
        ================================================= */}

        <InputBox

          value={
            input
          }

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
            loading ||
            loadingConversations
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

