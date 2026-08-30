/* Create Ticket page */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketService } from '../services/tickets';
import { AlertCircle, Send, ArrowLeft, Paperclip, Sparkles } from 'lucide-react';

export default function CreateTicket() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [attachmentFilename, setAttachmentFilename] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const ticket = await ticketService.createTicket({
        title,
        description,
        attachment_filename: attachmentFilename || undefined,
      });
      setSuccess(true);
      setTimeout(() => navigate(`/tickets/${ticket.id}`), 1500);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Failed to create ticket');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-1 text-sm text-surface-500 hover:text-surface-700 mb-6 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </button>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-surface-900">Submit a Support Request</h1>
        <p className="text-surface-500 mt-1">
          Describe your issue and our AI will categorize and prioritize it automatically
        </p>
      </div>

      {/* Success Message */}
      {success && (
        <div className="flex items-center gap-3 p-4 mb-6 bg-green-50 border border-green-200 rounded-xl text-green-700">
          <Sparkles className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">Ticket created successfully!</p>
            <p className="text-sm mt-0.5">AI has classified your ticket. Redirecting...</p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-4 mb-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-surface-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2.5 bg-surface-50 border border-surface-200 rounded-lg text-surface-900 placeholder-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              placeholder="Brief summary of your issue"
              required
              maxLength={255}
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-surface-700 mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2.5 bg-surface-50 border border-surface-200 rounded-lg text-surface-900 placeholder-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none"
              placeholder="Provide detailed information about your issue..."
              required
              rows={6}
            />
          </div>

          <div>
            <label htmlFor="attachment" className="block text-sm font-medium text-surface-700 mb-1">
              Attachment Filename <span className="text-surface-400 font-normal">(optional)</span>
            </label>
            <div className="flex items-center w-full bg-surface-50 border border-surface-200 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
              <div className="pl-3 pr-2 flex items-center justify-center text-surface-400 shrink-0 pointer-events-none">
                <Paperclip className="h-4 w-4" />
              </div>
              <input
                id="attachment"
                type="text"
                value={attachmentFilename}
                onChange={(e) => setAttachmentFilename(e.target.value)}
                className="w-full pr-4 py-2.5 bg-transparent text-surface-900 placeholder-surface-400 focus:outline-none border-none text-sm"
                placeholder="e.g., screenshot.png"
                maxLength={255}
              />
            </div>
            <p className="text-xs text-surface-400 mt-1">
              Enter the filename of any relevant attachment
            </p>
          </div>

          {/* AI Classification Info */}
          <div className="flex items-start gap-3 p-4 bg-primary-50 border border-primary-100 rounded-xl">
            <Sparkles className="h-5 w-5 text-primary-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-primary-800">AI-Powered Classification</p>
              <p className="text-xs text-primary-600 mt-0.5">
                When you submit this ticket, our AI will automatically suggest a category
                (IT, HR, Finance, Admin, Other) and priority level (Low, Medium, High).
              </p>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isSubmitting || success}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-medium rounded-lg transition-all duration-200 shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Submit Ticket
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
