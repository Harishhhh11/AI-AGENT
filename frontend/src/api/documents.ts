/** Document upload API. */

export interface DocumentChunk {
  id: number;
  title: string;
  uuid: string;
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  data: {
    title: string;
    category: string;
    source: string;
    chunks_created: number;
    chunks: DocumentChunk[];
    agent_id?: number | null;
  };
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export async function uploadDocument(
  file: File,
  category: string,
  agentId?: number | null,
): Promise<DocumentUploadResponse> {
  const token = localStorage.getItem("access_token");
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  if (agentId != null) formData.append("agent_id", String(agentId));

  const headers: HeadersInit = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    headers,
    body: formData,
  });

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
    throw new Error("Authentication required.");
  }
  if (!response.ok) {
    const detail = body && typeof body === "object" && "detail" in body ? (body as { detail?: unknown }).detail : null;
    throw new Error(typeof detail === "string" ? detail : `Document upload failed with status ${response.status}.`);
  }
  if (!body || typeof body !== "object") throw new Error("The document service returned an invalid response.");
  return body as DocumentUploadResponse;
}
