import { useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatWindow } from "@/components/ChatWindow";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useChatStore } from "@/store/chatStore";

function App() {
  const fetchChats = useChatStore((state) => state.fetchChats);

  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="hidden w-80 flex-shrink-0 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 md:flex">
        <Sidebar />
      </div>
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Insights Console</h1>
          <ThemeToggle />
        </div>
        <div className="md:hidden">
          <Sidebar className="max-h-64 border-b border-slate-200 dark:border-slate-800" />
        </div>
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
