import { useState } from "react";
import clsx from "clsx";
import { useChatStore } from "@/store/chatStore";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className = "" }: SidebarProps) {
  const { chatOrder, chats, activeChatId, createChat, selectChat, loading, error } = useChatStore(
    (state) => ({
      chatOrder: state.chatOrder,
      chats: state.chats,
      activeChatId: state.activeChatId,
      createChat: state.createChat,
      selectChat: state.selectChat,
      loading: state.loading,
      error: state.error
    })
  );
  const [creating, setCreating] = useState(false);

  const handleCreateChat = async () => {
    setCreating(true);
    try {
      await createChat();
    } finally {
      setCreating(false);
    }
  };

  const hasBorderOverride = className.split(" ").some((token) => token.startsWith("border-"));

  return (
    <aside
      className={clsx(
        "flex h-full w-full flex-col border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900",
        { "border-r": !hasBorderOverride },
        className
      )}
    >
      <div className="flex items-center justify-between px-4 py-4">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Market Mind</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">AI-driven financial insights</p>
        </div>
        <button
          type="button"
          onClick={handleCreateChat}
          disabled={creating}
          className="rounded-md bg-brand px-3 py-2 text-sm font-medium text-white shadow transition hover:bg-blue-600 disabled:opacity-50"
        >
          {creating ? "Creating..." : "New chat"}
        </button>
      </div>
      {error ? (
        <div className="px-4 text-sm text-red-500">{error}</div>
      ) : null}
      <nav className="flex-1 space-y-1 overflow-y-auto px-2 pb-8">
        {chatOrder.length === 0 && !loading ? (
          <p className="px-2 text-sm text-slate-500 dark:text-slate-400">
            Start a conversation to receive curated market insights.
          </p>
        ) : null}
        {chatOrder.map((chatId) => {
          const chat = chats[chatId];
          return (
            <button
              key={chatId}
              onClick={() => selectChat(chatId)}
              className={clsx(
                "w-full rounded-md px-3 py-2 text-left text-sm transition",
                activeChatId === chatId
                  ? "bg-slate-200 font-semibold text-slate-900 dark:bg-slate-700 dark:text-white"
                  : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              )}
            >
              <div className="truncate">{chat?.title ?? "Untitled chat"}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {new Date(chat?.updated_at ?? chat?.created_at ?? "").toLocaleString()}
              </div>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
