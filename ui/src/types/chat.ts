export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: DocumentSource[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface DocumentSource {
  id: string;
  title: string;
  snippet?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatResponse {
  answer: string;
  sources: DocumentSource[];
}

export interface SearchResult {
  id: string;
  item_uuid?: string;
  title: string;
  snippet?: string;
  score?: number;
  author?: string;
  year?: string;
  type?: string;
}

export interface AutocompleteResult {
  id: string;
  title: string;
}

export interface SearchFilters {
  type?: string;
  yearFrom?: string;
  yearTo?: string;
  author?: string;
}
