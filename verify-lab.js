/* Assertions for rag-lab.html.  Run:  node verify-lab.js
 *
 * Pulls the document, the index and the map layout straight out of the HTML and checks the
 * claims the lab makes on screen — that the index really contains no warranty, that the
 * nine chunks really are the document's nine sections, that the scripted demo scores are
 * what the speaker notes say, and above all that the map never draws a chunk nearer than
 * one with a better score. Written because the first version of the map did exactly that
 * on four of the eight scripted queries, and it looked fine in a screenshot.
 *
 * No dependencies. Exits non-zero on any failure. */
const fs = require('fs');
const path = require('path');
const s = fs.readFileSync(path.join(__dirname, 'rag-lab.html'), 'utf8');
const script = s.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = script.indexOf('const DOCUMENT=');
const end = script.indexOf('/* ================= 00 PIPELINE');
const block = script.slice(start, end);

const sandbox = { document: { getElementById: () => null } };
const fn = new Function('document', block + '\nreturn {DOCUMENT,CORPUS,CONMAP,STOP,toks,isCode,qConcepts,lexScore,semScore,byScore,scoreAll,SpaceMap};');
const M = fn(sandbox.document);

let fails = 0;
const ok = (name, cond, extra) => {
  if (!cond) { fails++; console.log('  FAIL  ' + name + (extra ? '  →  ' + extra : '')); }
  else console.log('  ok    ' + name + (extra ? '  ·  ' + extra : ''));
};

console.log('\n== 1. the index genuinely has no warranty ==');
const anyText = M.CORPUS.some(c => /warrant/i.test(c.text));
const anyCon = M.CORPUS.some(c => c.con.some(x => /warrant/i.test(x)));
const anyHead = M.CORPUS.some(c => /warrant|batter|heavy|money back/i.test(c.sec.h));
ok('no chunk text says warranty', !anyText);
ok('no chunk concept list says warranty', !anyCon);
ok('no heading leaks a demo keyword', !anyHead);

console.log('\n== 2. sections ARE the corpus ==');
const secs = M.DOCUMENT.parts.reduce((a, p) => a.concat(p.secs), []);
ok('9 sections', secs.length === 9, secs.length + '');
ok('9 chunks', M.CORPUS.length === 9, M.CORPUS.length + '');
ok('every chunk text is its section body verbatim',
   M.CORPUS.every((c, i) => c.text === secs[i].text));
const TAGS = ['§ display','§ power','§ sync','§ pricing','§ returns','§ stylus','§ updates','§ size','§ troubleshooting'];
const have = M.CORPUS.map(c => c.tag).sort();
ok('tag set unchanged from the original file (tab 08 couples by string)',
   JSON.stringify(have) === JSON.stringify(TAGS.slice().sort()),
   have.join(' '));

console.log('\n== 2b. the nine chunk texts are byte-identical to the pre-change file ==');
/* Transcribed from rag-lab.html:700-708 before this rewrite. Only semScore was meant to
   change; if a text drifted, the keyword column silently changes too. */
const ORIG = {
  display: "The Aeronote is a 10.3-inch e-ink tablet for handwriting and reading; its matte screen cuts glare and eye strain.",
  battery: "On a single charge it runs for about three weeks of typical daily note-taking before it needs power again.",
  export:  "Notes sync automatically to the cloud, and any page can be exported as a PDF or plain text file.",
  price:   "The Aeronote costs $399 for the base model; a premium bundle with folio cover and extra pen tips is $449.",
  refund:  "You can return the Aeronote within 45 days of delivery for a full refund, no questions asked.",
  stylus:  "The stylus charges wirelessly on the side of the tablet and lasts roughly a full day of writing per charge.",
  firmware:"Firmware updates arrive monthly and add new pen styles and reading fonts.",
  weight:  "The device weighs 375 grams and is about as thick as ten sheets of paper, so it slips easily into a bag.",
  error:   "If the screen stops responding, error code E-42 means the digitizer needs a reset; hold the power button for ten seconds."
};
const drift = M.CORPUS.filter(c => ORIG[c.id] !== c.text).map(c => c.id);
ok('no chunk text drifted', drift.length === 0, drift.join(','));
const ORIG_CON = { display:4, battery:4, export:5, price:4, refund:4, stylus:5, firmware:5, weight:4, error:3 };
ok('returns chunk lost exactly one concept (the typed-in "warranty")',
   M.CORPUS.every(c => c.con.length === ORIG_CON[c.id]));

console.log('\n== 3. scripted queries ==');
const rank = q => M.scoreAll(q, c => M.semScore(q, c)).filter(o => o.s > 0)
                   .map(o => o.tag + ' ' + o.s.toFixed(2));
const lexrank = q => M.scoreAll(q, c => M.lexScore(q, c.text)).filter(o => o.s > 0)
                      .map(o => o.tag + ' ' + o.s.toFixed(2));
const QUERIES = ['battery life', 'can I get my money back?', 'export notes as PDF', 'is it heavy?',
                 'how long is the warranty?', 'E-42', 'how do I get my notes onto my computer?',
                 'is the pen expensive?'];
QUERIES.forEach(q => {
  console.log('  "' + q + '"');
  console.log('      dense   ' + (rank(q).join('  |  ') || '— all zero'));
  console.log('      keyword ' + (lexrank(q).join('  |  ') || '— all zero'));
});

console.log('\n== 4. the demos the script depends on ==');
const top = q => { const r = M.scoreAll(q, c => M.semScore(q, c)); return r[0]; };
ok('battery life → § power 1.00', top('battery life').tag === '§ power' && top('battery life').s === 1);
ok('money back → § returns 0.75', top('can I get my money back?').tag === '§ returns'
   && top('can I get my money back?').s.toFixed(2) === '0.75');
ok('is it heavy? → § size 0.71', top('is it heavy?').tag === '§ size'
   && top('is it heavy?').s.toFixed(2) === '0.71');
ok('warranty → § returns 0.50 (least-far, not a match)', top('how long is the warranty?').tag === '§ returns'
   && top('how long is the warranty?').s.toFixed(2) === '0.50');
ok('E-42 → dense scores zero everywhere',
   M.CORPUS.every(c => M.semScore('E-42', c) === 0));
const chipA = M.scoreAll('how do I get my notes onto my computer?', c => M.semScore('how do I get my notes onto my computer?', c));
ok('chip A: § display wins (wrong)', chipA[0].tag === '§ display', chipA[0].s.toFixed(3));
ok('chip A: § sync is #2 (the reranker lifts it from second)', chipA[1].tag === '§ sync', chipA[1].s.toFixed(3));
const lexA = M.scoreAll('how do I get my notes onto my computer?', c => M.lexScore('how do I get my notes onto my computer?', c.text));
ok('chip A: keyword does NOT also pick § display', lexA[0].tag !== '§ display', lexA[0].tag + ' ' + lexA[0].s.toFixed(2));

console.log('\n== 5. tab 06 dense ordering must be unchanged ==');
['battery life', 'E-42', 'export notes as PDF'].forEach(q => {
  console.log('  ' + q + '  →  ' + (rank(q).join('  |  ') || '— all zero'));
});
const rrf = q => {
  const K = 60, fuse = {};
  const add = list => list.forEach((o, i) => { fuse[o.id] = (fuse[o.id] || 0) + 1 / (K + i + 1); });
  add(M.scoreAll(q, c => M.lexScore(q, c.text)).filter(o => o.s > 0));
  add(M.scoreAll(q, c => M.semScore(q, c)).filter(o => o.s > 0));
  return Object.entries(fuse).sort((a, b) => b[1] - a[1]).map(e => e[0] + ' ' + e[1].toFixed(4));
};
const f = rrf('export notes as PDF');
console.log('  RRF export notes as PDF → ' + f.join('  |  '));
ok('RRF top is 0.0328 (speaker notes)', f[0].endsWith('0.0328'), f[0]);
ok('RRF runner-up is 0.0161 (speaker notes)', f[1].endsWith('0.0161'), f[1]);

console.log('\n== 6. the map agrees with its own numbers ==');
const SM = M.SpaceMap;
QUERIES.concat(['can I return a tablet with a cracked screen?']).forEach(q => {
  const qc = M.qConcepts(q);
  if (!qc.size) { console.log('  (skip, no concepts) ' + q); return; }
  /* The map draws the question inside a FIXED layout of the nine chunks, so the claim it
     makes is: a chunk with a better score is drawn closer. Checked over every pair, not
     just the three that get a leader line — the room can compare any two dots by eye.
     Scores print to 2dp, so pairs that agree there are not constrained against each other. */
  const EPS = 0.005;
  const all = M.scoreAll(q, c => M.semScore(q, c));
  const p = SM._placeQuery(qc);
  const dOf = {};
  all.forEach(o => { dOf[o.id] = Math.hypot(SM._PT[o.ix].x - p.x, SM._PT[o.ix].y - p.y); });
  const viol = [];
  all.forEach(a => all.forEach(b => {
    if (a.id === b.id) return;
    if (a.s > b.s + EPS && dOf[a.id] >= dOf[b.id])
      viol.push(a.tag + '(' + a.s.toFixed(2) + ') drawn no nearer than ' + b.tag + '(' + b.s.toFixed(2) + ')');
  }));
  ok('drawn distance never contradicts the score  ["' + q + '"]', viol.length === 0, viol.slice(0, 3).join(' ; '));
});

console.log('\n== 6b. a wider sweep of questions a room might actually type ==');
const WILD = ['does it sync to the cloud?', 'can I write on it?', 'what is the refund window?',
  'my tablet is frozen', 'stylus battery life', 'how do I save a page as a file?',
  'is the screen good for reading outside?', 'how thin is it?', 'what does it cost?',
  'how do I update it?', 'how bright is the display?', 'why has my screen stopped responding?'];
let wildBad = 0;
WILD.forEach(q => {
  const qc = M.qConcepts(q); if (!qc.size) return;
  const all = M.scoreAll(q, c => M.semScore(q, c));
  const p = SM._placeQuery(qc);
  const dOf = {}; all.forEach(o => { dOf[o.id] = Math.hypot(SM._PT[o.ix].x - p.x, SM._PT[o.ix].y - p.y); });
  let bad = 0;
  all.forEach(a => all.forEach(b => { if (a.s > b.s + 0.005 && dOf[a.id] >= dOf[b.id]) bad++; }));
  if (bad) { wildBad++; console.log('    ' + q + ' → ' + bad + ' violations'); }
});
ok(WILD.length + ' unscripted questions also draw honestly', wildBad === 0, wildBad + ' failed');

console.log('\n== 7. layout sanity ==');
let minSep = 1e9, pair = '';
for (let i = 0; i < SM._PT.length; i++) for (let j = i + 1; j < SM._PT.length; j++) {
  const d = Math.hypot(SM._PT[i].x - SM._PT[j].x, SM._PT[i].y - SM._PT[j].y);
  if (d < minSep) { minSep = d; pair = M.CORPUS[i].tag + ' / ' + M.CORPUS[j].tag; }
}
ok('no two dots closer than 40px', minSep >= 40, minSep.toFixed(1) + 'px  (' + pair + ')');
ok('every chunk is inside the frame',
   SM._PT.every(p => p.x > 20 && p.x < SM.W - 20 && p.y > 20 && p.y < SM.H - 20));
const outside = [];
QUERIES.concat(WILD).forEach(q => {
  const qc = M.qConcepts(q); if (!qc.size) return;
  const p = SM._placeQuery(qc);
  if (p.x < 12 || p.x > SM.W - 12 || p.y < 14 || p.y > SM.H - 12) outside.push(q);
});
ok('the question dot stays inside the frame for every question', outside.length === 0, outside.join(' | '));
// does the layout still carry meaning? nearest neighbours should be semantically close
console.log('  nearest neighbour of each chunk in the drawn layout:');
M.CORPUS.forEach((c, i) => {
  let bi = -1, bd = 1e9;
  M.CORPUS.forEach((o, j) => { if (i === j) return; const d = Math.hypot(SM._PT[i].x - SM._PT[j].x, SM._PT[i].y - SM._PT[j].y); if (d < bd) { bd = d; bi = j; } });
  console.log('    ' + c.tag.padEnd(18) + '→ ' + M.CORPUS[bi].tag + '   (cos ' + SM._cos(c.con, M.CORPUS[bi].con).toFixed(2) + ')');
});

console.log('\n' + (fails ? fails + ' FAILURE(S)' : 'all assertions passed'));
process.exit(fails ? 1 : 0);
