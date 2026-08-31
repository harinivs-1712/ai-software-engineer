export function createConversation() {
  const now = new Date().toISOString();

  return {
    id: crypto.randomUUID(),

    title: "New Conversation",

    messages: [],

    createdAt: now,

    updatedAt: now,
  };
}

export function initializeConversations() {

  const stored =
    localStorage.getItem(
      "ai-software-engineer-conversations"
    );


  if (stored) {

    try {

      const conversations =
        JSON.parse(stored);


      if (
        Array.isArray(conversations) &&
        conversations.length > 0
      ) {
        return conversations;
      }

    } catch {
      // Ignore invalid stored data.
    }
  }


  return [
    createConversation()
  ];
}