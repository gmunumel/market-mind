import axios from "axios";
import type { ChatResponse, ChatSession } from "@/types/chat";
import { getUserId } from "./user";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 15000
});

api.interceptors.request.use((config) => {
  const userId = getUserId();
  config.headers = config.headers ?? {};
  config.headers["X-User-Id"] = userId;
  return config;
});

export async function fetchChats(): Promise<ChatSession[]> {
  const { data } = await api.get<ChatSession[]>("/chats");
  return data;
}

export async function fetchChatById(chatId: string): Promise<ChatSession> {
  const { data } = await api.get<ChatSession>(`/chats/${chatId}`);
  return data;
}

export async function createChat(title?: string): Promise<ChatSession> {
  const { data } = await api.post<ChatSession>("/chats", { title });
  return data;
}

export async function sendMessage(chatId: string, content: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>(`/chats/${chatId}/messages`, { content });
  return data;
}
