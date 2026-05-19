/**
 * ChatMessage Component — A single message bubble in the chat
 *
 * Think of this like a speech bubble in a comic book. Each message
 * looks different depending on WHO said it:
 * - User messages → appear on the RIGHT side, with a blue background
 * - AI messages   → appear on the LEFT side, with a white background
 *
 * This is a "presentational" component — it just displays data it receives.
 * It doesn't fetch data or manage state. Think of it as a picture frame:
 * you give it a picture (the message), and it displays it nicely.
 *
 * NOTE: Tool messages (role === "tool") are handled by the separate
 * ToolEvent component — ChatMessage only handles "user" and "assistant".
 */

"use client"; // Runs in the browser (needed for MUI components)

import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";
import Avatar from "@mui/material/Avatar";

// ---------------------------------------------------------------------------
// Props — the "inputs" this component accepts
// ---------------------------------------------------------------------------

interface ChatMessageProps {
  role: "user" | "assistant"; // Who sent this message?
  content: string; // What does the message say?
}

// ---------------------------------------------------------------------------
// The Component
// ---------------------------------------------------------------------------

export default function ChatMessage({ role, content }: ChatMessageProps) {
  // Determine if this message is from the user (true) or the AI (false)
  const isUser = role === "user";

  return (
    // Outer container — controls LEFT vs RIGHT alignment
    // "flex" = lay out children in a row
    // "justify-end" = push to the right (for user messages)
    // "justify-start" = push to the left (for AI messages)
    <div
      className={`flex items-start gap-3 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar — the little circle icon showing who sent the message */}
      <Avatar
        sx={{
          // Different colors for user vs AI
          bgcolor: isUser ? "primary.main" : "secondary.main",
          // Make it a bit smaller than default
          width: 36,
          height: 36,
        }}
      >
        {/* Show a person icon for users, robot icon for AI */}
        {isUser ? (
          <PersonIcon fontSize="small" />
        ) : (
          <SmartToyIcon fontSize="small" />
        )}
      </Avatar>

      {/* The message bubble itself */}
      {/* Paper is an MUI component that looks like a card with a shadow */}
      <Paper
        elevation={1} // elevation = shadow depth (1 = subtle shadow)
        sx={{
          // Different background colors
          bgcolor: isUser ? "primary.main" : "background.paper",
          // Text color — white on blue, dark on white
          color: isUser ? "white" : "text.primary",
        }}
        // Tailwind classes for spacing and sizing
        // px-4 = horizontal padding, py-2 = vertical padding
        // max-w-[75%] = bubble never takes more than 75% of the width
        // rounded-2xl = very rounded corners (like a real chat bubble)
        className="px-4 py-2 max-w-[75%] rounded-2xl"
      >
        {/* Typography is MUI's text component — handles font sizing nicely */}
        <Typography
          variant="body1" // "body1" = normal paragraph size
          // whitespace-pre-wrap = preserve line breaks in the message
          // break-words = break long words so they don't overflow
          className="whitespace-pre-wrap break-words"
        >
          {content}
        </Typography>
      </Paper>
    </div>
  );
}
