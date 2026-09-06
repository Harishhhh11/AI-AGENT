import { get } from "./client";

export interface IntegrationSummary {
  key: string;
  name: string;
  category: string;
  description: string;
  status: "configured" | "available";
  setup_hint: string;
  capabilities: string[];
}

export function getIntegrations(): Promise<{ integrations: IntegrationSummary[] }> {
  return get<{ integrations: IntegrationSummary[] }>("/integrations");
}
