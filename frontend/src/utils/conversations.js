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