import { get, patch } from "./client";

export interface Conversation {
  id: number;
  organization_id: number;
  user_id: number | null;
  session_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface ConversationStatusUpdate {
  status: string;
}

export async function getConversations(
  status?: string
): Promise<Conversation[]> {
  const endpoint = status
    ? `/conversations?status=${encodeURIComponent(status)}`
    : "/conversations";

  const response = await get<
    | Conversation[]
    | {
        data: Conversation[];
      }
  >(endpoint);

  if (Array.isArray(response)) {
    return response;
  }

  return response.data;
}

export async function getConversation(
  conversationId: number
): Promise<Conversation> {
  const response = await get<
    | Conversation
    | {
        data: Conversation;
      }
  >(`/conversations/${conversationId}`);

  if (
    typeof response === "object" &&
    response !== null &&
    "data" in response
  ) {
    return response.data;
  }

  return response;
}

export async function getMessages(
  conversationId: number
): Promise<Message[]> {
  const response = await get<
    | Message[]
    | {
        data: Message[];
      }
  >(
    `/conversations/${conversationId}/messages`
  );

  if (Array.isArray(response)) {
    return response;
  }

  return response.data;
}

export async function updateConversationStatus(
  conversationId: number,
  status: string
): Promise<Conversation> {
  const response = await patch<
    | Conversation
    | {
        data: Conversation;
      },
    ConversationStatusUpdate
  >(
    `/conversations/${conversationId}`,
    {
      status,
    }
  );

  if (
    typeof response === "object" &&
    response !== null &&
    "data" in response
  ) {
    return response.data;
  }

  return response;
}

/*
 * Backward-compatible alias.
 */
export const getConversationMessages =
  getMessages;