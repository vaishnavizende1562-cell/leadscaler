# Deployment & Self-Hosting Guide

## Prerequisites

- **n8n** `>= 1.60` or `2.x` (Docker or self-hosted, with `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` so `$env.*` keys resolve inside workflow nodes)
- **Python** `>= 3.10`
- **Node.js** `>= 20` (for automated workflow validation tests and optional Netlify CLI deployment)
- **Google Chrome / Patchright** + `xvfb` (for headless one-by-one verification on `https://mailmeteor.com/email-checker`)

---

## Step 1: Environment Setup

Copy `.env.example` and populate your provider keys:

```bash
cp .env.example /opt/n8n/.env
```

Ensure your n8n container loads `/opt/n8n/.env` and sets:
```env
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
```

---

## Step 2: Import the 78-Node n8n Workflow

```bash
# Via n8n CLI inside Docker:
docker cp b2b-smart-leadflow-n8n.json <n8n_container>:/tmp/b2b-smart-leadflow-n8n.json
docker exec -u node <n8n_container> n8n import:workflow --input=/tmp/b2b-smart-leadflow-n8n.json
docker exec -u node <n8n_container> n8n publish:workflow --id=SmartLeadFlowV1
docker restart <n8n_container>
```

Or import `b2b-smart-leadflow-n8n.json` directly through the **n8n Editor UI → Import from File** and click **Publish**.

To regenerate `b2b-smart-leadflow-n8n.json` from Python source after customization:
```bash
python3 workflows/build_n8n_workflow.py
npm test
```

---

## Step 3: Run Backend Services

### A. Parallel Race Coordinator + Smart Email Guesser + Mailmeteor Verifier (`:8097`)
```bash
xvfb-run -a python3 backend/mailmeteor_race_server.py
```

### B. Web Workspace & Multi-User API Server (`:8095`)
```bash
cp frontend/index.html /opt/leadgen/smart_web/index.html
python3 backend/smart_leadflow_web.py
```

 Verify health:
```bash
curl -s http://127.0.0.1:8095/api/health | python3 -m json.tool
```

---

## Step 4: Optional Netlify Frontend & Zero-Warning Proxy

`netlify.toml` and `netlify/functions/api.mjs` serve the static UI from Netlify's global CDN while proxying `/api/*` requests to your backend tunnel (with `ngrok-skip-browser-warning: true` and automatic secondary tunnel failover):

```bash
npx netlify-cli deploy --prod --dir=frontend --functions=netlify/functions
```
