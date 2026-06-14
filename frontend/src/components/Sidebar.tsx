import { MessageSquare, Upload, AlertCircle } from 'lucide-react';
import { View } from '../types';

interface Props {
  view: View;
  onViewChange: (v: View) => void;
  serverOnline: boolean | null;
}

const NAV_ITEMS = [
  { id: 'chat' as View, label: 'Ask Anything', Icon: MessageSquare },
  { id: 'ingest' as View, label: 'Upload Docs', Icon: Upload },
  { id: 'gaps' as View, label: 'Knowledge Gaps', Icon: AlertCircle },
];

export default function Sidebar({ view, onViewChange, serverOnline }: Props) {
  return (
    <aside className="w-56 flex-shrink-0 flex flex-col bg-[#1E3A5F] text-white select-none">
      <div className="px-4 py-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#0D9488] to-[#14B8A6] flex items-center justify-center text-sm font-black shrink-0">
            RU
          </div>
          <div>
            <p className="font-black text-[15px] leading-tight">RampUp</p>
            <p className="text-[11px] text-white/40 leading-tight">Knowledge Hub</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 flex flex-col gap-1">
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => onViewChange(id)}
            className={`flex items-center gap-2.5 w-full px-3 py-2.5 rounded-xl text-sm font-bold transition-all duration-150 text-left ${
              view === id
                ? 'bg-white/15 text-white'
                : 'text-white/50 hover:bg-white/10 hover:text-white/80'
            }`}
          >
            <Icon size={16} className="shrink-0" />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full shrink-0 transition-colors ${
              serverOnline === true
                ? 'bg-emerald-400 shadow-[0_0_0_3px_rgba(52,211,153,0.25)]'
                : 'bg-white/25'
            }`}
          />
          <span className="text-xs text-white/40 font-semibold">
            {serverOnline === null ? 'Checking server…' : serverOnline ? 'API online' : 'API offline'}
          </span>
        </div>
      </div>
    </aside>
  );
}
