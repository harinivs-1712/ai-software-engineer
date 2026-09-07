
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";


/* =================================================
   AUTH HEADERS
================================================= */

const getAuthHeaders = () => {

  const token =
    localStorage.getItem(
      "access_token"
    );

  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};
};


/* =================================================
   STREAM MESSAGE
================================================= */

export async function streamMessage(
  conversationId,
  message,
  mode,
  projectId,
  onChunk,
  signal
) {

  const response =
    await fetch(
      `${API_BASE_URL}/chat/stream`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },

        body: JSON.stringify({
          conversation_id:
            conversationId,

          message,

          mode:
            mode || "generate",

          project_id:
            projectId !== null && projectId !== undefined
              ? String(projectId)
              : null,
        }),

        signal,
      }
    );


  if (!response.ok) {
    let errorMessage = "The AI server returned an error.";

    try {
      const errorData = await response.json();
      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      } else if (typeof errorData.detail === "object" && errorData.detail !== null) {
        errorMessage = JSON.stringify(errorData.detail);
      } else if (errorData.message) {
        errorMessage = String(errorData.message);
      }
    } catch {
      // Response wasn't JSON.
    }

    throw new Error(errorMessage);
  }


  if (!response.body) {

    throw new Error(
      "The server did not provide a response stream."
    );

  }


  const reader =
    response.body.getReader();


  const decoder =
    new TextDecoder();


  let finished = false;


  while (!finished) {

    const {
      value,
      done,
    } =
      await reader.read();


    finished = done;


    if (value) {

      const chunk =
        decoder.decode(
          value,
          {
            stream: !done,
          }
        );


      if (chunk) {

        onChunk(chunk);

      }

    }

  }

}


/* =================================================
   FILE UPLOAD
================================================= */

export async function uploadFile(
  file
) {

  const formData =
    new FormData();


  formData.append(
    "file",
    file
  );


  const response =
    await fetch(
      `${API_BASE_URL}/upload`,
      {
        method: "POST",

        headers: {
          ...getAuthHeaders(),
        },

        body: formData,
      }
    );


  if (!response.ok) {

    let message =
      "File upload failed.";


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


  return response.json();

}


/* =================================================
   CREATE CONVERSATION
================================================= */

export async function createConversation(
  title = "New Chat"
) {

  const response =
    await fetch(
      `${API_BASE_URL}/conversations`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          ...getAuthHeaders(),
        },

        body: JSON.stringify({
          title,
        }),
      }
    );


  if (!response.ok) {

    let message =
      "Failed to create conversation.";


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


  return response.json();

}


/* =================================================
   GET ALL CONVERSATIONS
================================================= */

export async function getConversations() {

  const response =
    await fetch(
      `${API_BASE_URL}/conversations`,
      {
        method: "GET",

        headers: {
          ...getAuthHeaders(),
        },
      }
    );


  if (!response.ok) {

    let message =
      "Failed to load conversations.";


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


  return response.json();

}


/* =================================================
   GET ONE CONVERSATION
================================================= */

export async function getConversation(
  conversationId
) {

  const response =
    await fetch(
      `${API_BASE_URL}/conversations/${conversationId}`,
      {
        method: "GET",

        headers: {
          ...getAuthHeaders(),
        },
      }
    );


  if (!response.ok) {

    let message =
      "Failed to load conversation.";


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


  return response.json();

}


/* =================================================
   ADD MESSAGE
================================================= */

export async function addMessage(
  conversationId,
  role,
  content,
  mode = null
) {

  const response =
    await fetch(
      `${API_BASE_URL}/conversations/${conversationId}/messages`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          ...getAuthHeaders(),
        },

        body: JSON.stringify({

          role,

          content,

          mode,

        }),
      }
    );


  if (!response.ok) {

    let message =
      "Failed to save message.";


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


  return response.json();

}


/* =================================================
   RENAME CONVERSATION
================================================= */

export async function renameConversation(
  conversationId,
  title
) {

  const response =
    await fetch(
      `${API_BASE_URL}/conversations/${conversationId}`,
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",

          ...getAuthHeaders(),
        },

        body: JSON.stringify({
          title,
        }),
      }
    );


  if (!response.ok) {

    let message =
      "Failed to rename conversation.";


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


  return response.json();

}


/* =================================================
   DELETE CONVERSATION
================================================= */

export async function deleteConversation(
  conversationId
) {

  const response =
    await fetch(
      `${API_BASE_URL}/conversations/${conversationId}`,
      {
        method: "DELETE",

        headers: {
          ...getAuthHeaders(),
        },
      }
    );


  if (!response.ok) {

    let message =
      "Failed to delete conversation.";


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


  return response.json();
}


/* =================================================
   AUTH API SERVICES
================================================= */

export async function loginUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    let message = "Login failed.";
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Ignore
    }
    throw new Error(message);
  }

  return response.json();
}


export async function registerUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    let message = "Registration failed.";
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Ignore
    }
    throw new Error(message);
  }

  return response.json();
}


export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: "GET",
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    let message = "Failed to fetch current user profile.";
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Ignore
    }
    throw new Error(message);
  }

  return response.json();
}


export async function uploadProject(file) {

  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_BASE_URL}/projects/upload`,
    {
      method: "POST",

      headers: {
        ...getAuthHeaders(),
      },

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
        error.detail || message;

    } catch {}

    throw new Error(message);
  }

  return response.json();
}


export async function getProjects() {

  const response = await fetch(
    `${API_BASE_URL}/projects`,
    {
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {

    throw new Error(
      "Failed to load projects."
    );
  }

  return response.json();
}

export async function getProject(
  projectId
) {

  const response = await fetch(
    `${API_BASE_URL}/projects/${projectId}`,
    {
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {

    throw new Error(
      "Failed to load project."
    );
  }

  return response.json();
}

export async function deleteProject(
  projectId
) {

  const response = await fetch(
    `${API_BASE_URL}/projects/${projectId}`,
    {
      method: "DELETE",

      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {

    throw new Error(
      "Failed to delete project."
    );
  }

  return response.json();
}


