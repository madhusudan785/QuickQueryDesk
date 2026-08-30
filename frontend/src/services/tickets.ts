/* Ticket service */

import api from './api';
import type {
  Ticket,
  TicketListItem,
  CreateTicketPayload,
  TicketUpdatePayload,
  TicketReplyPayload,
  AuditLog,
  Metrics,
} from '../types';

export const ticketService = {
  async createTicket(payload: CreateTicketPayload): Promise<Ticket> {
    const response = await api.post<Ticket>('/tickets', payload);
    return response.data;
  },

  async getMyTickets(): Promise<TicketListItem[]> {
    const response = await api.get<TicketListItem[]>('/tickets/my');
    return response.data;
  },

  async getAllTickets(params?: {
    status?: string;
    category?: string;
    priority?: string;
    search?: string;
  }): Promise<TicketListItem[]> {
    const response = await api.get<TicketListItem[]>('/tickets', { params });
    return response.data;
  },

  async getTicket(id: string): Promise<Ticket> {
    const response = await api.get<Ticket>(`/tickets/${id}`);
    return response.data;
  },

  async updateTicket(id: string, payload: TicketUpdatePayload): Promise<Ticket> {
    const response = await api.patch<Ticket>(`/tickets/${id}`, payload);
    return response.data;
  },

  async replyToTicket(id: string, payload: TicketReplyPayload): Promise<Ticket> {
    const response = await api.post<Ticket>(`/tickets/${id}/reply`, payload);
    return response.data;
  },

  async getAuditLog(ticketId: string): Promise<AuditLog[]> {
    const response = await api.get<AuditLog[]>(`/tickets/${ticketId}/audit`);
    return response.data;
  },

  async getMetrics(): Promise<Metrics> {
    const response = await api.get<Metrics>('/metrics');
    return response.data;
  },
};
