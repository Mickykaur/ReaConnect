/**
 * Next.js API Proxy Route — POST /api/chat
 *
 * This is the "mail slot" in our front door. Here's what happens:
 *
 * 1. The browser sends a chat message HERE (to /api/chat)
 * 2. This code forwards that message to our Python backend (localhost:8000)
 * 3. The Python backend processes it and sends a reply
 * 4. This code passes that reply back to the browser
 *
 * WHY do we need this middleman?
 * Browsers have a security rule called "CORS" that blocks direct requests
 * to a different port (3000 → 8000). The proxy lives on the SAME port as
 * the frontend (3000), so the browser is happy. It's like having a friend
 * pick up your pizza from across town so you don't have to cross the bridge.
 *
 * NEW: This route now proxies the STREAMING endpoint (/api/v1/chat/stream).
 * Instead of waiting for the full response, it passes through a live stream
 * of Server-Sent Events (SSE) — like relaying a radio broadcast in real-time.
 */

import { NextRequest } from "next/server";

// The URL of our Python backend — where the AI chat logic lives
// In production, you'd use an environment variable for this
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    // Step 1: Read the JSON body from the browser's request
    // This contains { message: "...", conversation_id: "..." }
    const body = await request.json();

    // Step 2: Forward the request to the Python backend's STREAMING endpoint
    // We use the /stream endpoint now so we get live updates
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json", // Tell the backend we're sending JSON
      },
      body: JSON.stringify(body), // Convert the JS object back to a JSON string
    });

    // Step 3: If the backend returned an error, pass it through as JSON
    if (!backendResponse.ok) {
      // Try to read the error details from the backend
      const errorData = await backendResponse.json().catch(() => ({
        detail: "Backend error",
      }));

      return new Response(
        JSON.stringify({ error: errorData.detail || "Backend error" }),
        {
          status: backendResponse.status,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // Step 4: The backend is streaming SSE events. We need to pass them
    // through to the browser AS THEY ARRIVE — not wait for all of them.
    //
    // backendResponse.body is a "ReadableStream" — think of it like a pipe
    // that water (data) flows through. We connect this pipe directly to the
    // browser so the data flows straight through without us holding it up.
    if (!backendResponse.body) {
      // Safety check: if there's no body somehow, return an error
      return new Response(
        JSON.stringify({ error: "No response body from backend" }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // Step 5: Return the stream directly to the browser
    // We set the same SSE headers so the browser knows this is a stream
    return new Response(backendResponse.body, {
      status: 200,
      headers: {
        // "text/event-stream" = "this is a Server-Sent Events stream"
        "Content-Type": "text/event-stream",
        // "no-cache" = don't store this response (it's live data)
        "Cache-Control": "no-cache",
        // "keep-alive" = keep the connection open (don't hang up)
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    // If something went wrong (e.g., backend is not running), tell the user
    console.error("Proxy error:", error);
    return new Response(
      JSON.stringify({
        error:
          "Could not connect to the backend. Make sure the Python server is running on port 8000.",
      }),
      {
        status: 502, // 502 = "Bad Gateway" (the middleman couldn't reach the backend)
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}
