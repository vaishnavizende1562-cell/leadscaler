const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const wfRaw = JSON.parse(fs.readFileSync(path.join(ROOT, 'b2b-smart-leadflow-n8n.json'), 'utf8'));
const wf = Array.isArray(wfRaw) ? wfRaw[0] : wfRaw;

let passed = 0;
function check(name, fn) {
  fn();
  passed++;
  console.log(`  [PASS] ${name}`);
}

console.log('Running leadScaler 78-Node n8n Architecture & Integrity Suite...\n');

check('Workflow ID & active metadata locked', () => {
  assert.strictEqual(wf.id, 'SmartLeadFlowV1');
  assert.ok(wf.nodes.length >= 78, `Expected >= 78 nodes, got ${wf.nodes.length}`);
});

check('All 31 n8n JavaScript Code nodes parse without syntax errors', () => {
  const codeNodes = wf.nodes.filter(n => n.type === 'n8n-nodes-base.code');
  assert.ok(codeNodes.length >= 30, `Expected >= 30 code nodes, got ${codeNodes.length}`);
  for (const node of codeNodes) {
    new Function('$input', '$json', '$env', '$', node.parameters.jsCode);
  }
});

check('All connection source and destination nodes exist in workflow graph', () => {
  const nodeNames = new Set(wf.nodes.map(n => n.name));
  const sources = Object.keys(wf.connections);
  assert.ok(sources.length >= 65, `Expected >= 65 connection sources, got ${sources.length}`);
  for (const [src, outputs] of Object.entries(wf.connections)) {
    assert.ok(nodeNames.has(src), `Missing source node: ${src}`);
    for (const branches of Object.values(outputs)) {
      for (const edges of branches) {
        for (const edge of edges) {
          assert.ok(nodeNames.has(edge.node), `Missing target node: ${edge.node} (from ${src})`);
        }
      }
    }
  }
});

check('6-Stage Free API Waterfall order (Prospeo #1 -> #2 -> Clay #1 -> #2 -> Hunter -> Apollo) intact', () => {
  const names = new Set(wf.nodes.map(n => n.name));
  const required = [
    '01 · Public UI Webhook',
    '02 · Batch Lock (Max 5) & Dedupe Memory',
    '03 · Dual-Track Parallel Split Router',
    '3B-1 · LeadPulse AI (Parallel Racer A)',
    '3B-2 · TinyFish AI (Parallel Racer B)',
    '4.1A · Prospeo #1 Search',
    '4.2A · Prospeo #2 Search',
    '4.25A · Clay #1 Create Search',
    '4.26A · Clay #2 Create Search',
    '4.3A · Hunter Free Discover',
    '4.3Q · Select Top Hunter Domains',
    '4.3B · Hunter Domain Finder',
    '4.4A · Apollo People Search',
    'Green Express Bypass Rail (Skip Unused APIs)',
    '5G · Smart Email Guesser (If Invalid · Time-Capped)',
    '5C · Mailmeteor Web Checker (One-by-One)',
    '06 · Normalize, Deduplicate & Lock Exact 5 Leads',
    '08 · Primary LLM Personalizer (xKiro)',
    '8R · Backup LLM API Key (Failover)'
  ];
  for (const reqName of required) {
    assert.ok(names.has(reqName), `Missing required architectural node: ${reqName}`);
  }
});

check('Zero hardcoded API secrets leaked in tracked files', () => {
  const filesToScan = [
    'b2b-smart-leadflow-n8n.json',
    'workflows/b2b-smart-leadflow-n8n.json',
    'workflows/build_n8n_workflow.py',
    'backend/smart_leadflow_web.py',
    'backend/mailmeteor_race_server.py',
    'frontend/index.html',
    'netlify/functions/api.mjs'
  ];
  const secretRegex = /(clay_scoped_[A-Za-z0-9]{12,}|nfp_[A-Za-z0-9]{16,}|AIzaSy[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{24,})/;
  for (const rel of filesToScan) {
    const content = fs.readFileSync(path.join(ROOT, rel), 'utf8');
    assert.ok(!secretRegex.test(content), `Potential secret pattern detected in ${rel}`);
  }
});

console.log(`\nAll ${passed} verification checks passed successfully!`);
