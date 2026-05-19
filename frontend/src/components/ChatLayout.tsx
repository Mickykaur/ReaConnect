/**
 * ChatLayout Component — The overall page wrapper with a header
 *
 * Think of this like the frame of a house — it provides the walls,
 * roof, and structure. The actual content (furniture = messages,
 * input box) goes INSIDE it.
 *
 * Structure:
 * ┌─────────────────────────────┐
 * │  Header (ReaConnect logo)   │  ← AppBar (the blue bar at top)
 * ├─────────────────────────────┤
 * │                             │
 * │    {children go here}       │  ← Whatever we put inside ChatLayout
 * │                             │
 * └─────────────────────────────┘
 */

"use client";

import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import HomeIcon from "@mui/icons-material/Home";
import Container from "@mui/material/Container";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ChatLayoutProps {
  /** The content to render inside the layout (the chat window + input) */
  children: React.ReactNode;
  /** Function to call when the user clicks "New Chat" */
  onNewChat: () => void;
}

// ---------------------------------------------------------------------------
// The Component
// ---------------------------------------------------------------------------

export default function ChatLayout({ children, onNewChat }: ChatLayoutProps) {
  return (
    // "flex flex-col h-screen" = a full-screen column layout
    // The header is at the top, and the children fill the rest
    <div className="flex flex-col h-screen bg-gray-50">
      {/* ---- Header bar ---- */}
      {/* AppBar is MUI's top navigation bar component */}
      <AppBar
        position="static" // "static" = stays at the top, doesn't float over content
        elevation={2} // Subtle shadow underneath
      >
        <Toolbar>
          {/* Home/New Chat button on the left */}
          <IconButton
            edge="start" // Aligns nicely to the left edge
            color="inherit" // Use white (inherits from AppBar's text color)
            aria-label="New conversation"
            onClick={onNewChat}
            className="mr-2"
          >
            <HomeIcon />
          </IconButton>

          {/* App title */}
          <Typography
            variant="h6" // "h6" = medium-sized heading
            component="h1" // Render as an actual <h1> tag for accessibility
            className="flex-1" // Takes up remaining space (pushes other items to edges)
          >
            ReaConnect 🏠
          </Typography>

          {/* Status text on the right */}
          <Typography variant="caption" className="opacity-75">
            AI Real Estate Assistant
          </Typography>
        </Toolbar>
      </AppBar>

      {/* ---- Main content area ---- */}
      {/* Container centers the content and limits its max width */}
      <Container
        maxWidth="md" // "md" = medium width (about 900px max)
        disableGutters // Remove default horizontal padding
        // "flex-1" = grow to fill available space
        // "flex flex-col" = children stack vertically
        // "overflow-hidden" = prevent double scrollbars
        className="flex-1 flex flex-col overflow-hidden"
      >
        {/* This is where the ChatWindow and ChatInput get rendered */}
        {children}
      </Container>
    </div>
  );
}
