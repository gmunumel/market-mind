import { FormEvent, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { useChatStore } from "@/store/chatStore";
import type { Message } from "@/types/chat";

export function ChatWindow() {
  const { activeChatId, chats, sendMessage, loading, error } = useChatStore((state) => ({
    activeChatId: state.activeChatId,
    chats: state.chats,
    sendMessage: state.sendMessage,
    loading: state.loading,
    error: state.error
  }));
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const activeChat = activeChatId ? chats[activeChatId] : null;
  const conversation = activeChat?.messages ?? [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation.length, activeChatId]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    await sendMessage(trimmed);
    setMessage("");
  };

  if (!activeChatId) {
    return (
      <section className="flex h-full flex-1 items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="max-w-md rounded-xl border border-dashed border-slate-300 p-6 text-center dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Start exploring the markets</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Create a new chat to analyse equities, crypto, or macro trends backed by live data and historical context.
          </p>
        </div>
      </section>
    );
  }

  const renderMessage = (msg: Message) => {
    const isAssistant = msg.role === "assistant";
    const metadata = msg.metadata as { search_results?: string[]; vector_context?: string } | undefined;
    return (
      <div
        key={msg.id}
        className={clsx("mb-6 flex w-full", isAssistant ? "justify-start" : "justify-end")}
      >
        <div
          className={clsx(
            "max-w-3xl rounded-2xl px-4 py-3 text-sm shadow",
            isAssistant
              ? "bg-white text-slate-900 dark:bg-slate-800 dark:text-slate-100"
              : "bg-brand text-white"
          )}
        >
          <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>
          {isAssistant && metadata?.search_results ? (
            <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
              <p className="font-semibold">Sources</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {metadata.search_results.slice(0, 3).map((result, index) => (
                  <li key={`${msg.id}-source-${index}`}>{result}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </div>
    );
  };

  return (
    <section className="flex h-full flex-1 flex-col bg-slate-100 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{activeChat?.title}</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Ask about stocks, crypto, macro data, or risk signals. Market Mind will respond with concise, data-backed insights.
        </p>
      </header>
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {conversation.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No messages yet. Share your investment thesis or ask for a summary to begin.
          </p>
        ) : (
          conversation.map(renderMessage)
        )}
        <div ref={messagesEndRef} />
      </div>
      <footer className="border-t border-slate-200 bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-900">
        {error ? <p className="mb-2 text-sm text-red-500">{error}</p> : null}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Ask for a market summary, risk analysis, or sentiment check..."
            className="h-24 flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm shadow focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/40 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          />
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className="h-24 w-28 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? "Thinking..." : "Send"}
          </button>
        </form>
        <p className="mt-2 text-xs text-slate-400">
          Market Mind limits requests per user to protect resources. Heavy usage may temporarily pause responses.
        </p>
      </footer>
    </section>
  );
}
