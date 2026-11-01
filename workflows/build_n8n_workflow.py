import json
import uuid

def uid(n):
    return f"b2bf1000-0000-4000-8000-{n:012d}"

nodes = []
connections = {}

def add_conn(src, dst, src_output=0, dst_input=0):
    connections.setdefault(src, {}).setdefault("main", [])
    while len(connections[src]["main"]) <= src_output:
        connections[src]["main"].append([])
    connections[src]["main"][src_output].append({
        "node": dst,
        "type": "main",
        "index": dst_input
    })

def sticky(nid, name, content, x, y, w, h, color=5):
    nodes.append({
        "id": uid(nid),
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {
            "content": content,
            "width": w,
            "height": h,
            "color": color
        }
    })

def code_node(nid, name, js, x, y, notes=""):
    n = {
        "id": uid(nid),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
        "parameters": {
            "jsCode": js
        }
    }
    if notes:
        n["notes"] = notes
        n["notesInFlow"] = True
    nodes.append(n)

def if_eq_node(nid, name, left_expr, right_val, x, y):
    nodes.append({
        "id": uid(nid),
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [x, y],
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "version": 2,
                    "leftValue": "",
                    "rightValue": ""
                },
                "combinator": "and",
                "conditions": [
                    {
                        "id": "c1",
                        "leftValue": left_expr,
                        "rightValue": right_val,
                        "operator": {
                            "type": "string",
                            "operation": "equals"
                        }
                    }
                ]
            },
            "options": {}
        }
    })

def http_node(nid, name, method, url, headers_list, json_body, x, y, timeout=60000, batch_interval_ms=None):
    opts = {
        "timeout": timeout,
        "response": {
            "response": {
                "neverError": True
            }
        }
    }
    if batch_interval_ms is not None:
        opts["batching"] = {
            "batch": {
                "batchSize": 1,
                "batchInterval": batch_interval_ms
            }
        }
    params = {
        "method": method,
        "url": url,
        "sendHeaders": True,
        "headerParameters": {
            "parameters": headers_list
        },
        "options": opts
    }
    if method != "GET" and json_body is not None:
        params["sendBody"] = True
        params["specifyBody"] = "json"
        params["jsonBody"] = json_body
    nodes.append({
        "id": uid(nid),
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, y],
        "parameters": params
    })

def wait_node(nid, name, seconds, x, y):
    nodes.append({
        "id": uid(nid),
        "name": name,
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [x, y],
        "parameters": {
            "resume": "timeInterval",
            "amount": seconds,
            "unit": "seconds"
        }
    })

# ==================== STICKY NOTES (VISUAL ZONES MATCHING LOCKED DIAGRAM) ====================
sticky(1, "Zone 1", "## STAGE 01–03 · PUBLIC PROMPT INTAKE, MAX-5 LOCK & PARALLEL SPLIT\n- Single Prompt input from Public Web UI\n- Strict **Max 5 Leads / Run** cap (protects free API credits)\n- Loads **Saved Email Template** + **Excluded Old Leads** (`Make 5 Another Leads`)\n- Fires **Parallel Backup Race (LeadPulse AI + TinyFish AI)** + **Free Lead AI Waterfall**", -2220, -170, 820, 390, color=5)

sticky(2, "Zone 2", "## PARALLEL BACKUP RACE · LEADPULSE AI vs TINYFISH AI (3B-1, 3B-2, 3C)\n- **3B-1 LeadPulse AI** & **3B-2 TinyFish AI** start **simultaneously** in parallel\n- **First-Result-Wins Race:** Jiska result pehle aata hai woh turant jeet kar aage jaata hai (slow racer auto-cancel!)\n- **Standby Guard:** Agar Free Waterfall 5 leads de de, toh Mailmeteor bilkul skip rehta hai!", -1380, -650, 920, 440, color=6)

sticky(3, "Zone 3", "## STAGE 04 · FREE LEAD AI WATERFALL (1-by-1 Minimum Credit Chain) + GREEN EXPRESS BYPASS\n- **Priority (Default Pathway):** `4.1 Prospeo #1` -> `4.2 Prospeo #2` -> `4.25 Clay #1` -> `4.26 Clay #2` -> `4.3 Hunter.io` -> `4.4 Apollo.io` -> `+4.5 Future Lead API Slot`\n- **Stop-on-5 Rule:** Jaise hi 5 unique leads poore hon, **Green Express Bypass Rail** baaki saare APIs skip kar deti hai!\n- **Pathway Option:** User `TinyFish` pathway chune toh Stage 04 `0ms` me bypass hokar seedha TinyFish -> Smart Email Guesser -> Mailmeteor par jaata hai.", -1360, -170, 5040, 610, color=4)

sticky(4, "Zone 4", "## STAGE 05 · SUFFICIENCY GATE, SMART EMAIL GUESSER (TIME-CAPPED) & MAILMETEOR WEB CHECKER\n- **YES (5 Free Leads Ready):** Skip Backup Race & Skip Mailmeteor (`0` checks)\n- **NO / <5 Leads (or TinyFish Pathway):** `5B` TinyFish/Race Leads -> **`5G` Smart Email Pattern Guesser (Hard Time Cap <=8s/lead, <=20s total)** -> `5C` Check **ONE BY ONE** on **`https://mailmeteor.com/email-checker`** + `+5D`", 3720, -520, 1520, 740, color=3)

sticky(5, "Zone 5", "## STAGE 06–07 · LOCK 5 UNIQUE LEADS + SMART LINKEDIN + TINYFISH\n- Deduplicate against current batch + all previous batches\n- **7L Smart LinkedIn:** Direct Profile URL else Auto `Name + Company` LinkedIn Search URL\n- **7R TinyFish API:** Official company website finder *(called ONLY if website missing)* + `+7R Extra Scraper Slot`", 5280, -180, 980, 420, color=6)

sticky(6, "Zone 6", "## STAGE 08 · SAVED EMAIL TEMPLATE + MULTI-LLM FAILOVER\n- Loads User's pre-set **\"My Email Template\"** (`8L`)\n- Personalizes Subject & Body per lead (**Zero fake emails / Zero hallucinated facts**)\n- **Auto-Failover:** Primary LLM (`xKiro`) -> Backup LLM (`APInex / Gemini`) + `+8R Extra LLM Keys Slot`", 6300, -180, 1240, 560, color=4)

sticky(7, "Zone 7", "## STAGE 09–11 · PROMPT HISTORY, CSV EXPORT & \"MAKE 5 ANOTHER LEADS\"\n- Saves Prompt + 5 Leads + Exclusion Keys + Quota Log\n- Returns `nextBatchRequest` so clicking **\"Make 5 Another Leads\"** loops back to Stage 02 for **Leads 6–10, 11–15...**", 7580, -180, 780, 420, color=7)

sticky(8, "Zone 8", "## COMPANION PUBLIC UI ENDPOINTS\n- `POST /webhook/b2b-smart-leads-template` -> Save/Update **\"My Email Template\"**\n- `GET /webhook/b2b-smart-leads-history` -> Load **Prompt History, Previous Lead Batches & Quota Log**\n- `GET /webhook/b2b-smart-leads-health` -> Live **11-Stage Readiness & Provider Status**", -2220, 540, 1180, 760, color=5)


# ==================== STAGE 01 - 03 ====================
nodes.append({
    "id": uid(10),
    "name": "01 · Public UI Webhook",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 2,
    "position": [-2140, 0],
    "webhookId": "b2b-smart-leads-main",
    "parameters": {
        "httpMethod": "POST",
        "path": "b2b-smart-leads",
        "responseMode": "responseNode",
        "options": {}
    }
})

js_step02 = r"""
const raw = $input.first().json;
const body = (raw && typeof raw.body === 'object' && raw.body !== null) ? raw.body : raw;
const prompt = String(body.prompt || '').trim();
if (prompt.length < 3) {
  throw new Error('Please provide a valid B2B lead generation prompt (min 3 chars).');
}

// Persistent Workflow Memory (Prompt History, Exclusion Keys, Saved Email Template, Quota Log)
const store = $getWorkflowStaticData('global');
if (!store.templates) store.templates = {};
if (!store.seenByPrompt) store.seenByPrompt = {};
if (!store.history) store.history = [];
if (!store.quotaLog) {
  store.quotaLog = {
    prospeo_1_calls: 0,
    prospeo_2_calls: 0,
    clay_1_calls: 0,
    clay_2_calls: 0,
    hunter_calls: 0,
    apollo_calls: 0,
    leadpulse_fallbacks: 0,
    mailmeteor_verifications: 0,
    tinyfish_enrichments: 0,
    llm_personalizations: 0
  };
}

const userId = String(body.userId || 'public_default').trim() || 'public_default';
const promptKey = (userId + '::' + prompt.toLowerCase().replace(/\s+/g, ' ')).slice(0, 220);

if (!store.seenByPrompt[promptKey]) {
  store.seenByPrompt[promptKey] = { keys: [], companies: [], batches: 0 };
}
const promptMem = store.seenByPrompt[promptKey];

// Enforce STRICT MAX 5 LEADS PER RUN (Locked Rule #2)
const maxLeads = 5;

// Merge excluded leads from both persistent memory (if makeAnother5 / repeat prompt) & client payload
const clientReset = Boolean(body.resetHistory === true);
if (clientReset) {
  promptMem.keys = [];
  promptMem.companies = [];
  promptMem.batches = 0;
}

const excludedLeadKeys = Array.from(new Set([
  ...(Array.isArray(body.excludedLeadKeys) ? body.excludedLeadKeys.map(x => String(x).toLowerCase().trim()) : []),
  ...(body.makeAnother5 !== false ? promptMem.keys : [])
])).filter(Boolean);

const excludeCompanies = Array.from(new Set([
  ...(Array.isArray(body.excludeCompanies) ? body.excludeCompanies.map(x => String(x).trim()) : []),
  ...(body.makeAnother5 !== false ? promptMem.companies : [])
])).filter(Boolean);

const batchNumber = Number(body.batchNumber) || (promptMem.batches + 1);

// Load or update User's Pre-Saved "My Email Template" (Locked Rule #8)
const reqSender = String(body.senderName || 'Vaishnavi Zende').trim();
const reqOffer = String(body.offer || 'streamline operations and accelerate B2B growth with AI automation').trim();
const defaultTemplate = {
  subject: "Quick collaboration idea for {{companyName}}",
  body: `Hi {{decisionMakerName}},\n\nI came across {{companyName}} and was impressed by your work in {{industry}}.\n\nWe help B2B teams ${reqOffer}, and I thought this could be valuable for your role as {{jobTitle}}.\n\nWould you be open to a brief 10-minute chat this week?\n\nBest regards,\n{{senderName}}`,
  senderName: reqSender,
  senderCompany: String(body.senderCompany || '')
};

if (body.emailTemplate && (body.emailTemplate.subject || body.emailTemplate.body)) {
  store.templates[userId] = {
    subject: String(body.emailTemplate.subject || defaultTemplate.subject),
    body: String(body.emailTemplate.body || defaultTemplate.body),
    senderName: String(body.emailTemplate.senderName || defaultTemplate.senderName),
    senderCompany: String(body.emailTemplate.senderCompany || '')
  };
}
const savedTemplate = store.templates[userId] || defaultTemplate;

// Lightweight Zero-Credit Prompt Parser (extracts roles, location, industry hints)
const roleMap = [
  ['co-founder', 'Co-Founder'], ['founder', 'Founder'], ['ceo', 'CEO'],
  ['cto', 'CTO'], ['coo', 'COO'], ['cmo', 'CMO'], ['cfo', 'CFO'],
  ['owner', 'Owner'], ['managing director', 'Managing Director'],
  ['sales director', 'Sales Director'], ['head of sales', 'Head of Sales'],
  ['head of growth', 'Head of Growth'], ['head of operations', 'Head of Operations'],
  ['operations manager', 'Operations Manager'], ['vp', 'VP'], ['director', 'Director'],
  ['partner', 'Partner'], ['president', 'President']
];
const matchedRoles = [];
for (const [pat, label] of roleMap) {
  if (new RegExp(`\\b${pat.replace(/[-]/g, '[- ]?')}s?\\b`, 'i').test(prompt)) matchedRoles.push(label);
}
if (matchedRoles.includes('Founder') && !matchedRoles.includes('Co-Founder')) matchedRoles.push('Co-Founder');
if (matchedRoles.includes('CEO') && matchedRoles.length === 1) {
  matchedRoles.push('Managing Director', 'Founder', 'Director');
}
const fallbackRoles = matchedRoles.length ? matchedRoles : ['Founder', 'Co-Founder', 'CEO', 'Managing Director', 'Director', 'Owner'];

// Built-in Canonical Prospeo Industry Map (fallback when webhook called directly without Web UI resolver)
const indMap = [
  [/\b(chemical|chemicals|petrochemical|agrochemical|specialty chemical)\b/i, ['Chemical Manufacturing', 'Wholesale Chemical and Allied Products', 'Paint, Coating, and Adhesive Manufacturing']],
  [/\b(pharma|pharmaceutical|biotech|biotechnology)\b/i, ['Pharmaceutical Manufacturing', 'Biotechnology Research']],
  [/\b(plastic|plastics|polymer|polymers|rubber)\b/i, ['Plastics Manufacturing', 'Plastics and Rubber Product Manufacturing']],
  [/\b(packaging|containers)\b/i, ['Packaging and Containers']],
  [/\b(paint|coating|adhesive)\b/i, ['Paint, Coating, and Adhesive Manufacturing']],
  [/\b(textile|garment|apparel|fashion)\b/i, ['Textile Manufacturing', 'Apparel Manufacturing', 'Retail Apparel and Fashion']],
  [/\b(milk|dairy|ghee|paneer|curd|ice cream)\b/i, ['Dairy Product Manufacturing', 'Food and Beverage Manufacturing']],
  [/\b(chocolate|cocoa|confectionery|bakery|snack|coffee|tea|beverage|food|fmcg)\b/i, ['Food and Beverage Manufacturing', 'Food and Beverage Services']],
  [/\b(airline|airlines|aviation|airways)\b/i, ['Airlines and Aviation']],
  [/\b(solar|renewable|clean energy)\b/i, ['Renewable Energy', 'Electric Power Generation']],
  [/\b(oil|gas|mining|petroleum)\b/i, ['Oil, Gas, and Mining']],
  [/\b(construction|civil engineering|building material|builder)\b/i, ['Construction', 'Civil Engineering', 'Building Materials']],
  [/\b(real estate|proptech|property)\b/i, ['Real Estate']],
  [/\b(automotive|automobile|motor vehicle|ev)\b/i, ['Motor Vehicle Manufacturing', 'Automotive']],
  [/\b(electronic|electronics|electrical|semiconductor|hardware)\b/i, ['Appliances, Electrical, and Electronics Manufacturing', 'Semiconductor Manufacturing', 'Computer Hardware']],
  [/\b(machinery|industrial|automation machinery)\b/i, ['Industrial Machinery Manufacturing', 'Machinery Manufacturing', 'Automation Machinery Manufacturing']],
  [/\b(manufacturing|manufacturer|factory)\b/i, ['General Manufacturing', 'Industrial Machinery Manufacturing']],
  [/\b(logistics|supply chain|freight|transport|warehousing)\b/i, ['Transportation, Logistics, Supply Chain and Storage', 'Freight and Package Transportation', 'Warehousing and Storage']],
  [/\b(healthcare|hospital|medical|clinic|healthtech|dental)\b/i, ['Hospitals and Health Care', 'Medical Practices', 'Medical Equipment Manufacturing']],
  [/\b(education|edtech|e-learning|school|university)\b/i, ['E-Learning Providers', 'Higher Education', 'Education Administration Programs']],
  [/\b(fintech|financial|finance|banking|insurance|wealth|investment)\b/i, ['Financial Services', 'Banking', 'Investment Management', 'Insurance']],
  [/\b(ecommerce|e-commerce|online retail|d2c|retail)\b/i, ['Online and Mail Order Retail', 'General Retail']],
  [/\b(marketing|advertising|ad agency|digital agency|pr)\b/i, ['Marketing Services', 'Advertising Services', 'Public Relations and Communications Services']],
  [/\b(cybersecurity|network security|infosec)\b/i, ['Computer and Network Security', 'Data Security Software Products']],
  [/\b(saas|software|cloud|devops)\b/i, ['Software Development', 'Technology, Information and Internet', 'IT Services and IT Consulting']],
  [/\b(ai|artificial intelligence|machine learning|data|analytics)\b/i, ['Software Development', 'Data Infrastructure and Analytics', 'Technology, Information and Internet']],
  [/\b(it services|it consulting|it company|tech)\b/i, ['IT Services and IT Consulting', 'Software Development']],
  [/\b(consulting|consultancy|professional services)\b/i, ['Business Consulting and Services', 'Professional Services']],
  [/\b(cosmetic|beauty|personal care|skincare)\b/i, ['Cosmetics', 'Personal Care Product Manufacturing']],
  [/\b(hospitality|hotel|restaurant|travel)\b/i, ['Hospitality', 'Restaurants', 'Travel Arrangements']],
  [/\b(legal|law firm)\b/i, ['Law Practice', 'Legal Services']],
  [/\b(agriculture|farming|agri)\b/i, ['Farming', 'Agriculture, Construction, Mining Machinery Manufacturing']]
];

const fallbackIndustries = [];
for (const [rx, vals] of indMap) {
  if (rx.test(prompt)) {
    for (const v of vals) { if (!fallbackIndustries.includes(v)) fallbackIndustries.push(v); }
  }
}

const locMap = {
  'usa': 'United States', 'united states': 'United States', 'us': 'United States',
  'california': 'California, United States', 'texas': 'Texas, United States', 'new york': 'New York, United States',
  'india': 'India', 'delhi': 'Delhi, India', 'new delhi': 'Delhi, India',
  'mumbai': 'Maharashtra, India', 'pune': 'Maharashtra, India',
  'bangalore': 'Karnataka, India', 'bengaluru': 'Karnataka, India',
  'hyderabad': 'Telangana, India', 'chennai': 'Tamil Nadu, India',
  'ahmedabad': 'Gujarat, India', 'surat': 'Gujarat, India',
  'noida': 'Uttar Pradesh, India', 'gurgaon': 'Haryana, India', 'gurugram': 'Haryana, India',
  'kolkata': 'West Bengal, India', 'jaipur': 'Rajasthan, India',
  'uk': 'United Kingdom', 'united kingdom': 'United Kingdom', 'london': 'London, England, United Kingdom',
  'uae': 'United Arab Emirates', 'dubai': 'Dubai, United Arab Emirates',
  'canada': 'Canada', 'germany': 'Germany', 'australia': 'Australia', 'singapore': 'Singapore'
};
const locMatch = prompt.match(/\b(New Delhi|Delhi|United States|USA|United Kingdom|UK|Mumbai|Bangalore|Bengaluru|Hyderabad|Pune|Chennai|Ahmedabad|Surat|Noida|Gurgaon|Gurugram|Kolkata|Jaipur|India|Canada|Germany|UAE|Dubai|Australia|Singapore|New York|Texas|California)\b/i);
const fallbackLoc = locMatch ? (locMap[locMatch[1].toLowerCase()] || locMatch[1]) : '';

// Extract meaningful niche keywords (excluding generic filler/location/role words)
const stopWords = new Set(['find','search','get','give','me','top','best','list','of','companies','company','business','businesses','firms','startups','startup','in','at','from','near','around','for','with','and','or','the','a','an','to','by','employees','employee','size','decision','makers','maker','role','roles','ceo','ceos','cto','ctos','cfo','coo','cmo','founder','founders','cofounder','owner','owners','director','directors','managing','head','sales','vp','president','partner','india','delhi','new','mumbai','bangalore','bengaluru','hyderabad','pune','chennai','ahmedabad','surat','noida','gurgaon','gurugram','kolkata','jaipur','usa','united','states','kingdom','uk','dubai','uae','canada','germany','australia','singapore','california','texas','york','london','extra']);
const rawWords = prompt.toLowerCase().replace(/[^a-z0-9\s-]/g, ' ').split(/\s+/).filter(w => w.length >= 3 && !stopWords.has(w) && !/^\d+$/.test(w));
const clientKws = Array.isArray(body.industryKeywords) ? body.industryKeywords.map(k => String(k).toLowerCase().trim()).filter(Boolean) : [];
const industryKeywords = Array.from(new Set([...clientKws, ...rawWords])).slice(0, 12);

const pfIn = (body.prospeoFilters && typeof body.prospeoFilters === 'object') ? body.prospeoFilters : {};
const resolvedRoles = (Array.isArray(pfIn.roles) && pfIn.roles.length) ? pfIn.roles : fallbackRoles;
const resolvedLocations = (Array.isArray(pfIn.locations) && pfIn.locations.length) ? pfIn.locations : (fallbackLoc ? [fallbackLoc] : []);
const resolvedIndustries = (Array.isArray(pfIn.industries) && pfIn.industries.length) ? pfIn.industries : fallbackIndustries;
const resolvedHeadcount = (Array.isArray(pfIn.headcountRanges) && pfIn.headcountRanges.length) ? pfIn.headcountRanges : [];
const resolvedKeywords = (Array.isArray(pfIn.keywords) && pfIn.keywords.length)
  ? pfIn.keywords
  : (resolvedIndustries.length === 0 && industryKeywords.length > 0 ? industryKeywords.slice(0, 6) : []);

const resolvedExcludeIndustries = Array.isArray(pfIn.excludeIndustries) ? pfIn.excludeIndustries : [];
const mustMatchKeywords = Array.isArray(pfIn.mustMatchKeywords) ? pfIn.mustMatchKeywords.map(k => String(k).toLowerCase().trim()).filter(Boolean) : [];
const mustExcludeTerms = Array.isArray(pfIn.mustExcludeTerms) ? pfIn.mustExcludeTerms.map(k => String(k).toLowerCase().trim()).filter(Boolean) : [];
const coreNicheRoots = Array.isArray(pfIn.coreNicheRoots) ? pfIn.coreNicheRoots.map(k => String(k).toLowerCase().trim()).filter(Boolean) : [];
const targetWebsites = Array.isArray(pfIn.websites) ? pfIn.websites.filter(Boolean) : [];
const targetCompanyNames = Array.isArray(pfIn.companyNames) ? pfIn.companyNames.filter(Boolean) : [];

// Pathway selection: DEFAULT is ALWAYS 'free_apis' (Prospeo #1 -> Prospeo #2 -> Clay #1 -> Clay #2 -> Hunter -> Apollo)
const rawPathway = String(body.pathway || '').trim().toLowerCase();
const pathway = (rawPathway === 'tinyfish') ? 'tinyfish' : 'free_apis';
const forceTinyFishPathway = (pathway === 'tinyfish');
const skipFreeWaterfall = Boolean(body.forceBackupRaceTest || forceTinyFishPathway);

// Map known pure company names -> domains so Clay people search results resolve corporate domains in 0ms
const websiteByCompanyNorm = {};
for (let i = 0; i < Math.min(targetCompanyNames.length, targetWebsites.length); i++) {
  const cn = String(targetCompanyNames[i] || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const dm = String(targetWebsites[i] || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').split('/')[0].trim();
  if (cn && dm && dm.includes('.')) websiteByCompanyNorm[cn] = dm;
}

// Build Official Clay GTM Query-Mode Search String (POST https://api.clay.com/public/v0/search/query-mode)
const clayRoleList = resolvedRoles.slice(0, 6).map(r => `"${String(r).replace(/"/g, '')}"`).join(', ');
const exCoNormSet = new Set(excludeCompanies.map(c => String(c || '').toLowerCase().replace(/[^a-z0-9]/g, '')).filter(Boolean));
const skipProviders = Array.isArray(body.skipProviders) ? body.skipProviders.map(x => String(x || '').trim().toLowerCase()) : [];

const nicheTermsRaw = [
  ...mustMatchKeywords.slice(0, 4),
  ...industryKeywords.slice(0, 3),
  ...(resolvedIndustries.slice(0, 2))
].map(s => String(s || '').replace(/"/g, '').trim()).filter(s => s.length >= 2);
const uniqNicheTerms = Array.from(new Set(nicheTermsRaw)).slice(0, 4);
const clayNicheCsv = (uniqNicheTerms.length > 0 ? uniqNicheTerms : [prompt.slice(0, 45).replace(/"/g, '').trim() || 'B2B'])
  .map(t => `"${t}"`).join(', ');

const loc0 = String(resolvedLocations[0] || '').toLowerCase();
let locClause = '';
if (loc0.includes('india')) locClause += ' and location_country = "India"';
else if (loc0.includes('united states')) locClause += ' and location_country = "United States"';
else if (loc0.includes('united kingdom')) locClause += ' and location_country = "United Kingdom"';
else if (loc0.includes('canada')) locClause += ' and location_country = "Canada"';
else if (loc0.includes('australia')) locClause += ' and location_country = "Australia"';
else if (loc0.includes('germany')) locClause += ' and location_country = "Germany"';
else if (loc0.includes('singapore')) locClause += ' and location_country = "Singapore"';
else if (loc0.includes('united arab emirates')) locClause += ' and location_country = "United Arab Emirates"';

const stateHints = [
  ['delhi', 'Delhi'], ['mumbai', 'Maharashtra'], ['pune', 'Maharashtra'], ['maharashtra', 'Maharashtra'],
  ['bengaluru', 'Karnataka'], ['bangalore', 'Karnataka'], ['karnataka', 'Karnataka'],
  ['hyderabad', 'Telangana'], ['telangana', 'Telangana'],
  ['chennai', 'Tamil Nadu'], ['tamil nadu', 'Tamil Nadu'],
  ['ahmedabad', 'Gujarat'], ['surat', 'Gujarat'], ['gujarat', 'Gujarat'],
  ['kolkata', 'West Bengal'], ['west bengal', 'West Bengal'],
  ['gurugram', 'Haryana'], ['gurgaon', 'Haryana'], ['haryana', 'Haryana'],
  ['noida', 'Uttar Pradesh'], ['uttar pradesh', 'Uttar Pradesh'],
  ['jaipur', 'Rajasthan'], ['rajasthan', 'Rajasthan']
];
for (const [k, stName] of stateHints) {
  if (loc0.includes(k)) {
    locClause += ` and location_state = "${stName}"`;
    break;
  }
}

const claySearchQuery = `select from people where experiences.any(is_current = true and job_title is_similar_to (${clayRoleList}) and company.products_and_services is_similar_to (${clayNicheCsv}))` + locClause;

const countryOnlyLocations = resolvedLocations
  .map(l => {
    const parts = String(l || '').split(',').map(s => s.trim()).filter(Boolean);
    return parts.length > 1 ? parts[parts.length - 1] : parts[0];
  })
  .filter(Boolean);

const searchPage = Math.max(1, Math.floor((excludedLeadKeys.length || 0) / 12) + 1);
const buildProspeoFilterObj = (pageOffset = 0, variant = 1) => {
  const f = {
    max_person_per_company: 1,
    person_job_title: { include: resolvedRoles.slice(0, 8) }
  };
  const indBlock = {};
  if (resolvedIndustries.length > 0) indBlock.include = resolvedIndustries.slice(0, 15);
  if (resolvedExcludeIndustries.length > 0) indBlock.exclude = resolvedExcludeIndustries.slice(0, 25);

  // Case A: Canonical Prospeo industries exist (e.g. Dairy Product Manufacturing, Airlines and Aviation, Chemical Manufacturing, Pharma)
  // Variant 1 searches the full Prospeo industry + keywords + exact city/country (returns 25+ hits!).
  // Variant 2 searches AI-discovered pure websites (using country-level location so NCR/suburb HQs aren't dropped) or page+1!
  if (resolvedIndustries.length > 0) {
    if (variant === 2 && targetWebsites.length >= 5) {
      if (countryOnlyLocations.length > 0) {
        f.company_location_search = { include: Array.from(new Set(countryOnlyLocations)).slice(0, 3) };
      }
      f.company = {
        websites: { include: targetWebsites.slice(0, 50) },
        ...(excludeCompanies.length > 0 ? { names: { exclude: excludeCompanies.slice(0, 100) } } : {})
      };
      if (indBlock.exclude) f.company_industry = { exclude: indBlock.exclude };
      return { page: 1, filters: f };
    }
    if (resolvedLocations.length > 0) {
      f.company_location_search = { include: resolvedLocations.slice(0, 5) };
    }
    f.company_industry = indBlock;
    if (resolvedKeywords.length > 0) {
      f.company_keywords = {
        include: resolvedKeywords.slice(0, 10),
        include_all: false,
        search_everywhere: false,
        sources: ['specialties', 'products_services', 'ai_description', 'seo_description']
      };
    }
    if (resolvedHeadcount.length > 0) {
      f.company_headcount_range = resolvedHeadcount;
    }
    if (excludeCompanies.length > 0) {
      f.company = { names: { exclude: excludeCompanies.slice(0, 100) } };
    }
    return { page: searchPage + pageOffset, filters: f };
  }

  // Case B: Pure sub-niche with NO canonical Prospeo industry (e.g. "chocolate companies", "coffee brands")
  if (variant === 1 && targetWebsites.length > 0) {
    if (countryOnlyLocations.length > 0) {
      f.company_location_search = { include: Array.from(new Set(countryOnlyLocations)).slice(0, 3) };
    }
    f.company = {
      websites: { include: targetWebsites.slice(0, 50) },
      ...(excludeCompanies.length > 0 ? { names: { exclude: excludeCompanies.slice(0, 100) } } : {})
    };
    if (indBlock.exclude) f.company_industry = { exclude: indBlock.exclude };
    return { page: 1, filters: f };
  }
  if (variant === 2 && targetCompanyNames.length > 0) {
    if (countryOnlyLocations.length > 0) {
      f.company_location_search = { include: Array.from(new Set(countryOnlyLocations)).slice(0, 3) };
    }
    f.company = {
      names: {
        include: targetCompanyNames.slice(0, 50),
        ...(excludeCompanies.length > 0 ? { exclude: excludeCompanies.slice(0, 100) } : {})
      }
    };
    if (indBlock.exclude) f.company_industry = { exclude: indBlock.exclude };
    return { page: 1, filters: f };
  }

  if (resolvedLocations.length > 0) {
    f.company_location_search = { include: resolvedLocations.slice(0, 5) };
  }
  if (Object.keys(indBlock).length > 0) {
    f.company_industry = indBlock;
  }
  if (resolvedKeywords.length > 0) {
    f.company_keywords = {
      include: resolvedKeywords.slice(0, 10),
      include_all: false,
      search_everywhere: false,
      sources: ['specialties', 'products_services', 'ai_description', 'seo_description']
    };
  }
  if (resolvedHeadcount.length > 0) {
    f.company_headcount_range = resolvedHeadcount;
  }
  if (excludeCompanies.length > 0) {
    f.company = { names: { exclude: excludeCompanies.slice(0, 100) } };
  }
  return { page: searchPage + pageOffset, filters: f };
};

return [{
  json: {
    requestId: 'req_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),
    userId,
    prompt,
    promptKey,
    batchNumber,
    maxLeads,
    pathway,
    forceTinyFishPathway,
    forceBackupRaceTest: Boolean(body.forceBackupRaceTest),
    skipProviders,
    needed: skipFreeWaterfall ? 0 : maxLeads,
    excludedLeadKeys,
    excludeCompanies,
    savedTemplate,
    parsedCriteria: {
      roles: resolvedRoles,
      primaryRoleHint: String(pfIn.primaryRoleHint || '').toLowerCase(),
      location: resolvedLocations[0] || '',
      locations: resolvedLocations,
      industries: resolvedIndustries,
      excludeIndustries: resolvedExcludeIndustries,
      mustMatchKeywords,
      mustExcludeTerms,
      coreNicheRoots,
      keywords: resolvedKeywords,
      rawPrompt: prompt,
      industryKeywords,
      targetWebsites,
      targetCompanyNames,
      websiteByCompanyNorm,
      claySearchQuery,
      hasProspeoIndustryFilter: (resolvedIndustries.length > 0 || resolvedKeywords.length > 0 || targetWebsites.length > 0 || targetCompanyNames.length > 0),
      strictIndustry: Boolean(body.strictIndustry !== false && (resolvedIndustries.length > 0 || industryKeywords.length > 0 || mustMatchKeywords.length > 0)),
      searchPage,
      prospeoPayload1: buildProspeoFilterObj(0, 1),
      prospeoPayload2: buildProspeoFilterObj(1, 2)
    },
    freeLeads: [],
    providerTrace: []
  }
}];
"""
code_node(11, "02 · Batch Lock (Max 5) & Dedupe Memory", js_step02, -1880, 0)

js_step03 = r"""
// Stage 03: Pass identical state simultaneously to Parallel LeadPulse Backup (3B) AND Free Lead AI Waterfall (4.1)
const state = $input.first().json;
return [{ json: { ...state, splitTimestamp: new Date().toISOString() } }];
"""
code_node(12, "03 · Dual-Track Parallel Split Router", js_step03, -1620, 0)

add_conn("01 · Public UI Webhook", "02 · Batch Lock (Max 5) & Dedupe Memory")
add_conn("02 · Batch Lock (Max 5) & Dedupe Memory", "03 · Dual-Track Parallel Split Router")


# ==================== TRACK A: PARALLEL RACE — LEADPULSE AI vs TINYFISH AI (FIRST RESULT WINS!) ====================
http_node(
    20,
    "3B-1 · LeadPulse AI (Parallel Racer A)",
    "POST",
    "http://172.18.0.1:8097/racer/leadpulse",
    [{"name": "Content-Type", "value": "application/json"}],
    "={{ JSON.stringify({ raceId: $json.requestId, prompt: $json.prompt, count: 5, pathway: $json.pathway || 'free_apis', onlyTinyfish: Boolean($json.forceTinyFishPathway), excludeCompanies: $json.excludeCompanies || [], preferredCompanies: $json.parsedCriteria.targetCompanyNames || [], preferredDomains: $json.parsedCriteria.targetWebsites || [] }) }}",
    -1300, -510,
    timeout=160000
)

http_node(
    22,
    "3B-2 · TinyFish AI (Parallel Racer B)",
    "POST",
    "http://172.18.0.1:8097/racer/tinyfish",
    [{"name": "Content-Type", "value": "application/json"}],
    "={{ JSON.stringify({ raceId: $json.requestId, prompt: $json.prompt, count: 5, pathway: $json.pathway || 'free_apis', onlyTinyfish: Boolean($json.forceTinyFishPathway), excludeCompanies: $json.excludeCompanies || [], preferredCompanies: $json.parsedCriteria.targetCompanyNames || [], preferredDomains: $json.parsedCriteria.targetWebsites || [] }) }}",
    -1300, -310,
    timeout=130000
)

nodes.append({
    "id": uid(23),
    "name": "3B-Sync · Collect Parallel Racers",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 3.2,
    "position": [-1030, -410],
    "parameters": {
        "mode": "append",
        "numberInputs": 2,
        "options": {}
    }
})

js_node3c = r"""
const base = $('03 · Dual-Track Parallel Split Router').first().json;
const raceInputs = $input.all().map(x => x.json || {});

// Pick whichever racer won the First-to-Finish race (or whichever returned non-empty leads)
let winnerObj = raceInputs.find(r => r.wonRace && Array.isArray(r.leads) && r.leads.length > 0)
             || raceInputs.find(r => Array.isArray(r.leads) && r.leads.length > 0)
             || {};

const raceWinner = String(winnerObj.racer || winnerObj.winner || 'none');
const rawLeads = Array.isArray(winnerObj.leads) ? winnerObj.leads : [];

const normalizedBackup = rawLeads.map(l => ({
  companyName: String(l.companyName || l.company || '').trim(),
  officialWebsite: String(l.officialWebsite || l.website || '').trim(),
  domain: String(l.domain || '').toLowerCase().trim(),
  companySummary: String(l.companySummary || l.industry || '').slice(0, 220),
  industry: String(l.industry || ''),
  location: String(l.location || ''),
  decisionMakerName: String(l.decisionMakerName || l.name || 'Decision Maker').trim(),
  jobTitle: String(l.jobTitle || l.role || 'Decision Maker').trim(),
  linkedinRaw: String(l.linkedinRaw || l.linkedin || '').trim(),
  email: String(l.email || '').toLowerCase().trim(),
  candidateEmails: Array.isArray(l.candidateEmails) ? l.candidateEmails : (l.email ? [l.email] : []),
  verificationStatus: 'pending_mailmeteor_web',
  verifiedBy: 'pending',
  sourceProvider: raceWinner === 'tinyfish_ai' ? 'tinyfish_ai_race_winner' : 'leadpulse_ai_race_winner'
})).filter(x => x.companyName && x.decisionMakerName);

return [{
  json: {
    track: 'parallel_backup_race',
    requestId: base.requestId,
    raceWinner,
    raceElapsedMs: Number(winnerObj.elapsedMs || 0),
    leadpulseStatus: normalizedBackup.length ? `winner_${raceWinner}` : 'empty',
    backupCount: normalizedBackup.length,
    backupLeads: normalizedBackup
  }
}];
"""
code_node(21, "3C · First-Finish Race Winner (To Mailmeteor)", js_node3c, -780, -410)

add_conn("03 · Dual-Track Parallel Split Router", "3B-1 · LeadPulse AI (Parallel Racer A)")
add_conn("03 · Dual-Track Parallel Split Router", "3B-2 · TinyFish AI (Parallel Racer B)")
add_conn("3B-1 · LeadPulse AI (Parallel Racer A)", "3B-Sync · Collect Parallel Racers", src_output=0, dst_input=0)
add_conn("3B-2 · TinyFish AI (Parallel Racer B)", "3B-Sync · Collect Parallel Racers", src_output=0, dst_input=1)
add_conn("3B-Sync · Collect Parallel Racers", "3C · First-Finish Race Winner (To Mailmeteor)")


# ==================== TRACK B: STAGE 04 FREE LEAD AI WATERFALL ====================
# Helper JS snippet for deduplicating & merging candidate leads into state.freeLeads
HELPER_DEDUPE_FN = r"""
function makeKey(lead) {
  const dom = String(lead.domain || lead.officialWebsite || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').split('/')[0].trim();
  const em = String(lead.email || '').toLowerCase().trim();
  const nm = String(lead.decisionMakerName || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const co = String(lead.companyName || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return em || (dom && nm ? `${dom}|${nm}` : `${co}|${nm}`);
}
function mergeUniqueLeads(existing, candidates, excludedKeys, excludedCos, maxCap) {
  const exKeySet = new Set((excludedKeys || []).map(k => String(k).toLowerCase()));
  const exCoSet = new Set((excludedCos || []).map(c => String(c).toLowerCase().replace(/[^a-z0-9]/g, '')));
  for (const item of existing) {
    exKeySet.add(makeKey(item));
    if (item.domain) exKeySet.add(item.domain.toLowerCase());
  }
  const out = [...existing];
  for (const c of candidates) {
    if (out.length >= maxCap) break;
    if (!c.companyName || !c.decisionMakerName) continue;
    const k = makeKey(c);
    const coNorm = c.companyName.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (exKeySet.has(k) || (c.domain && exKeySet.has(c.domain.toLowerCase())) || (coNorm && exCoSet.has(coNorm))) {
      continue;
    }
    exKeySet.add(k);
    if (c.domain) exKeySet.add(c.domain.toLowerCase());
    out.push({ ...c, leadKey: k });
  }
  return out;
}
"""

# --- 4.1 PROSPEO ACCOUNT #1 ---
http_node(
    30,
    "4.1A · Prospeo #1 Search",
    "POST",
    "={{ ($env.PROSPEO_API_KEY_1 && $json.needed > 0 && !($json.skipProviders || []).includes('prospeo_1')) ? 'https://api.prospeo.io/search-person' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "X-KEY", "value": "={{ $env.PROSPEO_API_KEY_1 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ JSON.stringify($json.parsedCriteria.prospeoPayload1) }}",
    -1300, 0,
    timeout=30000
)

wait_node(96, "4.1P · Prospeo #1 Rate Guard (2s)", 2, -1200, 0)

js_41q = r"""
const st = $('03 · Dual-Track Parallel Split Router').first().json;
const searchResp = $('4.1A · Prospeo #1 Search').first().json || {};
const hasKey = Boolean(($env.PROSPEO_API_KEY_1 || '').trim());
if (!hasKey || st.needed <= 0 || !Array.isArray(searchResp.results) || searchResp.results.length === 0) {
  return [{ json: { skipEnrich: true } }];
}
const kws = (st.parsedCriteria?.industryKeywords || []);
const mustMatch = (st.parsedCriteria?.mustMatchKeywords || []);
const mustExInd = new Set((st.parsedCriteria?.excludeIndustries || []).map(x => String(x).toLowerCase()));
const mustExTerms = (st.parsedCriteria?.mustExcludeTerms || []);
const coreRoots = (st.parsedCriteria?.coreNicheRoots || []);
const roleHint = String(st.parsedCriteria?.primaryRoleHint || '').toLowerCase();
const exCos = new Set((st.excludeCompanies || []).map(c => String(c).toLowerCase().replace(/[^a-z0-9]/g, '')));
const exKeys = new Set((st.excludedLeadKeys || []).map(k => String(k).toLowerCase()));
const scored = searchResp.results.map((r, i) => {
  const p = r.person || r;
  const c = r.company || {};
  const cInd = String(c.industry || '').toLowerCase().trim();
  const cNameLow = String(c.name || '').toLowerCase();
  const cDescLow = `${c.description_ai || ''} ${c.description_seo || ''} ${c.description || ''} ${(c.keywords || []).join(' ')}`.toLowerCase();
  const hay = `${cNameLow} ${cInd} ${cDescLow} ${p.headline || ''} ${p.current_job_title || ''}`.toLowerCase();

  let rejected = false;
  if (cInd && mustExInd.has(cInd)) rejected = true;
  const nameHasCore = coreRoots.length > 0 && coreRoots.some(rt => rt && cNameLow.includes(rt));
  if (!nameHasCore && mustExTerms.length > 0 && mustExTerms.some(bad => bad && cDescLow.includes(bad))) {
    rejected = true;
  }
  if (mustMatch.length > 0 && !mustMatch.some(mk => mk && (cNameLow.includes(mk) || cDescLow.includes(mk) || cInd.includes(mk)))) {
    rejected = true;
  }

  let sc = 0;
  if (nameHasCore) sc += 8;
  for (const kw of kws) { if (kw && hay.includes(kw)) sc += 3; }
  for (const mk of mustMatch) { if (mk && (cNameLow.includes(mk) || cDescLow.includes(mk))) sc += 4; }
  if (roleHint && String(p.current_job_title || '').toLowerCase().includes(roleHint)) sc += 4;
  return { r, sc, i, rejected };
}).filter(x => !x.rejected).sort((a, b) => (b.sc - a.sc) || (a.i - b.i));

const seenCo = new Set();
const items = [];
const maxPick = Math.min(5, st.needed || 5);
for (const { r, sc } of scored) {
  if (items.length >= maxPick) break;
  if (st.parsedCriteria?.strictIndustry && !st.parsedCriteria?.hasProspeoIndustryFilter && sc <= 0) continue;
  const p = r.person || r;
  const c = r.company || {};
  const coName = String(c.name || '').trim();
  const coNorm = coName.toLowerCase().replace(/[^a-z0-9]/g, '');
  const nmNorm = String(p.full_name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const dom = String(c.domain || c.website || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').split('/')[0];
  if (!p.person_id || !coName) continue;
  if (exCos.has(coNorm) || seenCo.has(coNorm) || (dom && exKeys.has(dom)) || exKeys.has(`${dom}|${nmNorm}`)) continue;
  seenCo.add(coNorm);
  items.push({ json: { skipEnrich: false, person_id: p.person_id, fallbackCompany: coName } });
}
return items.length > 0 ? items : [{ json: { skipEnrich: true } }];
"""
code_node(98, "4.1Q · Select Top ICP Candidates (#1)", js_41q, -1100, 0)

http_node(
    31,
    "4.1B · Prospeo #1 Enrich Verified",
    "POST",
    "={{ (!$json.skipEnrich && $env.PROSPEO_API_KEY_1 && $json.person_id) ? 'https://api.prospeo.io/enrich-person' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "X-KEY", "value": "={{ $env.PROSPEO_API_KEY_1 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ JSON.stringify({ only_verified_email: true, data: { person_id: $json.person_id } }) }}",
    -980, 0,
    timeout=35000,
    batch_interval_ms=1450
)

js_41c = HELPER_DEDUPE_FN + r"""
const prev = $('03 · Dual-Track Parallel Split Router').first().json;
const searchResp = $('4.1A · Prospeo #1 Search').first().json || {};
const enrichItems = $input.all().map(x => x.json || {});
const hasKey = Boolean(($env.PROSPEO_API_KEY_1 || '').trim());

let added = [];
let statusNote = 'skipped_no_api_key (0 credits)';

if (hasKey) {
  const validItems = enrichItems.filter(it => it && it.error === false && it.person);
  if (validItems.length > 0) {
    added = validItems.map(item => {
      const p = item.person || {};
      const c = item.company || p.company || {};
      const emailObj = p.email || item.email || {};
      const emailStr = typeof emailObj === 'string' ? emailObj : (emailObj.email || '');
      const website = String(c.website || (c.domain ? `https://${c.domain}` : '') || '').trim();
      const domain = String(c.domain || website).replace(/^https?:\/\/(www\.)?/i, '').split('/')[0].toLowerCase();
      const cLoc = (typeof c.location === 'object' && c.location) ? [c.location.city, c.location.state, c.location.country].filter(Boolean).join(', ') : '';
      const pLoc = (typeof p.location === 'object' && p.location) ? [p.location.city, p.location.state, p.location.country].filter(Boolean).join(', ') : String(p.location || '');
      return {
        companyName: String(c.name || '').trim(),
        officialWebsite: website,
        domain,
        companySummary: String(c.description_ai || c.description_seo || c.description || c.industry || '').slice(0, 220),
        industry: String(c.industry || ''),
        location: cLoc || pLoc,
        decisionMakerName: String(p.full_name || `${p.first_name || ''} ${p.last_name || ''}`).trim(),
        jobTitle: String(p.current_job_title || p.job_title || p.title || 'Decision Maker').trim(),
        linkedinRaw: String(p.linkedin_url || '').trim(),
        email: String(emailStr || '').toLowerCase().trim(),
        emailVerified: Boolean(emailStr && String(emailStr).includes('@')),
        verificationStatus: 'valid',
        verifiedBy: 'prospeo_1_verified',
        verificationSource: 'prospeo_1_verified',
        sourceProvider: 'prospeo_acc_1'
      };
    }).filter(l => l.emailVerified && l.companyName);
    statusNote = `called_prospeo_1 (searchFree=${Boolean(searchResp.free)}, verified=${added.length})`;
  } else {
    const errItem = enrichItems.find(it => it && it.error);
    statusNote = searchResp.error ? `prospeo_1_search_err (${searchResp.error_code || 'err'})` : (errItem ? `prospeo_1_enrich_err (${errItem.error_code || 'err'})` : 'prospeo_1_0_verified');
  }
}

const merged = mergeUniqueLeads(prev.freeLeads, added, prev.excludedLeadKeys, prev.excludeCompanies, 5);
const skipFree = Boolean(prev.forceBackupRaceTest || prev.forceTinyFishPathway);
return [{
  json: {
    ...prev,
    freeLeads: merged,
    needed: skipFree ? 0 : Math.max(0, 5 - merged.length),
    providerTrace: [...prev.providerTrace, { provider: 'prospeo_acc_1', status: prev.forceTinyFishPathway ? 'bypassed_for_tinyfish_pathway (0 credits)' : (prev.forceBackupRaceTest ? 'bypassed_for_race_test (0 credits)' : statusNote), totalSoFar: merged.length }],
    route: (skipFree || merged.length >= 5) ? 'ready' : 'continue'
  }
}];
"""
code_node(32, "4.1C · Check Prospeo #1", js_41c, -860, 0)

if_eq_node(33, "IF 4.1 · 5 Leads Found?", "={{ $json.route }}", "ready", -660, 0)

add_conn("03 · Dual-Track Parallel Split Router", "4.1A · Prospeo #1 Search")
add_conn("4.1A · Prospeo #1 Search", "4.1P · Prospeo #1 Rate Guard (2s)")
add_conn("4.1P · Prospeo #1 Rate Guard (2s)", "4.1Q · Select Top ICP Candidates (#1)")
add_conn("4.1Q · Select Top ICP Candidates (#1)", "4.1B · Prospeo #1 Enrich Verified")
add_conn("4.1B · Prospeo #1 Enrich Verified", "4.1C · Check Prospeo #1")
add_conn("4.1C · Check Prospeo #1", "IF 4.1 · 5 Leads Found?")


# --- 4.2 PROSPEO ACCOUNT #2 (SEPARATE ACCOUNT FALLBACK #1) ---
http_node(
    34,
    "4.2A · Prospeo #2 Search",
    "POST",
    "={{ ($env.PROSPEO_API_KEY_2 && $json.needed > 0 && !($json.skipProviders || []).includes('prospeo_2')) ? 'https://api.prospeo.io/search-person' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "X-KEY", "value": "={{ $env.PROSPEO_API_KEY_2 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ JSON.stringify(($json.freeLeads && $json.freeLeads.length > 0) ? $json.parsedCriteria.prospeoPayload2 : $json.parsedCriteria.prospeoPayload1) }}",
    -440, 0,
    timeout=30000
)

wait_node(97, "4.2P · Prospeo #2 Rate Guard (2s)", 2, -340, 0)

js_42q = r"""
const st = $('IF 4.1 · 5 Leads Found?').first().json;
const searchResp = $('4.2A · Prospeo #2 Search').first().json || {};
const hasKey = Boolean(($env.PROSPEO_API_KEY_2 || '').trim());
if (!hasKey || st.needed <= 0 || !Array.isArray(searchResp.results) || searchResp.results.length === 0) {
  return [{ json: { skipEnrich: true } }];
}
const kws = (st.parsedCriteria?.industryKeywords || []);
const mustMatch = (st.parsedCriteria?.mustMatchKeywords || []);
const mustExInd = new Set((st.parsedCriteria?.excludeIndustries || []).map(x => String(x).toLowerCase()));
const mustExTerms = (st.parsedCriteria?.mustExcludeTerms || []);
const coreRoots = (st.parsedCriteria?.coreNicheRoots || []);
const roleHint = String(st.parsedCriteria?.primaryRoleHint || '').toLowerCase();
const exCos = new Set((st.excludeCompanies || []).map(c => String(c).toLowerCase().replace(/[^a-z0-9]/g, '')));
const exKeys = new Set((st.excludedLeadKeys || []).map(k => String(k).toLowerCase()));
const scored = searchResp.results.map((r, i) => {
  const p = r.person || r;
  const c = r.company || {};
  const cInd = String(c.industry || '').toLowerCase().trim();
  const cNameLow = String(c.name || '').toLowerCase();
  const cDescLow = `${c.description_ai || ''} ${c.description_seo || ''} ${c.description || ''} ${(c.keywords || []).join(' ')}`.toLowerCase();
  const hay = `${cNameLow} ${cInd} ${cDescLow} ${p.headline || ''} ${p.current_job_title || ''}`.toLowerCase();

  let rejected = false;
  if (cInd && mustExInd.has(cInd)) rejected = true;
  const nameHasCore = coreRoots.length > 0 && coreRoots.some(rt => rt && cNameLow.includes(rt));
  if (!nameHasCore && mustExTerms.length > 0 && mustExTerms.some(bad => bad && cDescLow.includes(bad))) {
    rejected = true;
  }
  if (mustMatch.length > 0 && !mustMatch.some(mk => mk && (cNameLow.includes(mk) || cDescLow.includes(mk) || cInd.includes(mk)))) {
    rejected = true;
  }

  let sc = 0;
  if (nameHasCore) sc += 8;
  for (const kw of kws) { if (kw && hay.includes(kw)) sc += 3; }
  for (const mk of mustMatch) { if (mk && (cNameLow.includes(mk) || cDescLow.includes(mk))) sc += 4; }
  if (roleHint && String(p.current_job_title || '').toLowerCase().includes(roleHint)) sc += 4;
  return { r, sc, i, rejected };
}).filter(x => !x.rejected).sort((a, b) => (b.sc - a.sc) || (a.i - b.i));

const seenCo = new Set((st.freeLeads || []).map(l => String(l.companyName || '').toLowerCase().replace(/[^a-z0-9]/g, '')));
const items = [];
const maxPick = Math.min(5, st.needed || 5);
for (const { r, sc } of scored) {
  if (items.length >= maxPick) break;
  if (st.parsedCriteria?.strictIndustry && !st.parsedCriteria?.hasProspeoIndustryFilter && sc <= 0) continue;
  const p = r.person || r;
  const c = r.company || {};
  const coName = String(c.name || '').trim();
  const coNorm = coName.toLowerCase().replace(/[^a-z0-9]/g, '');
  const nmNorm = String(p.full_name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const dom = String(c.domain || c.website || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').split('/')[0];
  if (!p.person_id || !coName) continue;
  if (exCos.has(coNorm) || seenCo.has(coNorm) || (dom && exKeys.has(dom)) || exKeys.has(`${dom}|${nmNorm}`)) continue;
  seenCo.add(coNorm);
  items.push({ json: { skipEnrich: false, person_id: p.person_id, fallbackCompany: coName } });
}
return items.length > 0 ? items : [{ json: { skipEnrich: true } }];
"""
code_node(99, "4.2Q · Select Top ICP Candidates (#2)", js_42q, -230, 0)

http_node(
    35,
    "4.2B · Prospeo #2 Enrich Verified",
    "POST",
    "={{ (!$json.skipEnrich && $env.PROSPEO_API_KEY_2 && $json.person_id) ? 'https://api.prospeo.io/enrich-person' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "X-KEY", "value": "={{ $env.PROSPEO_API_KEY_2 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ JSON.stringify({ only_verified_email: true, data: { person_id: $json.person_id } }) }}",
    -110, 0,
    timeout=35000,
    batch_interval_ms=1450
)

js_42c = HELPER_DEDUPE_FN + r"""
const prev = $('IF 4.1 · 5 Leads Found?').first().json;
const searchResp = $('4.2A · Prospeo #2 Search').first().json || {};
const enrichItems = $input.all().map(x => x.json || {});
const hasKey = Boolean(($env.PROSPEO_API_KEY_2 || '').trim());

let added = [];
let statusNote = 'skipped_no_api_key (0 credits)';

if (hasKey) {
  const validItems = enrichItems.filter(it => it && it.error === false && it.person);
  if (validItems.length > 0) {
    added = validItems.map(item => {
      const p = item.person || {};
      const c = item.company || p.company || {};
      const emailObj = p.email || item.email || {};
      const emailStr = typeof emailObj === 'string' ? emailObj : (emailObj.email || '');
      const website = String(c.website || (c.domain ? `https://${c.domain}` : '') || '').trim();
      const domain = String(c.domain || website).replace(/^https?:\/\/(www\.)?/i, '').split('/')[0].toLowerCase();
      const cLoc = (typeof c.location === 'object' && c.location) ? [c.location.city, c.location.state, c.location.country].filter(Boolean).join(', ') : '';
      const pLoc = (typeof p.location === 'object' && p.location) ? [p.location.city, p.location.state, p.location.country].filter(Boolean).join(', ') : String(p.location || '');
      return {
        companyName: String(c.name || '').trim(),
        officialWebsite: website,
        domain,
        companySummary: String(c.description_ai || c.description_seo || c.description || c.industry || '').slice(0, 220),
        industry: String(c.industry || ''),
        location: cLoc || pLoc,
        decisionMakerName: String(p.full_name || `${p.first_name || ''} ${p.last_name || ''}`).trim(),
        jobTitle: String(p.current_job_title || p.job_title || p.title || 'Decision Maker').trim(),
        linkedinRaw: String(p.linkedin_url || '').trim(),
        email: String(emailStr || '').toLowerCase().trim(),
        emailVerified: Boolean(emailStr && String(emailStr).includes('@')),
        verificationStatus: 'valid',
        verifiedBy: 'prospeo_2_verified',
        verificationSource: 'prospeo_2_verified',
        sourceProvider: 'prospeo_acc_2'
      };
    }).filter(l => l.emailVerified && l.companyName);
    statusNote = `called_prospeo_2 (searchFree=${Boolean(searchResp.free)}, verified=${added.length})`;
  } else {
    const errItem = enrichItems.find(it => it && it.error);
    statusNote = searchResp.error ? `prospeo_2_search_err (${searchResp.error_code || 'err'})` : (errItem ? `prospeo_2_enrich_err (${errItem.error_code || 'err'})` : 'prospeo_2_0_verified');
  }
}

const merged = mergeUniqueLeads(prev.freeLeads, added, prev.excludedLeadKeys, prev.excludeCompanies, 5);
return [{
  json: {
    ...prev,
    freeLeads: merged,
    needed: Math.max(0, 5 - merged.length),
    providerTrace: [...prev.providerTrace, { provider: 'prospeo_acc_2', status: statusNote, totalSoFar: merged.length }],
    route: merged.length >= 5 ? 'ready' : 'continue'
  }
}];
"""
code_node(36, "4.2C · Check Prospeo #2", js_42c, 10, 0)

if_eq_node(37, "IF 4.2 · 5 Leads Found?", "={{ $json.route }}", "ready", 200, 0)

add_conn("IF 4.1 · 5 Leads Found?", "4.2A · Prospeo #2 Search", src_output=1)
add_conn("4.2A · Prospeo #2 Search", "4.2P · Prospeo #2 Rate Guard (2s)")
add_conn("4.2P · Prospeo #2 Rate Guard (2s)", "4.2Q · Select Top ICP Candidates (#2)")
add_conn("4.2Q · Select Top ICP Candidates (#2)", "4.2B · Prospeo #2 Enrich Verified")
add_conn("4.2B · Prospeo #2 Enrich Verified", "4.2C · Check Prospeo #2")
add_conn("4.2C · Check Prospeo #2", "IF 4.2 · 5 Leads Found?")


# --- 4.25 CLAY ACCOUNT #1 (FALLBACK AFTER PROSPEO #2, BEFORE CLAY #2 -> HUNTER -> APOLLO) ---
http_node(
    130,
    "4.25A · Clay #1 Create Search",
    "POST",
    "={{ ($env.CLAY_API_KEY_1 && $json.needed > 0 && !($json.skipProviders || []).includes('clay_1')) ? 'https://api.clay.com/public/v0/search/query-mode' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "clay-api-key", "value": "={{ $env.CLAY_API_KEY_1 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Accept", "value": "application/json"}
    ],
    "={{ JSON.stringify({ query: $json.parsedCriteria.claySearchQuery }) }}",
    380, 0,
    timeout=45000
)

http_node(
    131,
    "4.25B · Clay #1 Run People Search",
    "POST",
    "={{ ($env.CLAY_API_KEY_1 && $json.search_id) ? ('https://api.clay.com/public/v0/search/query-mode/' + encodeURIComponent($json.search_id) + '/run') : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "clay-api-key", "value": "={{ $env.CLAY_API_KEY_1 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Accept", "value": "application/json"}
    ],
    "={{ JSON.stringify({ limit: 18 }) }}",
    530, 0,
    timeout=60000
)

js_425q = r"""
const st = $('IF 4.2 · 5 Leads Found?').first().json;
const createResp = $('4.25A · Clay #1 Create Search').first().json || {};
const runResp = $input.first().json || {};
const hasKey = Boolean(($env.CLAY_API_KEY_1 || '').trim());
if (!hasKey || st.needed <= 0 || !Array.isArray(runResp.data) || runResp.data.length === 0) {
  return [{ json: { skipClayVerify: true, clayCandidates: [], clayNeeded: 0, clayError: createResp.message || runResp.message || '' } }];
}
const domMap = (st.parsedCriteria && st.parsedCriteria.websiteByCompanyNorm) || {};
const mustExTerms = (st.parsedCriteria && st.parsedCriteria.mustExcludeTerms) || [];
const exCos = new Set([
  ...(st.excludeCompanies || []),
  ...((st.freeLeads || []).map(l => l.companyName))
].map(c => String(c || '').toLowerCase().replace(/[^a-z0-9]/g, '')).filter(Boolean));

const seenCo = new Set();
const cands = [];
for (const p of runResp.data) {
  if (cands.length >= Math.min(12, (st.needed || 5) + 7)) break;
  const exp = (Array.isArray(p.matched_experiences) && p.matched_experiences[0]) || {};
  const coName = String(exp.company || '').trim();
  const fullName = String(p.name || `${p.first_name || ''} ${p.last_name || ''}`).trim();
  const coNorm = coName.toLowerCase().replace(/[^a-z0-9]/g, '');
  if (!coName || !fullName || !coNorm || exCos.has(coNorm) || seenCo.has(coNorm)) continue;
  if (mustExTerms.length > 0 && mustExTerms.some(bad => bad && coName.toLowerCase().includes(bad))) continue;
  seenCo.add(coNorm);
  const knownDom = domMap[coNorm] || '';
  const locObj = p.location || {};
  const locStr = String(locObj.name || [locObj.city, locObj.state_or_province].filter(Boolean).join(', ') || exp.location || '').trim();
  cands.push({
    companyName: coName,
    domain: knownDom,
    officialWebsite: knownDom ? `https://${knownDom}` : '',
    companySummary: `${coName} — ${String(exp.title || 'Decision Maker').trim()}`,
    industry: (st.parsedCriteria && st.parsedCriteria.industries && st.parsedCriteria.industries[0]) || '',
    location: locStr,
    decisionMakerName: fullName,
    jobTitle: String(exp.title || 'Decision Maker').trim(),
    linkedinRaw: String(p.linkedin_url || '').trim(),
    sourceProvider: 'clay_acc_1'
  });
}
return [{ json: { skipClayVerify: cands.length === 0, clayCandidates: cands, clayNeeded: Math.min(5, st.needed || 5), clayError: '' } }];
"""
code_node(132, "4.25Q · Filter Clay #1 Pure Candidates", js_425q, 680, 0)

http_node(
    133,
    "4.25E · Clay #1 Email Resolver & Verifier",
    "POST",
    "={{ (!$json.skipClayVerify && $json.clayCandidates && $json.clayCandidates.length > 0) ? 'http://172.18.0.1:8097/mailmeteor/verify-leads' : 'http://127.0.0.1:5678/healthz' }}",
    [{"name": "Content-Type", "value": "application/json"}],
    "={{ JSON.stringify({ leads: $json.clayCandidates || [], needed: $json.clayNeeded || 5, enableSmartGuesser: true, perLeadTimeoutSec: 7.5, maxTotalGuessSec: 18.0, sourceProvider: 'clay_acc_1' }) }}",
    830, 0,
    timeout=75000
)

js_425c = HELPER_DEDUPE_FN + r"""
const prev = $('IF 4.2 · 5 Leads Found?').first().json;
const createResp = $('4.25A · Clay #1 Create Search').first().json || {};
const prep = $('4.25Q · Filter Clay #1 Pure Candidates').first().json || {};
const verResp = $input.first().json || {};
const hasKey = Boolean(($env.CLAY_API_KEY_1 || '').trim());

let added = [];
let statusNote = 'skipped_no_api_key (0 credits)';

if (hasKey && prev.needed > 0) {
  const vList = Array.isArray(verResp.verifiedLeads) ? verResp.verifiedLeads : [];
  if (vList.length > 0) {
    added = vList.map(l => ({
      ...l,
      emailVerified: true,
      verificationStatus: l.mailmeteorStatus === 'valid' ? 'valid' : 'accept_all',
      verifiedBy: l.verificationSource || 'clay_1_verified',
      sourceProvider: 'clay_acc_1'
    }));
    statusNote = `called_clay_1 (candidates=${(prep.clayCandidates || []).length}, verified=${added.length})`;
  } else {
    statusNote = createResp.message ? `clay_1_err (${createResp.message})` : `clay_1_0_verified`;
  }
}

const merged = mergeUniqueLeads(prev.freeLeads || [], added, prev.excludedLeadKeys, prev.excludeCompanies, 5);
return [{
  json: {
    ...prev,
    freeLeads: merged,
    needed: Math.max(0, 5 - merged.length),
    providerTrace: [...(prev.providerTrace || []), { provider: 'clay_acc_1', status: statusNote, totalSoFar: merged.length }],
    route: merged.length >= 5 ? 'ready' : 'continue'
  }
}];
"""
code_node(134, "4.25C · Check Clay #1", js_425c, 980, 0)
if_eq_node(135, "IF 4.25 · 5 Leads Found?", "={{ $json.route }}", "ready", 1130, 0)

add_conn("IF 4.2 · 5 Leads Found?", "4.25A · Clay #1 Create Search", src_output=1)
add_conn("4.25A · Clay #1 Create Search", "4.25B · Clay #1 Run People Search")
add_conn("4.25B · Clay #1 Run People Search", "4.25Q · Filter Clay #1 Pure Candidates")
add_conn("4.25Q · Filter Clay #1 Pure Candidates", "4.25E · Clay #1 Email Resolver & Verifier")
add_conn("4.25E · Clay #1 Email Resolver & Verifier", "4.25C · Check Clay #1")
add_conn("4.25C · Check Clay #1", "IF 4.25 · 5 Leads Found?")


# --- 4.26 CLAY ACCOUNT #2 (FALLBACK AFTER CLAY #1, BEFORE HUNTER -> APOLLO) ---
http_node(
    136,
    "4.26A · Clay #2 Create Search",
    "POST",
    "={{ ($env.CLAY_API_KEY_2 && $json.needed > 0 && !($json.skipProviders || []).includes('clay_2')) ? 'https://api.clay.com/public/v0/search/query-mode' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "clay-api-key", "value": "={{ $env.CLAY_API_KEY_2 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Accept", "value": "application/json"}
    ],
    "={{ JSON.stringify({ query: $json.parsedCriteria.claySearchQuery }) }}",
    1290, 0,
    timeout=45000
)

http_node(
    137,
    "4.26B · Clay #2 Run People Search",
    "POST",
    "={{ ($env.CLAY_API_KEY_2 && $json.search_id) ? ('https://api.clay.com/public/v0/search/query-mode/' + encodeURIComponent($json.search_id) + '/run') : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "clay-api-key", "value": "={{ $env.CLAY_API_KEY_2 ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Accept", "value": "application/json"}
    ],
    "={{ JSON.stringify({ limit: 18 }) }}",
    1440, 0,
    timeout=60000
)

js_426q = r"""
const st = $('IF 4.25 · 5 Leads Found?').first().json;
const createResp = $('4.26A · Clay #2 Create Search').first().json || {};
const runResp = $input.first().json || {};
const hasKey = Boolean(($env.CLAY_API_KEY_2 || '').trim());
if (!hasKey || st.needed <= 0 || !Array.isArray(runResp.data) || runResp.data.length === 0) {
  return [{ json: { skipClayVerify: true, clayCandidates: [], clayNeeded: 0, clayError: createResp.message || runResp.message || '' } }];
}
const domMap = (st.parsedCriteria && st.parsedCriteria.websiteByCompanyNorm) || {};
const mustExTerms = (st.parsedCriteria && st.parsedCriteria.mustExcludeTerms) || [];
const exCos = new Set([
  ...(st.excludeCompanies || []),
  ...((st.freeLeads || []).map(l => l.companyName))
].map(c => String(c || '').toLowerCase().replace(/[^a-z0-9]/g, '')).filter(Boolean));

const seenCo = new Set();
const cands = [];
for (const p of runResp.data) {
  if (cands.length >= Math.min(12, (st.needed || 5) + 7)) break;
  const exp = (Array.isArray(p.matched_experiences) && p.matched_experiences[0]) || {};
  const coName = String(exp.company || '').trim();
  const fullName = String(p.name || `${p.first_name || ''} ${p.last_name || ''}`).trim();
  const coNorm = coName.toLowerCase().replace(/[^a-z0-9]/g, '');
  if (!coName || !fullName || !coNorm || exCos.has(coNorm) || seenCo.has(coNorm)) continue;
  if (mustExTerms.length > 0 && mustExTerms.some(bad => bad && coName.toLowerCase().includes(bad))) continue;
  seenCo.add(coNorm);
  const knownDom = domMap[coNorm] || '';
  const locObj = p.location || {};
  const locStr = String(locObj.name || [locObj.city, locObj.state_or_province].filter(Boolean).join(', ') || exp.location || '').trim();
  cands.push({
    companyName: coName,
    domain: knownDom,
    officialWebsite: knownDom ? `https://${knownDom}` : '',
    companySummary: `${coName} — ${String(exp.title || 'Decision Maker').trim()}`,
    industry: (st.parsedCriteria && st.parsedCriteria.industries && st.parsedCriteria.industries[0]) || '',
    location: locStr,
    decisionMakerName: fullName,
    jobTitle: String(exp.title || 'Decision Maker').trim(),
    linkedinRaw: String(p.linkedin_url || '').trim(),
    sourceProvider: 'clay_acc_2'
  });
}
return [{ json: { skipClayVerify: cands.length === 0, clayCandidates: cands, clayNeeded: Math.min(5, st.needed || 5), clayError: '' } }];
"""
code_node(138, "4.26Q · Filter Clay #2 Pure Candidates", js_426q, 1590, 0)

http_node(
    139,
    "4.26E · Clay #2 Email Resolver & Verifier",
    "POST",
    "={{ (!$json.skipClayVerify && $json.clayCandidates && $json.clayCandidates.length > 0) ? 'http://172.18.0.1:8097/mailmeteor/verify-leads' : 'http://127.0.0.1:5678/healthz' }}",
    [{"name": "Content-Type", "value": "application/json"}],
    "={{ JSON.stringify({ leads: $json.clayCandidates || [], needed: $json.clayNeeded || 5, enableSmartGuesser: true, perLeadTimeoutSec: 7.5, maxTotalGuessSec: 18.0, sourceProvider: 'clay_acc_2' }) }}",
    1740, 0,
    timeout=75000
)

js_426c = HELPER_DEDUPE_FN + r"""
const prev = $('IF 4.25 · 5 Leads Found?').first().json;
const createResp = $('4.26A · Clay #2 Create Search').first().json || {};
const prep = $('4.26Q · Filter Clay #2 Pure Candidates').first().json || {};
const verResp = $input.first().json || {};
const hasKey = Boolean(($env.CLAY_API_KEY_2 || '').trim());

let added = [];
let statusNote = 'skipped_no_api_key (0 credits)';

if (hasKey && prev.needed > 0) {
  const vList = Array.isArray(verResp.verifiedLeads) ? verResp.verifiedLeads : [];
  if (vList.length > 0) {
    added = vList.map(l => ({
      ...l,
      emailVerified: true,
      verificationStatus: l.mailmeteorStatus === 'valid' ? 'valid' : 'accept_all',
      verifiedBy: l.verificationSource || 'clay_2_verified',
      sourceProvider: 'clay_acc_2'
    }));
    statusNote = `called_clay_2 (candidates=${(prep.clayCandidates || []).length}, verified=${added.length})`;
  } else {
    statusNote = createResp.message ? `clay_2_err (${createResp.message})` : `clay_2_0_verified`;
  }
}

const merged = mergeUniqueLeads(prev.freeLeads || [], added, prev.excludedLeadKeys, prev.excludeCompanies, 5);
return [{
  json: {
    ...prev,
    freeLeads: merged,
    needed: Math.max(0, 5 - merged.length),
    providerTrace: [...(prev.providerTrace || []), { provider: 'clay_acc_2', status: statusNote, totalSoFar: merged.length }],
    route: merged.length >= 5 ? 'ready' : 'continue'
  }
}];
"""
code_node(140, "4.26C · Check Clay #2", js_426c, 1890, 0)
if_eq_node(141, "IF 4.26 · 5 Leads Found?", "={{ $json.route }}", "ready", 2040, 0)

add_conn("IF 4.25 · 5 Leads Found?", "4.26A · Clay #2 Create Search", src_output=1)
add_conn("4.26A · Clay #2 Create Search", "4.26B · Clay #2 Run People Search")
add_conn("4.26B · Clay #2 Run People Search", "4.26Q · Filter Clay #2 Pure Candidates")
add_conn("4.26Q · Filter Clay #2 Pure Candidates", "4.26E · Clay #2 Email Resolver & Verifier")
add_conn("4.26E · Clay #2 Email Resolver & Verifier", "4.26C · Check Clay #2")
add_conn("4.26C · Check Clay #2", "IF 4.26 · 5 Leads Found?")


# --- 4.3 HUNTER.IO API (FALLBACK AFTER CLAY #2) ---
http_node(
    38,
    "4.3A · Hunter Free Discover",
    "POST",
    "={{ ($env.HUNTER_API_KEY && $json.needed > 0 && !($json.skipProviders || []).includes('hunter')) ? ('https://api.hunter.io/v2/discover?api_key=' + encodeURIComponent($env.HUNTER_API_KEY)) : 'http://127.0.0.1:5678/healthz' }}",
    [{"name": "Content-Type", "value": "application/json"}],
    "={{ JSON.stringify({ query: $json.prompt, limit: 10 }) }}",
    2200, 0,
    timeout=30000
)

js_43q = r"""
const st = $('IF 4.26 · 5 Leads Found?').first().json;
const discResp = $input.first().json || {};
const hasKey = Boolean(($env.HUNTER_API_KEY || '').trim());
if (!hasKey || st.needed <= 0 || (st.skipProviders || []).includes('hunter')) {
  return [{ json: { skipHunterDomain: true, domain: '' } }];
}
const exCos = new Set([
  ...(st.excludeCompanies || []),
  ...((st.freeLeads || []).map(l => l.companyName))
].map(c => String(c || '').toLowerCase().replace(/[^a-z0-9]/g, '')).filter(Boolean));
const exDoms = new Set([
  ...(st.excludedLeadKeys || []),
  ...((st.freeLeads || []).map(l => l.domain))
].map(d => String(d || '').toLowerCase().trim()).filter(Boolean));

const seenDom = new Set();
const out = [];
const maxDomains = Math.min(6, (st.needed || 5) + 1);

const pushCand = (domRaw, orgRaw) => {
  if (out.length >= maxDomains) return;
  const dom = String(domRaw || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').split('/')[0].trim();
  const orgNorm = String(orgRaw || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  if (!dom || !dom.includes('.') || seenDom.has(dom) || exDoms.has(dom)) return;
  if (orgNorm && exCos.has(orgNorm)) return;
  seenDom.add(dom);
  out.push({ json: { skipHunterDomain: false, domain: dom, fallbackOrg: String(orgRaw || '').trim() } });
};

for (const item of (Array.isArray(discResp.data) ? discResp.data : [])) {
  pushCand(item.domain, item.organization || item.domain);
}
const tw = (st.parsedCriteria && st.parsedCriteria.targetWebsites) || [];
const tn = (st.parsedCriteria && st.parsedCriteria.targetCompanyNames) || [];
for (let i = 0; i < tw.length && out.length < maxDomains; i++) {
  pushCand(tw[i], tn[i] || tw[i]);
}

if (out.length === 0) {
  return [{ json: { skipHunterDomain: true, domain: '' } }];
}
return out;
"""
code_node(142, "4.3Q · Select Top Hunter Domains", js_43q, 2340, 0)

http_node(
    39,
    "4.3B · Hunter Domain Finder",
    "GET",
    "={{ ($env.HUNTER_API_KEY && !$json.skipHunterDomain && $json.domain) ? ('https://api.hunter.io/v2/domain-search?domain=' + encodeURIComponent($json.domain) + '&type=personal&limit=5&api_key=' + encodeURIComponent($env.HUNTER_API_KEY)) : 'http://127.0.0.1:5678/healthz' }}",
    [{"name": "Accept", "value": "application/json"}],
    None,
    2480, 0,
    timeout=30000,
    batch_interval_ms=300
)

js_43c = HELPER_DEDUPE_FN + r"""
const prev = $('IF 4.26 · 5 Leads Found?').first().json;
const discResp = $('4.3A · Hunter Free Discover').first().json || {};
const domItems = $input.all().map(x => x.json || {});
const hasKey = Boolean(($env.HUNTER_API_KEY || '').trim());

let added = [];
let statusNote = 'skipped_no_api_key (0 credits)';

if ((prev.skipProviders || []).includes('hunter')) {
  statusNote = 'skipped_test_override';
} else if (hasKey && prev.needed > 0) {
  const execRx = /\b(founder|co-founder|ceo|chief|managing director|director|owner|president|partner|vp|vice president|head)\b/i;
  for (const domResp of domItems) {
    const dData = domResp.data || {};
    const emails = Array.isArray(dData.emails) ? dData.emails : [];
    const org = String(dData.organization || dData.domain || '').trim();
    const domain = String(dData.domain || '').toLowerCase().trim();
    if (!domain || emails.length === 0) continue;
    // Rank personal executive emails first, then highest confidence
    const ranked = [...emails].sort((a, b) => {
      const aExec = execRx.test(`${a.position || ''} ${a.seniority || ''}`) ? 1 : 0;
      const bExec = execRx.test(`${b.position || ''} ${b.seniority || ''}`) ? 1 : 0;
      if (bExec !== aExec) return bExec - aExec;
      const aNamed = (a.first_name || a.last_name) ? 1 : 0;
      const bNamed = (b.first_name || b.last_name) ? 1 : 0;
      if (bNamed !== aNamed) return bNamed - aNamed;
      return (b.confidence || 0) - (a.confidence || 0);
    });
    const best = ranked[0];
    if (best && best.value) {
      added.push({
        companyName: org || domain,
        officialWebsite: domain ? `https://${domain}` : '',
        domain,
        companySummary: String(dData.description || dData.industry || '').slice(0, 200),
        industry: String(dData.industry || ''),
        location: String([dData.city, dData.state, dData.country].filter(Boolean).join(', ') || ''),
        decisionMakerName: `${best.first_name || ''} ${best.last_name || ''}`.trim() || 'Executive Contact',
        jobTitle: String(best.position || best.seniority || 'Decision Maker').trim(),
        linkedinRaw: String(best.linkedin || '').trim(),
        email: String(best.value || '').toLowerCase().trim(),
        verificationStatus: best.verification?.status === 'valid' ? 'valid' : ((best.confidence || 0) >= 80 ? 'valid' : 'accept_all'),
        verifiedBy: 'hunter_finder_included',
        sourceProvider: 'hunter_api'
      });
    }
  }
  if (added.length > 0) {
    statusNote = `called_hunter (domains=${domItems.length}, found=${added.length})`;
  } else {
    statusNote = discResp.errors ? `hunter_error` : 'hunter_0_matches';
  }
}

const merged = mergeUniqueLeads(prev.freeLeads || [], added, prev.excludedLeadKeys, prev.excludeCompanies, prev.maxLeads);
const needed = Math.max(0, prev.maxLeads - merged.length);

return [{
  json: {
    ...prev,
    freeLeads: merged,
    needed,
    providerTrace: [...(prev.providerTrace || []), { provider: 'hunter_api', status: statusNote, totalSoFar: merged.length }],
    route: merged.length >= prev.maxLeads ? 'ready' : 'need_more'
  }
}];
"""
code_node(40, "4.3C · Check Hunter.io", js_43c, 2620, 0)
if_eq_node(41, "IF 4.3 · 5 Leads Found?", "={{ $json.route }}", "ready", 2760, 0)

add_conn("IF 4.26 · 5 Leads Found?", "4.3A · Hunter Free Discover", src_output=1)
add_conn("4.3A · Hunter Free Discover", "4.3Q · Select Top Hunter Domains")
add_conn("4.3Q · Select Top Hunter Domains", "4.3B · Hunter Domain Finder")
add_conn("4.3B · Hunter Domain Finder", "4.3C · Check Hunter.io")
add_conn("4.3C · Check Hunter.io", "IF 4.3 · 5 Leads Found?")


# --- 4.4 APOLLO.IO API (FALLBACK AFTER HUNTER) + 4.5 EXPANDABLE SLOT ---
http_node(
    42,
    "4.4A · Apollo People Search",
    "POST",
    "={{ ($env.APOLLO_API_KEY && $json.needed > 0 && !($json.skipProviders || []).includes('apollo')) ? 'https://api.apollo.io/api/v1/mixed_people/search' : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "x-api-key", "value": "={{ $env.APOLLO_API_KEY ?? '' }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ JSON.stringify({ page: $json.batchNumber || 1, per_page: Math.min(5, $json.needed || 5), person_titles: $json.parsedCriteria.roles, ...( $json.parsedCriteria.location ? { person_locations: [$json.parsedCriteria.location] } : {} ), q_keywords: $json.prompt.slice(0, 120) }) }}",
    2960, 0,
    timeout=15000
)

js_44b = HELPER_DEDUPE_FN + r"""
const prev = $('IF 4.3 · 5 Leads Found?').first().json;
const apResp = $input.first().json || {};
const hasKey = Boolean(($env.APOLLO_API_KEY || '').trim());

let added = [];
let statusNote = 'skipped_no_api_key (0 credits)';

if (hasKey && prev.needed > 0) {
  const people = Array.isArray(apResp.people) ? apResp.people : (Array.isArray(apResp.contacts) ? apResp.contacts : []);
  if (people.length > 0) {
    added = people.map(p => {
      const org = p.organization || {};
      const website = String(org.website_url || '').trim();
      const domain = String(org.primary_domain || website.replace(/^https?:\/\/(www\.)?/i, '').split('/')[0] || '').toLowerCase();
      const email = String(p.email || '').toLowerCase().trim();
      const validEmail = (email && !email.includes('email_not_unlocked')) ? email : '';
      return {
        companyName: String(org.name || p.organization_name || '').trim(),
        officialWebsite: website || (domain ? `https://${domain}` : ''),
        domain,
        companySummary: String(org.short_description || org.industry || '').slice(0, 200),
        industry: String(org.industry || ''),
        location: [p.city, p.country].filter(Boolean).join(', '),
        decisionMakerName: String(p.name || `${p.first_name || ''} ${p.last_name || ''}`).trim(),
        jobTitle: String(p.title || 'Decision Maker').trim(),
        linkedinRaw: String(p.linkedin_url || '').trim(),
        email: validEmail,
        verificationStatus: validEmail ? (p.email_status === 'verified' ? 'valid' : 'accept_all') : 'missing',
        verifiedBy: 'apollo_api',
        sourceProvider: 'apollo_api'
      };
    }).filter(x => x.email && x.companyName);
    statusNote = `called_apollo (found ${added.length})`;
  } else {
    statusNote = apResp.error_code === 'API_INACCESSIBLE' ? 'apollo_free_plan_search_restricted (0 credits)' : (apResp.error ? 'apollo_error' : 'apollo_0_matches');
  }
}

const merged = mergeUniqueLeads(prev.freeLeads || [], added, prev.excludedLeadKeys, prev.excludeCompanies, prev.maxLeads);
const needed = Math.max(0, prev.maxLeads - merged.length);

return [{
  json: {
    ...prev,
    freeLeads: merged,
    needed,
    providerTrace: [...(prev.providerTrace || []), { provider: 'apollo_api', status: statusNote, totalSoFar: merged.length }],
    route: merged.length >= prev.maxLeads ? 'ready' : 'need_more'
  }
}];
"""
code_node(43, "4.4B · Check Apollo.io", js_44b, 3140, 0)
if_eq_node(44, "IF 4.4 · 5 Leads Found?", "={{ $json.route }}", "ready", 3320, 0)

js_45_slot = r"""
// +4.5 EXPANDABLE WATERFALL SLOT:
// Future Free Lead APIs (e.g., Snov.io, RocketReach, Dropcontact) can be inserted right here!
const prev = $input.first().json;
return [{
  json: {
    ...prev,
    track: 'free_chain',
    bypassUsed: false
  }
}];
"""
code_node(45, "+4.5 · Future Free Lead API Slot", js_45_slot, 3520, 0, notes="Expandable Branch: Plug Snov.io / RocketReach here")

js_green_rail = r"""
// GREEN EXPRESS BYPASS RAIL:
// Triggered immediately as soon as ANY provider in Stage 04 reaches 5 unique leads!
// Skips all remaining downstream lead providers to save API credits.
const prev = $input.first().json;
return [{
  json: {
    ...prev,
    track: 'free_chain',
    bypassUsed: true
  }
}];
"""
code_node(46, "Green Express Bypass Rail (Skip Unused APIs)", js_green_rail, 3520, 260, notes="Saves credits by skipping remaining APIs")

add_conn("IF 4.3 · 5 Leads Found?", "4.4A · Apollo People Search", src_output=1)
add_conn("4.4A · Apollo People Search", "4.4B · Check Apollo.io")
add_conn("4.4B · Check Apollo.io", "IF 4.4 · 5 Leads Found?")
add_conn("IF 4.4 · 5 Leads Found?", "+4.5 · Future Free Lead API Slot", src_output=1)

# Connect all TRUE (YES: 5 Leads Found) branches onto the Green Express Bypass Rail!
add_conn("IF 4.1 · 5 Leads Found?", "Green Express Bypass Rail (Skip Unused APIs)", src_output=0)
add_conn("IF 4.2 · 5 Leads Found?", "Green Express Bypass Rail (Skip Unused APIs)", src_output=0)
add_conn("IF 4.25 · 5 Leads Found?", "Green Express Bypass Rail (Skip Unused APIs)", src_output=0)
add_conn("IF 4.26 · 5 Leads Found?", "Green Express Bypass Rail (Skip Unused APIs)", src_output=0)
add_conn("IF 4.3 · 5 Leads Found?", "Green Express Bypass Rail (Skip Unused APIs)", src_output=0)
add_conn("IF 4.4 · 5 Leads Found?", "Green Express Bypass Rail (Skip Unused APIs)", src_output=0)


# ==================== STAGE 05: SYNC PARALLEL TRACKS, SMART EMAIL GUESSER & MAILMETEOR WEB CHECKER ====================
nodes.append({
    "id": uid(50),
    "name": "Sync · Free Chain + Parallel Race Winner",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 3.2,
    "position": [3800, -140],
    "parameters": {
        "mode": "append",
        "numberInputs": 2,
        "options": {}
    }
})

add_conn("+4.5 · Future Free Lead API Slot", "Sync · Free Chain + Parallel Race Winner", src_output=0, dst_input=0)
add_conn("Green Express Bypass Rail (Skip Unused APIs)", "Sync · Free Chain + Parallel Race Winner", src_output=0, dst_input=0)
add_conn("3C · First-Finish Race Winner (To Mailmeteor)", "Sync · Free Chain + Parallel Race Winner", src_output=0, dst_input=1)

js_step05_eval = r"""
const items = $input.all().map(i => i.json);
const freeItem = items.find(x => Array.isArray(x.freeLeads)) || items[0] || {};
const backupItem = items.find(x => x.track === 'parallel_backup_race') || {};

const freeLeads = Array.isArray(freeItem.freeLeads) ? freeItem.freeLeads : [];
const backupLeads = Array.isArray(backupItem.backupLeads) ? backupItem.backupLeads : [];
const maxLeads = freeItem.maxLeads || 5;

const isSufficient = (!freeItem.forceBackupRaceTest && !freeItem.forceTinyFishPathway) && (freeLeads.length >= maxLeads);

return [{
  json: {
    ...freeItem,
    backupLeads,
    raceWinner: backupItem.raceWinner || 'none',
    raceElapsedMs: backupItem.raceElapsedMs || 0,
    leadpulseStatus: backupItem.leadpulseStatus || 'unknown',
    sufficiency: isSufficient ? 'sufficient' : 'use_race_winner_mailmeteor'
  }
}];
"""
code_node(51, "05 · Evaluate Free Chain Sufficiency", js_step05_eval, 4000, -140)
if_eq_node(52, "05 · Sufficiency Gate (5 Free Leads Ready?)", "={{ $json.sufficiency }}", "sufficient", 4200, -140)

add_conn("Sync · Free Chain + Parallel Race Winner", "05 · Evaluate Free Chain Sufficiency")
add_conn("05 · Evaluate Free Chain Sufficiency", "05 · Sufficiency Gate (5 Free Leads Ready?)")


# --- 5B -> 5G (SMART EMAIL GUESSER) -> 5C (MAILMETEOR OFFICIAL WEB CHECKER) -> 5D ---
js_5b = HELPER_DEDUPE_FN + r"""
const state = $input.first().json;
const existingFree = Array.isArray(state.freeLeads) ? state.freeLeads : [];
const deficit = Math.max(0, (state.maxLeads || 5) - existingFree.length);

// Filter backupLeads so we don't re-check companies already in existingFree or excluded
const exCos = new Set([
  ...(state.excludeCompanies || []),
  ...existingFree.map(l => l.companyName)
].map(c => String(c || '').toLowerCase().replace(/[^a-z0-9]/g, '')).filter(Boolean));

const candidatesForMailmeteor = (state.backupLeads || []).filter(l => {
  const cn = String(l.companyName || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return cn && !exCos.has(cn);
}).slice(0, 18);

return [{
  json: {
    ...state,
    deficitNeeded: deficit,
    leadpulseUsed: true,
    candidatesForMailmeteor
  }
}];
"""
code_node(53, "5B · Send Race Winner to Mailmeteor", js_5b, 4420, -340)

# 5G: Smart Email Pattern Guesser (Between TinyFish & Mailmeteor, Hard Time-Capped so output never lags!)
js_5g = r"""
const state = $input.first().json;
const honorifics = new Set(['mr','ms','mrs','dr','er','shri','smt','prof','ca','cs','decision','maker','executive','contact']);

const enrichedCandidates = (state.candidatesForMailmeteor || []).map(lead => {
  const dom = String(lead.domain || lead.officialWebsite || '')
    .toLowerCase()
    .replace(/^https?:\/\/(www\.)?/, '')
    .split('/')[0]
    .trim();
  const initialEmail = String(lead.email || '').toLowerCase().trim();
  const parts = String(lead.decisionMakerName || '')
    .toLowerCase()
    .split(/\s+/)
    .map(p => p.replace(/[^a-z]/g, ''))
    .filter(p => p.length >= 2 && !honorifics.has(p));

  const smartGuesses = [];
  if (dom && dom.includes('.')) {
    if (parts.length >= 1) {
      const first = parts[0];
      smartGuesses.push(`${first}@${dom}`);
      if (parts.length >= 2) {
        const last = parts[parts.length - 1];
        smartGuesses.push(`${first}.${last}@${dom}`);
        smartGuesses.push(`${first[0]}${last}@${dom}`);
        smartGuesses.push(`${first}${last}@${dom}`);
        smartGuesses.push(`${first}_${last}@${dom}`);
        smartGuesses.push(`${first}${last[0]}@${dom}`);
      }
    }
  }
  const uniqGuesses = Array.from(new Set(smartGuesses)).filter(g => g && g !== initialEmail);
  return {
    ...lead,
    domain: dom || lead.domain || '',
    smartEmailGuesses: uniqGuesses.slice(0, 6)
  };
});

return [{
  json: {
    ...state,
    candidatesForMailmeteor: enrichedCandidates,
    smartGuesserConfig: {
      enabled: true,
      perLeadTimeoutSec: 8.0,
      maxTotalGuessSec: 20.0,
      behaviorOnTimeout: 'abandon_immediately_and_proceed'
    }
  }
}];
"""
code_node(150, "5G · Smart Email Guesser (If Invalid · Time-Capped)", js_5g, 4640, -340, notes="Guesses email patterns if TinyFish email is invalid; strict 8s/lead & 20s max cap")

# 5C: Checks candidate emails ONE BY ONE on https://mailmeteor.com/email-checker + Time-Bounded Smart Guesser!
http_node(
    54,
    "5C · Mailmeteor Web Checker (One-by-One)",
    "POST",
    "={{ ($json.candidatesForMailmeteor && $json.candidatesForMailmeteor.length > 0 && $json.deficitNeeded > 0) ? 'http://172.18.0.1:8097/mailmeteor/verify-leads' : 'http://127.0.0.1:5678/healthz' }}",
    [{"name": "Content-Type", "value": "application/json"}],
    "={{ JSON.stringify({ leads: $json.candidatesForMailmeteor || [], needed: $json.deficitNeeded || 5, enableSmartGuesser: true, perLeadTimeoutSec: ($json.smartGuesserConfig && $json.smartGuesserConfig.perLeadTimeoutSec) || 8.0, maxTotalGuessSec: ($json.smartGuesserConfig && $json.smartGuesserConfig.maxTotalGuessSec) || 20.0 }) }}",
    4860, -340,
    timeout=90000
)

js_5d = HELPER_DEDUPE_FN + r"""
// +5D EXTRA VERIFIER BRANCH SLOT (Attaches One-by-One Mailmeteor + Smart Guesser Results)
const state = $('5G · Smart Email Guesser (If Invalid · Time-Capped)').first().json;
const mmResp = $input.first().json || {};
const gStats = mmResp.guesserStats || {};

const verifiedFromMailmeteor = (Array.isArray(mmResp.verifiedLeads) ? mmResp.verifiedLeads : []).map(l => ({
  ...l,
  emailVerified: true,
  verificationStatus: l.mailmeteorStatus === 'valid' ? 'valid' : 'accept_all',
  verificationSource: l.verificationSource || 'mailmeteor_web_checker',
  verifiedBy: l.verificationSource || 'mailmeteor_web_checker'
}));

const combined = mergeUniqueLeads(
  state.freeLeads || [],
  verifiedFromMailmeteor,
  state.excludedLeadKeys,
  state.excludeCompanies,
  state.maxLeads || 5
);

const checkLog = Array.isArray(mmResp.checkLog) ? mmResp.checkLog : [];
const checkedCount = Number(mmResp.checkedEmailsCount || checkLog.length || 0);

return [{
  json: {
    ...state,
    selectedLeads: combined,
    mailmeteorUsed: checkLog.length > 0,
    mailmeteorCheckedCount: checkedCount,
    mailmeteorCheckLog: checkLog,
    smartGuesserStats: gStats,
    providerTrace: [
      ...(state.providerTrace || []),
      {
        provider: `race_winner (${state.raceWinner || 'backup'}) -> smart_email_guesser (cap ${gStats.perLeadTimeCapSec || 8}s) -> mailmeteor.com/email-checker`,
        status: `race_won_in_${state.raceElapsedMs || 0}ms | guessed_recovered=${gStats.emailsRecoveredByGuesser || 0} | time_cap_dropped=${gStats.abandonedDueToTimeCap || 0} | verified=${verifiedFromMailmeteor.length}`,
        totalSoFar: combined.length
      }
    ]
  }
}];
"""
code_node(55, "+5D · Attach Mailmeteor Results & Extra Slot", js_5d, 5080, -340, notes="One-by-One Mailmeteor Web Result + Expandable Slot")

add_conn("05 · Sufficiency Gate (5 Free Leads Ready?)", "5B · Send Race Winner to Mailmeteor", src_output=1)
add_conn("5B · Send Race Winner to Mailmeteor", "5G · Smart Email Guesser (If Invalid · Time-Capped)")
add_conn("5G · Smart Email Guesser (If Invalid · Time-Capped)", "5C · Mailmeteor Web Checker (One-by-One)")
add_conn("5C · Mailmeteor Web Checker (One-by-One)", "+5D · Attach Mailmeteor Results & Extra Slot")


# ==================== STAGE 06: NORMALIZE, DEDUPLICATE & LOCK EXACT 5 LEADS ====================
js_step06 = HELPER_DEDUPE_FN + r"""
const inp = $input.first().json;
const rawList = Array.isArray(inp.selectedLeads) ? inp.selectedLeads : (Array.isArray(inp.freeLeads) ? inp.freeLeads : []);

const locked = mergeUniqueLeads([], rawList, inp.excludedLeadKeys, inp.excludeCompanies, 5).slice(0, 5);

return [{
  json: {
    requestId: inp.requestId,
    userId: inp.userId,
    prompt: inp.prompt,
    promptKey: inp.promptKey,
    batchNumber: inp.batchNumber,
    maxLeads: 5,
    savedTemplate: inp.savedTemplate,
    excludedLeadKeys: inp.excludedLeadKeys,
    excludeCompanies: inp.excludeCompanies,
    pathway: inp.pathway || 'free_apis',
    leadpulseUsed: Boolean(inp.leadpulseUsed),
    mailmeteorUsed: Boolean(inp.mailmeteorUsed),
    raceWinner: inp.raceWinner || "none",
    raceElapsedMs: Number(inp.raceElapsedMs || 0),
    mailmeteorCheckedCount: Number(inp.mailmeteorCheckedCount || 0),
    mailmeteorCheckLog: inp.mailmeteorCheckLog || [],
    smartGuesserStats: inp.smartGuesserStats || {},
    providerTrace: inp.providerTrace || [],
    lockedLeads: locked
  }
}];
"""
code_node(60, "06 · Normalize, Deduplicate & Lock Exact 5 Leads", js_step06, 5340, 0)

# Connect YES branch of Stage 05 AND Fallback 5D into Stage 06
add_conn("05 · Sufficiency Gate (5 Free Leads Ready?)", "06 · Normalize, Deduplicate & Lock Exact 5 Leads", src_output=0)
add_conn("+5D · Attach Mailmeteor Results & Extra Slot", "06 · Normalize, Deduplicate & Lock Exact 5 Leads", src_output=0)


# ==================== STAGE 07: SMART LINKEDIN (7L) + TINYFISH OFFICIAL WEBSITE (7R) ====================
js_7l = r"""
const state = $input.first().json;
const leads = (state.lockedLeads || []).map(l => {
  const rawLi = String(l.linkedinRaw || '').trim();
  const hasDirect = /^https?:\/\/([a-z]{2,3}\.)?linkedin\.com\/in\//i.test(rawLi);
  const searchKeywords = encodeURIComponent(`${l.decisionMakerName || ''} ${l.companyName || ''}`.trim());
  const searchUrl = `https://www.linkedin.com/search/results/people/?keywords=${searchKeywords}`;

  return {
    ...l,
    linkedin: {
      hasDirectUrl: hasDirect,
      url: hasDirect ? rawLi : searchUrl,
      searchFallbackUrl: searchUrl,
      buttonLabel: hasDirect ? 'Open LinkedIn Profile' : 'Search Name + Company on LinkedIn'
    }
  };
});

// Check if any lead is missing an official website URL so TinyFish is called ONLY if needed!
const firstMissingWebsiteLead = leads.find(l => !l.officialWebsite);

return [{
  json: {
    ...state,
    lockedLeads: leads,
    needsTinyFishWebsite: Boolean(firstMissingWebsiteLead),
    tinyFishQuery: firstMissingWebsiteLead ? `${firstMissingWebsiteLead.companyName} official website` : ''
  }
}];
"""
code_node(70, "7L · Smart LinkedIn Profile / Search Builder", js_7l, 5580, 0)

http_node(
    71,
    "7R · TinyFish API — Official Website Finder",
    "GET",
    "={{ ($json.needsTinyFishWebsite && $env.TINYFISH_KEY) ? (($env.TINYFISH_SEARCH || 'https://api.search.tinyfish.ai') + '/?query=' + encodeURIComponent($json.tinyFishQuery) + '&page=0') : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "X-API-Key", "value": "={{ $env.TINYFISH_KEY ?? '' }}"},
        {"name": "Accept", "value": "application/json"}
    ],
    None,
    5820, 0,
    timeout=35000
)

js_7r_slot = r"""
// +7R EXTRA WEBSITE SCRAPER BRANCH SLOT (Firecrawl / Jina Reader can plug here)
const state = $('7L · Smart LinkedIn Profile / Search Builder').first().json;
const tfResp = $input.first().json || {};
let tfUsed = false;

let foundUrl = '';
let foundSnippet = '';
const results = Array.isArray(tfResp.results) ? tfResp.results : (Array.isArray(tfResp.organic) ? tfResp.organic : []);
if (state.needsTinyFishWebsite && results.length > 0) {
  const good = results.find(r => r.url && !/linkedin\.com|facebook\.com|instagram\.com|youtube\.com|wikipedia\.org|zaubacorp|indiabiz/i.test(r.url)) || results[0];
  if (good && good.url) {
    foundUrl = String(good.url).trim();
    foundSnippet = String(good.snippet || good.description || '').slice(0, 200);
    tfUsed = true;
  }
}

let patchedFirst = false;
const enriched = (state.lockedLeads || []).map(l => {
  if (!l.officialWebsite && foundUrl && !patchedFirst) {
    patchedFirst = true;
    const dom = foundUrl.replace(/^https?:\/\/(www\.)?/i, '').split('/')[0].toLowerCase();
    return {
      ...l,
      officialWebsite: foundUrl,
      domain: l.domain || dom,
      companySummary: l.companySummary || foundSnippet
    };
  }
  return l;
});

return [{
  json: {
    ...state,
    lockedLeads: enriched,
    tinyFishUsed: tfUsed
  }
}];
"""
code_node(72, "+7R · Attach Website & Extra Scraper Slot", js_7r_slot, 6060, 0, notes="Expandable Research Slot")

add_conn("06 · Normalize, Deduplicate & Lock Exact 5 Leads", "7L · Smart LinkedIn Profile / Search Builder")
add_conn("7L · Smart LinkedIn Profile / Search Builder", "7R · TinyFish API — Official Website Finder")
add_conn("7R · TinyFish API — Official Website Finder", "+7R · Attach Website & Extra Scraper Slot")


# ==================== STAGE 08: SAVED EMAIL TEMPLATE + MULTI-LLM PERSONALIZATION ====================
js_8l = r"""
const state = $input.first().json;
const tpl = state.savedTemplate || {};
const leads = state.lockedLeads || [];

const leadBriefs = leads.map((l, idx) => ({
  index: idx,
  companyName: l.companyName,
  decisionMakerName: l.decisionMakerName,
  jobTitle: l.jobTitle,
  industry: l.industry || 'B2B',
  officialWebsite: l.officialWebsite || '',
  companySummary: l.companySummary || ''
}));

const llmSystemPrompt = [
  "You personalize a user's saved B2B cold outreach email template for each lead.",
  "STRICT RULES:",
  "1. Preserve the user's core offer, intent, tone, and sign-off from their saved template.",
  "2. Use ONLY real provided facts (decisionMakerName, jobTitle, companyName, industry, companySummary).",
  "3. NEVER invent fake email addresses, fake awards, or unverified company claims.",
  "4. Return ONLY valid JSON in exact format: {\"emails\":[{\"index\":0,\"subject\":\"...\",\"body\":\"...\"}]}"
].join('\n');

const llmUserPrompt = JSON.stringify({
  savedEmailTemplate: tpl,
  leads: leadBriefs
});

return [{
  json: {
    ...state,
    llmSystemPrompt,
    llmUserPrompt,
    hasLeadsForLlm: leads.length > 0
  }
}];
"""
code_node(80, "8L · Prepare User's Saved Email Template", js_8l, 6320, 0)

# Primary LLM: xKiro (verified HTTP 200 live on VPS!)
http_node(
    81,
    "08 · Primary LLM Personalizer (xKiro)",
    "POST",
    "={{ ($json.hasLeadsForLlm && $env.LLM2_KEY) ? (($env.LLM2_BASE || 'https://api.xkiro.com/v1') + '/chat/completions') : 'http://127.0.0.1:5678/healthz' }}",
    [
        {"name": "Authorization", "value": "={{ 'Bearer ' + ($env.LLM2_KEY ?? '') }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ JSON.stringify({ model: 'qwen/qwen3.7-flash:free', temperature: 0.3, messages: [ { role: 'system', content: $json.llmSystemPrompt }, { role: 'user', content: $json.llmUserPrompt } ], max_tokens: 2200 }) }}",
    6560, 0,
    timeout=45000
)

js_8a_check = r"""
const state = $('8L · Prepare User\'s Saved Email Template').first().json;
const resp = $input.first().json || {};

if (!state.hasLeadsForLlm) {
  return [{ json: { ...state, personalizedMap: {}, llmProviderUsed: 'none_0_leads', llmStatus: 'ok' } }];
}

let parsed = null;
try {
  const rawTxt = resp?.choices?.[0]?.message?.content || '';
  if (rawTxt) {
    const clean = String(rawTxt).trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '');
    const s = clean.indexOf('{');
    const e = clean.lastIndexOf('}');
    if (s >= 0 && e > s) {
      const obj = JSON.parse(clean.slice(s, e + 1));
      if (Array.isArray(obj.emails) && obj.emails.length > 0) {
        parsed = {};
        for (const item of obj.emails) {
          parsed[Number(item.index)] = {
            subject: String(item.subject || '').trim(),
            body: String(item.body || '').trim()
          };
        }
      }
    }
  }
} catch {}

return [{
  json: {
    ...state,
    personalizedMap: parsed || {},
    llmProviderUsed: parsed ? 'primary_llm_xkiro' : '',
    llmStatus: parsed ? 'ok' : 'need_backup'
  }
}];
"""
code_node(82, "8A · Check Primary LLM Output", js_8a_check, 6780, 0)
if_eq_node(83, "IF 08 · Primary LLM Succeeded?", "={{ $json.llmStatus }}", "ok", 6980, 0)

# Backup LLM: Gemini / APInex Failover
http_node(
    84,
    "8R · Backup LLM API Key (Failover)",
    "POST",
    "={{ ($env.LLM2_KEY) ? (($env.LLM2_BASE || 'https://api.xkiro.com/v1') + '/chat/completions') : (($env.GEMINI_BASE || 'https://generativelanguage.googleapis.com/v1beta') + '/models/' + ($env.GEMINI_MODEL || 'gemini-2.5-flash') + ':generateContent') }}",
    [
        {"name": "Authorization", "value": "={{ $env.LLM2_KEY ? ('Bearer ' + $env.LLM2_KEY) : '' }}"},
        {"name": "x-goog-api-key", "value": "={{ (!$env.LLM2_KEY && $env.GEMINI_KEY) ? $env.GEMINI_KEY : '' }}"},
        {"name": "Content-Type", "value": "application/json"}
    ],
    "={{ $env.LLM2_KEY ? JSON.stringify({ model: 'mistralai/mistral-large-2512', temperature: 0.3, messages: [{ role: 'system', content: $json.llmSystemPrompt }, { role: 'user', content: $json.llmUserPrompt }], max_tokens: 2200 }) : JSON.stringify({ contents: [{ parts: [{ text: $json.llmSystemPrompt + '\\n\\nINPUT:\\n' + $json.llmUserPrompt }] }] }) }}",
    7200, 220,
    timeout=45000
)

js_8r_slot = r"""
// +8R EXTRA FREE LLM KEYS SLOT (Groq / OpenRouter / Mistral can plug here)
const state = $('IF 08 · Primary LLM Succeeded?').first().json;
const resp = $input.first().json || {};
let parsed = null;

try {
  const rawTxt = resp?.candidates?.[0]?.content?.parts?.[0]?.text || resp?.choices?.[0]?.message?.content || '';
  if (rawTxt) {
    const clean = String(rawTxt).trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '');
    const s = clean.indexOf('{');
    const e = clean.lastIndexOf('}');
    if (s >= 0 && e > s) {
      const obj = JSON.parse(clean.slice(s, e + 1));
      if (Array.isArray(obj.emails) && obj.emails.length > 0) {
        parsed = {};
        for (const item of obj.emails) {
          parsed[Number(item.index)] = {
            subject: String(item.subject || '').trim(),
            body: String(item.body || '').trim()
          };
        }
      }
    }
  }
} catch {}

return [{
  json: {
    ...state,
    personalizedMap: parsed || {},
    llmProviderUsed: parsed ? 'backup_llm_failover' : 'deterministic_template_fill'
  }
}];
"""
code_node(85, "+8R · Extra Free LLM Keys Slot", js_8r_slot, 7400, 220, notes="Expandable LLM Key Pool")

add_conn("+7R · Attach Website & Extra Scraper Slot", "8L · Prepare User's Saved Email Template")
add_conn("8L · Prepare User's Saved Email Template", "08 · Primary LLM Personalizer (xKiro)")
add_conn("08 · Primary LLM Personalizer (xKiro)", "8A · Check Primary LLM Output")
add_conn("8A · Check Primary LLM Output", "IF 08 · Primary LLM Succeeded?")
add_conn("IF 08 · Primary LLM Succeeded?", "8R · Backup LLM API Key (Failover)", src_output=1)
add_conn("8R · Backup LLM API Key (Failover)", "+8R · Extra Free LLM Keys Slot")


# ==================== STAGE 09 - 11: ATTACH EMAILS, SAVE HISTORY & RESPOND ====================
js_8c = r"""
const state = $input.first().json;
const tpl = state.savedTemplate || {};
const pMap = state.personalizedMap || {};

function fillPlaceholders(str, lead) {
  const firstName = String(lead.decisionMakerName || 'there').split(/\s+/)[0];
  return String(str || '')
    .replace(/\{\{\s*companyName\s*\}\}|\[Company Name\]/gi, lead.companyName || 'your company')
    .replace(/\{\{\s*decisionMakerName\s*\}\}|\[Decision Maker Name\]|\[Name\]/gi, firstName)
    .replace(/\{\{\s*fullName\s*\}\}/gi, lead.decisionMakerName || firstName)
    .replace(/\{\{\s*jobTitle\s*\}\}|\[Role\]|\[Job Title\]/gi, lead.jobTitle || 'team lead')
    .replace(/\{\{\s*industry\s*\}\}|\[Industry\]/gi, lead.industry || 'your industry')
    .replace(/\{\{\s*senderName\s*\}\}|\[Your Name\]/gi, tpl.senderName || 'Vaishnavi Zende');
}

const finalLeads = (state.lockedLeads || []).map((l, idx) => {
  const custom = pMap[idx];
  const subject = (custom && custom.subject) ? custom.subject : fillPlaceholders(tpl.subject, l);
  const body = (custom && custom.body) ? custom.body : fillPlaceholders(tpl.body, l);

  return {
    leadNumber: ((state.batchNumber - 1) * 5) + idx + 1,
    batchNumber: state.batchNumber,
    leadKey: l.leadKey,
    companyName: l.companyName,
    officialWebsite: l.officialWebsite || '',
    companySummary: l.companySummary || '',
    industry: l.industry || '',
    location: l.location || '',
    decisionMakerName: l.decisionMakerName,
    jobTitle: l.jobTitle,
    linkedin: l.linkedin,
    email: {
      address: l.email || '',
      verificationStatus: l.email ? (l.verificationStatus || (l.emailVerified ? 'valid' : 'unverified')) : 'unverified',
      verifiedBy: l.verifiedBy || l.verificationSource || 'none'
    },
    sourceProvider: l.sourceProvider,
    customizedEmail: {
      subject,
      body
    }
  };
});

return [{
  json: {
    ...state,
    finalLeads
  }
}];
"""
code_node(90, "8C · Attach 5 Customized Emails", js_8c, 7640, 0)

add_conn("IF 08 · Primary LLM Succeeded?", "8C · Attach 5 Customized Emails", src_output=0)
add_conn("+8R · Extra Free LLM Keys Slot", "8C · Attach 5 Customized Emails", src_output=0)

js_step09 = r"""
const state = $input.first().json;
const store = $getWorkflowStaticData('global');
if (!store.seenByPrompt) store.seenByPrompt = {};
if (!store.history) store.history = [];
if (!store.quotaLog) store.quotaLog = {};

const pMem = store.seenByPrompt[state.promptKey] || { keys: [], companies: [], batches: 0 };
const newKeys = state.finalLeads.map(l => l.leadKey).filter(Boolean);
const newCos = state.finalLeads.map(l => l.companyName).filter(Boolean);

pMem.keys = Array.from(new Set([...(pMem.keys || []), ...newKeys])).slice(-500);
pMem.companies = Array.from(new Set([...(pMem.companies || []), ...newCos])).slice(-500);
pMem.batches = Math.max(Number(pMem.batches || 0), Number(state.batchNumber || 1));
store.seenByPrompt[state.promptKey] = pMem;

// Update Quota Log
if (state.leadpulseUsed) store.quotaLog.leadpulse_fallbacks = (store.quotaLog.leadpulse_fallbacks || 0) + 1;
if (state.mailmeteorUsed) store.quotaLog.mailmeteor_verifications = (store.quotaLog.mailmeteor_verifications || 0) + (state.mailmeteorCheckedCount || 0);
if (state.tinyFishUsed) store.quotaLog.tinyfish_enrichments = (store.quotaLog.tinyfish_enrichments || 0) + 1;
if (state.finalLeads.length > 0) store.quotaLog.llm_personalizations = (store.quotaLog.llm_personalizations || 0) + 1;

// Save to Prompt History (keep latest 50 batches)
const historyEntry = {
  id: state.requestId,
  createdAt: new Date().toISOString(),
  userId: state.userId,
  prompt: state.prompt,
  batchNumber: state.batchNumber,
  leadRange: `${(state.batchNumber - 1) * 5 + 1}–${(state.batchNumber - 1) * 5 + state.finalLeads.length}`,
  leadsReturned: state.finalLeads.length,
  routeUsed: state.leadpulseUsed ? `race_winner_${state.raceWinner || 'backup'}_mailmeteor_web` : 'free_lead_ai_waterfall',
  mailmeteorUsed: state.mailmeteorUsed,
  llmUsed: state.llmProviderUsed,
  leads: state.finalLeads
};
store.history = [historyEntry, ...(store.history || [])].slice(0, 50);

// Build ready CSV export string
function csvCell(v) {
  const s = String(v ?? '').replace(/"/g, '""');
  return `"${s}"`;
}
const csvRows = [
  ['Lead #', 'Company Name', 'Official Website', 'Decision Maker', 'Job Title', 'LinkedIn URL', 'LinkedIn Type', 'Email', 'Verification Status', 'Source', 'Custom Email Subject', 'Custom Email Body'].map(csvCell).join(',')
];
for (const l of state.finalLeads) {
  csvRows.push([
    l.leadNumber,
    l.companyName,
    l.officialWebsite,
    l.decisionMakerName,
    l.jobTitle,
    l.linkedin?.url || '',
    l.linkedin?.hasDirectUrl ? 'Direct Profile' : 'LinkedIn Search',
    l.email?.address || '',
    l.email?.verificationStatus || 'unverified',
    l.sourceProvider,
    l.customizedEmail?.subject || '',
    l.customizedEmail?.body || ''
  ].map(csvCell).join(','));
}

return [{
  json: {
    ok: true,
    workflow: 'B2B Smart LeadFlow (Locked Architecture v1)',
    requestId: state.requestId,
    prompt: state.prompt,
    batchNumber: state.batchNumber,
    maxLeadsPerBatch: 5,
    leadsCount: state.finalLeads.length,
    leadRange: historyEntry.leadRange,
    routingSummary: {
      pathwaySelected: state.pathway || 'free_apis',
      primaryRoute: state.pathway === 'tinyfish' ? 'tinyfish_pathway_smart_guesser_mailmeteor' : historyEntry.routeUsed,
      parallelBackupRaceWinner: state.raceWinner || 'none',
      parallelBackupRaceMs: state.raceElapsedMs || 0,
      leadpulseOrTinyfishFallbackUsed: state.leadpulseUsed,
      smartEmailGuesser: state.smartGuesserStats || {},
      mailmeteorWebCheckerUrl: 'https://mailmeteor.com/email-checker',
      mailmeteorOneByOneCheckedCount: state.mailmeteorUsed ? (state.mailmeteorCheckLog?.length || state.mailmeteorCheckedCount) : 0,
      mailmeteorCheckLog: state.mailmeteorCheckLog || [],
      tinyFishWebsiteLookupUsed: Boolean(state.tinyFishUsed),
      llmPersonalizerUsed: state.llmProviderUsed,
      providerTrace: state.providerTrace
    },
    leads: state.finalLeads,
    savedEmailTemplate: state.savedTemplate,
    make5AnotherLeadsPayload: {
      prompt: state.prompt,
      userId: state.userId,
      batchNumber: state.batchNumber + 1,
      makeAnother5: true,
      excludedLeadKeys: pMem.keys,
      excludeCompanies: pMem.companies
    },
    csvExport: csvRows.join('\n')
  }
}];
"""
code_node(91, "09 · Save Prompt History, Lead IDs & Quota Log", js_step09, 7880, 0)

nodes.append({
    "id": uid(92),
    "name": "10 · Reply 5 Lead Cards + CSV Ready",
    "type": "n8n-nodes-base.respondToWebhook",
    "typeVersion": 1.1,
    "position": [8120, 0],
    "parameters": {
        "respondWith": "firstIncomingItem",
        "options": {}
    }
})

add_conn("8C · Attach 5 Customized Emails", "09 · Save Prompt History, Lead IDs & Quota Log")
add_conn("09 · Save Prompt History, Lead IDs & Quota Log", "10 · Reply 5 Lead Cards + CSV Ready")


# ==================== COMPANION ENDPOINT 1: SAVE EMAIL TEMPLATE ====================
nodes.append({
    "id": uid(101),
    "name": "Webhook · POST /b2b-smart-leads-template",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 2,
    "position": [-2140, 640],
    "webhookId": "b2b-smart-leads-template",
    "parameters": {
        "httpMethod": "POST",
        "path": "b2b-smart-leads-template",
        "responseMode": "responseNode",
        "options": {}
    }
})

js_save_tpl = r"""
const raw = $input.first().json;
const body = (raw && typeof raw.body === 'object' && raw.body !== null) ? raw.body : raw;
const store = $getWorkflowStaticData('global');
if (!store.templates) store.templates = {};

const userId = String(body.userId || 'public_default').trim() || 'public_default';
const tpl = {
  subject: String(body.subject || body.emailTemplate?.subject || 'Quick collaboration idea for {{companyName}}').trim(),
  body: String(body.body || body.emailTemplate?.body || 'Hi {{decisionMakerName}},\n\nI noticed {{companyName}}...').trim(),
  senderName: String(body.senderName || body.emailTemplate?.senderName || 'Vaishnavi Zende').trim(),
  senderCompany: String(body.senderCompany || body.emailTemplate?.senderCompany || '').trim(),
  updatedAt: new Date().toISOString()
};
store.templates[userId] = tpl;

return [{ json: { ok: true, userId, message: 'My Email Template saved successfully!', emailTemplate: tpl } }];
"""
code_node(102, "Save My Email Template", js_save_tpl, -1840, 640)

nodes.append({
    "id": uid(103),
    "name": "Reply · Template Saved",
    "type": "n8n-nodes-base.respondToWebhook",
    "typeVersion": 1.1,
    "position": [-1560, 640],
    "parameters": {"respondWith": "firstIncomingItem", "options": {}}
})

add_conn("Webhook · POST /b2b-smart-leads-template", "Save My Email Template")
add_conn("Save My Email Template", "Reply · Template Saved")


# ==================== COMPANION ENDPOINT 2: PROMPT HISTORY & BATCHES ====================
nodes.append({
    "id": uid(111),
    "name": "Webhook · GET /b2b-smart-leads-history",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 2,
    "position": [-2140, 880],
    "webhookId": "b2b-smart-leads-history",
    "parameters": {
        "httpMethod": "GET",
        "path": "b2b-smart-leads-history",
        "responseMode": "responseNode",
        "options": {}
    }
})

js_read_hist = r"""
const raw = $input.first().json || {};
const query = raw.query || {};
const userId = String(query.userId || 'public_default').trim();
const store = $getWorkflowStaticData('global');

const allHistory = Array.isArray(store.history) ? store.history : [];
const filtered = userId === 'all' ? allHistory : allHistory.filter(h => h.userId === userId);

return [{
  json: {
    ok: true,
    userId,
    totalSavedBatches: filtered.length,
    savedEmailTemplate: (store.templates && store.templates[userId]) || null,
    quotaLog: store.quotaLog || {},
    history: filtered
  }
}];
"""
code_node(112, "Load Prompt History & Quota Log", js_read_hist, -1840, 880)

nodes.append({
    "id": uid(113),
    "name": "Reply · History",
    "type": "n8n-nodes-base.respondToWebhook",
    "typeVersion": 1.1,
    "position": [-1560, 880],
    "parameters": {"respondWith": "firstIncomingItem", "options": {}}
})

add_conn("Webhook · GET /b2b-smart-leads-history", "Load Prompt History & Quota Log")
add_conn("Load Prompt History & Quota Log", "Reply · History")


# ==================== COMPANION ENDPOINT 3: HEALTH & PROVIDER STATUS ====================
nodes.append({
    "id": uid(121),
    "name": "Webhook · GET /b2b-smart-leads-health",
    "type": "n8n-nodes-base.webhook",
    "typeVersion": 2,
    "position": [-2140, 1120],
    "webhookId": "b2b-smart-leads-health",
    "parameters": {
        "httpMethod": "GET",
        "path": "b2b-smart-leads-health",
        "responseMode": "responseNode",
        "options": {}
    }
})

js_health = r"""
return [{
  json: {
    ok: true,
    workflowId: 'SmartLeadFlowV1',
    name: 'B2B Smart LeadFlow · Locked Architecture (v1)',
    rulesLocked: {
      maxLeadsPerBatch: 5,
      defaultPathway: 'free_apis (prospeo_acc_1 -> prospeo_acc_2 -> clay_acc_1 -> clay_acc_2 -> hunter_api -> apollo_api)',
      optionalPathways: ['free_apis', 'tinyfish'],
      waterfallOrder: ['prospeo_acc_1', 'prospeo_acc_2', 'clay_acc_1', 'clay_acc_2', 'hunter_api', 'apollo_api', '+future_slot'],
      parallelBackupRace: 'first_result_wins (leadpulse_ai vs tinyfish_ai)',
      smartEmailGuesser: 'between_tinyfish_and_mailmeteor (time_capped: 8s/lead, 20s/stage_max)',
      mailmeteorWebChecker: 'https://mailmeteor.com/email-checker (one_by_one_only_when_free_waterfall_fails_or_tinyfish_pathway)',
      smartLinkedin: 'direct_profile_or_name_company_search_url',
      customEmail: 'saved_user_template_with_primary_and_backup_llm',
      repeatBatchLoop: 'make_5_another_leads_excludes_previous'
    },
    providersConfiguredInEnv: {
      prospeo_key_1: Boolean(($env.PROSPEO_API_KEY_1 || '').trim()),
      prospeo_key_2: Boolean(($env.PROSPEO_API_KEY_2 || '').trim()),
      clay_key_1: Boolean(($env.CLAY_API_KEY_1 || '').trim()),
      clay_key_2: Boolean(($env.CLAY_API_KEY_2 || '').trim()),
      hunter_api_key: Boolean(($env.HUNTER_API_KEY || '').trim()),
      apollo_api_key: Boolean(($env.APOLLO_API_KEY || '').trim()),
      leadpulse_pipeline_key: Boolean(($env.LEADPULSE_PIPELINE_KEY || '').trim()),
      mailmeteor_api_key: Boolean(($env.MAILMETEOR_API_KEY || '').trim()),
      local_smtp_verifier: Boolean(($env.VERIFY_URL || '').trim()),
      tinyfish_api_key: Boolean(($env.TINYFISH_KEY || '').trim()),
      primary_llm_xkiro: Boolean(($env.LLM2_KEY || '').trim()),
      backup_llm_gemini_or_apinex: Boolean(($env.GEMINI_KEY || $env.LLM1_KEY || '').trim())
    },
    endpoints: {
      generate5Leads: 'POST /webhook/b2b-smart-leads',
      saveEmailTemplate: 'POST /webhook/b2b-smart-leads-template',
      getHistoryAndQuota: 'GET /webhook/b2b-smart-leads-history',
      healthCheck: 'GET /webhook/b2b-smart-leads-health'
    }
  }
}];
"""
code_node(122, "Check All 11 Stages & Env Keys", js_health, -1840, 1120)

nodes.append({
    "id": uid(123),
    "name": "Reply · System Health",
    "type": "n8n-nodes-base.respondToWebhook",
    "typeVersion": 1.1,
    "position": [-1560, 1120],
    "parameters": {"respondWith": "firstIncomingItem", "options": {}}
})

add_conn("Webhook · GET /b2b-smart-leads-health", "Check All 11 Stages & Env Keys")
add_conn("Check All 11 Stages & Env Keys", "Reply · System Health")


workflow_doc = {
    "id": "SmartLeadFlowV1",
    "name": "B2B Smart LeadFlow · Locked Architecture (v1)",
    "nodes": nodes,
    "connections": connections,
    "settings": {
        "executionOrder": "v1"
    },
    "active": True,
    "pinData": {}
}

out_path = "/home/user/b2b-smart-leadflow-n8n.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(workflow_doc, f, indent=2, ensure_ascii=False)

print(f"Generated {out_path} with {len(nodes)} nodes and {len(connections)} connection sources!")
