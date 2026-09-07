import React from "react";

function Sidebar({
  conversations = [],
  activeConversationId,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
  projects = [],
  activeProjectId,
  onSelectProject,
  onDeleteProject,
}) {
  const handleRename = (conversation) => {
    const newTitle = window.prompt("Rename conversation:", conversation.title);
    if (newTitle && newTitle.trim()) {
      onRenameConversation(conversation.id, newTitle);
    }
  };

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-800 bg-gray-950 md:flex">
      {/* Header */}
      <div className="flex h-14 items-center border-b border-gray-800 px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-600 text-[10px] font-bold text-white shadow-sm shadow-indigo-500/30">
            AI
          </div>
          <span className="text-sm font-semibold text-white">AI Engineer</span>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-sm font-medium text-gray-200 transition hover:bg-gray-800 hover:text-white"
        >
          <span className="text-lg">+</span>
          New Chat
        </button>
      </div>

      {/* Sidebar Content (Scrollable) */}
      <div className="flex-1 overflow-y-auto px-2 space-y-4">
        {/* Uploaded Projects Section */}
        <div>
          <div className="flex items-center justify-between px-2 py-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
              📁 Uploaded Projects ({projects.length})
            </span>
          </div>

          <div className="space-y-1">
            {projects.length === 0 ? (
              <p className="px-2 py-1 text-xs text-gray-500 italic">
                No projects uploaded yet.
              </p>
            ) : (
              projects.map((project) => {
                const isSelected = project.id === activeProjectId;

                return (
                  <div
                    key={project.id}
                    className={`group flex items-center justify-between gap-2 rounded-lg px-3 py-2 transition ${
                      isSelected
                        ? "bg-indigo-950/80 border border-indigo-500/40 text-indigo-200"
                        : "hover:bg-gray-900 text-gray-300"
                    }`}
                  >
                    <button
                      onClick={() => onSelectProject && onSelectProject(project.id)}
                      className="min-w-0 flex-1 truncate text-left text-sm flex items-center gap-2"
                      title={project.name}
                    >
                      <span className="text-base">📦</span>
                      <span className="truncate font-medium">{project.name}</span>
                    </button>

                    <div className="flex items-center gap-1">
                      {project.file_count !== undefined && (
                        <span className="rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-400">
                          {project.file_count} f
                        </span>
                      )}

                      {onDeleteProject && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteProject(project.id);
                          }}
                          className="hidden group-hover:block rounded p-1 text-xs text-gray-500 hover:bg-red-900/50 hover:text-red-300 transition"
                          title="Delete Project"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Conversations Section */}
        <div>
          <p className="px-2 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            💬 Conversations ({conversations.length})
          </p>

          <div className="space-y-1">
            {conversations.map((conversation) => {
              const isActive = conversation.id === activeConversationId;

              return (
                <div
                  key={conversation.id}
                  className={`group flex items-center gap-2 rounded-lg px-3 py-2 transition ${
                    isActive ? "bg-gray-800 text-white" : "hover:bg-gray-900 text-gray-300"
                  }`}
                >
                  <button
                    onClick={() => onSelectConversation(conversation.id)}
                    className="min-w-0 flex-1 truncate text-left text-sm"
                  >
                    {conversation.title}
                  </button>

                  <div className="hidden shrink-0 items-center gap-1 group-hover:flex">
                    <button
                      onClick={() => handleRename(conversation)}
                      className="rounded p-1 text-xs text-gray-500 hover:bg-gray-700 hover:text-white"
                      title="Rename"
                    >
                      ✎
                    </button>

                    <button
                      onClick={() => onDeleteConversation(conversation.id)}
                      className="rounded p-1 text-xs text-gray-500 hover:bg-red-900 hover:text-red-300"
                      title="Delete"
                    >
                      ×
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-800 p-3">
        <p className="text-[11px] text-gray-500">
          Projects & Chats synced to database.
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;