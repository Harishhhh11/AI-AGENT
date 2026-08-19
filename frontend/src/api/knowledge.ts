import {
  get,
  post,
  patch,
  del,
} from "./client";


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

  is_active?: boolean;
}


/*
 * Get all knowledge records.
 */
export async function getKnowledge(): Promise<
  KnowledgeItem[]
> {
  const response = await get<
    | KnowledgeItem[]
    | {
        data: KnowledgeItem[];
      }
  >("/knowledge");

  if (Array.isArray(response)) {
    return response;
  }

  return response.data;
}


/*
 * Get one knowledge record.
 */
export async function getKnowledgeById(
  knowledgeId: number
): Promise<KnowledgeItem> {
  const response =
    await get<
      | KnowledgeItem
      | {
          data: KnowledgeItem;
        }
    >(
      `/knowledge/${knowledgeId}`
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
 * Create knowledge.
 *
 * The backend automatically generates
 * the embedding.
 */
export async function createKnowledge(
  data: KnowledgeCreate
): Promise<KnowledgeItem> {
  const response =
    await post<
      | KnowledgeItem
      | {
          data: KnowledgeItem;
        },
      KnowledgeCreate
    >(
      "/knowledge",
      data
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
 * Update knowledge.
 */
export async function updateKnowledge(
  knowledgeId: number,
  data: KnowledgeUpdate
): Promise<KnowledgeItem> {
  const response =
    await patch<
      | KnowledgeItem
      | {
          data: KnowledgeItem;
        },
      KnowledgeUpdate
    >(
      `/knowledge/${knowledgeId}`,
      data
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
 * Delete knowledge.
 */
export async function deleteKnowledge(
  knowledgeId: number
): Promise<void> {
  await del(
    `/knowledge/${knowledgeId}`
  );
}


/*
 * Deactivate knowledge.
 */
export async function deactivateKnowledge(
  knowledgeId: number
): Promise<KnowledgeItem> {
  const response =
    await post<
      | KnowledgeItem
      | {
          data: KnowledgeItem;
        },
      Record<string, never>
    >(
      `/knowledge/${knowledgeId}/deactivate`,
      {}
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
