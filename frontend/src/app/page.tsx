/**
 * Main Chat Page — The home page of ReaConnect (/)
 *
 * This is the "brain" of the frontend. It manages:
 * - The list of messages (state)
 * - The conversation ID (so the backend remembers context)
 * - Loading state (is the AI thinking?)
 * - Error state (did something go wrong?)
 *
 * It connects all our components together:
 *   ChatLayout (the frame)
 *     └── ChatWindow (the message list — including tool events!)
 *     └── ChatInput (the text box + send button)
 *
 * NEW: This page now uses STREAMING to show live updates from the AI.
 * Instead of waiting for the full response, the user sees:
 * 1. 🔧 "Calling query_listings..." (tool call event)
 * 2. ✅ "Result from query_listings..." (tool result event)
 * 3. 💬 "Here are the homes..." (AI text, appearing word by word)
 *
 * Think of the old version like ordering food and waiting silently.
 * The new version is like the waiter telling you: "I sent your order
 * to the kitchen... The chef is making it... Here it comes!"
 */

"use client"; // This page runs in the browser (it uses state and event handlers)

import { useState, useCallback } from "react";
import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import ChatLayout from "@/components/ChatLayout";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import { sendChatMessageStreaming } from "@/lib/chatApi";
import type { StreamEvent } from "@/lib/chatApi";
import type { Message } from "@/components/ChatWindow";

// ---------------------------------------------------------------------------
// The Page Component
// ---------------------------------------------------------------------------

export default function ChatPage() {
  // ---- State variables ----
  // These are like sticky notes the page keeps track of.

  // All the messages in the current conversation
  const [messages, setMessages] = useState<Message[]>([]);

  // The conversation ID from the backend (null = no conversation yet)
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Whether we're waiting for the AI to respond
  const [isLoading, setIsLoading] = useState(false);

  // Error message to show (null = no error)
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // ---- Handler: Send a message (STREAMING version) ----
  // This is the main function that handles user messages. It now uses
  // streaming, which means we get updates from the backend in real-time
  // instead of waiting for everything to finish.
  const handleSendMessage = useCallback(
    async (userMessage: string) => {
      // Step 1: Immediately show the user's message in the chat
      // We add it to the messages list BEFORE waiting for the AI
      // so it feels instant (good user experience!)
      const newUserMessage: Message = {
        role: "user",
        content: userMessage,
      };

      setMessages((previousMessages) => [...previousMessages, newUserMessage]);

      // Step 2: Show the loading indicator and clear any previous error
      setIsLoading(true);
      setErrorMessage(null);

      try {
        // Step 3: Send the message using our streaming function
        // The onEvent callback below is called every time a new
        // event arrives from the backend. Think of it as:
        // "Every time the backend has something to say, do THIS."
        await sendChatMessageStreaming(
          userMessage,
          // --- The event handler (callback) ---
          // This function is called for EACH event from the stream.
          // Different event types trigger different UI updates.
          (event: StreamEvent) => {
            switch (event.type) {
              // --- The backend tells us the conversation ID ---
              // We save this so future messages continue the same conversation
              case "conversation_id":
                setConversationId(event.conversation_id);
                break;

              // --- The AI is calling a tool ---
              // Add a tool message to show the user what's happening
              case "tool_call": {
                // Format the tool input as readable text
                // JSON.stringify with spacing makes it look nice
                const inputText = JSON.stringify(event.input, null, 2);

                const toolMessage: Message = {
                  role: "tool",
                  content: inputText,
                  toolName: event.name,
                  toolType: "call",
                };

                setMessages((prev) => [...prev, toolMessage]);
                break;
              }

              // --- A tool returned its results ---
              // Add another tool message showing the results
              case "tool_result": {
                // Safety: event.output might be an object or a string.
                // We need a string for React to display. If it's already
                // a string, use it as-is. If it's an object, convert it
                // to a nicely formatted JSON string.
                const outputText =
                  typeof event.output === "string"
                    ? event.output
                    : JSON.stringify(event.output, null, 2);

                const resultMessage: Message = {
                  role: "tool",
                  content: outputText,
                  toolName: event.name,
                  toolType: "result",
                };

                setMessages((prev) => [...prev, resultMessage]);
                break;
              }

              // --- A chunk of the AI's text response ---
              // This is where we build up the assistant's reply
              // piece by piece, like a typewriter effect.
              case "text": {
                setMessages((prev) => {
                  // Look at the last message in our list
                  const lastMessage = prev[prev.length - 1];

                  // If the last message is already an assistant message,
                  // we APPEND this text chunk to it (building it up)
                  if (lastMessage && lastMessage.role === "assistant") {
                    // Create a new array with all messages except the last one,
                    // then add the updated last message with the new text appended
                    const updatedMessages = [...prev];
                    updatedMessages[updatedMessages.length - 1] = {
                      ...lastMessage,
                      content: lastMessage.content + event.content,
                    };
                    return updatedMessages;
                  }

                  // If the last message is NOT an assistant message,
                  // this is the FIRST text chunk — create a new assistant message
                  return [
                    ...prev,
                    { role: "assistant" as const, content: event.content },
                  ];
                });
                break;
              }

              // --- The stream is complete ---
              // Stop the loading indicator
              case "done":
                setIsLoading(false);
                break;

              // --- Something went wrong ---
              // Show the error message
              case "error":
                setErrorMessage(event.message);
                setIsLoading(false);
                break;
            }
          },
          // Pass the conversation ID if we have one
          conversationId ?? undefined,
        );
      } catch (error) {
        // Something went wrong with the connection itself
        // (not an error from the stream, but a network error)
        const message =
          error instanceof Error
            ? error.message
            : "An unexpected error occurred. Please try again.";

        setErrorMessage(message);
        setIsLoading(false);
      }
    },
    [conversationId] // Re-create this function when conversationId changes
  );

  // ---- Handler: Start a new conversation ----
  const handleNewChat = useCallback(() => {
    // Reset everything back to the initial state
    setMessages([]); // Clear all messages
    setConversationId(null); // Forget the conversation ID
    setErrorMessage(null); // Clear any error
    setIsLoading(false); // Stop any loading
  }, []);

  // ---- Handler: Close the error snackbar ----
  const handleCloseError = useCallback(() => {
    setErrorMessage(null);
  }, []);

  // ---- Render the UI ----
  return (
    // ChatLayout provides the header and overall page structure
    <ChatLayout onNewChat={handleNewChat}>
      {/* ChatWindow shows all messages and the loading indicator */}
      <ChatWindow messages={messages} isLoading={isLoading} />

      {/* ChatInput is the text box at the bottom */}
      <ChatInput onSend={handleSendMessage} isLoading={isLoading} />

      {/* Snackbar shows error messages as a temporary popup at the bottom */}
      {/* It appears when errorMessage is not null, and disappears after 6 seconds */}
      <Snackbar
        open={errorMessage !== null} // Show when there's an error
        autoHideDuration={6000} // Disappear after 6 seconds
        onClose={handleCloseError} // Called when user dismisses it
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {/* Alert is a colored box — "error" makes it red */}
        <Alert
          onClose={handleCloseError}
          severity="error"
          variant="filled"
          className="w-full"
        >
          {errorMessage}
        </Alert>
      </Snackbar>
    </ChatLayout>
  );
}
