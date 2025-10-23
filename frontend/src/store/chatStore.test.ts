import { act } from "react-dom/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useChatStore } from "./chatStore";

const mockFetchChats = vi.fn();
const mockFetchChatById = vi.fn();
const mockCreateChat = vi.fn();
const mockSendMessage = vi.fn();

vi.mock("@/lib/api", () => ({
  fetchChats: () => mockFetchChats(),
  fetchChatById: (chatId: string) => mockFetchChatById(chatId),
  createChat: (title?: string) => mockCreateChat(title),
  sendMessage: (chatId: string, content: string) => mockSendMessage(chatId, content)
}));

describe("chat store", () => {
  beforeEach(() => {
    useChatStore.setState({
      chats: {},
      chatOrder: [],
      activeChatId: null,
      loading: false,
      error: null,
      theme: "light"
    });
    mockFetchChats.mockReset();
    mockFetchChatById.mockReset();
    mockCreateChat.mockReset();
    mockSendMessage.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("loads chats from the API", async () => {
    mockFetchChats.mockResolvedValueOnce([
      {
        id: "1",
        title: "USD Liquidity",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        messages: []
      }
    ]);

    await act(async () => {
      await useChatStore.getState().fetchChats();
    });

    const state = useChatStore.getState();
    expect(state.chatOrder).toEqual(["1"]);
    expect(state.chats["1"].title).toBe("USD Liquidity");
  });

  it("creates a chat and sets it active", async () => {
    mockCreateChat.mockResolvedValueOnce({
      id: "2",
      title: "BTC",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
      messages: []
    });
    mockFetchChatById.mockResolvedValueOnce({
      id: "2",
      title: "BTC",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
      messages: []
    });

    await act(async () => {
      await useChatStore.getState().createChat("BTC");
    });

    const state = useChatStore.getState();
    expect(state.activeChatId).toBe("2");
    expect(state.chats["2"]).toBeDefined();
  });

  it("appends messages when sending", async () => {
    useChatStore.setState({
      chats: {
        "3": {
          id: "3",
          title: "Rates",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          messages: []
        }
      },
      chatOrder: ["3"],
      activeChatId: "3",
      loading: false,
      error: null,
      theme: "light"
    });
    mockSendMessage.mockResolvedValueOnce({
      message: {
        id: "m1",
        role: "user",
        content: "Hi",
        created_at: "2024-01-01T00:00:00Z"
      },
      ai_response: {
        id: "m2",
        role: "assistant",
        content: "Hello",
        created_at: "2024-01-01T00:00:01Z"
      }
    });

    await act(async () => {
      await useChatStore.getState().sendMessage("Hi");
    });

    const state = useChatStore.getState();
    expect(state.chats["3"].messages?.length).toBe(2);
    expect(mockSendMessage).toHaveBeenCalledWith("3", "Hi");
  });
});
