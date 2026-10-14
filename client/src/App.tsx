import {useEffect,useMemo,useRef,useState} from "react";
import {ArrowDown,ArrowUp,ArrowUpRight,Check,ChevronRight,Copy,Download,Grid2X2,Info,Layers3,List,Menu,Moon,RefreshCw,Search,Sun,X} from "lucide-react";
import {ResponsiveContainer,LineChart,Line,Tooltip,XAxis,YAxis,CartesianGrid} from "recharts";
import type {Snapshot,Group,Stock} from "../../shared/schema";

const REPO="https://github.com/arjunbchavan1989-AB/nse-theme-tracker";
const RAW="https://raw.githubusercontent.com/arjunbchavan1989-AB/nse-theme-tracker/main/client/public/data/";
const fmt=(v:number|null|undefined,d=1)=>v==null?"N/A":v.toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const sign=(v:number|null|undefined)=>v==null?"":v>=0?"positive":"negative";
const pct=(v:number|null|undefined)=>v==null?"N/A":`${v>=0?"+":""}${fmt(v)}%`;
const tv=(symbol:string)=>"NSE:"+symbol.replace(/[&-]/g,"_");
const link=(s:string)=>"https://www.tradingview.com/chart/?symbol="+encodeURIComponent(tv(s));
const keys:[string,string][]=[["score","Leadership"],["d1","1D return"],["w1","1W return"],["m1","1M return"],["m3","3M return"],["rs_excess","RS excess"],["above50","Breadth"],["rank_change","Rank improvement"]];
type SortKey="score"|"d1"|"w1"|"m1"|"m3"|"rs_excess"|"above50"|"rank_change";
function value(g:Group,key:SortKey){return g[key];}
function exportCSV(rows:Record<string,unknown>[],name:string){
 if(!rows.length)return;
 const cols=Object.keys(rows[0]);const cell=(v:unknown)=>{
  const text=typeof v==="string"&&/^[=+\-@\t\r]/.test(v)?"'"+v:String(v??"");
  return `"${text.replaceAll('"','""')}"`;
 };
 const csv=[cols.map(cell).join(","),...rows.map(r=>cols.map(k=>cell(r[k])).join(","))].join("\n");
 const a=document.createElement("a");const url=URL.createObjectURL(new Blob(["\ufeff"+csv],{type:"text/csv;charset=utf-8"}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function Spark({data,color="var(--accent)"}:{data:number[];color?:string}){
 return <div className="spark" aria-label="Current-members 3-month normalized path"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.map((v,i)=>({i,v}))}><Line dataKey="v" type="monotone" stroke={color} strokeWidth={1.8} dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>;
}
export default function App(){
 const [data,setData]=useState<Snapshot|null>(null),[sessions,setSessions]=useState<string[]>([]),[session,setSession]=useState("latest");
 const [kind,setKind]=useState<"industry"|"theme">("industry"),[page,setPage]=useState("market"),[query,setQuery]=useState(""),[stockQuery,setStockQuery]=useState("");
 const [selected,setSelected]=useState(""),[sort,setSort]=useState<SortKey>("score"),[descending,setDescending]=useState(true);
 const [min,setMin]=useState(3),[view,setView]=useState("table"),[stockSort,setStockSort]=useState("score"),[trend,setTrend]=useState(false),[all,setAll]=useState(false);
 const [dark,setDark]=useState(()=>matchMedia("(prefers-color-scheme: dark)").matches),[mobile,setMobile]=useState(false);
 const [status,setStatus]=useState(""),[error,setError]=useState(""),[loading,setLoading]=useState(true),[fallback,setFallback]=useState(false),[manual,setManual]=useState("");
 const [copied,setCopied]=useState(false),[refreshing,setRefreshing]=useState(false);
 const copyOrigin=useRef<HTMLElement|null>(null);
 useEffect(()=>{document.documentElement.dataset.theme=dark?"dark":"light"},[dark]);
 useEffect(()=>{document.querySelector("main")?.scrollTo({top:0})},[page,kind]);
 useEffect(()=>{if(!status)return;const t=setTimeout(()=>setStatus(""),6500);return()=>clearTimeout(t)},[status]);
 async function read(name:string,markFallback=false){
   const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);
   try{const r=await fetch(RAW+name+"?v="+Math.floor(Date.now()/60000),{signal:controller.signal});if(!r.ok)throw Error("Remote feed unavailable");const p=await r.json();if(markFallback)setFallback(false);return p}
   catch{const r=await fetch("./data/"+name+"?v="+Math.floor(Date.now()/60000));if(!r.ok)throw Error("No validated snapshot available yet. The first daily workflow may still be running.");if(markFallback)setFallback(true);return r.json()}
   finally{clearTimeout(timer)}
 }
 async function refresh(explicit=false){
   setRefreshing(true);setError("");
   try{const p:Snapshot=await read(session==="latest"?"latest.json":`history/${session}.json`,true);if(p.schema_version!==1||!Array.isArray(p.stocks)||!Array.isArray(p.groups))throw Error("Invalid snapshot format");setData(p);setLoading(false);if(explicit)setStatus("Published snapshot reloaded. This does not start GitHub Actions.");}
   catch(e){setError((e as Error).message);setLoading(false)}
   finally{setRefreshing(false)}
 }
 useEffect(()=>{refresh();read("sessions.json").then(setSessions).catch(()=>{});const t=setInterval(()=>{if(session==="latest")refresh()},300000);return()=>clearInterval(t)},[session]);
 const groups=useMemo(()=>{
   const q=query.toLowerCase();
   const gs=(data?.groups||[]).filter(g=>g.kind===kind&&g.count>=min&&(g.name.toLowerCase().includes(q)||g.members.some(s=>s.toLowerCase().includes(q)||(data?.stocks.find(r=>r.symbol===s)?.name.toLowerCase().includes(q)))));
   return gs.sort((a,b)=>{const x=value(a,sort),y=value(b,sort);if(x==null&&y==null)return a.name.localeCompare(b.name);if(x==null)return 1;if(y==null)return -1;return (descending?y-x:x-y)||a.name.localeCompare(b.name)});
 },[data,kind,min,query,sort,descending]);
 const active=groups.find(g=>g.id===selected)||groups[0];
 const members=useMemo(()=>{
   let rows=(data?.stocks||[]).filter(r=>active?.members.includes(r.symbol)&&(!trend||r.above50===100)&&(!stockQuery||`${r.symbol} ${r.name}`.toLowerCase().includes(stockQuery.toLowerCase())));
   rows.sort((a,b)=>{const x=a[stockSort as keyof Stock] as number|null,y=b[stockSort as keyof Stock] as number|null;return x==null?y==null?a.symbol.localeCompare(b.symbol):1:y==null?-1:y-x||a.symbol.localeCompare(b.symbol)});
   return all?rows:rows.slice(0,10);
 },[data,active,trend,stockQuery,stockSort,all]);
 const ranked=(data?.groups||[]).filter(g=>g.kind===kind&&g.rank!=null);
 const leader=[...ranked].sort((a,b)=>(b.score||0)-(a.score||0))[0];
 const chart=active?.spark.map((v,i)=>({i:i-63,group:v}))||[];
 async function copySymbols(rows:Stock[]){
   copyOrigin.current=document.activeElement as HTMLElement;
   const text=[...new Set(rows.map(s=>tv(s.symbol)))].join(",");
   if(!text){setStatus("No stocks match the current filters.");return}
   try{await navigator.clipboard.writeText(text);setCopied(true);setStatus(`${rows.length} TradingView symbols copied.`);setTimeout(()=>setCopied(false),2200)}
   catch{setManual(text);setStatus("Clipboard blocked. Select and copy the symbols below.")}
 }
 useEffect(()=>{const fn=(e:KeyboardEvent)=>{if(e.key==="Escape"){setManual("");setMobile(false)}};document.addEventListener("keydown",fn);return()=>document.removeEventListener("keydown",fn)},[]);
 useEffect(()=>{
  if(!manual)return;
  const trap=(e:KeyboardEvent)=>{
   if(e.key!=="Tab")return;
   const elements=Array.from(document.querySelectorAll<HTMLElement>('.copy-modal textarea,.copy-modal button'));
   const first=elements[0],last=elements[elements.length-1];
   if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
   else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
  };
  document.addEventListener("keydown",trap);
  return()=>{document.removeEventListener("keydown",trap);copyOrigin.current?.focus()};
 },[manual]);
 function selectGroup(g:Group){
   setSelected(g.id);setStockQuery("");
   if(matchMedia("(max-width:1380px)").matches)requestAnimationFrame(()=>document.querySelector(".detail-panel")?.scrollIntoView({block:"start",behavior:"smooth"}));
 }
 function changeKind(k:"industry"|"theme"){setKind(k);setSelected("");setQuery("");setStockQuery("");setPage("market");setMobile(false)}
 function sortBy(k:SortKey){if(sort===k)setDescending(!descending);else{setSort(k);setDescending(true)}}
 const sourceDate=data?.last_trading_date||"Awaiting EOD";
 return <div className="app">
  <a className="skip" href="#main">Skip to market data</a>
  <aside className={`sidebar ${mobile?"open":""}`}>
   <a className="brand" href="#main" aria-label="Theme Atlas home" onClick={()=>setPage("market")}><svg role="img" aria-label="Theme Atlas mark" viewBox="0 0 32 32"><path d="M4 26V15h5v11zm9 0V9h5v17zm9 0V3h5v23z" fill="currentColor"/></svg><span>THEME ATLAS<small>INDIAN EQUITY RESEARCH</small></span></a>
   <div className="nav-label">WORKSPACE</div>
   <nav aria-label="Main navigation">
    <button className={page==="market"&&kind==="industry"?"active":""} onClick={()=>changeKind("industry")}><Layers3 size={18}/>Industry groups<span>{data?.groups.filter(g=>g.kind==="industry").length||"·"}</span></button>
    <button className={page==="market"&&kind==="theme"?"active":""} onClick={()=>changeKind("theme")}><Grid2X2 size={18}/>India themes<span>{data?.groups.filter(g=>g.kind==="theme").length||"·"}</span></button>
    <button className={page==="method"?"active":""} onClick={()=>{setPage("method");setMobile(false)}}><Info size={18}/>Ranking methodology</button>
    <button className={page==="health"?"active":""} onClick={()=>{setPage("health");setMobile(false)}}><RefreshCw size={18}/>Data & automation</button>
   </nav>
   <section className="universe"><div className="nav-label">YOUR TRADABLE UNIVERSE</div><p><span>Market cap</span><b>&gt; ₹500 Cr</b></p><p><span>Avg volume · 20D</span><b>&gt; 70,000</b></p><p><span>Avg turnover · 20D</span><b>&gt; ₹3 Cr</b></p><p><span>Avg range · 20D</span><b>&gt; 3%</b></p><small>Strict thresholds. EOD observations.</small></section>
   <div className="sidebar-bottom"><div className="session-dot"/>Daily EOD · 19:30 IST<small>Benchmark: Nifty MidSmallcap 400</small><a href={REPO} target="_blank" rel="noreferrer">View GitHub repository <ArrowUpRight size={14}/></a></div>
  </aside>
  {mobile&&<button className="shade" aria-label="Close navigation" onClick={()=>setMobile(false)}/>}
  <div className="workspace">
   <header className="topbar"><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={()=>setMobile(!mobile)}><Menu size={20}/></button><div className="crumb">Research desk <ChevronRight size={14}/><b>{page==="market"?(kind==="industry"?"Industry leadership":"Theme leadership"):page==="method"?"Methodology":"Data health"}</b></div><div className="header-actions"><span className="session-tag"><span className="session-dot"/>EOD {sourceDate}</span><button className="icon-button" onClick={()=>setDark(!dark)} aria-label={dark?"Switch to light mode":"Switch to dark mode"}>{dark?<Sun size={18}/>:<Moon size={18}/>}</button><button className="icon-button" aria-label="Refresh published data" disabled={refreshing} onClick={()=>refresh(true)}><RefreshCw size={18} className={refreshing?"spin":""}/></button></div></header>
   <main id="main" tabIndex={-1}>
    {error&&<div className="notice warning" role="alert">{error} <button onClick={()=>refresh(true)}>Retry</button></div>}
    {(fallback||data?.mode.includes("bootstrap"))&&<div className="notice warning"><Info size={16}/>{data?.mode.includes("bootstrap")?"Dated bootstrap preview. The first independent EOD refresh is pending.":"Using the bundled dated snapshot; the live GitHub feed is unavailable."} Session: {sourceDate}.</div>}
    {session!=="latest"&&<div className="notice">Archived snapshot: {session}. Current classifications are not used to recompute this view.</div>}
    {loading?<section className="loading"><div className="skeleton"/><div className="skeleton"/><div className="skeleton"/><p>Loading the latest validated EOD snapshot…</p></section>:data&&page==="market"?<>
     <div className="page-heading"><div><div className="eyebrow">FOLLOW STRENGTH. FIND THE LEADERS.</div><h1>{kind==="industry"?"Industry group leadership":"India theme leadership"}</h1><p>{kind==="industry"?"Find strong industries, then screen their leading stocks.":"Track official theme baskets within your tradable universe."}</p></div><label className="session-select">Session<select aria-label="Select EOD session" value={session} onChange={e=>setSession(e.target.value)}><option value="latest">Latest completed EOD</option>{sessions.map(s=><option key={s} value={s}>{s}</option>)}</select></label></div>
     <section className="kpis" aria-label="Market summary">
      <article><span>ELIGIBLE STOCKS</span><strong>{data.stocks.length.toLocaleString("en-IN")}</strong><small>Across the filtered NSE universe</small></article>
      <article><span>RANKED {kind==="industry"?"INDUSTRIES":"THEMES"}</span><strong>{ranked.length}<em> / {data.groups.filter(g=>g.kind===kind).length}</em></strong><small>3+ members, sufficient 3M history</small></article>
      <article className="leader-kpi"><span>LEADING {kind==="industry"?"INDUSTRY":"THEME"}</span><strong>{leader?.name||"Not available"}</strong><small>Composite score {fmt(leader?.score)} / 100</small></article>
      <article><span>UNIVERSE ABOVE SMA50</span><strong>{fmt(data.stocks.filter(r=>r.above50===100).length/Math.max(data.stocks.filter(r=>r.above50!==null).length,1)*100,0)}<em>%</em></strong><small>Known-history stocks only</small></article>
     </section>
     <div className="market-strip"><span>RS reference <b>Nifty MidSmallcap 400</b></span><span>1W <b className={sign(data.benchmark_returns.w1)}>{pct(data.benchmark_returns.w1)}</b></span><span>1M <b className={sign(data.benchmark_returns.m1)}>{pct(data.benchmark_returns.m1)}</b></span><span>3M <b className={sign(data.benchmark_returns.m3)}>{pct(data.benchmark_returns.m3)}</b></span><span className="strip-note">Custom equal-weight baskets · not official index returns</span></div>
     <div className="research-grid">
      <section className="panel ranking-panel"><div className="panel-title"><div><h2>Leadership rankings</h2><p>{groups.length} shown · {groups.filter(g=>g.rank!==null).length} ranked · {groups.filter(g=>g.rank===null).length} limited</p></div><div className="segmented"><button aria-label="Table view" className={view==="table"?"on":""} onClick={()=>setView("table")}><List size={17}/></button><button aria-label="Heatmap view" className={view==="heatmap"?"on":""} onClick={()=>setView("heatmap")}><Grid2X2 size={17}/></button></div></div>
       <div className="filters"><label className="search"><Search size={16}/><input aria-label="Search groups or member stocks" placeholder="Search group or stock…" value={query} onChange={e=>setQuery(e.target.value)}/>{query&&<button className="clear" aria-label="Clear group search" onClick={()=>setQuery("")}><X size={14}/></button>}</label><label>Min stocks<select aria-label="Minimum stocks per group" value={min} onChange={e=>setMin(+e.target.value)}><option value={0}>All groups</option><option value={3}>3 stocks</option><option value={5}>5 stocks</option><option value={10}>10 stocks</option></select></label><label>Sort<select aria-label="Sort groups" value={sort} onChange={e=>{setSort(e.target.value as SortKey);setDescending(true)}}>{keys.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label><button className="icon-button" aria-label={descending?"Sort ascending":"Sort descending"} onClick={()=>setDescending(!descending)}>{descending?<ArrowDown size={16}/>:<ArrowUp size={16}/>}</button></div>
       {view==="table"&&groups.length>0&&<div className="table-navigation"><span>Select a group to see its leaders. Scroll for all columns.</span><button aria-label="Scroll group table left" onClick={()=>document.querySelector(".ranking-panel>.table-scroll")?.scrollBy({left:-300,behavior:"smooth"})}>←</button><button aria-label="Scroll group table right" onClick={()=>document.querySelector(".ranking-panel>.table-scroll")?.scrollBy({left:300,behavior:"smooth"})}>→</button></div>}
       {groups.length===0?<div className="empty"><Search size={24}/><h3>No groups match</h3><p>Try a broader search or fewer members.</p><button onClick={()=>{setQuery("");setMin(0)}}>Reset filters</button></div>:view==="heatmap"?<div className="heatmap">{groups.map(g=><button key={g.id} className={`heat-tile ${active?.id===g.id?"selected":""}`} onClick={()=>selectGroup(g)} style={{"--heat":g.score==null?"var(--subtle)":`color-mix(in srgb, var(--accent) ${Math.max(5,g.score*.32)}%, var(--surface))`} as React.CSSProperties}><span>#{g.rank??"—"} · {g.count} stocks</span><b>{g.name}</b><strong>{fmt(g.score)}</strong><small>1M <i className={sign(g.m1)}>{pct(g.m1)}</i> · SMA50 {fmt(g.above50,0)}%</small></button>)}</div>:<div className="table-scroll"><table className="group-table"><thead><tr><th>Rank</th><th className="name-col">Group / 3M path</th><th><button onClick={()=>sortBy("score")}>Score {sort==="score"?(descending?"↓":"↑"):""}</button></th><th><button onClick={()=>sortBy("w1")}>1W</button></th><th><button onClick={()=>sortBy("m1")}>1M</button></th><th><button onClick={()=>sortBy("m3")}>3M</button></th><th><button onClick={()=>sortBy("above50")}>Breadth</button></th><th>Stocks</th></tr></thead><tbody>{groups.map(g=><tr key={g.id} className={active?.id===g.id?"selected":""} onClick={()=>selectGroup(g)}><td><span className={`rank ${g.rank&&g.rank<=3?"top":""}`}>{g.rank??"—"}</span>{g.rank_change!=null&&g.rank_change!==0&&<small className={sign(g.rank_change)}>{g.rank_change>0?"↑":"↓"}{Math.abs(g.rank_change)}</small>}</td><td><button className="group-name" onClick={e=>{e.stopPropagation();selectGroup(g)}}>{g.name}<small>{g.status}</small></button><Spark data={g.spark}/></td><td><b>{fmt(g.score)}</b><div className="score-track"><span style={{width:`${g.score||0}%`}}/></div></td><td className={sign(g.w1)}>{pct(g.w1)}</td><td className={sign(g.m1)}>{pct(g.m1)}</td><td className={sign(g.m3)}>{pct(g.m3)}</td><td>{g.above50==null?"N/A":fmt(g.above50,0)+"%"}<small>above SMA50</small></td><td>{g.count}</td></tr>)}</tbody></table></div>}
       <div className="panel-foot"><span>Scores are research composites, not buy signals.</span><button onClick={()=>exportCSV(groups.map(g=>({group:g.name,rank:g.rank,score:g.score,stocks:g.count,return_1d:g.d1,return_1w:g.w1,return_1m:g.m1,return_3m:g.m3,rs_excess_3m:g.rs_excess,above_sma50_pct:g.above50,rank_change:g.rank_change})),`theme-atlas-${kind}-${sourceDate}.csv`)}><Download size={14}/>Export groups</button></div>
      </section>
      <aside className="panel detail-panel" aria-label="Selected group leaders">{active?<><div className="detail-header"><span className="eyebrow">{kind==="industry"?"INDUSTRY GROUP":"OFFICIAL THEME BASKET"}</span><h2>{active.name}</h2><div className="detail-meta"><span className="badge">{active.status}</span><span>{active.count} eligible stocks</span><span>Rank {active.rank??"unavailable"}</span></div></div>
       <div className="detail-stats"><div><small>Leadership</small><strong>{fmt(active.score)}<em> /100</em></strong></div><div><small>3M RS excess</small><strong className={sign(active.rs_excess)}>{active.rs_excess==null?"N/A":`${active.rs_excess>=0?"+":""}${fmt(active.rs_excess)}`}<em> pp</em></strong></div><div><small>Above SMA50</small><strong>{fmt(active.above50,0)}<em>%</em></strong></div></div>
       <div className="detail-chart"><div><b>Current basket · 3M path</b><small>Normalized to 100 · 64-bar members only</small></div>{chart.length?<ResponsiveContainer width="100%" height={130}><LineChart data={chart} margin={{left:-24,right:8,top:12,bottom:0}}><CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="i" tick={{fill:"var(--muted)",fontSize:12}} tickLine={false} axisLine={false} minTickGap={45}/><YAxis domain={["auto","auto"]} tick={{fill:"var(--muted)",fontSize:12}} tickLine={false} axisLine={false}/><Tooltip contentStyle={{background:"var(--surface)",border:"1px solid var(--border)",fontSize:12}} labelFormatter={v=>`${Math.abs(Number(v))} sessions ago`}/><Line dataKey="group" name="Current basket" type="monotone" stroke="var(--accent)" strokeWidth={2} dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer>:<p className="muted">Insufficient common 3M history.</p>}</div>
       <div className="stock-heading"><h3>{all?"Group stocks":"Top 10 leaders"}</h3><button className="copy-button" onClick={()=>copySymbols(members)} disabled={!members.length}>{copied?<Check size={15}/>:<Copy size={15}/>}Copy {all?"shown":"top 10"}</button></div>
       <div className="stock-tools"><label className="search"><Search size={14}/><input placeholder="Find a stock…" aria-label="Search group stocks" value={stockQuery} onChange={e=>setStockQuery(e.target.value)}/></label><select aria-label="Sort group stocks" value={stockSort} onChange={e=>setStockSort(e.target.value)}><option value="score">Leader score</option><option value="m1">1M return</option><option value="m3">3M return</option><option value="rvol">RVOL</option><option value="d1">Daily move</option></select></div>
       <div className="stock-checks"><label><input type="checkbox" checked={trend} onChange={e=>setTrend(e.target.checked)}/>Above SMA50 only</label><label><input type="checkbox" checked={all} onChange={e=>setAll(e.target.checked)}/>Show all</label></div>
       <div className="table-scroll"><table className="stock-table"><thead><tr><th>Stock</th><th>Score</th><th>1M</th><th>RVOL</th><th aria-label="Chart"/></tr></thead><tbody>{members.map((r,i)=><tr key={r.symbol}><td><a href={link(r.symbol)} target="_blank" rel="noreferrer">{i+1}. {r.symbol}</a><small title={r.name}>{r.name}</small></td><td>{fmt(r.score,0)}</td><td className={sign(r.m1)}>{pct(r.m1)}</td><td>{fmt(r.rvol)}×</td><td><a className="icon-button" href={link(r.symbol)} target="_blank" rel="noreferrer" aria-label={`Open ${r.symbol} chart`}><ArrowUpRight size={15}/></a></td></tr>)}</tbody></table></div>
       {!members.length&&<div className="empty"><p>No stocks pass these filters.</p><button onClick={()=>{setTrend(false);setStockQuery("")}}>Reset stock filters</button></div>}
       <div className="stock-footer"><span>{members.length} shown of {active.count} eligible</span><button onClick={()=>exportCSV(members.map(r=>({symbol:r.symbol,name:r.name,score:r.score,industry:r.industry,close:r.close,market_cap_cr:r.market_cap_cr,return_1d:r.d1,return_1w:r.w1,return_1m:r.m1,return_3m:r.m3,rvol:r.rvol,rs_excess_3m:r.rs_excess,avg_volume_20d:r.avg_vol_20d,avg_turnover_cr_20d:r.avg_rvol_20d_cr,adr20:r.avg_range_pct_20d})),`theme-atlas-${active.name.replaceAll(/[^a-z0-9]/gi,"-")}-${sourceDate}.csv`)}><Download size={14}/>CSV</button></div>
       <div className="detail-note"><Info size={14}/><span>Missing history is N/A, never zero. {active.count<10?"Fewer than 10 stocks qualify; the list is not padded.":"Stock leaders are ranked within your eligible universe."}{active.kind==="theme"&&<> <a href={active.source_url} target="_blank" rel="noreferrer">Membership CSV</a> · verified {active.mapping_date}.</>}</span></div>
      </>:<div className="empty"><h2>Select a group</h2><p>Reset filters to explore its stock leaders.</p></div>}</aside>
     </div>
    </>:data&&page==="method"?<section className="prose"><div className="eyebrow">TRANSPARENT BY DESIGN</div><h1>How leadership is measured</h1><p>This is a custom swing-trading research framework, not an IBD proprietary rating or an official Nifty index.</p><h2>Group leadership · 0 to 100</h2><div className="formula"><b>55%</b> momentum + <b>25%</b> relative strength + <b>20%</b> breadth</div><ul><li>Momentum: 20% of the 1W percentile, 35% of the 1M percentile and 45% of the 3M percentile.</li><li>Relative strength: percentile of mean member 3M return excess over Nifty MidSmallcap 400.</li><li>Breadth: actual percentage of known-history members closing above SMA50.</li><li>Industry groups and themes are scored separately. All percentiles use average ranks for ties.</li></ul><h2>Top stock leadership · 0 to 100</h2><div className="formula">20% 1W + 30% 1M + 30% 3M + 20% RS excess</div><p>Each component is a percentile across the entire eligible stock universe, before selecting a group. Select an industry or theme to screen up to ten leaders; alternative sort options change the displayed leaders.</p><h2>Industry groups and themes</h2><p>Industry labels come from a versioned finance-provider classification map. Missing names use explicitly labelled Yahoo Finance industry metadata; these are not official NSE four-tier industry codes. The map is a current classification, not historical membership.</p><p>Themes use official Nifty constituent lists. Only constituents passing your four universe filters enter each basket. Index membership is not a complete census of businesses exposed to a theme, and a stock can appear in several themes.</p><p><a href="https://www.nseindia.com/static/products-services/industry-classification" target="_blank" rel="noreferrer">NSE classification framework</a> · <a href="https://www.niftyindices.com/Methodology/Method_Nifty_Thematic_Indices.pdf" target="_blank" rel="noreferrer">Official thematic methodology</a></p><h2>Returns, sample sizes and limitations</h2><ul>{data.notes.map(n=><li key={n}>{n}</li>)}</ul><h2>Status labels</h2><p>Leading: group RS-excess percentile ≥50 and positive 1M return. Improving: other ranked groups with positive 1W return. Lagging: remaining ranked groups. Limited sample: fewer than three eligible members, fewer than three 3M observations, or less than 70% 3M coverage.</p><p>Primary industry metadata is versioned and requires periodic review; daily refresh enriches missing symbols. No automatic narrative, revenue exposure or catalyst verification is implied.</p></section>:data&&page==="health"?<section className="prose"><div className="eyebrow">INDEPENDENT PIPELINE</div><h1>Data & daily automation</h1><p>Daily refresh is scheduled for 19:30 Asia/Kolkata, equivalent to 14:00 UTC. GitHub scheduled workflows can start late, and non-trading days retain the last verified completed session.</p><div className="health-links"><a className="primary" href={REPO+"/actions/workflows/daily-update.yml"} target="_blank" rel="noreferrer">Open daily workflow <ArrowUpRight size={16}/></a><a href={REPO} target="_blank" rel="noreferrer">Repository</a></div><h2>Snapshot</h2><dl className="health-grid"><dt>EOD session</dt><dd>{data.last_trading_date}</dd><dt>Generated</dt><dd>{data.generated_at}</dd><dt>Acquisition mode</dt><dd>{data.mode}</dd><dt>Feed</dt><dd>{fallback?"Bundled dated fallback":"Live public GitHub snapshot"}</dd><dt>Benchmark</dt><dd>{data.benchmark}</dd><dt>Industry coverage</dt><dd>{String(data.classification_health.coverage_pct)}%</dd><dt>Official themes available</dt><dd>{String(data.classification_health.official_themes_available)} / {String(data.classification_health.configured_themes)}</dd><dt>Industry maintenance</dt><dd>{String(data.classification_health.industry_maintenance)}</dd></dl><h2>Market coverage</h2><dl className="health-grid">{Object.entries(data.market_data).filter(([k])=>!k.endsWith("_symbols")).map(([k,v])=><div className="health-row" key={k}><dt>{k.replaceAll("_"," ")}</dt><dd>{typeof v==="object"?JSON.stringify(v):String(v)}</dd></div>)}</dl><h2>Missing or excluded classifications</h2><p>Unclassified: {(data.classification_health.unclassified as string[])?.join(", ")||"None"}. Unavailable themes: {(data.classification_health.unavailable_themes as string[])?.join(", ")||"None"}.</p><h2>Safeguards</h2><p>The workflow verifies exchange dates, official NSE closing bars, price-history coverage, shares coverage and classification coverage before replacing the last good snapshot. A failed acquisition does not overwrite published data.</p><p>No daily workflow reads another dashboard’s live feed. Source modules are reused, but acquisition, caches, classification and output are maintained in this repository.</p><p>GitHub may disable scheduled workflows in inactive public repositories after 60 days without repository activity. Review the Actions page if daily timestamps stop advancing.</p></section>:null}
    <footer className="footer"><span>THEME ATLAS · India market research</span><span>EOD only. Not investment advice.</span><span>Built with Perplexity Computer</span></footer>
   </main>
  </div>
  {status&&<div className="toast" role="status">{status}<button aria-label="Dismiss status" onClick={()=>setStatus("")}><X size={14}/></button></div>}
  {manual&&<div className="modal-backdrop" onClick={()=>setManual("")}><section className="copy-modal" role="dialog" aria-modal="true" aria-labelledby="copy-title" onClick={e=>e.stopPropagation()}><h2 id="copy-title">Copy TradingView symbols</h2><p>Your browser blocked automatic copying. Select all the text and copy it manually.</p><textarea aria-label="TradingView symbol list" value={manual} readOnly autoFocus onFocus={e=>e.target.select()}/><button onClick={()=>setManual("")}>Close</button></section></div>}
 </div>
}
