export function getErrorMessage(error) {

  if (!error) {
    return "Something went wrong.";
  }


  if (error.name === "AbortError") {
    return "The request was cancelled.";
  }


  if (
    error.message?.includes("Failed to fetch")
  ) {
    return "Unable to connect to the AI server. Please make sure the backend is running.";
  }


  return (
    error.message ||
    "Something went wrong while generating the response."
  );
}