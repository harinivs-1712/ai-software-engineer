import { useRef } from "react";


function FileUpload({
  onFileSelected,
  disabled = false,
}) {

  const inputRef =
    useRef(null);


  const handleChange = (
    event
  ) => {

    const file =
      event.target.files?.[0];


    if (!file) {
      return;
    }


    onFileSelected(file);


    event.target.value = "";
  };


  return (
    <>

      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />


      <button
        type="button"
        onClick={() =>
          inputRef.current?.click()
        }
        disabled={disabled}
        className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-300 transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        📎 Upload File
      </button>

    </>
  );
}


export default FileUpload;