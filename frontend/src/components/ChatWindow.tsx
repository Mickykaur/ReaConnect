/**
 * ChatWindow Component — The scrollable area showing all messages
 *
 * Think of this like the main screen of a messaging app — it shows all
 * the messages in order, from oldest at the top to newest at the bottom.
 *
 * Key features:
 * - Automatically scrolls to the bottom when new messages arrive
 * - Shows a welcome message when the conversation is empty
 * - Displays a "thinking" indicator when the AI is processing
 */

"use client";

import { useEffect, useRef } from "react";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import HomeIcon from "@mui/icons-material/Home";
import ChatMessage from "./ChatMessage";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A single message in the conversation */
export interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatWindowProps {
  /** The list of all messages in the conversation */
  messages: Message[];
  /** Whether the AI is currently thinking (show a loading indicator) */
  isLoading: boolean;
}

// ---------------------------------------------------------------------------
// The Component
// ---------------------------------------------------------------------------

export default function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  // "ref" is like putting a sticky note on an HTML element so we can
  // find it later. We use this to scroll to the bottom of the messages.
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // "useEffect" runs code AFTER the component renders.
  // Here, we scroll to the bottom whenever messages change or loading starts.
  // Think of it like an automatic "scroll down" button in a chat app.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]); // Re-run whenever messages or isLoading changes

  return (
    // The scrollable container
    // "flex-1" = take up all available space between header and input
    // "overflow-y-auto" = add a scrollbar when messages overflow
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* If there are no messages, show a welcome screen */}
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-center gap-4">
          {/* Big house icon */}
          <HomeIcon
            sx={{ fontSize: 64, color: "primary.main", opacity: 0.6 }}
          />
          {/* Welcome heading */}
          <Typography variant="h5" color="text.secondary">
            Welcome to ReaConnect! 🏠
          </Typography>
          {/* Instruction text */}
          <Typography
            variant="body1"
            color="text.secondary"
            className="max-w-md"
          >
            Ask me anything about real estate listings — prices, locations,
            availability, and more. I have access to real listing data!
          </Typography>
          {/* Example prompts to help the user get started */}
          <div className="flex flex-wrap justify-center gap-2 mt-2">
            {[
              "What homes are under $400k in Texas?",
              "Show me 3-bedroom houses",
              "What's the average listing price?",
            ].map((suggestion) => (
              <Typography
                key={suggestion}
                variant="body2"
                className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 cursor-default"
              >
                &ldquo;{suggestion}&rdquo;
              </Typography>
            ))}
          </div>
        </div>
      )}

      {/* Render each message as a ChatMessage bubble */}
      {messages.map((message, index) => (
        <ChatMessage
          // "key" helps React track which items changed — using index here
          // because messages don't have unique IDs
          key={index}
          role={message.role}
          content={message.content}
        />
      ))}

      {/* Loading indicator — shows when the AI is "thinking" */}
      {isLoading && (
        <div className="flex items-center gap-3 px-2">
          <CircularProgress size={20} />
          <Typography variant="body2" color="text.secondary">
            Thinking...
          </Typography>
        </div>
      )}

      {/* Invisible element at the bottom — we scroll to this */}
      {/* It's like a bookmark at the very end of the page */}
      <div ref={messagesEndRef} />
    </div>
  );
}
