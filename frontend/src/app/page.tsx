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
 *     └── ChatWindow (the message list)
 *     └── ChatInput (the text box + send button)
 *
 * Think of this page as the conductor of an orchestra — it doesn't play
 * any instrument itself, but it tells each section when to play and
 * makes sure they all work together harmoniously.
 */

"use client"; // This page runs in the browser (it uses state and event handlers)

import { useState, useCallback } from "react";
import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import ChatLayout from "@/components/ChatLayout";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import { sendChatMessage } from "@/lib/chatApi";
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

  // ---- Handler: Send a message ----
  // useCallback prevents this function from being re-created on every render.
  // Think of it like writing the instructions once and reusing the same sheet.
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

      // Step 2: Show the loading indicator
      setIsLoading(true);
      setErrorMessage(null); // Clear any previous error

      try {
        // Step 3: Send the message to the backend via our API helper
        // This goes: chatApi.ts → /api/chat proxy → Python backend → AI
        const response = await sendChatMessage(userMessage, conversationId ?? undefined);

        // Step 4: Save the conversation ID (so future messages continue this chat)
        setConversationId(response.conversation_id);

        // Step 5: Add the AI's reply to the messages list
        const aiReply: Message = {
          role: "assistant",
          content: response.reply,
        };
        setMessages((previousMessages) => [...previousMessages, aiReply]);
      } catch (error) {
        // Something went wrong — show an error message
        // "instanceof Error" checks if the error is a proper Error object
        const message =
          error instanceof Error
            ? error.message
            : "An unexpected error occurred. Please try again.";

        setErrorMessage(message);
      } finally {
        // Step 6: Hide the loading indicator (whether success or failure)
        // "finally" runs no matter what — like cleaning up after cooking,
        // whether the meal turned out good or bad.
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
