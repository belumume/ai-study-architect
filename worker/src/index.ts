import { Container } from "@cloudflare/containers";
import { env } from "cloudflare:workers";

const secrets = env as unknown as Record<string, string>;

export class StudyArchitectBackend extends Container {
  defaultPort = 8000;
  sleepAfter = "5m";
  enableInternet = true;
  pingEndpoint = "/health";
  envVars = {
    DATABASE_URL: secrets.DATABASE_URL,
    JWT_SECRET_KEY: secrets.JWT_SECRET_KEY,
    SECRET_KEY: secrets.SECRET_KEY,
    UPSTASH_REDIS_REST_URL: secrets.UPSTASH_REDIS_REST_URL,
    UPSTASH_REDIS_REST_TOKEN: secrets.UPSTASH_REDIS_REST_TOKEN,
    R2_ENDPOINT_URL: secrets.R2_ENDPOINT_URL,
    R2_ACCESS_KEY_ID: secrets.R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY: secrets.R2_SECRET_ACCESS_KEY,
  };
}

interface Env {
  BACKEND: DurableObjectNamespace & {
    getByName(name: string): StudyArchitectBackend;
  };
}

const ALLOWED_ORIGINS = [
  "https://aistudyarchitect.com",
  "https://www.aistudyarchitect.com",
];

const BLOCKED_PATHS = ["/api/docs", "/api/openapi.json", "/api/redoc"];

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Block API documentation endpoints
    if (BLOCKED_PATHS.includes(url.pathname)) {
      return new Response("Not Found", { status: 404 });
    }

    // Handle CORS preflight — mirror backend's allowed origins
    if (request.method === "OPTIONS") {
      const origin = request.headers.get("Origin") || "";
      const allowOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : "";
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": allowOrigin,
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
          "Access-Control-Allow-Headers":
            "Content-Type, Authorization, X-CSRF-Token",
          "Access-Control-Allow-Credentials": "true",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    // Route /api/* to the container (singleton pattern — single backend instance)
    if (url.pathname.startsWith("/api/") || url.pathname === "/health" || url.pathname === "/health/ready") {
      try {
        const container = env.BACKEND.getByName("singleton");
        await container.startAndWaitForPorts();
        return container.fetch(request);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        console.error("Container error:", message);
        return new Response(
          JSON.stringify({ error: "Service temporarily unavailable" }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        );
      }
    }

    // Everything else returns 404 (frontend is on Vercel)
    return new Response("Not Found", { status: 404 });
  },
};
