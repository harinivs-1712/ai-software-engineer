function FilePreview({
  file,
  onRemove,
}) {

  if (!file) {
    return null;
  }


  return (
    <div className="mt-3 rounded-xl border border-gray-800 bg-gray-950 p-3">

      <div className="flex items-center justify-between">

        <div className="flex min-w-0 items-center gap-3">

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-800">
            📄
          </div>


          <div className="min-w-0">

            <p className="truncate text-sm font-medium text-gray-200">
              {file.filename}
            </p>


            <p className="text-xs text-gray-500">
              {file.extension} ·{" "}
              {file.size} bytes
            </p>

          </div>

        </div>


        <button
          type="button"
          onClick={onRemove}
          className="rounded-md px-2 py-1 text-sm text-gray-500 hover:bg-gray-800 hover:text-white"
        >
          ×
        </button>

      </div>


      <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-black p-3 text-xs text-gray-300">
        {file.content}
      </pre>

    </div>
  );
}


export default FilePreview;