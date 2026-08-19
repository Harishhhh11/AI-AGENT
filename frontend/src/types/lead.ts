export interface Lead {
  id: number;
  organization_id: number;
  conversation_id: number | null;

  name: string | null;
  phone: string | null;
  email: string | null;

  interest: string | null;
  preferred_mode: string | null;
  preferred_time: string | null;

  notes: string | null;

  status: string;
}