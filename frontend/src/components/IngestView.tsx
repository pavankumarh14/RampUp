import { useState } from 'react';
import { Upload, CheckCircle, XCircle, FileText } from 'lucide-react';
import { ingestDocument } from '../api';

type Status = { type: 'success' | 'error'; message: string } | null;

const SOURCES = [
  { icon: '📄', name: 'SharePoint',        label: 'Connected via MS Graph',    ok: true  },
  { icon: '💬', name: 'Teams Transcripts', label: 'Placeholder – OAuth needed', ok: false },
  { icon: '📓', name: 'OneNote',           label: 'Placeholder – OAuth needed', ok: false },
];

export default function IngestView() {
  // Manual text ingest
  const [manualText, setManualText] = useState('');
  const [manualTitle, setManualTitle] = useState('');
  const [manualUrl, setManualUrl] = useState('');
  // Synthetic data ingest
  const [sourceType, setSourceType] = useState<'sharepoint' | 'teams'>('sharepoint');
  const [siteId, setSiteId] = useState('');

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Status>(null);

  const handleIngestText = async () => {
    if (!manualText.trim()) return;
    setLoading(true);
    setStatus(null);
    try {
      const data = await ingestDocument(
        manualUrl.trim() || undefined,
        manualTitle.trim() || undefined,
        manualText.trim()
      );
      setStatus({ type: 'success', message: data.message || 'Document ingested successfully!' });
      setManualText('');
      setManualTitle('');
      setManualUrl('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setStatus({ type: 'error', message: msg });
    } finally {
      setLoading(false);
    }
  };

  const handleIngestSynthetic = async () => {
    if (!siteId.trim()) return;
    setLoading(true);
    setStatus(null);
    try {
      const data = await ingestDocument(
        undefined,
        undefined,
        undefined,
        sourceType,
        siteId.trim()
      );
      setStatus({ type: 'success', message: data.message || 'Synthetic data ingested successfully!' });
      setSiteId('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setStatus({ type: 'error', message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
      <div className="px-8 py-6 bg-white border-b border-slate-100 shrink-0">
        <h1 className="text-lg font-black text-slate-900">Upload Documents</h1>
        <p className="text-sm text-slate-400 mt-1">
          Add content to the knowledge base via manual text or synthetic M365 data.
        </p>
      </div>

      <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6 max-w-6xl">
        {/* Manual text ingest */}
        <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm">
          <div className="text-3xl mb-3">✏️</div>
          <h3 className="font-black text-slate-900 text-base mb-1">Ingest from Text</h3>
          <p className="text-sm text-slate-400 mb-5">
            Paste text directly or add a document title and URL.
          </p>
          <div className="flex flex-col gap-3">
            <input
              type="text"
              value={manualTitle}
              onChange={e => setManualTitle(e.target.value)}
              placeholder="Document title (optional)"
              className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 focus:border-[#0D9488] bg-slate-50 focus:bg-white text-sm font-semibold outline-none transition-colors"
            />
            <input
              type="text"
              value={manualUrl}
              onChange={e => setManualUrl(e.target.value)}
              placeholder="Document URL (optional)"
              className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 focus:border-[#0D9488] bg-slate-50 focus:bg-white text-sm font-semibold outline-none transition-colors"
            />
            <textarea
              value={manualText}
              onChange={e => setManualText(e.target.value)}
              placeholder="Paste your document text here..."
              rows={8}
              className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 focus:border-[#0D9488] bg-slate-50 focus:bg-white text-sm font-semibold outline-none transition-colors resize-none"
            />
            <button
              onClick={handleIngestText}
              disabled={!manualText.trim() || loading}
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-gradient-to-r from-[#1E3A5F] to-[#0D9488] text-white text-sm font-bold shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileText size={15} />
              {loading ? 'Ingesting...' : 'Ingest Text'}
            </button>
          </div>
        </div>

        {/* Synthetic M365 data ingest */}
        <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm">
          <div className="text-3xl mb-3">📊</div>
          <h3 className="font-black text-slate-900 text-base mb-1">Synthetic M365 Data</h3>
          <p className="text-sm text-slate-400 mb-5">
            Load sample SharePoint or Teams data into the knowledge base.
          </p>
          <div className="flex flex-col gap-3">
            <select
              value={sourceType}
              onChange={e => setSourceType(e.target.value as 'sharepoint' | 'teams')}
              className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 focus:border-[#0D9488] bg-slate-50 focus:bg-white text-sm font-semibold outline-none transition-colors"
            >
              <option value="sharepoint">SharePoint</option>
              <option value="teams">Teams</option>
            </select>
            <input
              type="text"
              value={siteId}
              onChange={e => setSiteId(e.target.value)}
              placeholder="Site/Team ID (any string for demo)"
              className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 focus:border-[#0D9488] bg-slate-50 focus:bg-white text-sm font-semibold outline-none transition-colors"
            />
            <button
              onClick={handleIngestSynthetic}
              disabled={!siteId.trim() || loading}
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-gradient-to-r from-[#0D9488] to-[#14B8A6] text-white text-sm font-bold shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Upload size={15} />
              {loading ? 'Ingesting...' : 'Load Sample Data'}
            </button>
          </div>
        </div>

        {/* Connected sources (info) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm md:col-span-2">
          <div className="text-3xl mb-3">📂</div>
          <h3 className="font-black text-slate-900 text-base mb-1">Connected Sources</h3>
          <p className="text-sm text-slate-400 mb-5">
            Document sources available for indexing.
          </p>
          <div className="flex flex-wrap gap-3">
            {SOURCES.map(src => (
              <div
                key={src.name}
                className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200"
              >
                <span className="text-xl">{src.icon}</span>
                <div>
                  <p className="text-sm font-bold text-slate-700">{src.name}</p>
                  <p className={`text-xs font-semibold ${src.ok ? 'text-emerald-600' : 'text-slate-400'}`}>
                    {src.label}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {status && (
        <div className={`mx-8 mb-8 flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold ${status.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'}`}>
          {status.type === 'success' ? <CheckCircle size={15} className="shrink-0" /> : <XCircle size={15} className="shrink-0" />}
          {status.message}
        </div>
      )}
    </div>
  );
}
