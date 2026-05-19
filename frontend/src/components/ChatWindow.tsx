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
 * - NEW: Shows tool call and tool result events in real-time!
 *
 * We now support THREE types of messages:
 * 1. "user" — what the human typed (rendered by ChatMessage)
 * 2. "assistant" — what the AI replied (rendered by ChatMessage)
 * 3. "tool" — when the AI calls a tool or gets results (rendered by ToolEvent)
 *
 * This component acts like a traffic cop — it looks at each message's
 * role and decides which component should display it.
 */

"use client";

import { useEffect, useRef } from "react";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import HomeIcon from "@mui/icons-material/Home";
import ChatMessage from "./ChatMessage";
import ToolEvent from "./ToolEvent";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * A single message in the conversation.
 *
 * BEFORE streaming, we only had "user" and "assistant" messages.
 * NOW we also have "tool" messages that show when the AI is calling
 * a tool or when a tool returns results.
 *
 * Think of it like a group chat:
 * - "user" = you talking
 * - "assistant" = the AI talking
 * - "tool" = a helper in the background reporting what they're doing
 */
export interface Message {
  // Who sent this message?
  role: "user" | "assistant" | "tool";
  // The text content of the message
  content: string;
  // Extra info for tool messages (only present when role === "tool")
  toolName?: string; // Which tool was called (e.g. "query_listings")
  toolType?: "call" | "result"; // Is this a call or a result?
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

      {/* Render each message using the RIGHT component for its type */}
      {/* This is like a sorting machine: tool messages go to ToolEvent, */}
      {/* everything else goes to ChatMessage */}
      {messages.map((message, index) => {
        // If it's a tool message, use the ToolEvent component
        if (message.role === "tool") {
          return (
            <ToolEvent
              key={index}
              toolName={message.toolName || "unknown"}
              toolType={message.toolType || "call"}
              content={message.content}
            />
          );
        }

        // Otherwise (user or assistant), use the regular ChatMessage
        return (
          <ChatMessage
            key={index}
            role={message.role}
            content={message.content}
          />
        );
      })}

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
