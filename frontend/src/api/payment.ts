import { api } from "./client";

export interface InitPaymentRequest {
  booking_id: string;
  amount: number;
  trip_id?: string;
  pin: string;
}

export interface InitPaymentResponse {
  payment_id: string;
  status: string;
}

export interface PaymentHistoryResponse {
  payment_id: string
  booking_id: string
  user_id: string
  amount: number
  complete_at: string
  expires_at: string
  status: string
}

export async function initPayment(body: InitPaymentRequest): Promise<InitPaymentResponse> {
  return api<InitPaymentResponse>("/payment/payments/init", {
    method: "POST",
    body,
    requireAuth: true,
  });
}

export async function getPaymentHistory(): Promise<PaymentHistoryResponse> {
  return api<PaymentHistoryResponse>("/payment/payments/history", {
    method: "GET",
    requireAuth: true,
  });
}