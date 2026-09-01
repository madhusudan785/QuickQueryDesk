/* Agent Ticket Detail - Full view with overrides, AI draft, reply, audit log */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketService } from '../services/tickets';
import type { Ticket, AuditLog } from '../types';
import { CATEGORIES, PRIORITIES } from '../types';
import {
  ArrowLeft,
  Clock,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Paperclip,
  MessageSquare,
  Send,
  User,
  History,
  ArrowRightLeft,
  Bot,
  FileText,
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

export default function AgentTicketDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Override state
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState('');

  // Reply state
  const [replyText, setReplyText] = useState('');
  const [isReplying, setIsReplying] = useState(false);
  const [replySuccess, setReplySuccess] = useState(false);

  useEffect(() => {
    if (id) {
      loadTicket(id);
      loadAuditLogs(id);
    }
  }, [id]);

  const loadTicket = async (ticketId: string) => {
    try {
      setIsLoading(true);
      const data = await ticketService.getTicket(ticketId);
      setTicket(data);
      setSelectedCategory(data.current_category || '');
      setSelectedPriority(data.current_priority || '');
      // Pre-fill reply with AI draft if available
      if (data.ai_draft_reply && !data.final_reply) {
        setReplyText(data.ai_draft_reply);
      }
    } catch {
      setError('Failed to load ticket details');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAuditLogs = async (ticketId: string) => {
    try {
      const data = await ticketService.getAuditLog(ticketId);
      setAuditLogs(data);
    } catch {
      // Non-critical, silently fail
    }
  };

  const handleOverride = async () => {
    if (!ticket || !id) return;
    const updates: Record<string, string> = {};
    if (selectedCategory && selectedCategory !== ticket.current_category) {
      updates.current_category = selectedCategory;
    }
    if (selectedPriority && selectedPriority !== ticket.current_priority) {
      updates.current_priority = selectedPriority;
    }
    if (Object.keys(updates).length === 0) return;

    try {
      setIsUpdating(true);
      setUpdateSuccess('');
      const updated = await ticketService.updateTicket(id, updates);
      setTicket(updated);
      setUpdateSuccess('Category/Priority updated successfully');
      loadAuditLogs(id);
      setTimeout(() => setUpdateSuccess(''), 3000);
    } catch {
      setError('Failed to update ticket');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleReply = async () => {
    if (!id || !replyText.trim()) return;
    try {
      setIsReplying(true);
      const updated = await ticketService.replyToTicket(id, { final_reply: replyText });
      setTicket(updated);
      setReplySuccess(true);
    } catch {
      setError('Failed to send reply');
    } finally {
      setIsReplying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error && !ticket) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5" />
          {error}
        </div>
      </div>
    );
  }

  if (!ticket) return null;

  const hasOverrideChanges =
    (selectedCategory && selectedCategory !== ticket.current_category) ||
    (selectedPriority && selectedPriority !== ticket.current_priority);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate('/agent/dashboard')}
        className="flex items-center gap-1 text-sm text-surface-500 hover:text-surface-700 mb-6 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </button>

      {error && (
        <div className="flex items-center gap-2 p-4 mb-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Left 2/3 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Ticket Header */}
          <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
            <div className="flex items-start justify-between mb-4">
              <h1 className="text-xl font-bold text-surface-900 flex-1 pr-4">{ticket.title}</h1>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border shrink-0 ${
                  ticket.status === 'open'
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-green-50 text-green-700 border-green-200'
                }`}
              >
                {ticket.status === 'open' ? <Clock className="h-4 w-4 mr-1.5" /> : <CheckCircle2 className="h-4 w-4 mr-1.5" />}
                {ticket.status === 'open' ? 'Open' : 'Resolved'}
              </span>
            </div>

            <div className="flex items-center gap-2 mb-4 text-sm text-surface-500">
              <User className="h-4 w-4" />
              <span>Submitted by <span className="font-medium text-surface-700">{ticket.employee_name || 'Unknown'}</span></span>
              <span className="text-surface-300">•</span>
              <span>{new Date(ticket.created_at).toLocaleString()}</span>
            </div>

            <p className="text-surface-700 whitespace-pre-wrap leading-relaxed">{ticket.description}</p>

            {ticket.attachment_filename && (
              <div className="flex items-center gap-2 mt-4 text-sm text-surface-500 bg-surface-50 px-3 py-2 rounded-lg inline-flex">
                <Paperclip className="h-4 w-4" />
                {ticket.attachment_filename}
              </div>
            )}
          </div>

          {/* AI Classification Comparison */}
          <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-surface-900">AI Classification</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Category</p>
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="text-left">
                    <p className="text-[11px] text-surface-400 mb-1">AI Suggested</p>
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${categoryColors[ticket.ai_category || ''] || categoryColors.Other}`}>
                      {ticket.ai_category || 'N/A'}
                    </span>
                  </div>
                  {ticket.ai_category !== ticket.current_category && (
                    <>
                      <ArrowRightLeft className="h-4 w-4 text-surface-300 shrink-0 self-end mb-1" />
                      <div className="text-left">
                        <p className="text-[11px] text-surface-400 mb-1">Current (Overridden)</p>
                        <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${categoryColors[ticket.current_category || ''] || categoryColors.Other}`}>
                          {ticket.current_category || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Priority</p>
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="text-left">
                    <p className="text-[11px] text-surface-400 mb-1">AI Suggested</p>
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold border ${priorityColors[ticket.ai_priority || ''] || ''}`}>
                      {ticket.ai_priority || 'N/A'}
                    </span>
                  </div>
                  {ticket.ai_priority !== ticket.current_priority && (
                    <>
                      <ArrowRightLeft className="h-4 w-4 text-surface-300 shrink-0 self-end mb-1" />
                      <div className="text-left">
                        <p className="text-[11px] text-surface-400 mb-1">Current (Overridden)</p>
                        <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold border ${priorityColors[ticket.current_priority || ''] || ''}`}>
                          {ticket.current_priority || 'N/A'}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* AI Draft Reply */}
          {ticket.ai_draft_reply && (
            <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-3">
                <Bot className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-surface-900">AI Draft Reply</h2>
              </div>
              <div className="bg-primary-50 border border-primary-100 rounded-xl p-4">
                <p className="text-surface-800 whitespace-pre-wrap text-sm">{ticket.ai_draft_reply}</p>
              </div>

              {/* RAG Sources */}
              {ticket.rag_sources && ticket.rag_sources.length > 0 && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-4 w-4 text-surface-500" />
                    <p className="text-sm font-medium text-surface-600">Knowledge Base Sources</p>
                  </div>
                  <div className="space-y-2">
                    {ticket.rag_sources.map((source, idx) => (
                      <div key={idx} className="bg-surface-50 border border-surface-200 rounded-lg p-3">
                        <p className="text-sm font-medium text-surface-700">{source.title}</p>
                        {source.content_preview && (
                          <p className="text-xs text-surface-500 mt-1 line-clamp-2">{source.content_preview}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Reply Section */}
          {ticket.status === 'open' ? (
            <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-4">
                <MessageSquare className="h-5 w-5 text-green-600" />
                <h2 className="text-lg font-semibold text-surface-900">Send Reply</h2>
              </div>
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="w-full px-4 py-3 bg-surface-50 border border-surface-200 rounded-xl text-surface-900 placeholder-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none text-sm"
                placeholder="Write your reply to the employee... You can edit the AI draft above if available."
                rows={6}
              />
              <div className="flex items-center justify-between mt-3">
                <p className="text-xs text-surface-400">
                  Sending will resolve the ticket and notify the employee
                </p>
                <button
                  onClick={handleReply}
                  disabled={!replyText.trim() || isReplying}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-medium rounded-lg transition-all duration-200 shadow-lg shadow-green-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isReplying ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Send Reply
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Show final reply for resolved tickets */
            ticket.final_reply && (
              <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare className="h-5 w-5 text-green-600" />
                  <h2 className="text-lg font-semibold text-surface-900">Final Reply</h2>
                  {replySuccess && (
                    <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">Sent!</span>
                  )}
                </div>
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <p className="text-surface-800 whitespace-pre-wrap text-sm">{ticket.final_reply}</p>
                </div>
                {ticket.resolved_at && (
                  <p className="text-xs text-surface-400 mt-2">
                    Resolved on {new Date(ticket.resolved_at).toLocaleString()}
                  </p>
                )}
              </div>
            )
          )}
        </div>

        {/* Sidebar - Right 1/3 */}
        <div className="space-y-6">
          {/* Override Controls */}
          {ticket.status === 'open' && (
            <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-surface-900 mb-4">Override Classification</h3>

              {updateSuccess && (
                <div className="flex items-center gap-1 p-2 mb-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-xs">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {updateSuccess}
                </div>
              )}

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-surface-500 mb-1">Category</label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-50 border border-surface-200 rounded-lg text-sm text-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-surface-500 mb-1">Priority</label>
                  <select
                    value={selectedPriority}
                    onChange={(e) => setSelectedPriority(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-50 border border-surface-200 rounded-lg text-sm text-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {PRIORITIES.map((pri) => (
                      <option key={pri} value={pri}>{pri}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleOverride}
                  disabled={!hasOverrideChanges || isUpdating}
                  className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-surface-900 hover:bg-surface-800 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  {isUpdating ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    'Update Classification'
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Ticket Info */}
          <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
            <h3 className="text-sm font-semibold text-surface-900 mb-3">Ticket Info</h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-xs text-surface-400">Ticket ID</dt>
                <dd className="text-sm text-surface-700 font-mono">{ticket.id.slice(0, 8)}...</dd>
              </div>
              <div>
                <dt className="text-xs text-surface-400">Created</dt>
                <dd className="text-sm text-surface-700">{new Date(ticket.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-xs text-surface-400">Updated</dt>
                <dd className="text-sm text-surface-700">{new Date(ticket.updated_at).toLocaleString()}</dd>
              </div>
              {ticket.resolved_at && (
                <div>
                  <dt className="text-xs text-surface-400">Resolved</dt>
                  <dd className="text-sm text-surface-700">{new Date(ticket.resolved_at).toLocaleString()}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Audit Log */}
          {auditLogs.length > 0 && (
            <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-3">
                <History className="h-4 w-4 text-surface-500" />
                <h3 className="text-sm font-semibold text-surface-900">Override History</h3>
              </div>
              <div className="space-y-3">
                {auditLogs.map((log) => (
                  <div key={log.id} className="border-l-2 border-surface-200 pl-3">
                    <p className="text-sm text-surface-700">
                      <span className="font-medium capitalize">{log.field}</span> changed
                    </p>
                    <div className="flex items-center gap-1 text-xs mt-0.5">
                      <span className="text-red-500 line-through">{log.old_value}</span>
                      <span className="text-surface-400">→</span>
                      <span className="text-green-600 font-medium">{log.new_value}</span>
                    </div>
                    <p className="text-xs text-surface-400 mt-0.5">
                      by {log.agent_name} • {new Date(log.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
