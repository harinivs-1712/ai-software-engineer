export function getErrorMessage(error) {
  if (!error) {
    return "Something went wrong.";
  }

  if (typeof error === "string") {
    return error;
  }

  if (error.name === "AbortError") {
    return "The request was cancelled.";
  }

  if (error.detail && typeof error.detail === "string") {
    return error.detail;
  }

  if (error.message && typeof error.message === "string") {
    if (error.message.includes("Failed to fetch")) {
      return "Unable to connect to the AI server. Please make sure the backend is running on port 8000.";
    }
    return error.message;
  }

  if (typeof error === "object") {
    try {
      return error.detail || error.message || JSON.stringify(error);
    } catch {
      return "Something went wrong while generating the response.";
    }
  }

  return String(error);
}