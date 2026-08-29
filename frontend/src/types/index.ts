/* TypeScript interfaces for the application */

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'agent';
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: 'employee' | 'agent';
  name: string;
}

export interface Ticket {
  id: string;
  employee_id: string;
  employee_name?: string;
  title: string;
  description: string;
  attachment_filename?: string;
  ai_category?: string;
  current_category?: string;
  ai_priority?: string;
  current_priority?: string;
  status: 'open' | 'resolved';
  ai_draft_reply?: string;
  final_reply?: string;
  rag_sources?: RagSource[];
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolved_by?: string;
}

export interface TicketListItem {
  id: string;
  title: string;
  current_category?: string;
  current_priority?: string;
  status: 'open' | 'resolved';
  created_at: string;
  updated_at: string;
  employee_name?: string;
}

export interface CreateTicketPayload {
  title: string;
  description: string;
  attachment_filename?: string;
}

export interface TicketUpdatePayload {
  current_category?: string;
  current_priority?: string;
}

export interface TicketReplyPayload {
  final_reply: string;
}

export interface AuditLog {
  id: string;
  ticket_id: string;
  agent_id: string;
  agent_name?: string;
  field: string;
  old_value: string;
  new_value: string;
  created_at: string;
}

export interface RagSource {
  title: string;
  content_preview?: string;
}

export interface Metrics {
  status_counts: {
    open: number;
    resolved: number;
  };
  category_distribution: Record<string, number>;
  median_resolution_hours: number | null;
  ai_override_percentage: number;
  total_tickets: number;
  total_classified: number;
  total_overridden: number;
}

export type Category = 'IT' | 'HR' | 'Finance' | 'Admin' | 'Other';
export type Priority = 'Low' | 'Medium' | 'High';

export const CATEGORIES: Category[] = ['IT', 'HR', 'Finance', 'Admin', 'Other'];
export const PRIORITIES: Priority[] = ['Low', 'Medium', 'High'];
