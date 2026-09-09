import { post } from "./client";

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  agent_id?: number | null;
}

export interface ChatResponse {
  session_id: string;
  response: string;
}

export async function sendMessage(
  message: string,
  sessionId?: string | null,
  agentId?: number | null,
): Promise<ChatResponse> {
  return post<ChatResponse, ChatRequest>("/chat", {
    message,
    session_id: sessionId ?? null,
    agent_id: agentId ?? null,
  });
}
