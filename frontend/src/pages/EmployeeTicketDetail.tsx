/* Employee Ticket Detail page */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketService } from '../services/tickets';
import type { Ticket } from '../types';
import {
  ArrowLeft,
  Clock,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Paperclip,
  MessageSquare,
} from 'lucide-react';

const priorityColors: Record<string, string> = {
  High: 'bg-red-100 text-red-700 border-red-200',
  Medium: 'bg-amber-100 text-amber-700 border-amber-200',
  Low: 'bg-green-100 text-green-700 border-green-200',
};

const categoryColors: Record<string, string> = {
  IT: 'bg-blue-100 text-blue-700',
  HR: 'bg-purple-100 text-purple-700',
  Finance: 'bg-emerald-100 text-emerald-700',
  Admin: 'bg-orange-100 text-orange-700',
  Other: 'bg-surface-100 text-surface-700',
};

export default function EmployeeTicketDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) loadTicket(id);
  }, [id]);

  const loadTicket = async (ticketId: string) => {
    try {
      setIsLoading(true);
      const data = await ticketService.getTicket(ticketId);
      setTicket(data);
    } catch {
      setError('Failed to load ticket details');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5" />
          {error || 'Ticket not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-1 text-sm text-surface-500 hover:text-surface-700 mb-6 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to My Tickets
      </button>

      {/* Ticket Header */}
      <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <h1 className="text-xl font-bold text-surface-900 flex-1">{ticket.title}</h1>
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${
              ticket.status === 'open'
                ? 'bg-amber-50 text-amber-700 border-amber-200'
                : 'bg-green-50 text-green-700 border-green-200'
            }`}
          >
            {ticket.status === 'open' ? (
              <Clock className="h-4 w-4 mr-1.5" />
            ) : (
              <CheckCircle2 className="h-4 w-4 mr-1.5" />
            )}
            {ticket.status.charAt(0).toUpperCase() + ticket.status.slice(1)}
          </span>
        </div>

        <p className="text-surface-700 whitespace-pre-wrap mb-4">{ticket.description}</p>

        {ticket.attachment_filename && (
          <div className="flex items-center gap-2 text-sm text-surface-500">
            <Paperclip className="h-4 w-4" />
            {ticket.attachment_filename}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3 mt-4 pt-4 border-t border-surface-100">
          {ticket.current_category && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${categoryColors[ticket.current_category] || categoryColors.Other}`}>
              {ticket.current_category}
            </span>
          )}
          {ticket.current_priority && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${priorityColors[ticket.current_priority] || ''}`}>
              {ticket.current_priority} Priority
            </span>
          )}
          <span className="text-sm text-surface-400">
            Created {new Date(ticket.created_at).toLocaleString()}
          </span>
          {ticket.resolved_at && (
            <span className="text-sm text-surface-400">
              Resolved {new Date(ticket.resolved_at).toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* AI Classification Info */}
      {(ticket.ai_category || ticket.ai_priority) && (
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-surface-900">AI Classification</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-surface-500 mb-1">AI-Suggested Category</p>
              <p className="font-medium text-surface-900">{ticket.ai_category || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-surface-500 mb-1">AI-Suggested Priority</p>
              <p className="font-medium text-surface-900">{ticket.ai_priority || 'N/A'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Agent Reply */}
      {ticket.final_reply && (
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="h-5 w-5 text-green-600" />
            <h2 className="text-lg font-semibold text-surface-900">Agent Reply</h2>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <p className="text-surface-800 whitespace-pre-wrap">{ticket.final_reply}</p>
          </div>
        </div>
      )}

      {/* Waiting for reply */}
      {ticket.status === 'open' && (
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 text-center">
          <Clock className="h-8 w-8 text-amber-500 mx-auto mb-2" />
          <p className="text-surface-600 font-medium">Waiting for agent response</p>
          <p className="text-sm text-surface-400 mt-1">An agent will review your ticket and respond soon</p>
        </div>
      )}
    </div>
  );
}
