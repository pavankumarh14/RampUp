export type View = 'chat' | 'ingest' | 'gaps';

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  text: string;
  sources?: string[];
  confidence?: string;
  isTyping?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  confidence: string;
}

export interface IngestResponse {
  status: string;
  message: string;
  num_chunks?: number;
}

export interface KnowledgeGap {
  id: string;
  query_text: string;
  topic_category: string | null;
  reported_at: string;
  resolved: boolean;
}
