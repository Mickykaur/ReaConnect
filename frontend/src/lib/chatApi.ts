/**
 * Chat API Helper — the "phone" our UI uses to talk to the backend
 *
 * Instead of writing fetch() calls everywhere in our components, we put
 * all the API communication logic in ONE place. This is like having a
 * single phone in the house — everyone uses the same phone to call out.
 *
 * Benefits:
 * - If the API URL changes, we only update it here (not in 10 places)
 * - Error handling is consistent
 * - TypeScript types keep us safe from typos
 */

// ---------------------------------------------------------------------------
// Types — the "shape" of data we send and receive
// ---------------------------------------------------------------------------

/**
 * What we send TO the backend when the user sends a message.
 * Think of this as the envelope we put the message in.
 */
export interface ChatRequestBody {
  message: string; // The user's message text
  conversation_id?: string; // Optional: to continue an existing conversation
}

/**
 * What we get BACK from the backend after the AI replies.
 * Think of this as the reply letter we receive.
 */
export interface ChatResponseBody {
  reply: string; // The AI's response text
  conversation_id: string; // The conversation ID (always returned)
}

/**
 * If something goes wrong, the backend sends an error in this shape.
 */
export interface ChatErrorBody {
  error: string; // A human-readable error message
}

// ---------------------------------------------------------------------------
// The main function — sends a message and gets a reply
// ---------------------------------------------------------------------------

/**
 * Send a chat message to the AI and get a reply.
 *
 * @param message - What the user typed
 * @param conversationId - (Optional) ID to continue an existing conversation
 * @returns The AI's reply and the conversation ID
 * @throws Error if the request fails
 *
 * Example usage:
 *   const response = await sendChatMessage("What homes are in Texas?");
 *   console.log(response.reply);           // "Here are the listings..."
 *   console.log(response.conversation_id); // "abc-123-..."
 */
export async function sendChatMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponseBody> {
  // Build the request body (the data we're sending)
  const requestBody: ChatRequestBody = {
    message,
    // Only include conversation_id if we have one
    // (undefined values are automatically excluded from JSON)
    ...(conversationId && { conversation_id: conversationId }),
  };

  // Make the API call to our Next.js proxy (NOT directly to the Python backend)
  // The proxy at /api/chat will forward it to the Python backend for us
  const response = await fetch("/api/chat", {
    method: "POST", // POST = "I'm sending data" (vs GET = "I'm asking for data")
    headers: {
      "Content-Type": "application/json", // Tell the server we're sending JSON
    },
    body: JSON.stringify(requestBody), // Convert our JS object to a JSON string
  });

  // Parse the response JSON
  const data = await response.json();

  // If the response is not OK (status 200-299), throw an error
  if (!response.ok) {
    // Try to get a useful error message from the response
    const errorMessage =
      data.error || data.detail || "Something went wrong. Please try again.";
    throw new Error(errorMessage);
  }

  // Everything went well — return the AI's reply
  return data as ChatResponseBody;
}
