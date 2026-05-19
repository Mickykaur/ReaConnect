/**
 * ChatInput Component — The text box and send button at the bottom
 *
 * Think of this like the compose area in any messaging app (iMessage,
 * WhatsApp, etc.). The user types their message here and hits Send.
 *
 * This component:
 * - Shows a text field where the user types
 * - Shows a Send button (disabled when empty or loading)
 * - Calls a function (onSend) when the user submits
 * - Supports pressing Enter to send (Shift+Enter for new line)
 */

"use client";

import { useState } from "react";
import TextField from "@mui/material/TextField";
import IconButton from "@mui/material/IconButton";
import SendIcon from "@mui/icons-material/Send";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";

// ---------------------------------------------------------------------------
// Props — what the parent component passes to us
// ---------------------------------------------------------------------------

interface ChatInputProps {
  /** Function to call when the user sends a message */
  onSend: (message: string) => void;
  /** Whether we're waiting for the AI to reply (disables the input) */
  isLoading: boolean;
}

// ---------------------------------------------------------------------------
// The Component
// ---------------------------------------------------------------------------

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  // "state" is like a sticky note the component keeps for itself.
  // inputValue holds whatever text the user has typed so far.
  // setInputValue is how we update that sticky note.
  const [inputValue, setInputValue] = useState("");

  /**
   * Handle the form submission (when the user clicks Send or presses Enter).
   *
   * We prevent the default form behavior (which would reload the page),
   * check that the message isn't empty, call onSend, then clear the input.
   */
  const handleSubmit = (event: React.FormEvent) => {
    // preventDefault stops the browser from reloading the page
    event.preventDefault();

    // .trim() removes whitespace from both ends of the string
    // If the message is empty or we're loading, do nothing
    const trimmedMessage = inputValue.trim();
    if (!trimmedMessage || isLoading) return;

    // Call the parent's onSend function with the message
    onSend(trimmedMessage);

    // Clear the text field so the user can type a new message
    setInputValue("");
  };

  /**
   * Handle keyboard shortcuts.
   * - Enter (without Shift) = send the message
   * - Shift+Enter = add a new line (default behavior, we don't interfere)
   */
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      // Prevent the default "add new line" behavior
      event.preventDefault();
      // Trigger form submission
      handleSubmit(event);
    }
  };

  return (
    // Paper gives us a nice card-like container with a shadow
    <Paper
      elevation={3}
      className="p-3"
    >
      {/* form wraps the input + button so Enter key triggers submission */}
      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-2"
      >
        {/* The text input field */}
        <TextField
          // "multiline" allows the text field to grow for long messages
          multiline
          maxRows={4} // Don't let it grow taller than 4 lines
          fullWidth // Take up all available horizontal space
          placeholder={
            isLoading
              ? "Waiting for reply..." // Show this when AI is thinking
              : "Ask about real estate listings..." // Default placeholder
          }
          value={inputValue} // Controlled input — React manages the value
          onChange={(event) => setInputValue(event.target.value)} // Update state on every keystroke
          onKeyDown={handleKeyDown} // Listen for Enter key
          disabled={isLoading} // Gray out the field while loading
          variant="outlined" // Show a border around the field
          size="small" // Slightly smaller than default
          // sx lets us customize MUI styles directly
          sx={{
            // Make the text field corners rounded to match our design
            "& .MuiOutlinedInput-root": {
              borderRadius: "1rem", // 1rem ≈ 16px, nicely rounded
            },
          }}
        />

        {/* The Send button */}
        <IconButton
          type="submit" // Clicking this button submits the form
          color="primary" // Uses our theme's primary color (blue)
          // Disabled when: no text typed, or waiting for AI reply
          disabled={!inputValue.trim() || isLoading}
          // Tailwind: slightly larger button with transitions
          className="transition-transform hover:scale-110"
          aria-label="Send message" // Accessibility label for screen readers
        >
          {/* Show a spinner while loading, Send arrow when ready */}
          {isLoading ? (
            <CircularProgress size={24} /> // Spinning loading indicator
          ) : (
            <SendIcon /> // Arrow icon
          )}
        </IconButton>
      </form>
    </Paper>
  );
}
