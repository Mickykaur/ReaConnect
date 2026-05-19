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
 */

import { NextRequest, NextResponse } from "next/server";

// The URL of our Python backend — where the AI chat logic lives
// In production, you'd use an environment variable for this
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    // Step 1: Read the JSON body from the browser's request
    // This contains { message: "...", conversation_id: "..." }
    const body = await request.json();

    // Step 2: Forward the request to the Python backend
    // fetch() is like making a phone call to another server
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json", // Tell the backend we're sending JSON
      },
      body: JSON.stringify(body), // Convert the JS object back to a JSON string
    });

    // Step 3: Read the backend's response
    const data = await backendResponse.json();

    // Step 4: If the backend returned an error, pass it through
    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: data.detail || "Backend error" },
        { status: backendResponse.status }
      );
    }

    // Step 5: Send the successful response back to the browser
    return NextResponse.json(data);
  } catch (error) {
    // If something went wrong (e.g., backend is not running), tell the user
    console.error("Proxy error:", error);
    return NextResponse.json(
      {
        error:
          "Could not connect to the backend. Make sure the Python server is running on port 8000.",
      },
      { status: 502 } // 502 = "Bad Gateway" (the middleman couldn't reach the backend)
    );
  }
}
