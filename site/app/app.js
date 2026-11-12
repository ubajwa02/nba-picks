"use strict";
/* NBA Picks app: the same tabs and sections as the NBA Picks dashboard, in the Fundamentalist app's design.
   Reads site/data.json (the exporter's format) or an embedded snapshot already in the dashboard's format. */
const ICON={
 today:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5v17M6 6c2.6 2.2 2.6 9.8 0 12M18 6c-2.6 2.2-2.6 9.8 0 12"/></svg>',
 days:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg>',
 picks:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></svg>',
 tickets:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2a3 3 0 0 0 0 6v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-2a3 3 0 0 0 0-6z"/><path d="M14 5v14" stroke-dasharray="2 2"/></svg>',
 record:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 18l5-6 4 3 7-9"/><path d="M4 21h16"/></svg>',
 research:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>'};
const SHORT={today:'Today',days:'Days',picks:'Picks',tickets:'Parlays',record:'Record',research:'Research'};

/* data.json (nbapicks/dashboard.py) -> the shape this page reads */
function adapt(x){
 if(x.straights)return x;
 const T=x.today||{},perf=x.performance||{},P=perf.posted_leans||{},m=x.meta||{},tk=x.tickets||{};
 const rejected=[];let propModel=null;
 for(const d of x.picks_by_day||[]){
  for(const r of [...(d.research||[]),...(d.candidates||[]).filter(c=>c.decision==='watch')]){
   if(!propModel&&r.market==='prop')propModel=r.model_version;
   rejected.push({slate:d.date,label:r.player?`${r.player} ${r.label}`:r.label,category:r.category,ev:r.ev,prob:r.prob,price_american:r.price_american,status:r.status,decision:r.decision,legs:(r.legs||[]).map(l=>l.label)})}}
 return{dk_links:T.dk_links||{},book_links:T.book_links||{},games:T.games||[],
  meta:{generated_at:m.generated_at,today:T.date||m.today,tz:m.timezone||'America/Toronto',last_success:m.last_success||{},stale:m.stale||{},warnings:m.warnings||[],failed:m.last_failed||[],dry_run:m.dry_run,market_status:m.market_status||{}},
  straights:P.rows||[],tickets:tk.rows||[],notes:tk.notes||{},rejected,by_market:P.by_market||{},
  models:{game:(T.predict_run||{}).model||'–',props:propModel||'–'},allmodel:perf.all_model||{n:0,net_units:0,hit_rate:null},runs:[]}}

async function loadData(){
 const emb=document.getElementById('embedded').textContent.trim();
 if(emb)return JSON.parse(emb);
 for(const url of ['../data.json','data.json']){try{const r=await fetch(url,{cache:'no-store'});if(r.ok)return await r.json()}catch(e){}}
 throw new Error('data.json not found')}

document.getElementById('theme').addEventListener('click',()=>{
 const cur=document.documentElement.dataset.theme||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'),t=cur==='dark'?'light':'dark';
 document.documentElement.dataset.theme=t;try{localStorage.setItem('nba-theme',t)}catch(e){}});

loadData().then(x=>start(adapt(x))).catch(e=>{document.getElementById('main').innerHTML=`<p class="empty">Could not load the picks (${String(e.message).replace(/</g,'&lt;')}). Try again in a minute.</p>`});

function start(D){

const TZ=D.meta.tz,$=s=>document.querySelector(s);
const STAT={pts:'PTS',reb:'REB',ast:'AST',fg3m:'3PM'};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const u=(x,dp=2)=>x==null?'–':(x>0?'+':x<0?'−':'')+Math.abs(x).toFixed(dp)+'u';
const cls=x=>x>0?'pos':x<0?'neg':'mut';
const pc=(x,dp=0)=>x==null?'–':(x*100).toFixed(dp)+'%';
const am=x=>x==null?'–':(x>0?'+'+x:String(x));
const day=(s,o={weekday:'short',month:'short',day:'numeric'})=>new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{...o,timeZone:'UTC'});
const tip=iso=>new Date(iso.replace('Z',':00Z').replace('::','::')).toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit',timeZone:TZ});
const pill=r=>{const k=r||'pending';return `<span class="pill ${k}">${k==='win'?'Won':k==='loss'?'Lost':k==='void'?'Void':k==='push'?'Push':'Pending'}</span>`};
// ---- derive
const S=D.straights,T=D.tickets;
const all=[...S.map(r=>({...r,type:'straight'})),...T.map(r=>({...r,type:r.kind}))];
const settled=r=>r.result==='win'||r.result==='loss';
function rec(rows){const w=rows.filter(r=>r.result==='win').length,l=rows.filter(r=>r.result==='loss').length,pe=rows.filter(r=>!r.result||r.result==='pending').length;
 const net=rows.reduce((a,r)=>a+(r.net_units||0),0),st=rows.filter(r=>['win','loss','push'].includes(r.result)).reduce((a,r)=>a+(r.stake||1),0);
 return{w,l,pe,n:rows.length,net,roi:st?net/st:null,hit:w+l?w/(w+l):null,avgp:rows.length?rows.filter(settled).reduce((a,r)=>a+r.prob,0)/Math.max(1,w+l):null}}
const Rs=rec(S),Rt=rec(T);
const TYPES=[['straight','Straights'],['parlay','Parlays'],['lotto','Lotto']];
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}}
const pool=()=>all.filter(r=>r.type===F.bt);
const TL=()=>TYPES.find(x=>x[0]===F.bt)[1];
const typeSeg=()=>`<div class="seg tseg" role="group" aria-label="Bet type">${TYPES.map(([v,l])=>`<button data-f="bt" data-v="${v}" aria-pressed="${F.bt===v}">${l}</button>`).join('')}</div>`;
const slates=[...new Set(all.map(r=>r.slate))].sort();
const latest=slates[slates.length-1];
const age=(Date.now()-new Date(D.meta.generated_at))/6e4;
const stale=D.meta.stale.odds||D.meta.stale.ingest||D.meta.failed.length>0;
$('#updated').innerHTML='<span class="live-dot'+(stale?' stale':'')+'"></span> Updated '+new Date(D.meta.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZone:TZ})+' ET';
const VIEWS=[['today','Today'],['days','Day by day'],['picks','Picks'],['tickets','Parlays & Lotto'],['record','Record'],['research','Research']];
let view='today',F={res:'all',mkt:'all',day:'all',tk:'all',bt:'straight'};{const s=ls('nba-bt');if(TYPES.some(x=>x[0]===s))F.bt=s}
function nav(){$('#tabs').innerHTML=VIEWS.map(([k,l])=>`<a href="#${k}" class="${k===view?'active':''}" aria-current="${k===view?'page':'false'}">${l}</a>`).join('');
 $('#btabs').innerHTML=VIEWS.map(([k])=>`<a href="#${k}" class="${k===view?'active':''}" aria-current="${k===view?'page':'false'}">${ICON[k]}${SHORT[k]}</a>`).join('')}
// ---- components
function pickCard(r){const p=r.stat?`${STAT[r.stat]||r.stat}`:'';const res=r.result||'pending';
 const sel=r.selection;const side=r.market==='prop'?`${sel==='over'?'Over':'Under'} ${r.line} ${p}`:esc(r.label);
 const name=r.market==='prop'?esc(r.label.replace(/ [ou][\d.]+ \w+$/,'')):esc(r.label);
 const t=r.market==='prop'?name:esc(r.label);
 const sub=r.market==='prop'?`${side} · ${esc(r.matchup||'')}`:`${r.market.toUpperCase()} · ${esc(r.matchup||'')}`;
 const out=r.result&&r.stat_value!=null?` · result ${r.stat_value}`:'';
 return `<div class="pick ${res}"><div class="t">${t}</div><div class="r">${pill(r.result)}<span class="num ${cls(r.net_units)}">${r.result?u(r.net_units):''}</span></div><div class="m">${sub}${out}</div><div class="m"><span class="num">${am(r.price_american)}</span> · model ${pc(r.prob)}</div></div>`}
function tkCard(t){const res=t.result||'pending';return `<div class="tk"><div class="h"><div><b>${t.kind==='lotto'?'Lotto':'Parlay'} · ${t.legs.length} legs</b> <span class="mut">${day(t.slate,{month:'short',day:'numeric'})}</span></div><div>${pill(t.result)} <span class="num ${cls(t.net_units)}">${t.result?u(t.net_units):''}</span></div></div>
<div class="st"><span>Pays <b class="num" style="color:var(--fg)">${am(t.price_american)}</b></span><span>Hit chance <b class="num" style="color:var(--fg)">${pc(t.prob,1)}</b></span><span>Edge <b class="num" style="color:var(--fg)">${t.ev>0?'+':''}${pc(t.ev,1)}</b></span><span class="pill paper">Paper</span></div>
<ul>${t.legs.map(l=>`<li><span><i class="legdot ${l.result||''}"></i>${esc(l.label)}</span><span class="num mut">${am(l.price_american)}</span></li>`).join('')}</ul></div>`}
const tipOf=r=>{const g=D.games.find(g=>r.matchup===`${g.away} @ ${g.home}`);return g?tip(g.start_utc):''};
function parts(r){const m=String(r.label).match(/^(.*) ([ou])([\d.]+) (\w+)$/);if(m)return{who:m[1],bet:`${m[2]==='o'?'Over':'Under'} ${m[3]} ${STAT[m[4]]||m[4].toUpperCase()}`};
 return{who:r.label,bet:{ml:'Moneyline',spread:'Spread',total:'Total'}[r.market]||'Game line'}}
// Past game_id -> matchup (2026-27 games to Nov 1). Newer games come from leg.matchup or today's slate.
const GM={"401909088":"BOS @ DET","401909089":"PHI @ NY","401909090":"OKC @ SA","401909834":"ATL @ ORL","401909835":"MIL @ WSH","401909091":"MIN @ MIA","401909836":"CHA @ BKN","401909837":"CHI @ TOR","401909838":"UTAH @ MEM","401909839":"IND @ NO","401909840":"DAL @ HOU","401909092":"GS @ LAL","401909841":"PHX @ POR","401909842":"SAC @ LAC","401909093":"CLE @ PHI","401909094":"DEN @ OKC","401909848":"CHI @ MIL","401909095":"NY @ BOS","401909843":"ATL @ CHA","401909844":"DAL @ IND","401909845":"MIN @ ORL","401909846":"TOR @ WSH","401909847":"DET @ MIA","401909096":"HOU @ SA","401909849":"NO @ UTAH","401909850":"MEM @ GS","401909851":"LAC @ LAL","401909852":"POR @ SAC","401909861":"LAL @ UTAH","401909862":"IND @ BKN","401909863":"ORL @ NY","401909864":"TOR @ MIN","401909865":"LAC @ OKC","401909866":"DET @ PHI","401909867":"MEM @ SAC","401909868":"WSH @ CHA","401909869":"MIN @ CLE","401909870":"CHI @ BOS","401909871":"DAL @ MIA","401909872":"IND @ MIL","401909873":"PHX @ OKC","401909874":"ATL @ HOU","401909875":"MEM @ UTAH","401909876":"GS @ DEN","401909877":"BKN @ BOS","401909878":"DET @ NY","401909879":"SAC @ SA","401909880":"POR @ LAL","401909853":"MIA @ CHA","401909854":"BKN @ CLE","401909855":"MIL @ PHI","401909857":"WSH @ CHI","401909858":"SA @ DAL","401909856":"HOU @ ATL","401909859":"NO @ DEN","401909860":"GS @ PHX","401909881":"MIA @ ATL","401909882":"WSH @ CLE","401909883":"CHA @ DET","401909884":"PHI @ IND","401909885":"ORL @ TOR","401909886":"NY @ CHI","401909887":"HOU @ MIL","401909888":"GS @ MIN","401909889":"DEN @ NO","401909890":"SA @ UTAH","401909891":"OKC @ DAL","401909892":"LAL @ LAC","401909893":"CLE @ ATL","401909894":"SAC @ NO","401909895":"MEM @ POR","401909277":"CHA @ WSH","401909278":"CHI @ BOS","401909279":"DET @ BKN","401909280":"NY @ PHI","401909281":"ORL @ TOR","401909282":"IND @ MIA","401909283":"HOU @ DAL","401909284":"LAC @ MIN","401909285":"LAL @ GS","401909286":"DEN @ PHX","401909896":"POR @ UTAH","401909897":"PHI @ CHA","401909898":"ATL @ NO","401909899":"SAC @ MEM","401909900":"CLE @ MIL","401909901":"MIN @ SA","401909902":"OKC @ HOU","401909903":"BOS @ ORL","401909904":"BKN @ IND","401909905":"LAC @ GS","401909906":"TOR @ LAL"};
function legGame(l){const g=D.games.find(g=>g.game_id===l.game_id);const m=l.matchup||(g?`${g.away} @ ${g.home}`:GM[l.game_id]);
 const st=l.start_utc||(g&&g.start_utc);return m?(isPend(l)&&st?`${m} · ${tip(st)}`:m):''}
const isPend=r=>!r.result||r.result==='pending';
function hd(c){return `<li class="row hd"><span>Result</span><span>${c}</span><span>Game</span><span>DK odds</span><span>Actual</span><span>Units</span></li>`}
// ---- bet buttons (today's card only; logic ported from nba-picks site/index.html slipLinks/comboLinks)
const BOOKS=[['draftkings','DK','sportsbook.draftkings.com'],['fanduel','FD','sportsbook.fanduel.com']];
const normName=s=>String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/-/g,' ').replace(/[^a-z ]/g,'').split(/\s+/).filter(w=>w&&!['jr','sr','ii','iii','iv'].includes(w)).join(' ');
const propPlayer=r=>{const m=/^(.*?) [ou]\d+(?:\.\d+)? \w+$/.exec(String(r.label||''));return normName(m?m[1]:r.player)};
const fmtLine=x=>(x>0?'+':'')+x;
function closest(outs,r){const same=outs.filter(o=>o.market===r.market&&o.selection===r.selection&&(r.market!=='prop'||(o.stat===r.stat&&o.player===propPlayer(r))));
 const o=same.find(o=>r.market==='ml'||(o.line!=null&&r.line!=null&&Math.abs(o.line-r.line)<1e-6))||same.filter(o=>o.line!=null&&r.line!=null).sort((a,b)=>Math.abs(a.line-r.line)-Math.abs(b.line-r.line))[0];
 return o?{o,other:r.market!=='ml'&&o.line!=null&&Math.abs(o.line-r.line)>1e-6?(r.market==='spread'?fmtLine(o.line):String(o.line)):null}:null}
const okHost=(u,h)=>{try{const x=new URL(u);return x.protocol==='https:'&&x.host===h}catch(e){return false}};
function slipLinks(r){const gid=String(r.game_id),bl=(D.book_links||{})[gid]||{},dk=(D.dk_links||{})[gid],out=[];
 for(const [book,short,host] of BOOKS){let hit=closest(bl[book]||[],r),url=hit&&hit.o.link;
  if(!hit&&book==='draftkings'&&dk&&r.market!=='prop'){hit=closest(dk.outcomes||[],r);url=hit&&`${dk.event_url}?outcomes=${encodeURIComponent(hit.o.outcome_id)}`}
  if(hit&&okHost(url,host))out.push({url,book,label:`Bet ${short}${hit.other!=null?' '+hit.other:''}`,slip:1})}
 if(!out.some(x=>x.book==='draftkings')&&dk&&okHost(dk.event_url,'sportsbook.draftkings.com'))out.push({url:dk.event_url,book:'draftkings',label:'DK game'});
 return out}
function comboLinks(legsIn,partial){const out=[];
 for(const [book,short] of BOOKS){let legs=legsIn.map(l=>slipLinks(l).find(k=>k.book===book&&k.slip));const tot=legs.length;
  if(partial)legs=legs.filter(Boolean);
  if(legs.length<2||legs.some(k=>!k))continue;const qs=legs.map(k=>new URL(k.url).searchParams);let url;
  if(book==='draftkings')url='https://sportsbook.draftkings.com/?outcomes='+qs.map(q=>encodeURIComponent(q.get('outcomes')||'')).join('+');
  else url='https://sportsbook.fanduel.com/addToBetslip?'+qs.map((q,i)=>`marketId[${i}]=${encodeURIComponent(q.get('marketId')||'')}&selectionId[${i}]=${encodeURIComponent(q.get('selectionId')||'')}`).join('&');
  if(qs.every(q=>q.get(book==='draftkings'?'outcomes':'selectionId'))&&okHost(url,BOOKS.find(b=>b[0]===book)[2]))out.push(`<a class="dk${book==='fanduel'?' fd':''}" href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="Tries to put every leg on one ${short} slip. Check all ${legs.length} legs are on the slip before placing.">${short} parlay${legs.length<tot?` (${legs.length} of ${tot} legs)`:''} (unverified) ↗</a>`)}
 return out.join('')}
const aBtn=k=>`<a class="dk${k.book==='fanduel'?' fd':''}" href="${esc(k.url)}" target="_blank" rel="noopener noreferrer">${esc(k.label)} ↗</a>`;
function betBtns(r){if(r.slate&&r.slate!==D.meta.today)return '';const b=slipLinks(r).map(aBtn).join('');return b?`<span class="bb">${b}</span>`:''}
function betRow(r){const p=parts(r),pe=isPend(r),res=r.result||'pending';
 return `<li class="row ${res}"><span class="res">${pill(r.result)}</span><span class="who"><b>${esc(p.who)}</b><span class="bet">${p.bet}</span>${betBtns(r)}</span><span class="gm">${esc(r.matchup||'')}</span><span class="odds">${am(r.price_american)}</span><span class="act" data-l="${pe?'Tip':'Actual'}">${pe?(tipOf(r)||''):r.stat_value!=null?`<b>${r.stat_value}</b>`:''}</span><span class="un ${cls(r.net_units)}">${pe?'1u':u(r.net_units)}</span></li>`}
function tkRow(t){const pe=isPend(t),res=t.result||'pending';
 return `<li class="row tkr ${res}"><span class="res">${pill(t.result)}</span><span class="who"><b>${t.kind==='lotto'?'Lotto':'Parlay'} · ${t.legs.length} legs</b>${t.slate===D.meta.today&&pe?(()=>{const c=comboLinks(t.legs);return c?`<span class="bb">${c}</span>`:''})():''}<span class="legs">${t.legs.map(l=>{const p=parts(l);return `<span class="leg ${isPend(l)?'':l.result}">${esc(p.who)} <b>${p.bet}</b>${!isPend(l)&&l.stat_value!=null?` <span>(${l.stat_value})</span>`:''}${legGame(l)?`<span class="lg">${esc(legGame(l))}</span>`:''}${t.slate===D.meta.today?betBtns(Object.assign({slate:D.meta.today},l)):''}</span>`}).join('')}</span></span><span class="gm">${pc(t.prob,0)} to hit</span><span class="odds">${am(t.price_american)}</span><span class="act"></span><span class="un ${cls(t.net_units)}">${pe?'1u':u(t.net_units)}</span></li>`}
const betList=rows=>rows.length?`<ul class="bl">${hd('Pick')}${rows.map(betRow).join('')}</ul>`:'';
const tkList=rows=>rows.length?`<ul class="bl">${hd('Ticket')}${rows.map(tkRow).join('')}</ul>`:'';
function kpi(l,v,s,c='',main=false){return `<div class="kpi ${main?'main':''}"><div class="l">${l}</div><div class="v ${c}">${v}</div><div class="s">${s}</div></div>`}
// ---- views
function vToday(){
 const td=D.meta.today,todayS=all.filter(r=>r.slate===td),st=todayS.filter(r=>r.type==='straight'),tt=todayS.filter(r=>r.type!=='straight');
 const prev=slates.filter(d=>d<td).pop(),last=all.filter(r=>r.slate===prev),rl=rec(last),rt=rec(todayS);
 const np=tt.filter(t=>t.kind==='parlay').length,nl=tt.filter(t=>t.kind==='lotto').length;
 let h=`<div class="hero"><p class="eyebrow">${day(td,{weekday:'long',month:'long',day:'numeric'})} · ${D.games.length} games</p><h1>${todayS.length?'Today’s bets':'Today’s card is not posted yet'}</h1>
 ${todayS.length?`<p class="sub">${st.length} straight picks, ${np} parlays and ${nl} lotto · ${rt.pe?`${rt.pe} pending`:`graded ${rt.w}–${rt.l}, ${u(rt.net)}`}</p>`:''}</div>`;
 if(todayS.length){h+=`<div class="lab2">Straight picks</div>${(()=>{const c=comboLinks(st.filter(isPend),true);return c?`<span class="bb">${c.replace(/parlay/g,'all straights on one slip')}</span>`:''})()}${betList(st)}`;if(tt.length)h+=`<div class="lab2">Parlays and lotto</div>${tkList(tt)}`;(D.notes[td]||[]).forEach(n=>h+=`<div class="note">${esc(n)}</div>`)}
 else h+=`<div class="empty" style="margin-top:14px"><b>Nothing posted for ${day(td,{weekday:'long'})} yet</b>Weekday picks post around 4:30 PM ET and weekend picks around 11 AM ET. Straights, two parlays and a lotto appear here as soon as they post.</div>`;
 {const Ra=rec(pool());h+=`<h2>Season · ${TL()}</h2><div class="tools">${typeSeg()}</div><div class="kpis" style="margin-top:0">${kpi(TL()+' units',u(Ra.net),`${Ra.n} paper ${F.bt==='straight'?'picks':'tickets'}, 1u each`,cls(Ra.net),true)}${kpi('Record',`${Ra.w}–${Ra.l}`,`${pc(Ra.hit)} hit rate`)}${kpi('ROI',pc(Ra.roi,1),'on units staked',cls(Ra.roi))}${kpi('Pending',Ra.pe,Ra.pe?'waiting on final scores':'everything graded')}</div>`}
 if(last.length){const ls=last.filter(r=>r.type==='straight'),lt=last.filter(r=>r.type!=='straight');
  h+=`<h2>Last card · ${day(prev)} <small>${rl.w}–${rl.l}, <span class="${cls(rl.net)}">${u(rl.net)}</span></small></h2>${betList(ls)}${lt.length?`<div class="lab2">Parlays and lotto</div>${tkList(lt)}`:''}`;
  (D.notes[prev]||[]).forEach(n=>h+=`<div class="note">${esc(n)}</div>`)}
 h+=`<details class="fold"><summary>Tonight’s slate · ${D.games.length} games, tip times in ET</summary><div class="games">${D.games.map(g=>`<div class="g"><b>${g.away} @ ${g.home}</b><span>${tip(g.start_utc)}</span>${(()=>{const e=((D.dk_links||{})[g.game_id]||{}).event_url,u=okHost(e,'sportsbook.draftkings.com')?e:'https://sportsbook.draftkings.com/leagues/basketball/nba';return `<a class="dk" href="${esc(u)}" target="_blank" rel="noopener noreferrer">DK game ↗</a>`})()}</div>`).join('')}</div><p class="sub">Buttons open the DraftKings game page. Bet buttons use slip links supplied by The Odds API; they have not been click-tested by us. If the book offers a different line the button shows it. Parlay buttons are built by joining those links and are unverified. Always check the line, price and every leg on the slip before betting. “DK game” only opens the game page.</p></details>`;
 h+=`<div class="note w"><b>Paper results only.</b> Lines and odds come from DraftKings (via ESPN), since there is no free FanDuel feed. FanDuel may post a different line or skip a player entirely. These are model picks tracked at 1 unit each. No real wagers are logged, and every market is still labelled research.</div>`;
 return h}
function vDays(){
 const ds=[...slates].reverse().filter(d=>pool().some(r=>r.slate===d)),isS=F.bt==='straight';
 return `<div class="hero"><p class="eyebrow">Every posted card and how it graded</p><h1>Day by day · ${TL()}</h1></div>
 <div class="tools">${typeSeg()}<span class="mut">Newest first. Only posted picks appear here.</span></div>
 ${ds.map((d,i)=>{const rows=pool().filter(r=>r.slate===d),a=rec(rows);
 return `<details class="day" ${i<2?'open':''}><summary class="dh" style="cursor:pointer;list-style:none"><h3>${day(d,{weekday:'long',month:'short',day:'numeric'})}</h3><div class="chips"><div class="chip"><span>${TL()}</span><b>${a.w}–${a.l}${a.pe?` · ${a.pe} pending`:''}</b></div><div class="chip"><span>Units</span><b class="${cls(a.net)}">${u(a.net)}</b></div></div></summary>
 <div class="db">${isS?betList(rows):tkList(rows)}${isS?'':(D.notes[d]||[]).map(n=>`<div class="note">${esc(n)}</div>`).join('')}</div></details>`}).join('')||'<p class="empty">Nothing posted for this bet type yet.</p>'}`}
function vPicks(){
 const rows=S.filter(r=>(F.res==='all'||(F.res==='pending'?(!r.result||r.result==='pending'):r.result===F.res))&&(F.mkt==='all'||r.market===F.mkt)&&(F.day==='all'||r.slate===F.day)).sort((a,b)=>b.slate.localeCompare(a.slate));
 const rr=rec(rows);
 const seg=(k,opts)=>`<div class="seg" role="group">${opts.map(([v,l])=>`<button data-f="${k}" data-v="${v}" aria-pressed="${F[k]===v}">${l}</button>`).join('')}</div>`;
 return `<div class="hero"><p class="eyebrow">Straight picks</p><h1>${rr.w}–${rr.l} · ${u(rr.net)}</h1></div>
 <div class="tools">${seg('res',[['all','All'],['pending','Pending'],['win','Won'],['loss','Lost']])}${seg('mkt',[['all','All markets'],['prop','Props'],['ml','ML'],['spread','Spread']])}
 <select id="dsel" aria-label="Day"><option value="all">All days</option>${[...new Set(S.map(r=>r.slate))].sort().reverse().map(d=>`<option value="${d}" ${F.day===d?'selected':''}>${day(d)}</option>`).join('')}</select><span class="mut">${rows.length} picks</span></div>
 <div class="tw"><table><thead><tr><th>Day</th><th>Pick</th><th>Game</th><th class="n">Price</th><th class="n">Model</th><th class="n">Actual</th><th>Result</th><th class="n">Units</th></tr></thead><tbody>${rows.map(r=>`<tr><td class="mut" style="white-space:nowrap">${day(r.slate,{month:'short',day:'numeric'})}</td><td><b>${esc(r.label)}</b></td><td class="mut">${esc(r.matchup||'')}</td><td class="n">${am(r.price_american)}</td><td class="n">${pc(r.prob)}</td><td class="n">${r.stat_value??'–'}</td><td>${pill(r.result)}</td><td class="n ${cls(r.net_units)}">${r.result?u(r.net_units):''}</td></tr>`).join('')||'<tr><td colspan="8" class="mut">No picks match these filters.</td></tr>'}</tbody></table></div>`}
function vTickets(){
 const rows=T.filter(r=>F.tk==='all'||r.kind===F.tk).sort((a,b)=>b.slate.localeCompare(a.slate));
 const rp=rec(T.filter(t=>t.kind==='parlay')),rlo=rec(T.filter(t=>t.kind==='lotto'));
 return `<div class="hero"><p class="eyebrow">Parlays and lotto · paper</p><h1>Parlays <span class="${cls(rp.net)}">${u(rp.net)}</span> · Lotto <span class="${cls(rlo.net)}">${u(rlo.net)}</span></h1></div>
 <div class="kpis">${kpi('Parlays',`${rp.w}–${rp.l}`,u(rp.net),cls(rp.net))}${kpi('Lotto',`${rlo.w}–${rlo.l}`,u(rlo.net),cls(rlo.net))}${kpi('Parlay hit rate',pc(rp.hit,0),`model expected ${pc(rp.avgp,0)}`)}${kpi('Lotto hit rate',pc(rlo.hit,0),`model expected ${pc(rlo.avgp,0)}`)}</div>
 <div class="tools" style="margin-top:14px"><div class="seg">${[['all','All'],['parlay','Parlays'],['lotto','Lotto']].map(([v,l])=>`<button data-f="tk" data-v="${v}" aria-pressed="${F.tk===v}">${l}</button>`).join('')}</div></div>
 ${tkList(rows)}
 <div class="note">Each day posts two parlays and one lotto from the highest-probability legs. Tickets pay out only when every leg wins, so short winning streaks and long losing ones are normal.</div>`}
function series(which){const by={};all.filter(r=>r.result&&r.result!=='pending'&&r.type===which).forEach(r=>{by[r.slate]=(by[r.slate]||0)+(r.net_units||0)});
 let c=0;return Object.keys(by).sort().map(d=>(c+=by[d],{d,day:by[d],cum:c}))}
function vRecord(){
 const R=rec(pool()),isS=F.bt==='straight',sr=series(F.bt);
 const mk=Object.entries(D.by_market).map(([k,v])=>({k:{prop:'Props',ml:'Moneyline',spread:'Spread',total:'Total'}[k]||k,...v}));
 return `<div class="hero"><p class="eyebrow">Performance over time · ${TL()}</p><h1><span class="${cls(R.net)}">${u(R.net)}</span> on ${TL().toLowerCase()} since ${pool().length?day(pool().map(r=>r.slate).sort()[0],{month:'short',day:'numeric'}):'–'}</h1></div>
 <div class="tools" style="margin-top:14px">${typeSeg()}</div>
 <div class="kpis" style="margin-top:0">${kpi('Units',u(R.net),`${R.n} ${isS?'picks':'tickets'} at 1u`,cls(R.net),true)}${kpi('Record',`${R.w}–${R.l}`,`${pc(R.hit)} hit rate${R.pe?` · ${R.pe} pending`:''}`)}${kpi('ROI',pc(R.roi,1),'on units staked',cls(R.roi))}${kpi('Model vs actual',`${pc(R.avgp)} → ${pc(R.hit)}`,'average model chance vs hit rate')}</div>
 <h2>Cumulative units · ${TL()}</h2><div class="panel"><div class="chart" id="c1" role="img" aria-label="Cumulative units by day"></div></div>
 <div class="cols"><div><h2>Daily result</h2><div class="panel"><div class="chart" id="c2" role="img" aria-label="Net units per day"></div></div></div>
 ${isS?`<div><h2>By market</h2><div class="panel"><div class="bars">${mk.map(m=>`<div class="bar2"><b>${m.k}</b><div><div class="track" title="hit rate"><i style="width:${(m.hit_rate||0)*100}%"></i></div><span class="mut" style="font-size:12px">${m.wins}–${m.losses} · ${pc(m.hit_rate)} hit</span></div><span class="num ${cls(m.net_units)}">${u(m.net_units)}</span></div>`).join('')}</div></div></div>`:`<div><h2>How often it cashes</h2><div class="panel"><div class="bars"><div class="bar2"><b>Expected</b><div><div class="track"><i style="width:${(R.avgp||0)*100}%;background:var(--mut)"></i></div></div><span class="num">${pc(R.avgp)}</span></div><div class="bar2"><b>Actual</b><div><div class="track"><i style="width:${(R.hit||0)*100}%"></i></div></div><span class="num">${pc(R.hit)}</span></div></div></div></div>`}</div>
 <h2>Day by day · ${TL()}</h2><div class="tw"><table><thead><tr><th>Day</th><th class="n">Record</th><th class="n">Units</th><th class="n">Running</th></tr></thead><tbody>${[...sr].reverse().map(s=>{const a=rec(pool().filter(r=>r.slate===s.d));return `<tr><td>${day(s.d)}</td><td class="n">${a.w}–${a.l}</td><td class="n ${cls(s.day)}">${u(s.day)}</td><td class="n ${cls(s.cum)}">${u(s.cum)}</td></tr>`}).join('')}</tbody></table></div>
 <div class="note w">${sr.length} graded days is a small sample. Treat these numbers as a progress report, not proof of an edge.</div>`}
function vResearch(){
 const ms=Object.entries(D.meta.market_status),ls=D.meta.last_success;
 const rej=D.rejected,days=[...new Set(rej.map(r=>r.slate))];
 return `<div class="hero"><p class="eyebrow">Model and system</p><h1>Everything is still in research</h1></div>
 <div class="hl" style="margin-top:14px">${ms.map(([k,v])=>`<div class="chip"><span>${k}</span><b>${v}</b></div>`).join('')}<div class="chip"><span>Game model</span><b>${esc(D.models.game)}</b></div><div class="chip"><span>Prop model</span><b>${esc(D.models.props)}</b></div></div>
 <div class="note">The full model run (${D.allmodel.n.toLocaleString()} graded candidates at 1u each) is ${u(D.allmodel.net_units,0)} with a ${pc(D.allmodel.hit_rate,1)} hit rate. Only the picks that cleared our checks are posted, and those are what the other tabs show.</div>
 <h2>Pipeline health <small>${stale?'needs attention':'all steps current'}</small></h2><div class="hl">${Object.entries(ls).map(([k,v])=>`<div class="chip"><span>${k}</span><b>${new Date(v).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZone:TZ})}</b></div>`).join('')}</div>
 <details class="fold"><summary>Rejected and watch-list candidates (${rej.length}, last ${days.length} days)</summary><p class="mut">These were scored but never posted. They are not counted in any record.</p>
 <div class="tw"><table><thead><tr><th>Day</th><th>Candidate</th><th class="n">Edge</th><th class="n">Hit chance</th><th>Outcome</th></tr></thead><tbody>${rej.map(r=>`<tr><td class="mut">${day(r.slate,{month:'short',day:'numeric'})}</td><td>${r.legs.length?r.legs.map(esc).join(' + '):esc(r.label)}</td><td class="n">${r.ev>0?'+':''}${pc(r.ev,0)}</td><td class="n">${pc(r.prob)}</td><td>${pill(r.status==='win'?'win':r.status==='loss'?'loss':'pending')}</td></tr>`).join('')}</tbody></table></div></details>`}
// ---- charts
function line(el,pts,which){
 if(!el)return;const W=el.clientWidth||600,H=Math.min(280,Math.max(190,W*.4)),m={l:44,r:14,t:12,b:26};
 if(!pts.length){el.innerHTML='<p class="mut">No graded picks yet.</p>';return}
 const xs=pts.map((p,i)=>i),y0=Math.min(0,...pts.map(p=>p[which])),y1=Math.max(0,...pts.map(p=>p[which]));
 const pad=(y1-y0)*.12||1,lo=y0-(y0<0?pad:0),hi=y1+pad;
 const X=i=>m.l+(pts.length>1?i/(pts.length-1):.5)*(W-m.l-m.r),Y=v=>m.t+(1-(v-lo)/(hi-lo))*(H-m.t-m.b);
 const step=Math.ceil((hi-lo)/4),tk=[];for(let v=Math.ceil(lo/step)*step;v<=hi;v+=step)tk.push(v);
 let s=`<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">`;
 tk.forEach(v=>s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)" stroke-width="${v===0?1.5:1}" ${v===0?'':'stroke-dasharray="2 4"'}/><text x="${m.l-8}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--mut)" font-family="var(--mono)">${v>0?'+':''}${v}</text>`);
 const every=Math.ceil(pts.length/6);pts.forEach((p,i)=>{if(i%every===0||(i===pts.length-1&&i%every>=every/2))s+=`<text x="${X(i)}" y="${H-6}" text-anchor="middle" font-size="11" fill="var(--mut)">${day(p.d,{month:'short',day:'numeric'})}</text>`});
 if(which==='cum'){const d=pts.map((p,i)=>`${i?'L':'M'}${X(i)},${Y(p.cum)}`).join('');
  s+=`<path d="${d}L${X(pts.length-1)},${Y(0)}L${X(0)},${Y(0)}Z" fill="var(--chart)" opacity=".12" class="area"/><path class="ln" pathLength="1" d="${d}" fill="none" stroke="var(--chart)" stroke-width="2.5" stroke-linejoin="round"/>`;
  const l=pts[pts.length-1];s+=`<circle cx="${X(pts.length-1)}" cy="${Y(l.cum)}" r="5" fill="var(--chart)" stroke="var(--panel)" stroke-width="2"/>`}
 else{const bw=Math.max(6,Math.min(36,(W-m.l-m.r)/pts.length-6));pts.forEach((p,i)=>{const y=Y(p.day),z=Y(0);s+=`<rect x="${X(i)-bw/2}" y="${Math.min(y,z)}" width="${bw}" height="${Math.max(2,Math.abs(y-z))}" rx="3" fill="${p.day>=0?'var(--posbar)':'var(--negbar)'}"/>`})}
 s+=`<line id="xh" y1="${m.t}" y2="${H-m.b}" stroke="var(--mut)" stroke-dasharray="3 3" style="display:none"/></svg><div class="tip" style="display:none"></div>`;
 el.innerHTML=s;const svg=el.querySelector('svg'),tp=el.querySelector('.tip'),xh=el.querySelector('#xh');
 const mv=e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)*(W/r.width);let i=Math.round((px-m.l)/((W-m.l-m.r)/Math.max(1,pts.length-1)));i=Math.max(0,Math.min(pts.length-1,i));const p=pts[i];
  xh.style.display='';xh.setAttribute('x1',X(i));xh.setAttribute('x2',X(i));tp.style.display='';tp.style.left=Math.max(70,Math.min(W-70,X(i)))+'px';tp.style.top=Y(p[which])+'px';
  tp.innerHTML=`<b>${day(p.d)}</b><br>Day <span class="${cls(p.day)}">${u(p.day)}</span> · Running <span class="${cls(p.cum)}">${u(p.cum)}</span>`};
 svg.addEventListener('pointermove',mv);svg.addEventListener('pointerdown',mv);svg.addEventListener('pointerleave',()=>{tp.style.display='none';xh.style.display='none'})}
function charts(){if(view!=='record')return;const p=series(F.bt);line($('#c1'),p,'cum');line($('#c2'),p,'day')}
function render(enter){nav();$('#main').innerHTML=`<div class="view${enter?' enter':''}">`+{today:vToday,days:vDays,picks:vPicks,tickets:vTickets,record:vRecord,research:vResearch}[view]()+'</div>';charts();
 document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{F[b.dataset.f]=b.dataset.v;if(b.dataset.f==='bt')ls('nba-bt',b.dataset.v);const y=scrollY;render();scrollTo(0,y)});
 const ds=$('#dsel');if(ds)ds.onchange=()=>{F.day=ds.value;render()}}
function route(){const h=location.hash.slice(1);view=VIEWS.some(v=>v[0]===h)?h:'today';render(true);scrollTo(0,0)}
let lastW=innerWidth;addEventListener('hashchange',route);addEventListener('resize',()=>{if(innerWidth!==lastW){lastW=innerWidth;charts()}});route();
}
