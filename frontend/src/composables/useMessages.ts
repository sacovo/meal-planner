import { coreApiGetMessages } from "@/client";

export function useMessages() {
  async function fetchMessages() {
    return await coreApiGetMessages()
      .then((response) => {
        if (!response.data) {
          return [];
        }
        return response.data;
      })
      .catch((err) => {
        console.error("Failed to load messages:", err);
        return [];
      });
  }

  return { fetchMessages };
}
