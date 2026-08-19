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