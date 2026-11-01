const UPSTREAMS = [
  "https://disown-poking-squabble.ngrok-free.dev",
  "https://goal-trends-tools-holding.trycloudflare.com"
];

export default async (req) => {
  const url = new URL(req.url);
  const headers = {
    "Accept": "application/json",
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "leadScaler-NetlifyProxy/2.0"
  };
  const ct = req.headers.get("content-type");
  if (ct) headers["Content-Type"] = ct;
  const tok = req.headers.get("x-auth-token");
  if (tok) headers["X-Auth-Token"] = tok;

  const rawBody = (req.method !== "GET" && req.method !== "HEAD") ? await req.text() : undefined;

  let lastStatus = 502;
  let lastBody = JSON.stringify({ ok: false, error: "Upstream unreachable" });
  let lastCt = "application/json; charset=utf-8";

  for (const base of UPSTREAMS) {
    try {
      const upstream = await fetch(base + url.pathname + url.search, {
        method: req.method,
        headers,
        body: rawBody
      });
      const text = await upstream.text();
      const respCt = upstream.headers.get("content-type") || "application/json; charset=utf-8";
      lastStatus = upstream.status;
      lastBody = text;
      lastCt = respCt;
      // If Ngrok rate-limits (429) or returns tunnel HTML/5xx, seamlessly fail over to secondary tunnel!
      if (upstream.status !== 429 && upstream.status < 502 && respCt.includes("json")) {
        return new Response(text, {
          status: upstream.status,
          headers: { "Content-Type": respCt, "Cache-Control": "no-store" }
        });
      }
    } catch (_) {}
  }

  return new Response(lastBody, {
    status: lastStatus,
    headers: { "Content-Type": lastCt, "Cache-Control": "no-store" }
  });
};

export const config = {
  path: "/api/*"
};
