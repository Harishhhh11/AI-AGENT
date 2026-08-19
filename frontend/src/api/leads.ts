import {
  get,
  patch,
  del,
} from "./client";

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

export interface LeadUpdate {
  name?: string | null;

  phone?: string | null;

  email?: string | null;

  interest?: string | null;

  preferred_mode?: string | null;

  preferred_time?: string | null;

  notes?: string | null;

  status?: string;
}

export async function getLeads(): Promise<
  Lead[]
> {
  const response = await get<
    Lead[] | {
      data: Lead[];
    }
  >("/leads");

  if (Array.isArray(response)) {
    return response;
  }

  return response.data;
}

export async function updateLead(
  leadId: number,
  data: LeadUpdate
): Promise<Lead> {
  const response =
    await patch<
      Lead | {
        data: Lead;
      },
      LeadUpdate
    >(
      `/leads/${leadId}`,
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

export async function deleteLead(
  leadId: number
): Promise<void> {
  await del<void>(`/leads/${leadId}`);
}
