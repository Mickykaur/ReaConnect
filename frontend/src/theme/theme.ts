/**
 * MUI Theme Configuration for ReaConnect
 *
 * Think of a "theme" like a style guide for a brand — it defines the
 * colors, fonts, and overall look-and-feel so everything looks consistent.
 *
 * Material UI uses this theme object to automatically style all its
 * components (buttons, text fields, cards, etc.) with our chosen colors.
 */

"use client"; // This tells Next.js this code runs in the browser, not on the server

import { createTheme } from "@mui/material/styles";

// createTheme() builds a theme object from our settings
const theme = createTheme({
  // -- Color palette --
  // "palette" is like a paint palette — it defines the main colors used everywhere
  palette: {
    // "primary" is the main brand color (used for buttons, links, etc.)
    primary: {
      main: "#1976d2", // A professional blue color
    },
    // "secondary" is an accent color for highlights
    secondary: {
      main: "#388e3c", // A green color — fitting for real estate!
    },
    // Background colors for the whole page and individual cards/surfaces
    background: {
      default: "#f5f5f5", // Light gray page background
      paper: "#ffffff", // White card/surface background
    },
  },

  // -- Typography (fonts and text styles) --
  typography: {
    // Use the Geist font that Next.js already loaded for us
    fontFamily: "var(--font-geist-sans), Arial, Helvetica, sans-serif",
  },

  // -- Component-level overrides --
  // This lets us customize how specific MUI components look globally
  components: {
    // Make all MUI buttons NOT fully uppercase (more modern look)
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none", // "none" means keep the original casing
        },
      },
    },
  },
});

// Export the theme so other files can use it
export default theme;
