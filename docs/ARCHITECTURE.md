# leadScaler — 11-Stage System Architecture

<p align="center">
  <img src="../assets/leadscaler-workflow-architecture.png" alt="leadScaler 78-Node Architecture" width="100%" />
</p>

## Stage-by-Stage Execution Flow

1. **Stage 01 · Public Web Workspace (`frontend/index.html` + `backend/smart_leadflow_web.py`)**
   - Supports **Prompt Mode** and **Filter Mode**, private passwordless `@handle` workspaces, saved cold outreach templates, live estimated execution timers, and a compact **Dual Pathway Selector**:
     - `free_apis` (*Recommended*, Default): 6-stage Free API Waterfall with parallel AI top-up.
     - `tinyfish`: Direct TinyFish AI + Smart Email Guesser + Mailmeteor verification pipeline.

2. **Stage 02 · Batch Lock (Max 5) & Dedupe Memory**
   - Enforces a strict ceiling of **5 leads per batch**.
   - Maps user prompts to canonical Prospeo industries, Clay `products_and_services` queries, positive must-match niche terms, and negative exclusion industries.
   - Injects all previously delivered company names and email keys for the active user + prompt signature so repeat batches never return duplicates.

3. **Stage 03 · Dual-Track Parallel Split Router**
   - Simultaneously triggers **Track A** (Parallel AI Discovery Race: `LeadPulse AI` vs `TinyFish AI`) and **Track B** (Sequential Free Lead AI Waterfall).

4. **Stage 04 · 6-Stage Sequential Free Lead AI Waterfall + Green Express Bypass**
   - **4.1 Prospeo Account #1** → **4.2 Prospeo Account #2** (with automatic Page-1 takeover if Account #1 returns 0 leads) → **4.25 Clay Account #1** → **4.26 Clay Account #2** → **4.3 Hunter.io** (`4.3A` Free Discover + `4.3Q` Multi-Domain Selector + `4.3B` Domain Search across up to 6 distinct companies) → **4.4 Apollo.io** → **+4.5 Expandable Future API Slot**.
   - As soon as `freeLeads.length === 5`, the **Green Express Bypass Rail** skips all remaining downstream providers.

5. **Stage 05 · Sufficiency Gate, Smart Email Guesser & Mailmeteor One-by-One Verifier**
   - If Stage 04 already delivered 5 verified leads, Stage 05 bypasses Mailmeteor completely.
   - Otherwise, `5G · Smart Email Guesser` generates corporate email patterns (`first@`, `first.last@`, `flast@`, `firstlast@`) within a strict **`8.0s` per-lead / `20.0s` per-stage hard time cap**, pre-filters MX-less domains in ~`80ms` via Google DNS-over-HTTPS, heals dead domains, and checks candidates one by one on `https://mailmeteor.com/email-checker`.

6. **Stage 06 · Normalize, Deduplicate & Lock Exact 5 Verified Leads**
   - Normalizes fields across all providers, enforces 1 lead per unique company, and locks up to 5 verified leads.

7. **Stage 07 · Company Website & Smart LinkedIn Enricher**
   - Attaches verified direct LinkedIn `/in/` URLs or builds a guaranteed `Person Name + Company Name` LinkedIn People Search URL; optionally fetches missing official website context via TinyFish.

8. **Stage 08 · Multi-LLM Cold Outreach Personalizer**
   - Customizes the user's saved outreach template for each lead via Primary LLM (`xKiro`) with automatic failover to Backup LLM (`8B`) on rate-limit or timeout.

9. **Stages 09–11 · Persistent History, CSV Export & `"Make 5 Another Leads"` Loop**
   - Stores each batch in per-user SQLite history, enables one-click email copy and CSV download, and powers infinite 5-lead pagination with zero company overlap.
