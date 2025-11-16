'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

type ContentEvent = {
  id: string;
  title: string;
  content_type: string;
  scheduled_date: string;
  status: string;
  platform?: string;
  content?: string;
  media_url?: string;
};

const platformConfig = {
  instagram: { icon: '', color: 'from-gold-intense to-cobalt', name: 'Instagram' },
  linkedin: { icon: '', color: 'from-cobalt to-cobalt-700', name: 'LinkedIn' },
  facebook: { icon: '', color: 'from-cobalt to-cobalt-600', name: 'Facebook' },
  x: { icon: '', color: 'from-slate-800 to-slate-900', name: 'X' },
  tiktok: { icon: '', color: 'from-royal-900 to-cobalt', name: 'TikTok' },
  youtube: { icon: '', color: 'from-red-600 to-red-700', name: 'YouTube' },
  reddit: { icon: '', color: 'from-gold-intense to-red-500', name: 'Reddit' },
  tumblr: { icon: '', color: 'from-cobalt to-royal', name: 'Tumblr' },
};

export default function ContentCalendar() {
  const router = useRouter();
  const [events, setEvents] = useState<ContentEvent[]>([]);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [publishingEventId, setPublishingEventId] = useState<string | null>(null);
  const [publishingAll, setPublishingAll] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    content_type: 'text',
    status: 'draft',
    platform: 'instagram',
    content: ''
  });

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await api.get('/calendar/events');
      setEvents(data.events || []);
    } catch (err: unknown) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const newEvent = {
      id: Date.now().toString(),
      ...formData,
      scheduled_date: selectedDate?.toISOString() || new Date().toISOString()
    };

    try {
      const res = await api.post(`/calendar/events`, newEvent);
      
      if (res.ok) {
        await loadEvents();
        setShowAddModal(false);
        setFormData({ title: '', content_type: 'text', status: 'draft', platform: 'instagram', content: '' });
      }
    } catch (err) {
      console.error('Failed to create event');
    }
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }
    return days;
  };

  const getEventsForDate = (date: Date | null) => {
    if (!date) return [];
    const dateStr = date.toISOString().split('T')[0];
    return events.filter(e => e.scheduled_date.startsWith(dateStr));
  };

  const handleDateClick = (date: Date | null) => {
    if (date) {
      setSelectedDate(date);
      setShowAddModal(true);
    }
  };

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const days = getDaysInMonth(currentMonth);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-gold-600/80';
      case 'scheduled': return 'bg-cobalt/80';
      case 'draft': return 'bg-gold-600/80';
      default: return 'bg-gray-600/80';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'blog': return '';
      case 'video': return '';
      case 'carousel': return '';
      case 'text': return '';
      default: return '';
    }
  };

  const getPlatformIcon = (platform?: string) => {
    if (!platform) return '';
    return platformConfig[platform as keyof typeof platformConfig]?.icon || '';
  };

  const handlePublishEvent = async (eventId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent calendar date click

    if (publishingEventId) return; // Already publishing

    if (!confirm('Publish this event immediately?')) return;

    setPublishingEventId(eventId);
    try {
      const response = await api.post(`/calendar/events/${eventId}/publish`, {});

      if (response.success) {
        alert(`✅ ${response.message || 'Published successfully!'}\n${response.post_url || ''}`);
        await loadEvents(); // Reload to get updated status
      } else {
        alert(`❌ Failed to publish: ${response.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Publish error:', err);
      alert('❌ Failed to publish event');
    } finally {
      setPublishingEventId(null);
    }
  };

  const handlePublishAllDue = async () => {
    if (publishingAll) return; // Already publishing

    const dueEvents = events.filter(e =>
      e.status === 'scheduled' &&
      new Date(e.scheduled_date) <= new Date()
    );

    if (dueEvents.length === 0) {
      alert('No due events to publish');
      return;
    }

    if (!confirm(`Publish ${dueEvents.length} due event(s) now?`)) return;

    setPublishingAll(true);
    try {
      const response = await api.post('/calendar/publish-all-due', {});

      if (response.success) {
        const summary = response.summary;
        alert(
          `✅ Bulk Publish Complete!\n\n` +
          `Published: ${summary.published}\n` +
          `Failed: ${summary.failed}\n` +
          `Total: ${summary.total}`
        );
        await loadEvents(); // Reload calendar
      } else {
        alert(`❌ Bulk publish failed: ${response.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Bulk publish error:', err);
      alert('❌ Failed to publish events');
    } finally {
      setPublishingAll(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-4 sm:p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <div>
            <Link href="/dashboard" className="text-gold hover:text-cobalt-300 mb-2 inline-block text-sm">
              ← Back to Dashboard
            </Link>
            <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
              Content Calendar
            </h1>
            <p className="text-cobalt-300 mt-2">Plan and schedule ORLA³-created content across all platforms</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handlePublishAllDue}
              disabled={publishingAll}
              className="bg-gradient-to-r from-royal to-cobalt hover:from-royal-700 hover:to-cobalt-700 disabled:from-gray-500 disabled:to-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-lg transition-all flex items-center gap-2"
            >
              {publishingAll ? 'Publishing...' : 'Publish All Due'}
            </button>
            <button
              onClick={() => router.push('/dashboard/social')}
              className="bg-gradient-to-r from-cobalt to-royal-700 hover:from-cobalt-700 hover:to-royal text-white font-bold py-3 px-6 rounded-lg transition-all"
            >
              Create in Social Manager
            </button>
            <button
              onClick={() => {
                setSelectedDate(new Date());
                setShowAddModal(true);
              }}
              className="bg-gradient-to-r from-gold to-gold-600 hover:from-gold-600 hover:to-gold-700 text-black font-bold py-3 px-6 rounded-lg transition-all"
            >
              Quick Add
            </button>
          </div>
        </div>

        {/* Calendar */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/10 mb-3 sm:mb-4 md:mb-6">
          <div className="flex items-center justify-between mb-3 sm:mb-4 md:mb-6">
            <button
              onClick={previousMonth}
              className="bg-white/10 hover:bg-white/20 text-white font-bold py-2 px-3 sm:px-4 rounded-lg transition-all"
            >
              ← Previous
            </button>
            <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white">
              {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
            </h2>
            <button
              onClick={nextMonth}
              className="bg-white/10 hover:bg-white/20 text-white font-bold py-2 px-3 sm:px-4 rounded-lg transition-all"
            >
              Next →
            </button>
          </div>

          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-2 mb-2">
            {dayNames.map(day => (
              <div key={day} className="text-center text-cobalt-300 font-bold text-sm py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-2">
            {days.map((day, index) => {
              const dayEvents = getEventsForDate(day);
              const isToday = day && day.toDateString() === new Date().toDateString();
              
              return (
                <div
                  key={index}
                  onClick={() => handleDateClick(day)}
                  className={`min-h-32 p-2 rounded-lg border transition-all ${
                    day
                      ? isToday
                        ? 'bg-royal-900/30 border-cobalt cursor-pointer hover:bg-royal-900/40'
                        : 'bg-white/5 border-white/10 cursor-pointer hover:bg-white/10 hover:border-cobalt/30'
                      : 'bg-transparent border-transparent'
                  }`}
                >
                  {day && (
                    <>
                      <div className={`text-sm font-bold mb-2 ${isToday ? 'text-gold' : 'text-white'}`}>
                        {day.getDate()}
                      </div>
                      <div className="space-y-1">
                        {dayEvents.slice(0, 3).map(event => (
                          <div
                            key={event.id}
                            className={`text-xs p-1.5 rounded ${getStatusColor(event.status)} text-white truncate flex items-center gap-1 group relative`}
                            title={`${event.title} - ${event.platform}`}
                          >
                            <span>{getPlatformIcon(event.platform)}</span>
                            <span>{getTypeIcon(event.content_type)}</span>
                            <span className="flex-1 truncate">{event.title}</span>
                            {event.status === 'scheduled' && (
                              <button
                                onClick={(e) => handlePublishEvent(event.id, e)}
                                disabled={publishingEventId === event.id}
                                className="opacity-0 group-hover:opacity-100 bg-white/20 hover:bg-white/30 disabled:bg-gray-500/50 disabled:cursor-not-allowed px-1.5 py-0.5 rounded text-xs font-semibold transition-all"
                                title="Publish now"
                              >
                                {publishingEventId === event.id ? '⏳' : '▶'}
                              </button>
                            )}
                          </div>
                        ))}
                        {dayEvents.length > 3 && (
                          <div className="text-xs text-gold font-semibold">
                            +{dayEvents.length - 3} more
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4">
          <div className="bg-gold-600/40 border border-gold/30 rounded-xl p-3 sm:p-4">
            <h3 className="text-white font-bold mb-2">Published</h3>
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-gold">
              {events.filter(e => e.status === 'published').length}
            </p>
          </div>
          <div className="bg-royal-900/40 border border-cobalt-400/30 rounded-xl p-3 sm:p-4">
            <h3 className="text-white font-bold mb-2">Scheduled</h3>
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-cobalt-300">
              {events.filter(e => e.status === 'scheduled').length}
            </p>
          </div>
          <div className="bg-gold-900/40 border border-gold-400/30 rounded-xl p-3 sm:p-4">
            <h3 className="text-white font-bold mb-2">Drafts</h3>
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-gold-400">
              {events.filter(e => e.status === 'draft').length}
            </p>
          </div>
          <div className="bg-royal-900/40 border border-cobalt-400/30 rounded-xl p-3 sm:p-4">
            <h3 className="text-white font-bold mb-2">Total</h3>
            <p className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-gold">
              {events.length}
            </p>
          </div>
        </div>
      </div>

      {/* Add Event Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 sm:p-6 md:p-8" onClick={() => setShowAddModal(false)}>
          <div className="bg-slate-900 rounded-2xl border border-white/20 max-w-2xl w-full p-4 sm:p-6 md:p-8" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3 sm:mb-4 md:mb-6">Quick Add to Calendar</h3>
            <p className="text-gray-400 mb-3 sm:mb-4 md:mb-6">
              {selectedDate?.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
            
            <form onSubmit={handleSubmit} className="space-y-2 sm:space-y-3 md:space-y-4">
              <div>
                <label className="block text-white font-bold mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-3 sm:px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cobalt"
                  placeholder="e.g., Morning motivation post"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 md:gap-4">
                <div>
                  <label className="block text-white font-bold mb-2">Content Type</label>
                  <select
                    value={formData.content_type}
                    onChange={(e) => setFormData({...formData, content_type: e.target.value})}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 sm:px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cobalt"
                  >
                    <option value="text">Text Post</option>
                    <option value="video">Video</option>
                    <option value="carousel">Carousel</option>
                    <option value="blog">Blog</option>
                  </select>
                </div>

                <div>
                  <label className="block text-white font-bold mb-2">Platform</label>
                  <select
                    value={formData.platform}
                    onChange={(e) => setFormData({...formData, platform: e.target.value})}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 sm:px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cobalt"
                  >
                    <option value="instagram">Instagram</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="facebook">Facebook</option>
                    <option value="x">X</option>
                    <option value="tiktok">TikTok</option>
                    <option value="youtube">YouTube</option>
                    <option value="reddit">Reddit</option>
                    <option value="tumblr">Tumblr</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-white font-bold mb-2">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-3 sm:px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cobalt"
                >
                  <option value="draft">Draft</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="published">Published</option>
                </select>
              </div>

              <div>
                <label className="block text-white font-bold mb-2">Content (Optional)</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-3 sm:px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-cobalt h-32 resize-none"
                  placeholder="Add your caption or content here..."
                />
              </div>

              <div className="flex gap-2 sm:gap-3 md:gap-4">
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 text-white font-bold py-3 px-6 rounded-lg transition-all"
                >
                  Add to Calendar
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 bg-white/10 hover:bg-white/20 text-white font-bold py-3 px-6 rounded-lg transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
