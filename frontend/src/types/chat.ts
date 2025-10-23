export type MessageRole = "user" | "assistant";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  metadata?: Record<string, unknown> | null;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface ChatResponse {
  message: Message;
  ai_response: Message;
}
