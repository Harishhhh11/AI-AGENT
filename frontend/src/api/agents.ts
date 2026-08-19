import { get, patch, post } from "./client";

export interface Agent {
  id: number;
  organization_id: number;
  name: string;
  public_slug: string;
  welcome_message: string;
  system_instructions?: string | null;
  is_published: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  public_slug: string;
  welcome_message: string;
  system_instructions?: string;
}

export const getAgents = () => get<Agent[]>("/agents");
export const createAgent = (data: AgentCreate) => post<Agent, AgentCreate>("/agents", data);
export const updateAgent = (id: number, data: Partial<AgentCreate & { is_active: boolean }>) => patch<Agent, typeof data>(`/agents/${id}`, data);
export const publishAgent = (id: number) => post<Agent, Record<string, never>>(`/agents/${id}/publish`, {});
export const unpublishAgent = (id: number) => post<Agent, Record<string, never>>(`/agents/${id}/unpublish`, {});
