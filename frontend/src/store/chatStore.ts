import { create } from "zustand";
import { fetchChatById, fetchChats, createChat as createChatApi, sendMessage as sendMessageApi } from "@/lib/api";
import type { ChatSession, ChatResponse } from "@/types/chat";

type ThemeMode = "light" | "dark";

interface ChatState {
  chats: Record<string, ChatSession>;
  chatOrder: string[];
  activeChatId: string | null;
  loading: boolean;
  error: string | null;
  theme: ThemeMode;
  fetchChats: () => Promise<void>;
  createChat: (title?: string) => Promise<void>;
  selectChat: (chatId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<ChatResponse | null>;
  toggleTheme: () => void;
}

function detectTheme(): ThemeMode {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem("market-mind-theme") as ThemeMode | null;
  if (stored) return stored;
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  return prefersDark ? "dark" : "light";
}

function applyTheme(theme: ThemeMode) {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", theme === "dark");
  document.documentElement.setAttribute("data-theme", theme);
  window.localStorage.setItem("market-mind-theme", theme);
}

export const useChatStore = create<ChatState>((set, get) => ({
  chats: {},
  chatOrder: [],
  activeChatId: null,
  loading: false,
  error: null,
  theme: detectTheme(),

  fetchChats: async () => {
    set({ loading: true, error: null });
    try {
      const chats = await fetchChats();
      set({
        chats: chats.reduce<Record<string, ChatSession>>((acc, chat) => {
          acc[chat.id] = { ...chat, messages: chat.messages ?? [] };
          return acc;
        }, {}),
        chatOrder: chats.map((chat) => chat.id),
        loading: false
      });
    } catch (error) {
      set({ error: "Unable to fetch chats. Please try again.", loading: false });
    }
  },

  createChat: async (title?: string) => {
    set({ loading: true, error: null });
    try {
      const chat = await createChatApi(title);
      const updatedOrder = [chat.id, ...get().chatOrder.filter((id) => id !== chat.id)];
      set((state) => ({
        chats: {
          ...state.chats,
          [chat.id]: { ...chat, messages: [] }
        },
        chatOrder: updatedOrder,
        activeChatId: chat.id,
        loading: false
      }));
      await get().selectChat(chat.id);
    } catch (error) {
      set({ error: "Failed to create chat. Please retry.", loading: false });
    }
  },

  selectChat: async (chatId: string) => {
    set({ activeChatId: chatId, error: null });
    const chat = get().chats[chatId];
    if (chat && chat.messages && chat.messages.length > 0) {
      return;
    }
    try {
      const detailed = await fetchChatById(chatId);
      set((state) => ({
        chats: {
          ...state.chats,
          [chatId]: { ...state.chats[chatId], ...detailed }
        }
      }));
    } catch (error) {
      set({ error: "Unable to load conversation history." });
    }
  },

  sendMessage: async (content: string) => {
    const chatId = get().activeChatId;
    if (!chatId) {
      set({ error: "Please select or create a chat first." });
      return null;
    }
    if (!content.trim()) {
      return null;
    }
    set({ loading: true, error: null });
    try {
      const response = await sendMessageApi(chatId, content);
      set((state) => {
        const existing = state.chats[chatId]?.messages ?? [];
        const updatedChat: ChatSession = {
          ...state.chats[chatId],
          messages: [...existing, response.message, response.ai_response],
          updated_at: response.ai_response.created_at
        };
        return {
          chats: {
            ...state.chats,
            [chatId]: updatedChat
          },
          loading: false
        };
      });
      return response;
    } catch (error) {
      set({ error: "Failed to send message. Please try again.", loading: false });
      return null;
    }
  },

  toggleTheme: () => {
    const nextTheme: ThemeMode = get().theme === "light" ? "dark" : "light";
    applyTheme(nextTheme);
    set({ theme: nextTheme });
  }
}));

// Apply persisted theme on load.
applyTheme(detectTheme());
