import React from "react";

function Navbar({ user, onLogout }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-800 bg-gray-950/95 px-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white shadow-md shadow-indigo-500/20">
          AI
        </div>

        <div>
          <h1 className="text-sm font-semibold text-white">
            AI Software Engineer
          </h1>
          <p className="hidden text-[11px] text-gray-400 sm:block">
            Your intelligent coding assistant
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900/90 px-3 py-1 text-xs text-gray-300">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="font-medium">{user.email}</span>
          </div>
        )}

        <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-3 py-1.5 hidden md:flex">
          <span className="h-2 w-2 rounded-full bg-green-500" />
          <span className="text-xs text-gray-400">Online</span>
        </div>

        {onLogout && (
          <button
            onClick={onLogout}
            title="Sign out"
            className="flex items-center gap-1.5 rounded-lg border border-gray-800 bg-gray-900 px-3 py-1.5 text-xs font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
            <span>Logout</span>
          </button>
        )}
      </div>
    </header>
  );
}

export default Navbar;