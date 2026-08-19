import { post } from "./client";

export interface ChatRequest {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  session_id: string;
  response: string;
}

export async function sendMessage(
  message: string,
  sessionId?: string | null
): Promise<ChatResponse> {
  return post<
    ChatResponse,
    ChatRequest
  >(
    "/chat",
    {
      message,
      session_id: sessionId ?? null,
    }
  );
}