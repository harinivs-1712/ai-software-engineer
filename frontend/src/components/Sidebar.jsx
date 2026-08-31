function Sidebar({
  onNewChat,
}) {

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-800 bg-gray-950 md:flex">

      {/* Header */}

      <div className="flex h-14 items-center border-b border-gray-800 px-4">

        <div className="flex items-center gap-2">

          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600 text-[10px] font-bold text-white">
            AI
          </div>

          <span className="text-sm font-semibold">
            AI Engineer
          </span>

        </div>

      </div>


      {/* New Chat */}

      <div className="p-3">

        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-sm font-medium text-gray-200 transition hover:border-gray-600 hover:bg-gray-800"
        >

          <span className="text-lg leading-none">
            +
          </span>

          New Chat

        </button>

      </div>


      {/* Conversations */}

      <div className="flex-1 overflow-y-auto px-3">

        <p className="px-2 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-600">
          Recent
        </p>


        <div className="group flex cursor-pointer items-center gap-3 rounded-lg bg-gray-900 px-3 py-2.5">

          <span className="text-gray-500">
            ◇
          </span>

          <span className="truncate text-sm text-gray-300">
            Current conversation
          </span>

        </div>

      </div>


      {/* Footer */}

      <div className="border-t border-gray-800 p-3">

        <div className="rounded-lg px-3 py-2">

          <p className="text-xs font-medium text-gray-400">
            AI Software Engineer
          </p>

          <p className="mt-1 text-[11px] text-gray-600">
            v1.0
          </p>

        </div>

      </div>

    </aside>
  );
}


export default Sidebar;