export interface SuggestionPrompt {
  id: string;
  title: string;
  description: string;
  prompt: string;
}

export const CHAT_SUGGESTIONS: SuggestionPrompt[] = [
  {
    id: "market-summary",
    title: "Market summary",
    description: "Get a concise overview of major indices and macro drivers.",
    prompt:
      "Provide a concise market summary that covers major global indices, notable sector moves, and the key macro drivers influencing today's session."
  },
  {
    id: "risk-analysis",
    title: "Risk analysis",
    description: "Assess downside risks and volatility catalysts.",
    prompt:
      "Run a risk analysis highlighting downside scenarios, volatility catalysts, and any warning signals investors should keep in mind."
  },
  {
    id: "sentiment-check",
    title: "Sentiment check",
    description: "Gauge news and social sentiment for tickers I care about.",
    prompt:
      "Perform a sentiment check that blends recent news tone, social chatter, and options flow for the most discussed tickers today."
  }
];

export const CHAT_INPUT_PLACEHOLDER =
  "Ask for a market summary, risk analysis, or sentiment check...";
