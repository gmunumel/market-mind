import { FormEvent, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { Trash2 } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import type { Message } from "@/types/chat";
import { CHAT_INPUT_PLACEHOLDER, CHAT_SUGGESTIONS } from "@/prompts/chatPrompts";

const markdownComponents: Components = {
  h1: ({ children }) => <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{children}</h1>,
  h2: ({ children }) => <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{children}</h2>,
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{children}</h3>
  ),
  p: ({ children }) => <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-200">{children}</p>,
  ul: ({ children }) => <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-200">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-200">{children}</ol>,
  li: ({ children }) => <li className="pl-1">{children}</li>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-brand underline underline-offset-4 hover:text-blue-600"
    >
      {children}
    </a>
  ),
  code: ({ inline, children }) =>
    inline ? (
      <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs text-slate-800 dark:bg-slate-800 dark:text-slate-100">
        {children}
      </code>
    ) : (
      <pre className="overflow-x-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100 dark:bg-slate-800">
        <code>{children}</code>
      </pre>
    ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-slate-200 pl-4 italic text-slate-500 dark:border-slate-700 dark:text-slate-300">
      {children}
    </blockquote>
  )
};

export function ChatWindow() {
  const { activeChatId, chats, sendMessage, deleteChat, loading, error } = useChatStore((state) => ({
    activeChatId: state.activeChatId,
    chats: state.chats,
    sendMessage: state.sendMessage,
    deleteChat: state.deleteChat,
    loading: state.loading,
    error: state.error
  }));
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const activeChat = activeChatId ? chats[activeChatId] : null;
  const conversation = activeChat?.messages ?? [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation.length, activeChatId]);

  const handleSuggestionSelect = (prompt: string) => {
    setMessage(prompt);
    textareaRef.current?.focus();
  };

  const handleDeleteChat = async () => {
    if (!activeChatId) return;
    const confirmed = window.confirm("Delete this chat? This will remove the conversation permanently.");
    if (!confirmed) return;
    await deleteChat(activeChatId);
  };

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
    const renderContent = () => {
      if (isAssistant) {
        return (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
            skipHtml
          >
            {msg.content}
          </ReactMarkdown>
        );
      }
      return <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>;
    };

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
          {renderContent()}
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
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{activeChat?.title}</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Ask about stocks, crypto, macro data, or risk signals. Market Mind will respond with concise, data-backed insights.
            </p>
          </div>
          <button
            type="button"
            onClick={handleDeleteChat}
            disabled={loading}
            className={clsx(
              "inline-flex items-center gap-2 rounded-md border border-transparent px-3 py-2 text-xs font-medium text-red-500 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:cursor-not-allowed disabled:opacity-60",
              !loading &&
                "hover:border-red-200 hover:bg-red-50 hover:text-red-600 dark:hover:border-red-700 dark:hover:bg-red-950 dark:hover:text-red-300"
            )}
            title="Delete chat"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
        </div>
      </header>
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {conversation.length === 0 ? (
          <>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 text-sm shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">Insights Console</h3>
              <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                Kick off a session with a market summary, risk analysis, or sentiment check. We will analyze the latest
                data and return a concise brief tailored to your focus.
              </p>
            </div>
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
              No messages yet. Share your investment thesis or choose a suggestion to begin.
            </p>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {CHAT_SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion.id}
                  type="button"
                  onClick={() => handleSuggestionSelect(suggestion.prompt)}
                  className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm transition hover:border-brand hover:shadow-md focus:outline-none focus:ring-2 focus:ring-brand/40 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-brand"
                >
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{suggestion.title}</h3>
                  <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{suggestion.description}</p>
                </button>
              ))}
            </div>
          </>
        ) : (
          conversation.map(renderMessage)
        )}
        <div ref={messagesEndRef} />
      </div>
      <footer className="border-t border-slate-200 bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-900">
        {error ? <p className="mb-2 text-sm text-red-500">{error}</p> : null}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder={CHAT_INPUT_PLACEHOLDER}
            className="h-24 flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm shadow focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/40 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          />
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className={clsx(
              "h-24 w-28 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white shadow transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 disabled:cursor-not-allowed disabled:opacity-60",
              loading ? "animate-pulse bg-blue-500/90" : "hover:bg-blue-600 active:scale-[0.99]"
            )}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Thinking…
              </span>
            ) : (
              "Send"
            )}
          </button>
        </form>
        <p className="mt-2 text-xs text-slate-400">
          Market Mind limits requests per user to protect resources. Heavy usage may temporarily pause responses.
        </p>
      </footer>
    </section>
  );
}
