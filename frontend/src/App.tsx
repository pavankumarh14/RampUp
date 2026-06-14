import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import IngestView from './components/IngestView';
import GapsView from './components/GapsView';
import { View } from './types';
import { healthCheck } from './api';

export default function App() {
  const [view, setView] = useState<View>('chat');
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);

  useEffect(() => {
    healthCheck().then(setServerOnline);
    const id = setInterval(() => healthCheck().then(setServerOnline), 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      <Sidebar view={view} onViewChange={setView} serverOnline={serverOnline} />
      <main className="flex-1 min-w-0 overflow-hidden">
        {view === 'chat' && <ChatView />}
        {view === 'ingest' && <IngestView />}
        {view === 'gaps' && <GapsView />}
      </main>
    </div>
  );
}
