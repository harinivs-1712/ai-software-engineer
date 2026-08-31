const STORAGE_KEY =
  "ai-software-engineer-conversations";


export function loadConversations() {

  try {

    const stored =
      localStorage.getItem(STORAGE_KEY);


    if (!stored) {
      return [];
    }


    const conversations =
      JSON.parse(stored);


    if (!Array.isArray(conversations)) {
      return [];
    }


    return conversations;

  } catch (error) {

    console.error(
      "Failed to load conversations:",
      error
    );

    return [];
  }
}


export function saveConversations(
  conversations
) {

  try {

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(conversations)
    );

  } catch (error) {

    console.error(
      "Failed to save conversations:",
      error
    );

  }
}


export function clearStoredConversations() {

  try {

    localStorage.removeItem(
      STORAGE_KEY
    );

  } catch (error) {

    console.error(
      "Failed to clear conversations:",
      error
    );

  }
}

const updateConversation = (
  conversationId,
  updates
) => {

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

            ...updates,

            updatedAt:
              new Date().toISOString(),
          };

        }
      )
  );

};

