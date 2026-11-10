import { NextResponse } from "next/server";

export async function GET() {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/markets/compare",
      { cache: "no-store" }
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: "Market comparison unavailable" },
        { status: 502 }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Backend connection failed" },
      { status: 502 }
    );
  }
}
