import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  BookOpen, 
  IndianRupee, 
  Plus, 
  LogOut, 
  CheckCircle2, 
  Sparkles, 
  Bot, 
  Send,
  MessageSquare
} from 'lucide-react';

export default function Dashboard() {
  const { user, logout, isAdmin } = useAuth();
  const [books, setBooks] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketDetails, setTicketDetails] = useState(null);
  const [replyMessage, setReplyMessage] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  // New ticket modal state
  const [showModal, setShowModal] = useState(false);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [booksRes, ticketsRes] = await Promise.all([
        api.get('/books/'),
        api.get('/support/'),
      ]);
      setBooks(booksRes.data.results || booksRes.data || []);
      const ticketList = ticketsRes.data.results || ticketsRes.data || [];
      setTickets(ticketList);
      
      if (ticketList.length > 0 && !selectedTicket) {
        loadTicketDetails(ticketList[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  };

  const loadTicketDetails = async (id) => {
    try {
      const res = await api.get(`/support/${id}/`);
      setSelectedTicket(id);
      setTicketDetails(res.data);
    } catch (err) {
      console.error('Failed to load ticket details:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post('/support/', { subject, description });
      setSubject('');
      setDescription('');
      setShowModal(false);
      await fetchData();
      if (res.data?.id) {
        loadTicketDetails(res.data.id);
      }
    } catch (err) {
      alert('Error creating ticket: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() || !selectedTicket) return;
    setSendingReply(true);
    try {
      await api.post(`/support/${selectedTicket}/messages/`, {
        message: replyMessage,
        is_internal_note: false,
      });
      setReplyMessage('');
      await loadTicketDetails(selectedTicket);
    } catch (err) {
      alert('Failed to send reply: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSendingReply(false);
    }
  };

  const handleAdoptAIResponse = () => {
    if (ticketDetails?.ai_suggested_response) {
      setReplyMessage(ticketDetails.ai_suggested_response);
    }
  };

  const totalSales = books.reduce((acc, b) => acc + (b.sales_count || 0), 0);
  const pendingRoyalty = books.reduce((acc, b) => acc + parseFloat(b.royalty_pending || 0), 0);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-emerald-600 text-white p-2 rounded-lg">
              <BookOpen size={20} />
            </div>
            <span className="font-bold text-slate-800 text-lg">AuthorConnect</span>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
              isAdmin ? 'bg-purple-100 text-purple-700' : 'bg-emerald-100 text-emerald-700'
            }`}>
              {isAdmin ? 'ADMIN CONSOLE' : 'AUTHOR PORTAL'}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-slate-600">
              Logged in as: <strong className="text-slate-800">{user?.username}</strong>
            </span>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:text-red-600 rounded-lg hover:bg-slate-50 transition"
              title="Sign Out"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
              <BookOpen size={24} />
            </div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Published Titles</p>
              <h3 className="text-2xl font-bold text-slate-800">{books.length}</h3>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
              <CheckCircle2 size={24} />
            </div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Lifetime Units Sold</p>
              <h3 className="text-2xl font-bold text-slate-800">{totalSales}</h3>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
              <IndianRupee size={24} />
            </div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Pending Royalty Payout</p>
              <h3 className="text-2xl font-bold text-emerald-600">₹{pendingRoyalty.toLocaleString('en-IN')}</h3>
            </div>
          </div>
        </div>

        {/* Support System */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-white via-white to-emerald-50/40">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-slate-800 text-lg">Support Desk & AI Triage Center</h2>
                <span className="flex items-center gap-1 bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-xs px-2.5 py-0.5 rounded-full font-medium shadow-sm">
                  <Sparkles size={12} /> AI Enabled
                </span>
              </div>
              <p className="text-sm text-slate-500">
                Automated sentiment & intent analysis, instant category tagging, and knowledge-base draft generation.
              </p>
            </div>
            {!isAdmin && (
              <button
                onClick={() => setShowModal(true)}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition shadow-sm"
              >
                <Plus size={16} /> New Support Request
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[520px]">
            {/* Ticket List Column */}
            <div className="lg:col-span-5 border-r border-slate-200 divide-y divide-slate-100 max-h-[620px] overflow-y-auto">
              {tickets.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-sm">No tickets found.</div>
              ) : (
                tickets.map((t) => (
                  <div
                    key={t.id}
                    onClick={() => loadTicketDetails(t.id)}
                    className={`p-4 cursor-pointer transition border-l-4 ${
                      selectedTicket === t.id
                        ? 'bg-emerald-50/50 border-emerald-600'
                        : 'hover:bg-slate-50 border-transparent'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-semibold text-slate-800 text-sm truncate">{t.subject}</span>
                      <span className="text-xs font-mono text-slate-400">#{t.id}</span>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
                      <span>{t.author_name}</span>
                      <span>&bull;</span>
                      <span>{new Date(t.created_at).toLocaleDateString()}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-100 text-emerald-800">
                        {t.category}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                        t.priority === 'CRITICAL' || t.priority === 'HIGH'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {t.priority}
                      </span>
                      <span className="ml-auto text-[11px] text-slate-500 font-medium">
                        {t.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Ticket Details & Chat Thread Column */}
            <div className="lg:col-span-7 flex flex-col bg-slate-50/50">
              {ticketDetails ? (
                <div className="flex-1 flex flex-col h-full">
                  {/* Ticket Header */}
                  <div className="p-6 bg-white border-b border-slate-200 space-y-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-slate-800 text-lg">{ticketDetails.subject}</h3>
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                            #{ticketDetails.id}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Raised by {ticketDetails.author?.username} ({ticketDetails.author?.email})
                        </p>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                        {ticketDetails.status}
                      </span>
                    </div>

                    {/* AI COPILOT CARD - SIRF ADMIN KO DIKHEGA */}
                    {isAdmin && (
                      <div className="bg-gradient-to-br from-emerald-50 via-teal-50/50 to-white border border-emerald-200 rounded-xl p-4 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Bot className="text-emerald-600" size={18} />
                            <span className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                              BookLeaf AI Copilot (Admin Review)
                            </span>
                          </div>
                          <span className="text-[11px] text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded-full font-medium">
                            Confidence: Verified
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-xs mb-3">
                          <div className="bg-white/80 p-2 rounded-lg border border-emerald-100">
                            <span className="text-slate-400 block text-[10px] uppercase font-bold">Auto Category</span>
                            <span className="font-semibold text-slate-700">{ticketDetails.ai_category || ticketDetails.category}</span>
                          </div>
                          <div className="bg-white/80 p-2 rounded-lg border border-emerald-100">
                            <span className="text-slate-400 block text-[10px] uppercase font-bold">Assessed Priority</span>
                            <span className="font-semibold text-slate-700">{ticketDetails.ai_priority || ticketDetails.priority}</span>
                          </div>
                        </div>

                        {ticketDetails.ai_suggested_response && (
                          <div className="bg-white/90 border border-emerald-100 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-[11px] font-semibold text-emerald-800 flex items-center gap-1">
                                <Sparkles size={12} /> Suggested FAQ Resolution (Draft):
                              </span>
                              <button
                                type="button"
                                onClick={handleAdoptAIResponse}
                                className="text-[11px] font-medium text-emerald-700 hover:text-emerald-900 underline"
                              >
                                Insert into Reply Box
                              </button>
                            </div>
                            <p className="text-xs text-slate-600 italic leading-relaxed">
                              "{ticketDetails.ai_suggested_response}"
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Messages Thread */}
                  <div className="flex-1 p-6 overflow-y-auto space-y-4 max-h-[320px]">
                    {ticketDetails.messages?.map((msg) => {
                      const isMe = msg.sender.username === user.username;
                      return (
                        <div
                          key={msg.id}
                          className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}
                        >
                          <div
                            className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                              isMe
                                ? 'bg-emerald-600 text-white rounded-br-none'
                                : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-4 mb-1 text-xs opacity-80">
                              <span className="font-semibold">{msg.sender.username}</span>
                              <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                            <p className="leading-relaxed whitespace-pre-wrap">{msg.message}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Reply Input Box */}
                  <div className="p-4 bg-white border-t border-slate-200">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                      <input
                        type="text"
                        value={replyMessage}
                        onChange={(e) => setReplyMessage(e.target.value)}
                        placeholder={isAdmin ? "Type your reply or adopt AI draft above..." : "Type your message..."}
                        className="flex-1 px-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none text-slate-800"
                      />
                      <button
                        type="submit"
                        disabled={sendingReply}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-lg text-sm font-medium flex items-center gap-1 transition disabled:opacity-50"
                      >
                        <Send size={16} /> {sendingReply ? 'Sending...' : 'Send'}
                      </button>
                    </form>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-400 text-sm">
                  <Bot size={36} className="text-slate-300 mb-2" />
                  Select a ticket from the left to view conversation.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Books Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100">
            <h2 className="font-bold text-slate-800 text-lg">Author Portfolio & Royalties</h2>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase">
                <th className="py-3 px-6">Title</th>
                {isAdmin && <th className="py-3 px-6">Author</th>}
                <th className="py-3 px-6">Genre</th>
                <th className="py-3 px-6">ISBN</th>
                <th className="py-3 px-6">Status</th>
                <th className="py-3 px-6 text-right">Units Sold</th>
                <th className="py-3 px-6 text-right">Pending Royalty</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {books.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50">
                  <td className="py-4 px-6 font-medium text-slate-800">{b.title}</td>
                  {isAdmin && <td className="py-4 px-6 text-slate-600">{b.author_name}</td>}
                  <td className="py-4 px-6 text-slate-600">{b.genre}</td>
                  <td className="py-4 px-6 text-slate-500 font-mono text-xs">{b.isbn}</td>
                  <td className="py-4 px-6">
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700">
                      {b.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right font-medium">{b.sales_count}</td>
                  <td className="py-4 px-6 text-right font-semibold text-emerald-600">₹{b.royalty_pending}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {/* Ticket Creation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="text-emerald-600" size={20} />
              <h3 className="text-lg font-bold text-slate-800">Raise Support Ticket</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Submit your query regarding royalties, publishing status, or distribution.
            </p>

            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="e.g. Discrepancy in monthly royalty payout"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  rows={4}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Provide context on your query..."
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border rounded-lg text-sm hover:bg-slate-50 text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 font-medium disabled:opacity-50 flex items-center gap-2"
                >
                  <Sparkles size={14} />
                  {submitting ? 'Analyzing & Submitting...' : 'Submit Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}