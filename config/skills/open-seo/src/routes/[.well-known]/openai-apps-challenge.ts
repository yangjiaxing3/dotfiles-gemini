import { createFileRoute } from "@tanstack/react-router";

// Public verification challenge value configured via environment variable.
const OPENAI_APPS_CHALLENGE_VALUE =
  process.env.OPENAI_APPS_CHALLENGE_VALUE ?? "";

export const Route = createFileRoute("/.well-known/openai-apps-challenge")({
  server: {
    handlers: {
      GET: async () => {
        return new Response(OPENAI_APPS_CHALLENGE_VALUE, {
          headers: {
            "content-type": "text/plain; charset=utf-8",
          },
        });
      },
    },
  },
});
