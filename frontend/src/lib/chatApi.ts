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
 *
 * NEW: We now have a streaming version (sendChatMessageStreaming) that
 * receives live updates from the backend as the AI works. Think of the
 * old version like sending a letter and waiting for a reply, and the new
 * version like being on a phone call where you hear everything in real-time.
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
 * What we get BACK from the backend after the AI replies (non-streaming).
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
// Streaming event types — the different kinds of updates we receive
// ---------------------------------------------------------------------------
// These match exactly what the Python backend sends.
// Think of them like different colored flags on a conveyor belt:
// - Blue flag = conversation ID
// - Yellow flag = tool is being called
// - Green flag = tool returned results
// - White flag = text content from the AI
// - Checkered flag = done!
// - Red flag = error

/**
 * The backend tells us which conversation this is.
 * Sent first, before anything else happens.
 */
export interface ConversationIdEvent {
  type: "conversation_id";
  conversation_id: string;
}

/**
 * The AI decided to call a tool (like "query_listings").
 * This is sent BEFORE the tool runs, so the user knows
 * the AI is looking something up.
 */
export interface ToolCallEvent {
  type: "tool_call";
  name: string; // The tool's name (e.g. "query_listings")
  input: Record<string, unknown>; // The arguments passed to the tool
}

/**
 * A tool finished and returned its results.
 * This is sent AFTER the tool runs, so the user can see
 * what data came back.
 */
export interface ToolResultEvent {
  type: "tool_result";
  name: string; // The tool's name (same as the tool_call)
  output: string | Record<string, unknown>; // The results — could be a string or an object
}

/**
 * A chunk of the AI's text response.
 * These arrive one at a time, like words appearing on a typewriter.
 * We'll combine them all to form the complete reply.
 */
export interface TextEvent {
  type: "text";
  content: string; // A small piece of the AI's reply
}

/**
 * The stream is complete — everything is done.
 */
export interface DoneEvent {
  type: "done";
}

/**
 * Something went wrong during streaming.
 */
export interface ErrorEvent {
  type: "error";
  message: string;
}

/**
 * A union type that represents ANY of the possible events.
 * "Union type" means "could be any one of these types."
 * It's like saying "this package could contain a book, a toy, or a letter."
 */
export type StreamEvent =
  | ConversationIdEvent
  | ToolCallEvent
  | ToolResultEvent
  | TextEvent
  | DoneEvent
  | ErrorEvent;

// ---------------------------------------------------------------------------
// Callback type — what the caller provides to handle each event
// ---------------------------------------------------------------------------

/**
 * A function that gets called every time a new event arrives from the stream.
 *
 * Think of this like a mail carrier who rings your doorbell each time
 * a new package arrives. You tell them: "When a package comes, do THIS."
 * That's what a callback is — instructions for what to do when something happens.
 */
export type OnStreamEvent = (event: StreamEvent) => void;

// ---------------------------------------------------------------------------
// The main streaming function
// ---------------------------------------------------------------------------

/**
 * Send a chat message and receive streaming updates as the AI works.
 *
 * Unlike sendChatMessage (which waits for the full reply), this function
 * calls your onEvent callback every time something happens:
 * - "I'm calling a tool..." → onEvent({ type: "tool_call", ... })
 * - "The tool returned..." → onEvent({ type: "tool_result", ... })
 * - "Here's part of my answer..." → onEvent({ type: "text", ... })
 * - "All done!" → onEvent({ type: "done" })
 *
 * @param message - What the user typed
 * @param onEvent - Your callback function that handles each event
 * @param conversationId - (Optional) ID to continue an existing conversation
 * @throws Error if the initial connection fails
 *
 * Example usage:
 *   await sendChatMessageStreaming(
 *     "What homes are in Texas?",
 *     (event) => {
 *       if (event.type === "text") console.log(event.content);
 *       if (event.type === "tool_call") console.log("Calling:", event.name);
 *     }
 *   );
 */
export async function sendChatMessageStreaming(
  message: string,
  onEvent: OnStreamEvent,
  conversationId?: string,
): Promise<void> {
  // Build the request body (same shape as before)
  const requestBody: ChatRequestBody = {
    message,
    ...(conversationId && { conversation_id: conversationId }),
  };

  // Make the API call to our Next.js proxy
  // The proxy forwards this to the Python backend's /stream endpoint
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  // If the response is not OK, throw an error
  // (This catches things like 404 "conversation not found" or 502 "backend down")
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      error: "Something went wrong",
    }));
    throw new Error(errorData.error || errorData.detail || "Request failed");
  }

  // Make sure we got a response body (the stream of data)
  if (!response.body) {
    throw new Error("No response body received");
  }

  // --- Read the stream line by line ---
  // response.body is a ReadableStream — think of it as a garden hose.
  // We need a "reader" to catch the water (data) as it flows out.
  const reader = response.body.getReader();

  // TextDecoder converts raw bytes into text strings
  // (computers send data as numbers, we need to turn them into letters)
  const decoder = new TextDecoder();

  // Buffer to hold partial lines
  // Sometimes a line arrives in two pieces (the hose sputters).
  // We collect the pieces here until we have a complete line.
  let buffer = "";

  try {
    // Keep reading until the stream is done
    while (true) {
      // Read the next chunk of data from the stream
      // "done" = true when there's nothing left to read
      // "value" = the raw bytes of this chunk
      const { done, value } = await reader.read();

      // If the stream is finished, stop the loop
      if (done) break;

      // Convert the raw bytes to text and add to our buffer
      buffer += decoder.decode(value, { stream: true });

      // Split the buffer by double-newline (SSE events are separated by \n\n)
      // Each complete event looks like: "data: {...}\n\n"
      const parts = buffer.split("\n\n");

      // The LAST part might be incomplete (waiting for more data),
      // so we keep it in the buffer. All other parts are complete events.
      buffer = parts.pop() || "";

      // Process each complete event
      for (const part of parts) {
        // Each SSE line starts with "data: " — we need to remove that prefix
        const line = part.trim();

        // Skip empty lines (sometimes there are extra blank lines)
        if (!line) continue;

        // Remove the "data: " prefix to get the JSON string
        if (line.startsWith("data: ")) {
          const jsonString = line.slice(6); // "data: " is 6 characters

          try {
            // Parse the JSON string into a JavaScript object
            const event: StreamEvent = JSON.parse(jsonString);

            // Call the user's callback with this event!
            // This is where the magic happens — the UI updates in real-time
            onEvent(event);
          } catch {
            // If we can't parse the JSON, log it and skip
            // (This shouldn't happen, but better safe than sorry)
            console.warn("Could not parse SSE event:", jsonString);
          }
        }
      }
    }
  } finally {
    // Always release the reader when we're done
    // This is like turning off the garden hose — clean up after yourself!
    reader.releaseLock();
  }
}

// ---------------------------------------------------------------------------
// Keep the old non-streaming function for backwards compatibility
// ---------------------------------------------------------------------------

/**
 * Send a chat message to the AI and get a reply (non-streaming version).
 *
 * This is the original function — it waits for the complete reply
 * before returning. Use sendChatMessageStreaming for real-time updates.
 *
 * @param message - What the user typed
 * @param conversationId - (Optional) ID to continue an existing conversation
 * @returns The AI's reply and the conversation ID
 * @throws Error if the request fails
 */
export async function sendChatMessage(
  message: string,
  conversationId?: string,
): Promise<ChatResponseBody> {
  const requestBody: ChatRequestBody = {
    message,
    ...(conversationId && { conversation_id: conversationId }),
  };

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMessage =
      data.error || data.detail || "Something went wrong. Please try again.";
    throw new Error(errorMessage);
  }

  return data as ChatResponseBody;
}
