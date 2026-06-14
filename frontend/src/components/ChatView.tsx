import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { ChatMessage } from '../types';
import { queryKnowledge } from '../api';

const SUGGESTED_QUESTIONS = [
  'What is the engineering team structure?',
  'How do I set up my development environment?',
  'What is the PTO and leave policy?',
  'Who should I contact about IT issues?',
];

const CONFIDENCE_STYLES: Record<string, string> = {
  high: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  medium: 'bg-amber-50 text-amber-700 border-amber-200',
  low: 'bg-red-50 text-red-600 border-red-200',
  not_found: 'bg-red-50 text-red-600 border-red-200',
};

function Avatar({ label, teal }: { label: string; teal?: boolean }) {
  return (
    <div
      className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-[11px] font-black shrink-0 ${
        teal ? 'bg-gradient-to-br from-[#0D9488] to-[#14B8A6]' : 'bg-gradient-to-br from-[#1E3A5F] to-[#0D9488]'
      }`}
    >
      {label}
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex gap-3 items-end">
      <Avatar label="RU" />
      <div className="bg-white border border-slate-200 rounded-tl-none rounded-2xl shadow-sm px-5 py-4">
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-slate-300 animate-bounce-dot"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const resizeTextarea = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const send = async (text = input) => {
    const question = text.trim();
    if (!question || busy) return;

    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    const userMsg: ChatMessage = { id: `u-${Date.now()}`, role: 'user', text: question };
    const typingMsg: ChatMessage = { id: 'typing', role: 'ai', text: '', isTyping: true };
    setMessages(prev => [...prev, userMsg, typingMsg]);
    setBusy(true);

    try {
      const data = await queryKnowledge(question);
      setMessages(prev =>
        prev
          .filter(m => m.id !== 'typing')
          .concat({
            id: `a-${Date.now()}`,
            role: 'ai',
            text: data.answer,
            sources: data.sources,
            confidence: data.confidence,
          }),
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setMessages(prev =>
        prev.filter(m => m.id !== 'typing').concat({
          id: `a-${Date.now()}`,
          role: 'ai',
          text: `Could not reach the API: ${msg}\n\nStart the backend:\n  uv run uvicorn app.main:app --reload`,
          confidence: 'not_found',
        }),
      );
    } finally {
      setBusy(false);
    }
  };

  const confClass = (conf: string) =>
    CONFIDENCE_STYLES[conf.toLowerCase().replace(/\s/g, '_')] ||
    'bg-slate-100 text-slate-500 border-slate-200';

  return (
    <div className="flex flex-col h-full bg-slate-50">
      <div className="flex items-start justify-between px-7 py-5 bg-white border-b border-slate-100 shrink-0">
        <div>
          <h1 className="text-lg font-black text-slate-900">Ask Your Knowledge Base</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Source-cited answers from SharePoint, Teams, and OneNote
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="text-xs font-bold text-slate-400 hover:text-slate-700 border border-slate-200 hover:border-slate-300 px-3 py-1.5 rounded-xl transition-colors"
          >
            Clear chat
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-7 py-6 flex flex-col gap-5">
        {messages.length === 0 && (
          <div className="flex gap-3 items-start">
            <Avatar label="RU" />
            <div className="bg-white border border-slate-200 rounded-tl-none rounded-2xl shadow-sm p-5 max-w-xl">
              <p className="text-sm text-slate-600 leading-relaxed">
                Hi there! 👋 I'm your onboarding assistant. Ask me anything about company
                policies, processes, team structures, or tools — I'll answer with citations
                from your company's indexed documents.
              </p>
              <div className="mt-4">
                <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">
                  Try asking
                </p>
                <div className="flex flex-col gap-2">
                  {SUGGESTED_QUESTIONS.map(q => (
                    <button
                      key={q}
                      onClick={() => send(q)}
                      className="text-left text-sm font-semibold text-slate-600 px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:border-[#0D9488] hover:text-[#0D9488] hover:bg-teal-50 transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map(msg => {
          if (msg.isTyping) return <TypingBubble key="typing" />;

          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="flex gap-3 items-end flex-row-reverse">
                <Avatar label="You" teal />
                <div className="bg-[#1E3A5F] text-white rounded-tr-none rounded-2xl shadow-sm px-4 py-3 max-w-[65%] text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </div>
              </div>
            );
          }

          return (
            <div key={msg.id} className="flex gap-3 items-start">
              <Avatar label="RU" />
              <div className="bg-white border border-slate-200 rounded-tl-none rounded-2xl shadow-sm px-5 py-4 max-w-[72%]">
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </p>

                {msg.confidence && (
                  <span
                    className={`inline-flex items-center mt-2.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${confClass(
                      msg.confidence
                    )}`}
                  >
                    {msg.confidence}
                  </span>
                )}

                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">
                      Sources
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.sources.map((s, i) => (
                        <a
                          key={i}
                          href={s.startsWith('http') ? s : undefined}
                          target={s.startsWith('http') ? '_blank' : undefined}
                          rel={s.startsWith('http') ? 'noopener noreferrer' : undefined}
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[11px] font-semibold text-slate-500 ${s.startsWith('http') ? 'hover:bg-slate-200 cursor-pointer' : ''}`}
                        >
                          📄 {s.length > 60 ? `${s.slice(0, 60)}…` : s}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>

      <div className="px-7 py-4 bg-white border-t border-slate-100 shrink-0">
        <div className="flex items-end gap-3 bg-slate-50 border-2 border-slate-200 focus-within:border-[#0D9488] focus-within:bg-white rounded-2xl px-4 py-3 transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            rows={1}
            placeholder="Ask anything about your company…"
            className="flex-1 bg-transparent text-sm text-slate-800 placeholder:text-slate-400 resize-none outline-none leading-relaxed max-h-28 overflow-y-auto"
            onChange={e => {
              setInput(e.target.value);
              resizeTextarea();
            }}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || busy}
            className="w-9 h-9 shrink-0 rounded-xl flex items-center justify-center transition-all bg-[#1E3A5F] text-white hover:bg-[#0D9488] disabled:bg-slate-200 disabled:cursor-not-allowed"
          >
            <Send size={15} />
          </button>
        </div>
        <p className="text-[11px] text-slate-400 text-center mt-2 font-semibold">
          Answers grounded in company documents.
          <span className="text-amber-500"> Unanswered questions are logged as knowledge gaps.</span>
        </p>
      </div>
    </div>
  );
}
