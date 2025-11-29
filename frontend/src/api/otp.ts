import { api } from "./client";

export interface VerifyOtpRequest {
  booking_id: string;
  otp_code: string;
}

export async function verifyOtp(body: VerifyOtpRequest): Promise<{ ok: boolean }>{
  return api("/payment/verify_otp", {
    method: "POST",
    body,
    requireAuth: true,
  });
}