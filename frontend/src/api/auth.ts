import { get, post } from "./client";

export interface AuthEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
}

export interface OnboardingInput {
  organization_name: string;
  organization_email: string;
  first_name: string;
  last_name: string;
  admin_email: string;
  password: string;
  phone?: string;
  agent_name: string;
  public_slug: string;
}

export interface OnboardingResult {
  organization_id: number;
  admin_user_id: number;
  agent_id: number;
  public_slug: string;
}

export function login(email: string, password: string) {
  return post<AuthEnvelope<LoginResult>, { email: string; password: string }>("/auth/login", { email, password });
}

export function registerCompany(input: OnboardingInput) {
  return post<AuthEnvelope<OnboardingResult>, OnboardingInput>("/onboarding/register-company", input);
}

export function getCurrentUser() {
  return get<AuthEnvelope<Record<string, unknown>>>("/auth/me");
}