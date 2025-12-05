import { api } from "./client";

export interface AccountMeResponse {
  ok: boolean;
  user_id: string;
  name: string;
  phone_number: string;
  balance: number;
  username: string;
  email: string;
  passenger_type?: string;
}

export async function getAccountMe(): Promise<AccountMeResponse> {
  return api<AccountMeResponse>("/account/me", { method: "GET", requireAuth: true });
}

