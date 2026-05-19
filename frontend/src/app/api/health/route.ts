/**
 * Next.js API Proxy Route — GET /api/health
 *
 * This is a simple "health check" proxy. It asks the Python backend:
 * "Hey, are you alive?" and passes the answer back to the browser.
 *
 * Useful for showing a connection status indicator in the UI —
 * like a green/red dot showing if the backend is reachable.
 */

import { NextResponse } from "next/server";

// The URL of our Python backend
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    // Try to reach the backend's health endpoint
    const backendResponse = await fetch(`${BACKEND_URL}/health`);
    const data = await backendResponse.json();

    // Pass the backend's response straight through
    return NextResponse.json(data);
  } catch {
    // Backend is unreachable — return an error status
    return NextResponse.json(
      {
        status: "error",
        service: "ReaConnect Chat API",
        error: "Backend is not reachable. Is the Python server running?",
      },
      { status: 503 } // 503 = "Service Unavailable"
    );
  }
}
