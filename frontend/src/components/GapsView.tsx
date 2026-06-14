import { useState, useEffect } from 'react';
import { AlertCircle, RefreshCw, CheckCircle } from 'lucide-react';
import { listKnowledgeGaps } from '../api';
import type { KnowledgeGap } from '../types';

export default function GapsView() {
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  const [loading, setLoading] = useState(false);
  const [showResolved, setShowResolved] = useState(false);

  const loadGaps = async () => {
    setLoading(true);
    try {
      const data = await listKnowledgeGaps(showResolved);
      setGaps(data);
    } catch (err) {
      console.error("Failed to load knowledge gaps:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGaps();
  }, [showResolved]);

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
      <div className="px-8 py-6 bg-white border-b border-slate-100 shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-black text-slate-900">Knowledge Gaps</h1>
          <p className="text-sm text-slate-400 mt-1">
            Questions the system couldn't answer — perfect for prioritizing new content!
          </p>
        </div>
        <button
          onClick={loadGaps}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border-2 border-slate-200 bg-slate-50 text-sm font-bold text-slate-600 hover:border-[#0D9488] hover:text-[#0D9488] hover:bg-teal-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="px-8 py-4 border-b border-slate-100">
        <label className="flex items-center gap-2 text-sm font-bold text-slate-600">
          <input
            type="checkbox"
            checked={showResolved}
            onChange={e => setShowResolved(e.target.checked)}
            className="rounded border-slate-300 text-[#0D9488] focus:ring-[#0D9488]"
          />
          Show resolved gaps
        </label>
      </div>

      <div className="p-8 space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw size={24} className="animate-spin text-[#0D9488]" />
          </div>
        ) : gaps.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle size={48} className="text-emerald-500 mb-4" />
            <h3 className="text-lg font-black text-slate-900 mb-1">No knowledge gaps!</h3>
            <p className="text-sm text-slate-400">
              The system is answering all questions confidently.
            </p>
          </div>
        ) : (
          gaps.map(gap => (
            <div
              key={gap.id}
              className="flex items-start gap-4 p-5 bg-white border border-slate-200 rounded-2xl shadow-sm"
            >
              <AlertCircle size={24} className="text-amber-500 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-base font-semibold text-slate-800 leading-relaxed">
                  {gap.query_text}
                </p>
                <div className="mt-2 flex items-center gap-4 text-xs text-slate-400 font-bold">
                  <span>Reported {new Date(gap.reported_at).toLocaleString()}</span>
                  {gap.resolved ? (
                    <span className="flex items-center gap-1 text-emerald-600">
                      <CheckCircle size={12} />
                      Resolved
                    </span>
                  ) : null}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
