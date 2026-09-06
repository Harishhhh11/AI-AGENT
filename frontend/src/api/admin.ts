import { get, post, put, del } from "./client";

export interface Organization {
  id: number;
  name: string;
  email: string;
}

export interface TeamMember {
  id: number;
  uuid: string;
  organization_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  role_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: number;
  uuid: string;
  organization_id: number;
  name: string;
  description: string | null;
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface TeamMemberCreate {
  organization_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  password: string;
}

function unwrap<T>(response: T | { data: T }): T {
  return typeof response === "object" && response !== null && "data" in response
    ? response.data
    : response;
}

export async function getOrganization(): Promise<Organization> {
  return unwrap(await get<Organization | { data: Organization }>("/organizations/me"));
}

export async function updateOrganization(
  organizationId: number,
  data: Pick<Organization, "name" | "email">,
): Promise<Organization> {
  return unwrap(await put<Organization | { data: Organization }, typeof data>(
    `/organizations/${organizationId}`,
    data,
  ));
}

export async function getTeamMembers(): Promise<TeamMember[]> {
  return unwrap(await get<TeamMember[] | { data: TeamMember[] }>("/users"));
}

export async function createTeamMember(data: TeamMemberCreate): Promise<TeamMember> {
  return unwrap(await post<TeamMember | { data: TeamMember }, TeamMemberCreate>("/users", data));
}

export async function deleteTeamMember(userId: number): Promise<void> {
  await del(`/users/${userId}`);
}

export async function getRoles(): Promise<Role[]> {
  return unwrap(await get<Role[] | { data: Role[] }>("/roles"));
}
