"use strict";
/* NBA Picks app. Reads the same data.json the old dashboard reads (site/data.json, written by nbapicks/dashboard.py).
   Views: Tonight (picks + parlays), Games, Record, Players, More. Tap a pick for its details drawer.
   Design family: the Fundamentalist app (see app.css header). */

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (x, d = 0) => (x == null || isNaN(x) ? "–" : (x * 100).toFixed(d) + "%");
const spct = (x, d = 1) => (x == null || isNaN(x) ? "–" : (x >= 0 ? "+" : "−") + Math.abs(x * 100).toFixed(d) + "%");
const units = (x, d = 2) => (x == null || isNaN(x) ? "–" : (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(d) + "u");
const am = (a) => (a == null ? "–" : (a > 0 ? "+" : a < 0 ? "−" : "") + Math.abs(a));
const sign = (x) => (x == null ? "" : x > 0 ? "pos" : x < 0 ? "neg" : "");
const TZ = "America/Toronto";
const ymdET = (d = new Date()) => d.toLocaleDateString("en-CA", { timeZone: TZ });
const toDate = (iso) => { const s = String(iso); return new Date(/([zZ]|[+-]\d\d:\d\d)$/.test(s) ? s : s + "Z"); };
const tipTime = (iso) => { if (!iso) return ""; const t = toDate(iso); return isNaN(t) ? "" : t.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", timeZone: TZ }); };
const clock = (iso) => { if (!iso) return "–"; const t = toDate(iso); return isNaN(t) ? "–" : t.toLocaleString([], { weekday: "short", hour: "numeric", minute: "2-digit", timeZone: TZ }); };
const dayName = (ymd, o = { weekday: "long", month: "short", day: "numeric" }) => new Date(ymd + "T12:00:00").toLocaleDateString([], o);
const STAT = { pts: "Points", reb: "Rebounds", ast: "Assists", fg3m: "3-Pointers", stl: "Steals", blk: "Blocks", pra: "Pts + Reb + Ast" };

let D = null, EMBEDDED = false;
const state = { cand: null };

/* ---------------------------------------------------------------- reading a pick */
// "Alex Sarr u7.5 reb" -> {who: "Alex Sarr", bet: "Under 7.5 Rebounds"}; game lines read in plain words too.
function readLabel(label) {
  const l = String(label || "");
  let m = /^(.*?) ([ou])(\d+(?:\.\d+)?) (\w+)$/.exec(l);
  if (m) return { who: m[1], bet: `${m[2] === "o" ? "Over" : "Under"} ${m[3]} ${STAT[m[4]] || m[4]}` };
  m = /^(\S+) ([ou])(\d+(?:\.\d+)?)$/.exec(l);
  if (m) return { who: m[1].replace("@", " @ "), bet: `${m[2] === "o" ? "Over" : "Under"} ${m[3]} total points` };
  m = /^(\S+) ML$/.exec(l) || /^(\S+) Moneyline$/.exec(l);
  if (m) return { who: m[1], bet: `${m[1]} to win` };
  m = /^(\S+) ([+-]\d+(?:\.\d+)?)$/.exec(l);
  if (m) return { who: m[1], bet: `${m[1]} ${m[2]}` };
  return { who: "", bet: l };
}
const candKey = (r) => [r.game_id, r.market, r.player_id || "", r.stat || "", r.line ?? "", r.selection || ""].join("|");
function candIndex() {
  if (state.cand) return state.cand;
  const m = {};
  for (const day of D.picks_by_day || []) for (const c of [...(day.candidates || []), ...(day.qualified || [])]) if (c && c.game_id) m[candKey(c)] = c;
  return (state.cand = m);
}
const gameById = (gid) => ((D.today || {}).games || []).find((g) => String(g.game_id) === String(gid));
function enrich(r) {
  const c = candIndex()[candKey(r)] || {};
  const g = gameById(r.game_id) || {};
  const lab = readLabel(r.label);
  const implied = c.implied ?? (r.price_dec ? 1 / r.price_dec : null);
  return { ...r, who: lab.who || c.player || "", bet: lab.bet, implied, ev: c.ev ?? (r.prob != null && r.price_dec ? r.prob * r.price_dec - 1 : null),
    why: c.why || null, reason: c.reason || "", book: c.book || "", team: c.team || "", opponent: c.opponent || "",
    start_utc: c.start_utc || g.start_utc || null, status: g.status || c.game_status || null, matchup: r.matchup || c.matchup || (g.away ? `${g.away} @ ${g.home}` : "") };
}
function last5Of(p) {
  const row = (p.why || []).find((w) => /^Last 5/i.test(w[0]));
  if (!row) return null;
  const v = String(row[1]).split(/,\s*/).map(Number).filter((x) => !isNaN(x));
  return v.length ? v.reverse() : null;                          // oldest -> newest, left to right
}
const clears = (v, line, sel) => (sel === "under" ? v < line : v > line);

/* ---------------------------------------------------------------- bet-slip links (same rules as the old dashboard) */
const BOOKS = [["draftkings", "DK", "sportsbook.draftkings.com"], ["fanduel", "FD", "sportsbook.fanduel.com"]];
const fmtLine = (x) => (x > 0 ? "+" : "") + x;
const normName = (s) => String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/-/g, " ")
  .replace(/[^a-z ]/g, "").split(/\s+/).filter((w) => w && !["jr", "sr", "ii", "iii", "iv"].includes(w)).join(" ");
const propPlayer = (r) => { const m = /^(.*?) [ou]\d+(?:\.\d+)? \w+$/.exec(String(r.label || "")); return normName(m ? m[1] : r.player); };
function closest(outs, r) {
  const same = outs.filter((o) => o.market === r.market && o.selection === r.selection && (r.market !== "prop" || (o.stat === r.stat && o.player === propPlayer(r))));
  const o = same.find((o) => r.market === "ml" || (o.line != null && r.line != null && Math.abs(o.line - r.line) < 1e-6))
    || same.filter((o) => o.line != null && r.line != null).sort((a, b) => Math.abs(a.line - r.line) - Math.abs(b.line - r.line))[0];
  return o ? { o, other: r.market !== "ml" && Math.abs(o.line - r.line) > 1e-6 ? (r.market === "spread" ? fmtLine(o.line) : String(o.line)) : null } : null;
}
const okHost = (url, host) => { try { const x = new URL(url); return x.protocol === "https:" && x.host === host; } catch (e) { return false; } };
function slipLinks(r) {
  const T = D.today || {}, gid = String(r.game_id), bl = (T.book_links || {})[gid] || {}, dk = (T.dk_links || {})[gid];
  const out = [];
  for (const [book, short, host] of BOOKS) {
    let hit = closest(bl[book] || [], r), url = hit && hit.o.link;
    if (!hit && book === "draftkings" && dk && r.market !== "prop") {
      hit = closest(dk.outcomes || [], r);
      url = hit && `${dk.event_url}?outcomes=${encodeURIComponent(hit.o.outcome_id)}`;
    }
    if (hit && okHost(url, host)) out.push({ url, book, short, slip: true, label: `${short} slip${hit.other != null ? " at " + hit.other : ""}`,
      title: hit.other != null ? `${short} only offers ${hit.other} right now; opens the slip with that line.` : `Opens ${short} with this bet on the slip.` });
  }
  if (!out.some((x) => x.book === "draftkings") && dk && okHost(dk.event_url, "sportsbook.draftkings.com"))
    out.push({ url: dk.event_url, book: "draftkings", short: "DK", slip: false, label: "DK game", title: "Opens this game on DraftKings. The bet is not pre-selected." });
  return out;
}
function comboLinks(items, what, title) {
  const out = [];
  for (const [book, short] of BOOKS) {
    const legs = items.map((l) => slipLinks(l).find((k) => k.book === book && k.slip));
    if (legs.length < 2 || legs.some((k) => !k)) continue;
    const qs = legs.map((k) => new URL(k.url).searchParams);
    if (!qs.every((q) => q.get(book === "draftkings" ? "outcomes" : "selectionId"))) continue;
    const url = book === "draftkings"
      ? "https://sportsbook.draftkings.com/?outcomes=" + qs.map((q) => encodeURIComponent(q.get("outcomes") || "")).join("+")
      : "https://sportsbook.fanduel.com/addToBetslip?" + qs.map((q, i) => `marketId[${i}]=${encodeURIComponent(q.get("marketId") || "")}&selectionId[${i}]=${encodeURIComponent(q.get("selectionId") || "")}`).join("&");
    out.push(`<a class="book${book === "draftkings" ? " primary" : ""}" href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="${esc(title(short, legs.length))}">${esc(short + " · " + what(legs.length))} <span class="arw">↗</span></a>`);
  }
  return out.join("");
}
const bookBtns = (r) => slipLinks(r).map((k) => `<a class="book${k.book === "draftkings" && k.slip ? " primary" : ""}" href="${esc(k.url)}" target="_blank" rel="noopener noreferrer"
  title="${esc(k.title + " Check the line and price before placing.")}" data-stop>${esc(k.label)} <span class="arw">↗</span></a>`).join("");
const gameOpen = (r) => { const g = gameById(r.game_id); return !g || !g.status || g.status === "scheduled"; };

/* ---------------------------------------------------------------- small pieces */
function resChip(r) {
  const res = r.result || "pending";
  if (res === "win") return `<span class="res win">✓ Won ${esc(units(r.net_units))}</span>`;
  if (res === "loss") return `<span class="res loss">✗ Lost ${esc(units(r.net_units))}</span>`;
  if (res === "push") return `<span class="res push">= Push</span>`;
  if (res === "void") return `<span class="res void">Void</span>`;
  if (res === "cashout") return `<span class="res push">Cash-out ${esc(units(r.net_units))}</span>`;
  const g = gameById(r.game_id);
  if (g && g.status && g.status !== "scheduled" && g.status !== "final") return `<span class="res live">● Live</span>`;
  return `<span class="res pending">${r.start_utc ? esc(tipTime(r.start_utc)) : "Pending"}</span>`;
}
function edgeMeter(p, i = 0) {
  const model = p.prob, book = p.implied;
  if (model == null) return "";
  const diff = book != null ? model - book : null;
  return `<div class="edge" style="--i:${i}">
    <div class="edge-top"><span>Model <b>${pct(model)}</b></span><span>Book ${book != null ? `<b>${pct(book)}</b>` : "–"}</span></div>
    <div class="track" role="img" aria-label="Model chance ${pct(model)}, book's implied chance ${pct(book)}"><i class="fill" style="width:${(model * 100).toFixed(1)}%"></i>${book != null ? `<i class="tick" style="left:${(book * 100).toFixed(1)}%"></i>` : ""}</div>
    <div class="edge-note">${diff == null ? "" : diff >= 0 ? `<span class="up">${(diff * 100).toFixed(1)} pts</span> above the price` : `${(-diff * 100).toFixed(1)} pts below the price`}${p.ev != null ? ` · model edge ${spct(p.ev)}` : ""}</div>
  </div>`;
}
function last5(p, big = false) {
  const v = last5Of(p);
  if (!v || p.line == null) return "";
  const top = Math.max(...v, p.line * 1.6, 1);
  const h = (x) => Math.max(4, (x / top) * 100);
  const hits = v.filter((x) => clears(x, p.line, p.selection)).length;
  const chart = `<div class="l5${big ? " big" : ""}" role="img" aria-label="Last five games: ${v.join(", ")}. The bet would have won ${hits} of 5.">
    <div class="l5-plot"><span class="ln" style="bottom:${h(p.line).toFixed(1)}%"></span>${v.map((x, i) => `<i class="b${clears(x, p.line, p.selection) ? " hit" : ""}" style="height:${h(x).toFixed(1)}%;--i:${i}"></i>`).join("")}</div>
    <div class="l5-x">${v.map((x) => `<span>${x}</span>`).join("")}</div></div>`;
  return big ? chart : `<div class="l5-wrap">${chart}<span class="l5-cap">Last 5<br><b class="${hits >= 3 ? "pos" : ""}">${hits}/5</b> clear</span></div>`;
}
function sparkline(vals) {
  if (!vals || vals.length < 2) return "";
  const W = 100, H = 26, lo = Math.min(0, ...vals), hi = Math.max(0, ...vals), sp = hi - lo || 1;
  const pts = vals.map((v, i) => [(i / (vals.length - 1)) * W, H - ((v - lo) / sp) * H]);
  const z = H - ((0 - lo) / sp) * H;
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2="${W}" y1="${z}" y2="${z}" stroke="var(--line2)" stroke-dasharray="2 3" vector-effect="non-scaling-stroke"/><polyline points="${pts.map((p) => p.join(",")).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="1.6" vector-effect="non-scaling-stroke"/><circle cx="${pts.at(-1)[0]}" cy="${pts.at(-1)[1]}" r="2.2" fill="var(--accent)"/></svg>`;
}

/* ---------------------------------------------------------------- data shortcuts */
const posted = () => (D.performance || {}).posted_leans || {};
const history = () => (posted().rows || []).map(enrich);
const byDay = () => Object.entries(posted().by_day || {}).sort(([a], [b]) => a.localeCompare(b));
const settledDays = () => byDay().filter(([, s]) => (s.settled || 0) > 0);
function cumulative() { let c = 0; return settledDays().map(([d, s]) => [d, (c += s.net_units || 0)]); }
const slateDate = () => (D.today || {}).date || (D.meta || {}).today;
const tonightPicks = () => ((D.today || {}).leans || []).map((r) => enrich({ ...r, slate: r.slate || slateDate() }));
const tickets = (date) => (((D.tickets || {}).rows) || []).filter((t) => !date || t.slate === date);
function tally(rows) {
  const w = rows.filter((r) => r.result === "win").length, l = rows.filter((r) => r.result === "loss").length;
  return { w, l, n: w + l, net: rows.reduce((a, r) => a + (r.net_units || 0), 0), pending: rows.filter((r) => !r.result || r.result === "pending").length };
}

function banner() {
  const m = D.meta || {}, out = [], sd = slateDate(), now = ymdET();
  if (sd && sd < now && !EMBEDDED_FIXED_DATE()) out.push(`<b>Not updated today.</b> These are the picks for ${esc(dayName(sd))}. Today's run hasn't posted yet, so check again later.`);
  if (m.paused) out.push(`<b>New picks are paused.</b> ${esc(m.paused.reason || "")}`);
  if ((m.stale || {}).odds) out.push(`<b>Prices may be old.</b> The last odds are ${Math.round((m.stale || {}).odds_age_minutes || 0)} minutes old.`);
  for (const w of (m.warnings || []).filter((x) => !/discord/i.test(x))) out.push(esc(w));
  return out.map((x) => `<div class="fresh" role="status"><span aria-hidden="true">!</span><div>${x}</div></div>`).join("");
}
// A snapshot copy (the preview) is allowed to show an older slate without the "not updated" warning.
const EMBEDDED_FIXED_DATE = () => EMBEDDED && !!document.querySelector('meta[name="nba-snapshot"]');

/* ---------------------------------------------------------------- views */
const V = {};

V.tonight = () => {
  const T = D.today || {}, picks = tonightPicks(), sd = slateDate(), games = T.games || [];
  const t = tally(picks), firstTip = games.map((g) => g.start_utc).filter(Boolean).sort()[0];
  let line;
  if (!picks.length) line = `No picks yet for ${sd === ymdET() ? "tonight" : esc(dayName(sd, { weekday: "long" }))}.`;
  else if (t.n === 0) line = `<b>${picks.length} ${picks.length === 1 ? "pick" : "picks"}</b> across ${games.length} ${games.length === 1 ? "game" : "games"}.${firstTip ? ` First tip ${esc(tipTime(firstTip))}.` : ""}`;
  else if (t.pending) line = `<b>${t.w}-${t.l}</b> so far, <span class="${sign(t.net)}">${units(t.net)}</span>. ${t.pending} still to play.`;
  else line = `Went <b>${t.w}-${t.l}</b>, <span class="${sign(t.net)}">${units(t.net)}</span>.`;

  const P = posted(), days = settledDays(), last = days.filter(([d]) => d < sd).at(-1) || days.at(-1);
  const strip = `<section class="strip" aria-label="Record">
    <div class="tile"><span class="l">Season record</span><span class="v">${P.wins ?? 0}-${P.losses ?? 0}</span><span class="s">${pct(P.hit_rate)} won${days.length ? ` · since ${esc(dayName(days[0][0], { month: "short", day: "numeric" }))}` : ""}</span></div>
    <div class="tile"><span class="l">Net units</span><span class="v ${sign(P.net_units)}">${units(P.net_units)}</span>${sparkline(cumulative().map((x) => x[1]))}</div>
    <div class="tile"><span class="l">Return on stake</span><span class="v">${spct(P.roi)}</span><span class="s">${P.roi_ci ? `Likely range ${spct(P.roi_ci[0], 0)} to ${spct(P.roi_ci[1], 0)}` : ""}</span></div>
    <div class="tile"><span class="l">${last ? esc(dayName(last[0], { weekday: "long" })) : "Last slate"}</span><span class="v">${last ? `${last[1].wins}-${last[1].losses}` : "–"}</span><span class="s ${last ? sign(last[1].net_units) : ""}">${last ? units(last[1].net_units) : ""}</span></div>
  </section>`;

  const all = comboLinks(picks.filter(gameOpen), (n) => `all ${n} on one slip`, (s, n) => `Puts all ${n} picks on one ${s} slip. Choose singles (straight bets) on the slip, not a parlay, and check each line and price before placing.`);
  const slips = picks.length ? `<ul class="slips">${picks.map((p, i) => slipRow(p, i)).join("")}</ul>`
    : `<p class="empty">Picks post about 2 hours before the first tip (4:30 PM ET on most weekdays, 11:00 AM on weekends).</p>`;
  const tk = tickets(sd);
  return `${banner()}
  <div class="head"><div><p class="kicker">${esc(dayName(sd, { weekday: "long", month: "short", day: "numeric" }))} · ${games.length} ${games.length === 1 ? "game" : "games"}</p>
    <p class="verdict">${line}</p><p class="sub">1 unit on each pick. Updated ${esc(clock((D.meta || {}).generated_at))}.</p></div></div>
  ${strip}
  <div class="sec-h"><h2>Straight picks</h2><span class="meta">Tap a pick for the numbers behind it</span></div>
  ${all ? `<div class="allrow">${all}</div>` : ""}
  ${slips}
  <div class="sec-h"><h2>Parlays and lotto</h2><span class="tag">Research</span></div>
  <p class="sub" style="margin:0 0 14px">Built from the likeliest props in different games. The edge is the model's own estimate and can be negative.</p>
  ${tk.length ? `<div class="tickets">${tk.map(ticketCard).join("")}</div>` : `<p class="empty">Not posted yet. Parlays are built when the picks go out.</p>`}
  <p class="disclosure">Paper record: every pick is graded at 1 unit from final box scores. The model's chance is its own estimate; the book's chance is 1 ÷ the decimal price, which includes the book's margin. A good record over a few weeks can still be luck. See Record for how often the model's numbers have held up.</p>`;
};
function slipRow(p, i) {
  return `<li class="slip" data-pick="${esc(p.lean_id)}" tabindex="0" role="button" aria-label="${esc(`${p.who} ${p.bet}, details`)}">
    <div><div class="who"><span class="p">${esc(p.who)}</span><span>${esc(p.matchup)}</span></div>
      <div class="bet">${esc(p.bet)}<span class="odds">${esc(am(p.price_american))}</span></div>
      <div class="slip-books">${bookBtns(p)}</div></div>
    ${edgeMeter(p, i)}
    <div class="slip-r">${resChip(p)}${last5(p)}</div>
  </li>`;
}
function ticketCard(t) {
  const legs = (t.legs || []).map(enrich);
  const kind = t.kind === "lotto" ? "Lotto" : "Parlay";
  return `<article class="ticket">
    <div class="ticket-h"><span class="t">${legs.length}-leg ${kind.toLowerCase()}</span>${resChip({ ...t, start_utc: legs.map((l) => l.start_utc).filter(Boolean).sort()[0] })}</div>
    <div class="ticket-nums"><div><span>Pays</span><b class="mono">${esc(am(t.price_american))}</b></div><div><span>Model chance</span><b>${pct(t.prob, 1)}</b></div><div><span>Model edge</span><b class="${sign(t.ev)}">${spct(t.ev)}</b></div></div>
    <ul class="legs">${legs.map((l) => `<li data-pick="${esc(l.lean_id)}" data-ticket="${esc(t.ticket_id)}" style="cursor:pointer"><span><b>${esc(l.who)}</b> ${esc(l.bet)}</span><span class="r"><span class="mono muted">${esc(am(l.price_american))}</span>${l.result && l.result !== "pending" ? resChip(l) : ""}</span><span class="m">${esc(l.matchup)} · ${pct(l.prob)}</span></li>`).join("")}</ul>
    <div class="slip-books">${comboLinks(legs, () => "parlay slip", (s, n) => `Tries to put all ${n} legs on one ${s} slip. Check every leg is there before placing.`)}</div>
  </article>`;
}

V.games = () => {
  const T = D.today || {}, games = T.games || [], picks = tonightPicks(), sd = slateDate();
  const ch = {};
  for (const r of (D.valuation || {}).rows || []) if (r.market === "ml" && r.team && r.prob != null) (ch[r.matchup] = ch[r.matchup] || {})[r.team] = r.prob;
  const card = (g, i) => {
    const c = ch[`${g.away} @ ${g.home}`] || {};
    let a = c[g.away], h = c[g.home];
    if (a == null && h != null) a = 1 - h; if (h == null && a != null) h = 1 - a;
    const live = g.status && g.status !== "scheduled", st = g.status === "final" ? "Final" : !live ? tipTime(g.start_utc) : "Live";
    const gp = picks.filter((p) => String(p.game_id) === String(g.game_id));
    const side = (t, p, sc, fav) => `<div class="team${fav ? " fav" : ""}"><span class="ab">${esc(t)}</span><span class="pc">${p == null ? "" : `${pct(p)} to win`}</span><span class="sc">${live && sc != null ? esc(sc) : ""}</span></div>`;
    return `<article class="game" style="--i:${i}">
      <div class="game-h"><span>${esc(st)}</span><span>${gp.length ? `${gp.length} ${gp.length === 1 ? "pick" : "picks"}` : "No picks"}</span></div>
      ${side(g.away, a, g.away_score, a != null && a >= 0.5)}${side(g.home, h, g.home_score, h != null && h > 0.5)}
      ${a != null ? `<div class="split" role="img" aria-label="Model: ${esc(g.away)} ${pct(a)}, ${esc(g.home)} ${pct(h)}"><i class="${a >= 0.5 ? "fav" : ""}" style="width:${(a * 100).toFixed(1)}%"></i><i class="${h > 0.5 ? "fav" : ""}" style="width:${(h * 100).toFixed(1)}%"></i></div>` : ""}
      ${gp.length ? `<div class="game-picks">${gp.map((p) => `<button data-pick="${esc(p.lean_id)}"><span class="gp-b">${esc(p.who)} · ${esc(p.bet)}</span><span class="mono muted">${esc(am(p.price_american))}</span></button>`).join("")}</div>` : ""}
    </article>`;
  };
  return `${banner()}<div class="head"><div><p class="kicker">${esc(dayName(sd, { weekday: "long", month: "short", day: "numeric" }))}</p>
    <h1>${games.length} ${games.length === 1 ? "game" : "games"}</h1><p class="sub">The model's chance for each team to win, and the picks in each game.</p></div></div>
    ${games.length ? `<div class="games">${games.map(card).join("")}</div>` : `<p class="empty">No games on this slate.</p>`}`;
};

V.record = () => {
  const P = posted(), days = settledDays(), cum = cumulative(), rows = history();
  const first = days[0] ? dayName(days[0][0], { month: "short", day: "numeric" }) : "";
  const tk = tickets(), tp = tally(tk.filter((t) => t.kind === "parlay")), tl = tally(tk.filter((t) => t.kind === "lotto"));
  const mk = Object.entries(P.by_market || {}).filter(([, s]) => s.settled);
  const maxAbs = Math.max(1, ...mk.map(([, s]) => Math.abs(s.net_units || 0)));
  const MK = { prop: "Player props", ml: "Moneyline", spread: "Spread", total: "Totals" };
  const sc = (D.performance || {}).scorecard || {};
  const bk = (P.by_bucket || []).filter((b) => b.n);
  const dayRows = [...byDay()].reverse().map(([d, s]) => {
    const pr = rows.filter((r) => r.slate === d);
    return `<li><details class="day"><summary><span class="d">${esc(dayName(d, { weekday: "short", month: "short", day: "numeric" }))}</span><span class="wl">${s.settled ? `${s.wins}-${s.losses}` : `${s.pending} open`}</span><span class="u ${sign(s.net_units)}">${s.settled ? units(s.net_units) : ""}</span><span class="chev" aria-hidden="true">›</span></summary>
      <ul class="day-picks">${pr.map((r) => `<li data-pick="${esc(r.lean_id)}" style="cursor:pointer"><span><b>${esc(r.who)}</b> ${esc(r.bet)}</span><span class="r">${resChip(r)}</span><span class="m">${esc(r.matchup)} · ${esc(am(r.price_american))} · model ${pct(r.prob)}</span></li>`).join("")}</ul></details></li>`;
  }).join("");
  return `<div class="head"><div><p class="kicker">Since ${esc(first)} · ${P.settled ?? 0} graded picks</p>
    <p class="verdict"><b>${P.wins ?? 0}-${P.losses ?? 0}</b>, <span class="${sign(P.net_units)}">${units(P.net_units)}</span>. A ${spct(P.roi)} return on ${Number(P.units_staked || 0).toFixed(0)} units staked.</p>
    <p class="sub">Straight picks only, 1 unit each. Worst dip ${units((P.advanced || {}).max_drawdown_units)}; longest losing run ${(P.advanced || {}).longest_losing_streak ?? "–"}.</p></div></div>
  ${chart(cum)}
  <div class="two">
    <section><h2>By market</h2><ul class="rows">${mk.map(([k, s], i) => {
      const w = (Math.abs(s.net_units || 0) / maxAbs) * 50;
      return `<li class="mkt"><span><b>${esc(MK[k] || k)}</b><br><span class="n">${s.wins}-${s.losses} · ${pct(s.hit_rate)}</span></span>
        <span class="hbar" role="img" aria-label="${esc(units(s.net_units))}"><i class="${s.net_units >= 0 ? "p" : "n"}" style="${s.net_units >= 0 ? `left:50%;width:${w}%` : `left:${50 - w}%;width:${w}%`};animation-delay:${i * 60}ms"></i><span class="mid"></span></span>
        <span class="mono ${sign(s.net_units)}" style="text-align:right">${units(s.net_units)}</span></li>`; }).join("")}
      <li class="mkt"><span><b>Parlays</b><br><span class="n">${tp.w}-${tp.l} · research</span></span><span></span><span class="mono ${sign(tp.net)}" style="text-align:right">${units(tp.net)}</span></li>
      <li class="mkt"><span><b>Lotto</b><br><span class="n">${tl.w}-${tl.l} · research</span></span><span></span><span class="mono ${sign(tl.net)}" style="text-align:right">${units(tl.net)}</span></li></ul></section>
    <section><h2>Is the model right?</h2>
      ${bk.length ? `<div class="calib">${bk.map((b, i) => `<div class="cb"><span class="k">Said ${Math.round(b.lo * 100)}–${Math.round(b.hi * 100)}%</span>
        <span class="track" role="img" aria-label="Predicted ${pct(b.predicted)}, won ${pct(b.observed)}"><i class="obs" style="width:${(b.observed * 100).toFixed(1)}%;animation-delay:${i * 60}ms"></i><i class="pred" style="left:${(b.predicted * 100).toFixed(1)}%;animation-delay:${i * 60 + 120}ms"></i></span>
        <span class="v">won ${pct(b.observed)} · ${b.n}</span></div>`).join("")}</div>
        <p class="legend">Green bar: how often those picks won. White tick: what the model said. Small groups swing a lot.</p>` : `<p class="empty">Not enough graded picks yet.</p>`}
      <div class="honest">
        ${P.roi_ci ? `<p><b>The return is likely between ${spct(P.roi_ci[0], 0)} and ${spct(P.roi_ci[1], 0)}.</b> Above zero so far, but ${P.settled} picks is a small sample, so a range this wide can still shrink to nothing.</p>` : ""}
        ${sc.brier ? `<p>Across all ${Number(sc.brier.n).toLocaleString()} model predictions since ${esc(sc.since ? dayName(sc.since, { month: "short", day: "numeric" }) : "the start")}, the books' prices were ${sc.brier.market <= sc.brier.model ? "slightly more accurate than" : "less accurate than"} the model (error ${sc.brier.market.toFixed(3)} vs ${sc.brier.model.toFixed(3)}; lower is better).${sc.brier.market <= sc.brier.model ? " So there is no proven edge yet." : ""}</p>` : ""}
      </div>
    </section>
  </div>
  <h2>By day</h2><ul class="rows">${dayRows || `<li class="empty">No graded days yet.</li>`}</ul>`;
};
function chart(cum) {
  if (cum.length < 2) return "";
  const W = 1000, H = 220, L = 44, R = 12, Tp = 10, B = 26;
  const vals = cum.map((x) => x[1]), lo = Math.min(0, ...vals), hi = Math.max(0, ...vals);
  const step = niceStep((hi - lo) / 4), y0 = Math.floor(lo / step) * step, y1 = Math.ceil(hi / step) * step;
  const X = (i) => L + (i / (cum.length - 1)) * (W - L - R), Y = (v) => Tp + (1 - (v - y0) / (y1 - y0 || 1)) * (H - Tp - B);
  const ticks = []; for (let v = y0; v <= y1 + 1e-9; v += step) ticks.push(v);
  const pts = cum.map((c, i) => `${X(i).toFixed(1)},${Y(c[1]).toFixed(1)}`);
  const lab = [0, Math.floor((cum.length - 1) / 2), cum.length - 1];
  return `<figure class="chart" style="margin:0"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Net units by day, from ${units(vals[0])} to ${units(vals.at(-1))}">
    <g class="grid">${ticks.map((v) => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" vector-effect="non-scaling-stroke"/>`).join("")}</g>
    <line class="zero" x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}" vector-effect="non-scaling-stroke"/>
    <g class="plot"><polygon class="area" points="${X(0)},${Y(0)} ${pts.join(" ")} ${X(cum.length - 1)},${Y(0)}"/>
    <polyline class="ln" points="${pts.join(" ")}" vector-effect="non-scaling-stroke"/></g>
  </svg>
  <div style="position:relative;height:0">${ticks.map((v) => `<span class="mono faint" style="position:absolute;left:0;font-size:11px;top:${-H - 8 + Y(v)}px">${v > 0 ? "+" : ""}${v}u</span>`).join("")}</div>
  <div class="legend" style="display:flex;justify-content:space-between">${lab.map((i) => `<span>${esc(dayName(cum[i][0], { month: "short", day: "numeric" }))}</span>`).join("")}</div>
  <figcaption class="legend">Net units, added up day by day. Now <b class="${sign(vals.at(-1))}">${units(vals.at(-1))}</b>.</figcaption></figure>`;
}
function niceStep(x) { const p = Math.pow(10, Math.floor(Math.log10(x || 1))); const n = x / p; return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p; }

V.players = () => {
  const ids = new Set(((D.today || {}).games || []).map((g) => String(g.game_id)));
  const ps = ((D.players || {}).players || []).filter((p) => !ids.size || ids.has(String(p.game_id))).slice(0, 10);
  const card = (p) => `<article class="player"><div class="player-h"><b>${esc(p.player)}</b><span class="meta">${esc(p.team)} vs ${esc(p.opponent)} · ${esc(tipTime(p.start_utc))}</span></div>
    <ul class="props">${(p.props || []).map((x) => {
      const fake = { line: x.line, selection: x.side, why: x.last5 ? [["Last 5", x.last5.join(", ")]] : null };
      return `<li><span><span class="pb">${esc(x.label || `${x.side} ${x.line} ${x.stat_label}`)}</span><br><span class="pm">${pct(x.prob)} model · <span class="mono">${esc(am(x.price_american))}</span>${x.line_hits_last10 ? ` · cleared ${x.line_hits_last10.h}/${x.line_hits_last10.n} of last 10` : ""}${x.stale ? " · old price" : ""}</span></span>${last5(fake)}</li>`; }).join("")}</ul></article>`;
  return `<div class="head"><div><p class="kicker">Tonight's slate</p><h1>Players to watch</h1>
    <p class="sub">The players with the likeliest props tonight and their three best lines. These are not picks: early in the season they rest on small samples.</p></div></div>
    ${ps.length ? `<div class="players">${ps.map(card).join("")}</div>` : `<p class="empty">No props yet. They show once tonight's lines are posted.</p>`}`;
};

V.more = () => {
  const m = D.meta || {}, ls = m.last_success || {}, ms = m.market_status || {};
  const NAMES = { ingest: "Scores and odds fetched", predict: "Predictions made", publish: "Picks posted", settle: "Results graded", export: "This app's data written" };
  return `<div class="head"><div><p class="kicker">About this app</p><h1>More</h1></div></div>
  <ul class="more-list"><li><a href="#record">Full record by day <span aria-hidden="true">›</span></a></li><li><a href="#players">Players to watch <span aria-hidden="true">›</span></a></li>${EMBEDDED ? "" : `<li><a href="../">The old dashboard (all tables) <span aria-hidden="true">›</span></a></li>`}</ul>
  <h2>Last runs</h2><dl class="kv">${Object.entries(NAMES).map(([k, n]) => `<dt>${esc(n)}</dt><dd>${esc(clock(ls[k]))}</dd>`).join("")}<dt>Mode</dt><dd>${m.dry_run ? "Paper only (no real bets placed)" : "Live"}</dd></dl>
  <h2>Markets</h2><dl class="kv">${Object.entries(ms).map(([k, s]) => `<dt>${esc({ ml: "Moneyline", spread: "Spread", total: "Totals", prop: "Player props", parlay: "Parlays", lotto: "Lotto" }[k] || k)}</dt><dd>${s === "research" ? "Research: posted for tracking, not validated yet" : esc(s)}</dd>`).join("")}</dl>
  <h2>How to read a pick</h2><dl class="kv">
    <dt>Model</dt><dd>The model's chance the bet wins.</dd>
    <dt>Book</dt><dd>The chance the price implies (1 ÷ decimal odds). It includes the book's margin, so the model has to beat it by a few points to make money.</dd>
    <dt>Last 5</dt><dd>The player's last five games against tonight's line, oldest on the left. Green bars would have won the bet.</dd>
    <dt>DK / FD slip</dt><dd>Opens DraftKings or FanDuel with the bet on the slip. "at 6.5" means the book's line differs and its closest line is used.</dd></dl>
  <p class="disclosure">Paper picks for research. Not betting advice. If gambling stops being fun, call 1-866-531-2600 (ConnexOntario) or visit connexontario.ca.</p>`;
};

/* ---------------------------------------------------------------- drawer */
function findPick(id, ticketId) {
  if (ticketId) { const t = tickets().find((x) => x.ticket_id === ticketId); const l = t && (t.legs || []).find((x) => x.lean_id === id); if (l) return enrich(l); }
  return tonightPicks().find((p) => p.lean_id === id) || history().find((p) => p.lean_id === id) || null;
}
function openPick(id, ticketId) {
  const p = findPick(id, ticketId);
  if (!p) return;
  const why = (p.why || []).filter((w) => !/^Last 5/i.test(w[0]));
  $("#drawer-body").innerHTML = `
    <div class="dh"><div class="who"><span class="p">${esc(p.who)}</span><span>${esc(p.matchup)}${p.start_utc ? ` · ${esc(clock(p.start_utc))}` : ""}</span></div>
      <div class="bet">${esc(p.bet)}<span class="odds">${esc(am(p.price_american))}</span></div><div style="margin-top:8px">${resChip(p)}${p.result && p.result !== "pending" && p.stat_value != null ? ` <span class="meta">Finished with ${esc(p.stat_value)}</span>` : ""}</div></div>
    <div class="dfacts"><div><span>Model chance</span><b>${pct(p.prob)}</b></div><div><span>Book's chance</span><b>${pct(p.implied)}</b></div><div><span>Model edge</span><b class="${sign(p.ev)}">${spct(p.ev)}</b></div></div>
    ${edgeMeter(p)}
    ${last5Of(p) ? `<section class="dsec"><h3>Last 5 games vs ${esc(p.line)}</h3>${last5(p, true)}</section>` : ""}
    ${slipLinks(p).length && gameOpen(p) ? `<div class="slip-books">${bookBtns(p)}</div>` : ""}
    ${why.length ? `<section class="dsec"><h3>The numbers behind it</h3><dl class="why">${why.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl></section>` : ""}
    ${p.reason ? `<p class="reason">${esc(p.reason)}</p>` : ""}
    <p class="disclosure" style="margin-top:0">Model numbers are estimates from recent games. Check the line and price on the book before you place anything.</p>`;
  const dr = $("#drawer");
  dr.classList.add("open"); dr.setAttribute("aria-hidden", "false"); $("#scrim").hidden = false;
  document.body.style.overflow = "hidden";
  setTimeout(() => $("#drawer-close").focus(), 50);
}
function closeDrawer() {
  const dr = $("#drawer"); if (!dr.classList.contains("open")) return;
  dr.classList.remove("open"); dr.setAttribute("aria-hidden", "true"); $("#scrim").hidden = true; document.body.style.overflow = "";
}

/* ---------------------------------------------------------------- routing and boot */
const VIEWS = ["tonight", "games", "record", "players", "more"];
function route() {
  const v = VIEWS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "tonight";
  $$(".tabs a, .bottom-tabs a").forEach((a) => { a.classList.toggle("active", a.dataset.view === v); a.setAttribute("aria-current", a.dataset.view === v ? "page" : "false"); });
  closeDrawer();
  const main = $("#main");
  try { main.innerHTML = `<div class="view">${V[v]()}</div>`; }
  catch (e) { main.innerHTML = `<p class="empty">This view could not be drawn (${esc(e.message)}).</p>`; console.error(e); }
  window.scrollTo(0, 0);
}
function chrome() {
  const m = D.meta || {};
  const old = slateDate() < ymdET() && !EMBEDDED_FIXED_DATE();
  $("#updated").innerHTML = `<span class="live-dot${old || (m.stale || {}).odds || (m.warnings || []).length ? " stale" : ""}" id="dot"></span> Updated ${esc(clock(m.generated_at))}`;
  $("#foot-run").textContent = `Data written ${clock(m.generated_at)}`;
}
async function load(force) {
  const emb = $("#embedded").textContent.trim();
  if (emb && !force) { EMBEDDED = true; return JSON.parse(emb); }
  for (const url of ["../data.json", "data.json"]) {
    try { const r = await fetch(url, { cache: "no-store" }); if (r.ok) return await r.json(); } catch (e) {}
  }
  if (emb) { EMBEDDED = true; return JSON.parse(emb); }
  throw new Error("data.json not found");
}
async function boot(force = false) {
  try { D = await load(force); state.cand = null; }
  catch (e) { $("#main").innerHTML = `<p class="empty">Could not load the picks (${esc(e.message)}). Try ↻ in a minute.</p>`; return; }
  if (!D.meta) { $("#main").innerHTML = `<p class="empty">This data file is from an older exporter. Re-run the export step.</p>`; return; }
  chrome(); route();
}

window.addEventListener("hashchange", route);
document.addEventListener("click", (e) => {
  if (e.target.closest("a[data-stop], .book")) return;                 // book buttons open the book, not the drawer
  const el = e.target.closest("[data-pick]");
  if (el) openPick(el.dataset.pick, el.dataset.ticket);
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") return closeDrawer();
  if ((e.key === "Enter" || e.key === " ") && e.target.matches && e.target.matches(".slip[data-pick]")) { e.preventDefault(); openPick(e.target.dataset.pick); }
});
$("#drawer-close").addEventListener("click", closeDrawer);
$("#scrim").addEventListener("click", closeDrawer);
$("#refresh").addEventListener("click", () => boot(true));
$("#theme").addEventListener("click", () => {
  const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  const t = cur === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = t; try { localStorage.setItem("nba-theme", t); } catch (e) {}
});
setInterval(() => { if (!EMBEDDED && document.visibilityState === "visible" && !$("#drawer").classList.contains("open")) boot(true); }, 5 * 60 * 1000);
boot();
