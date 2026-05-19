/**
 * Root Layout — The outermost wrapper for EVERY page in the app
 *
 * Think of this like the foundation and outer walls of a building.
 * Every room (page) in the building sits inside this structure.
 *
 * This file does three important things:
 * 1. Loads the Geist font (the typeface for all text)
 * 2. Wraps everything in MUI's ThemeProvider (so all MUI components
 *    use our custom colors and styles from theme.ts)
 * 3. Sets up the HTML structure (<html>, <body>) with Tailwind classes
 *
 * "ThemeProvider" is like setting the dress code for a party —
 * once you set it here, every component inside automatically follows it.
 */

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import theme from "@/theme/theme";
import "./globals.css";

// ---------------------------------------------------------------------------
// Font Loading
// ---------------------------------------------------------------------------
// Next.js automatically downloads and hosts these fonts for us.
// "variable" creates a CSS variable (like a named color swatch) we can
// reference in our theme and Tailwind config.

const geistSans = Geist({
  variable: "--font-geist-sans", // CSS variable name
  subsets: ["latin"], // Only load Latin characters (English, Spanish, etc.)
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono", // Monospace font for code-like text
  subsets: ["latin"],
});

// ---------------------------------------------------------------------------
// Page Metadata (shows in the browser tab)
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title: "ReaConnect — AI Real Estate Assistant",
  description:
    "Chat with an AI assistant that has access to real estate listing data. Ask about prices, locations, and availability.",
};

// ---------------------------------------------------------------------------
// The Layout Component
// ---------------------------------------------------------------------------

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode; // Whatever page content goes inside this layout
}>) {
  return (
    // <html> tag with font CSS variables and Tailwind's "h-full" for full height
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {/*
          AppRouterCacheProvider solves a tricky problem:
          MUI generates styles at render time, but Next.js streams HTML to the browser.
          This provider makes sure MUI's styles arrive in the right order.
          Think of it like making sure the paint dries before hanging pictures.
        */}
        <AppRouterCacheProvider>
          {/*
            ThemeProvider passes our theme to ALL MUI components inside it.
            Every Button, TextField, AppBar, etc. will use our colors and fonts.
          */}
          <ThemeProvider theme={theme}>
            {/*
              CssBaseline is MUI's version of a CSS reset — it normalizes
              default browser styles so things look the same across Chrome,
              Firefox, Safari, etc. Think of it like leveling the ground
              before building a house.
            */}
            <CssBaseline />
            {/* The actual page content gets rendered here */}
            {children}
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
