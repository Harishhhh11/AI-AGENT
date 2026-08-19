const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export interface PublicAgent {
  name: string;
  public_slug: string;
  welcome_message: string;
}

export interface PublicChatResponse {
  session_id: string;
  response: string;
}

async function publicRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { Accept: "application/json", "Content-Type": "application/json", ...options?.headers },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = (
      body && typeof body === "object" && "detail" in body
        ? (body as { detail?: unknown }).detail
        : null
    );
    throw new Error(typeof detail === "string" ? detail : "This AI receptionist is unavailable.");
  }
  if (body === null || typeof body !== "object") {
    throw new Error("The receptionist returned an invalid response. Please try again.");
  }
  return body as T;
}

export function getPublicAgent(slug: string): Promise<PublicAgent> {
  return publicRequest<PublicAgent>(`/public/agents/${encodeURIComponent(slug)}`);
}

export function sendPublicMessage(slug: string, message: string, sessionId?: string | null): Promise<PublicChatResponse> {
  return publicRequest<PublicChatResponse>(`/public/agents/${encodeURIComponent(slug)}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId ?? null }),
  });
}
