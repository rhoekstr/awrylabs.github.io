// Build the self-contained, first-party, no-network county-fragility choropleth
// served at assets/gravel-fragility-map.html and embedded (via <iframe>) in the
// Gravel story and project page.
//
// The map ships zero third-party runtime JS: the county geometry and the real
// isolation-risk data are baked into the SVG at build time; the only script is a
// tiny first-party hover-tooltip handler. No network calls once loaded.
//
// INPUTS (place both in the current working directory before running):
//   counties-10m.json  -- US counties TopoJSON (lon/lat), e.g.
//                         curl -o counties-10m.json https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json
//   fragility.csv      -- per-county isolation fragility, from the gravel repo:
//                         cp ~/…/gravel/data/sample-results/county_isolation_fragility.csv ./fragility.csv
//
// DEPS:  npm i d3-geo topojson-client
// RUN:   node build-fragility-map.mjs      (writes ../assets/gravel-fragility-map.html)
import { readFileSync, writeFileSync } from 'node:fs';
import { feature, mesh } from 'topojson-client';
import { geoAlbersUsa, geoPath } from 'd3-geo';

const topo = JSON.parse(readFileSync('counties-10m.json', 'utf8'));
const counties = feature(topo, topo.objects.counties).features;
const stateMesh = mesh(topo, topo.objects.states, (a, b) => a !== b);
const nationMesh = mesh(topo, topo.objects.nation);

// ---- fragility data ----
const lines = readFileSync('fragility.csv', 'utf8').trim().split('\n');
const head = lines[0].split(',');
const col = Object.fromEntries(head.map((h, i) => [h, i]));
const data = new Map();
for (let i = 1; i < lines.length; i++) {
  const c = lines[i].split(',');
  data.set(c[col.fips].padStart(5, '0'), {
    risk: parseFloat(c[col.isolation_risk]),
    name: c[col.county_name],
    state: c[col.state_name],
  });
}

// ---- color ramp: RdYlGn reversed (green = resilient, red = fragile), domain [0, 0.7] ----
const STOPS = ['#1a9850','#66bd63','#a6d96a','#d9ef8b','#ffffbf','#fee08b','#fdae61','#f46d43','#d73027']
  .map(h => [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)]);
const DMAX = 0.7;
function color(risk) {
  if (!(risk >= 0)) return '#c9c9c9';
  let t = Math.max(0, Math.min(1, risk / DMAX)) * (STOPS.length - 1);
  const i = Math.min(STOPS.length - 2, Math.floor(t)), f = t - i;
  const mix = k => Math.round(STOPS[i][k] + (STOPS[i+1][k] - STOPS[i][k]) * f);
  return '#' + [mix(0), mix(1), mix(2)].map(v => v.toString(16).padStart(2, '0')).join('');
}

// ---- project lon/lat -> 975x610 via Albers USA (AK/HI rendered as insets) ----
const proj = geoAlbersUsa().fitSize([975, 610], feature(topo, topo.objects.counties));
const path = geoPath(proj);
const rnd = s => s ? s.replace(/-?\d+\.\d+/g, m => Math.round(+m)) : '';

let paths = '', withData = 0, without = 0;
for (const f of counties) {
  const fips = String(f.id).padStart(5, '0');
  const rec = data.get(fips);
  const d = rnd(path(f));
  if (!d) continue;
  if (rec) withData++; else without++;
  const name = rec ? `${rec.name}, ${rec.state}` : `FIPS ${fips}`;
  const rtxt = rec && rec.risk >= 0 ? rec.risk.toFixed(3) : 'no data';
  paths += `<path d="${d}" fill="${rec ? color(rec.risk) : '#c9c9c9'}" data-n="${name.replace(/&/g,'&amp;').replace(/"/g,'&quot;')}" data-r="${rtxt}"/>`;
}
const statePath = rnd(path(stateMesh));
const nationPath = rnd(path(nationMesh));

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>US County Road Network Isolation Risk &mdash; Gravel</title>
<style>
  :root { color-scheme: light dark; --ink:#1a1a1a; --mute:#666; --rule:rgba(0,0,0,.12); --panel:rgba(255,255,255,.92); --cstroke:rgba(255,255,255,.35); --sstroke:rgba(40,40,40,.45); }
  @media (prefers-color-scheme: dark){ :root{ --ink:#e5e5e5; --mute:#9a9a9a; --rule:rgba(255,255,255,.14); --panel:rgba(28,28,30,.94); --cstroke:rgba(0,0,0,.28); --sstroke:rgba(255,255,255,.4);} }
  * { box-sizing:border-box; margin:0; }
  html,body { background:transparent; }
  body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif; color:var(--ink); }
  .wrap { position:relative; width:100%; }
  svg { width:100%; height:auto; display:block; }
  .counties path { stroke:var(--cstroke); stroke-width:.2; vector-effect:non-scaling-stroke; cursor:crosshair; }
  .counties path.hot { stroke:var(--ink); stroke-width:1.4; }
  .states { fill:none; stroke:var(--sstroke); stroke-width:.6; vector-effect:non-scaling-stroke; pointer-events:none; }
  .nation { fill:none; stroke:var(--sstroke); stroke-width:1; vector-effect:non-scaling-stroke; pointer-events:none; }
  .tip { position:absolute; pointer-events:none; background:var(--panel); color:var(--ink); border:1px solid var(--rule); border-radius:7px; padding:.4rem .55rem; font-size:.78rem; line-height:1.35; box-shadow:0 6px 18px -8px rgba(0,0,0,.5); transform:translate(-50%,calc(-100% - 12px)); white-space:nowrap; z-index:5; }
  .tip strong { font-weight:700; }
  .tip .v { font-variant-numeric:tabular-nums; }
  .legend .lk { fill:var(--ink); font:700 13px -apple-system,system-ui,sans-serif; letter-spacing:.04em; }
  .legend .lk2 { fill:var(--mute); font:600 12px -apple-system,system-ui,sans-serif; }
</style>
</head>
<body>
<div class="wrap">
  <svg viewBox="0 0 975 672" role="img" aria-label="Choropleth map of road-network isolation risk for all 3,221 US counties. The Great Plains and Midwest are low-risk (green); the Appalachians, the mountain West, and many coastal, island, and peninsular counties are high-risk (red). Jackson County, North Carolina scores 0.673.">
    <defs>
      <linearGradient id="lg" x1="0" x2="1" y1="0" y2="0">
        <stop offset="0" stop-color="#1a9850"/><stop offset=".25" stop-color="#a6d96a"/>
        <stop offset=".5" stop-color="#ffffbf"/><stop offset=".75" stop-color="#fdae61"/>
        <stop offset="1" stop-color="#d73027"/>
      </linearGradient>
    </defs>
    <g class="counties">${paths}</g>
    <path class="states" d="${statePath}"/>
    <path class="nation" d="${nationPath}"/>
    <g class="legend" transform="translate(8,636)">
      <text class="lk" x="0" y="11">Resilient</text>
      <rect x="78" y="2" width="220" height="11" rx="5.5" fill="url(#lg)"/>
      <text class="lk" x="306" y="11">fragile, cut off</text>
      <text class="lk2" x="967" y="11" text-anchor="end">isolation risk &#183; 3,221 US counties</text>
    </g>
  </svg>
  <div class="tip" hidden></div>
</div>
<script>
(function(){
  var svg=document.querySelector('svg'), tip=document.querySelector('.tip'), wrap=document.querySelector('.wrap'), last=null;
  svg.addEventListener('mousemove', function(e){
    var t=e.target;
    if(t.tagName==='path' && t.parentNode.classList.contains('counties')){
      if(last && last!==t) last.classList.remove('hot');
      t.classList.add('hot'); last=t;
      tip.innerHTML='<strong>'+t.dataset.n+'</strong><br>Isolation risk: <span class="v">'+t.dataset.r+'</span>';
      tip.hidden=false;
      var r=wrap.getBoundingClientRect();
      tip.style.left=(e.clientX-r.left)+'px';
      tip.style.top=(e.clientY-r.top)+'px';
    } else { tip.hidden=true; if(last){last.classList.remove('hot'); last=null;} }
  });
  svg.addEventListener('mouseleave', function(){ tip.hidden=true; if(last){last.classList.remove('hot'); last=null;} });
})();
</script>
</body>
</html>`;

const OUT = new URL('../assets/gravel-fragility-map.html', import.meta.url);
writeFileSync(OUT, html);
console.log(`counties: ${withData} with data, ${without} without`);
console.log(`wrote ${OUT.pathname} (${(html.length / 1024).toFixed(0)} KB)`);
