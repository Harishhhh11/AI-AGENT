import { get, post, patch, del } from "./client";

export interface KnowledgeItem {
  id: number;
  organization_id: number;
  agent_id: number | null;
  title: string;
  content: string;
  source: string;
  category: string;
  uuid: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface KnowledgeCreate {
  title: string;
  content: string;
  source: string;
  category: string;
  agent_id?: number | null;
}

export interface KnowledgeUpdate {
  title?: string;
  content?: string;
  source?: string;
  category?: string;
  agent_id?: number | null;
  is_active?: boolean;
}

export async function getKnowledge(agentId?: number, scope: "all" | "shared" | "agent" | "available" = "all"): Promise<KnowledgeItem[]> {
  const query = new URLSearchParams();
  if (agentId != null) query.set("agent_id", String(agentId));
  if (scope !== "all") query.set("scope", scope);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await get<KnowledgeItem[] | { data: KnowledgeItem[] }>(`/knowledge${suffix}`);
  return Array.isArray(response) ? response : response.data;
}

export async function getKnowledgeById(knowledgeId: number): Promise<KnowledgeItem> {
  const response = await get<KnowledgeItem | { data: KnowledgeItem }>(`/knowledge/${knowledgeId}`);
  return typeof response === "object" && response !== null && "data" in response ? response.data : response;
}

export async function createKnowledge(data: KnowledgeCreate): Promise<KnowledgeItem> {
  const response = await post<KnowledgeItem | { data: KnowledgeItem }, KnowledgeCreate>("/knowledge", data);
  return typeof response === "object" && response !== null && "data" in response ? response.data : response;
}

export async function updateKnowledge(knowledgeId: number, data: KnowledgeUpdate): Promise<KnowledgeItem> {
  const response = await patch<KnowledgeItem | { data: KnowledgeItem }, KnowledgeUpdate>(`/knowledge/${knowledgeId}`, data);
  return typeof response === "object" && response !== null && "data" in response ? response.data : response;
}

export async function deleteKnowledge(knowledgeId: number): Promise<void> {
  await del(`/knowledge/${knowledgeId}`);
}

export async function deactivateKnowledge(knowledgeId: number): Promise<KnowledgeItem> {
  const response = await post<KnowledgeItem | { data: KnowledgeItem }, Record<string, never>>(`/knowledge/${knowledgeId}/deactivate`, {});
  return typeof response === "object" && response !== null && "data" in response ? response.data : response;
}
