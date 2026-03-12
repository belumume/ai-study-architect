import { Container } from "@cloudflare/containers";

export class StudyArchitectBackend extends Container {
  defaultPort = 8000;
  sleepAfter = "5m";
  enableInternet = true;
  pingEndpoint = "/health";
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
      const container = env.BACKEND.getByName("singleton");
      await container.startAndWaitForPorts();
      return container.fetch(request);
    }

    // Everything else returns 404 (frontend is on Vercel)
    return new Response("Not Found", { status: 404 });
  },
};
