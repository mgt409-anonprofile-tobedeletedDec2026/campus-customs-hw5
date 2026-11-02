export type AgentId = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";

export interface PaymentRequestBrief {
  id: number;
  kind: string;
  amount: number;
  status: string;
}

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  status: string;
  state: "open" | "resolved";
  notes: string | null;
  latest_update: { agent: string; new_status: string; note: string; shop_date: string } | null;
  draft_count: number;
  payment_requests: PaymentRequestBrief[];
  awaiting_david: PaymentRequestBrief[];
}

export interface TicketBoard {
  today: string;
  tickets: Ticket[];
}

export interface AgentEvent {
  index: number;
  time_utc: string;
  run_id: string;
  ticket_id: number | null;
  agent: AgentId | null;
  character: string;
  event: string;
  said?: string | null;
  tool?: string;
  detail?: unknown;
  to?: AgentId;
  from_agent?: AgentId;
  needs_human?: boolean;
  human_action?: string | null;
}

export interface EventsResponse {
  total: number;
  running: boolean;
  events: AgentEvent[];
}

export interface RunStatus {
  running: boolean;
  ticket_id: number | null;
  run_id: string | null;
  started_utc: string | null;
  result: { error: string | null; model_requests: number; total_tokens: number } | null;
}

export interface PaymentRequest {
  id: number;
  ticket_id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number | null;
  vendor_id: number | null;
  sku: string | null;
  size: string | null;
  qty: number | null;
  amount: number;
  requested_by: string;
  reason: string;
  status: string;
  shop_date: string;
  decided_by: string | null;
  decision_note: string | null;
  risk?: PaymentRisk;
}

export interface PaymentRisk {
  at_risk: boolean;
  warning?: string;
  cash_now: number;
  cash_after_this: number;
  reserve_needed: number;
  bills_at_risk: string[];
  recommended_order: { label: string; why: string; affordable: boolean; cash_after: number }[];
}

export interface CashResponse {
  checking_balance: number | null;
  as_of: string | null;
}
