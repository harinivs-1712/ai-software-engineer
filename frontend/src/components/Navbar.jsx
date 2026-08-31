function Navbar() {

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-800 bg-gray-950/95 px-4 backdrop-blur">

      <div className="flex items-center gap-3">

        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white">
          AI
        </div>


        <div>

          <h1 className="text-sm font-semibold text-white">
            AI Software Engineer
          </h1>

          <p className="hidden text-[11px] text-gray-500 sm:block">
            Your intelligent coding assistant
          </p>

        </div>

      </div>


      <div className="flex items-center gap-2">

        <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-3 py-1.5">

          <span className="h-2 w-2 rounded-full bg-green-500" />

          <span className="text-xs text-gray-400">
            Online
          </span>

        </div>

      </div>

    </header>
  );
}


export default Navbar;