/**
 * ToolEvent Component — Shows tool calls and results in the chat
 *
 * When the AI decides to look something up (like querying real estate
 * listings), we show a small notification-style card in the chat.
 * This lets the user see what's happening behind the scenes.
 *
 * There are TWO kinds of tool events:
 * 1. "call" — The AI is STARTING to use a tool (wrench icon, orange)
 * 2. "result" — The tool FINISHED and returned data (checkmark, green)
 *
 * These look different from regular chat messages on purpose — they're
 * compact status updates, like sticky notes between the speech bubbles.
 * Think of them like a waiter telling you "I'm going to check the kitchen"
 * and then coming back with "Here's what the chef said."
 */

"use client";

import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Avatar from "@mui/material/Avatar";
import BuildIcon from "@mui/icons-material/Build";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

// ---------------------------------------------------------------------------
// Props — the "inputs" this component accepts
// ---------------------------------------------------------------------------

interface ToolEventProps {
  /** The name of the tool being called (e.g. "query_listings") */
  toolName: string;
  /** Is this a "call" (starting) or "result" (finished)? */
  toolType: "call" | "result";
  /** The content to display — tool arguments for calls, output for results */
  content: string;
}

// ---------------------------------------------------------------------------
// The Component
// ---------------------------------------------------------------------------

export default function ToolEvent({ toolName, toolType, content }: ToolEventProps) {
  // Is this a tool call (starting) or a result (finished)?
  const isCall = toolType === "call";

  // Safety: make sure content is a string before rendering.
  // Sometimes the backend sends objects (like {type, text, id}).
  // React can't display objects directly — it crashes with
  // "Objects are not valid as a React child." So we convert
  // any non-string content to a readable JSON string.
  const displayContent =
    typeof content === "string"
      ? content
      : JSON.stringify(content, null, 2);

  return (
    <div className="flex items-start gap-3 flex-row">
      {/* Avatar — small circle with an icon */}
      <Avatar
        sx={{
          bgcolor: isCall ? "#ed6c02" : "#2e7d32",
          width: 32,
          height: 32,
        }}
      >
        {isCall ? (
          <BuildIcon sx={{ fontSize: 16 }} />
        ) : (
          <CheckCircleIcon sx={{ fontSize: 16 }} />
        )}
      </Avatar>

      {/* The tool status card */}
      <Paper
        elevation={0}
        sx={{
          bgcolor: isCall ? "#fff3e0" : "#e8f5e9",
          color: isCall ? "#e65100" : "#1b5e20",
          border: 1,
          borderColor: isCall ? "#ffe0b2" : "#c8e6c9",
        }}
        className="px-3 py-2 max-w-[80%] rounded-xl"
      >
        {/* Tool name as a small bold header */}
        <Typography
          variant="caption"
          component="div"
          sx={{ fontWeight: 600 }}
        >
          {isCall
            ? `🔧 Calling: ${toolName}`
            : `✅ Result from: ${toolName}`}
        </Typography>

        {/* The tool details (arguments or output) */}
        <Typography
          variant="caption"
          component="div"
          className="whitespace-pre-wrap break-words mt-1 opacity-80"
        >
          {displayContent}
        </Typography>
      </Paper>
    </div>
  );
}
