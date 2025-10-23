const STORAGE_KEY = "market-mind-user-id";

function generateUserId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `user-${Math.random().toString(36).slice(2, 12)}`;
}

export function getUserId(): string {
  if (typeof window === "undefined") return "anonymous-test-user";
  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) {
    return existing;
  }
  const id = generateUserId();
  window.localStorage.setItem(STORAGE_KEY, id);
  return id;
}
