import { del, get, patch, post, put } from "./client";
import type { KnowledgeItem } from "./knowledge";

export interface Agent {
  id: number;
  uuid?: string;
  organization_id: number;
  name: string;
  public_slug: string;
  welcome_message: string;
  system_instructions?: string | null;
  is_published: boolean;
  is_active: boolean;
  knowledge_item_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  public_slug: string;
  welcome_message: string;
  system_instructions?: string | null;
  knowledge_item_ids: number[];
}

export interface AgentKnowledgeUpdate {
  knowledge_item_ids: number[];
}

export const getAgents = () => get<Agent[]>("/agents");
export const getAgent = (id: number) => get<Agent>(`/agents/${id}`);
export const createAgent = (data: AgentCreate) => post<Agent, AgentCreate>("/agents", data);
export const updateAgent = (id: number, data: Partial<AgentCreate & { is_active: boolean }>) => patch<Agent, typeof data>(`/agents/${id}`, data);
export const getAgentKnowledge = (id: number) => get<KnowledgeItem[]>(`/agents/${id}/knowledge`);
export const updateAgentKnowledge = (id: number, data: AgentKnowledgeUpdate) => put<Agent, AgentKnowledgeUpdate>(`/agents/${id}/knowledge`, data);
export const publishAgent = (id: number) => post<Agent, Record<string, never>>(`/agents/${id}/publish`, {});
export const unpublishAgent = (id: number) => post<Agent, Record<string, never>>(`/agents/${id}/unpublish`, {});
export const deleteAgent = (id: number) => del(`/agents/${id}`);
