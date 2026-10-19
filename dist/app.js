const IND = {
  ED: 'ED presentations',
  ADM: 'Hospital admissions',
  WAIT: 'Median ED waiting time (minutes)',
  ASTHMA: 'Asthma hospitalisation rate (age-standardised, per 100,000)',
  SMOKE: 'Smoking prevalence'
};
const COUNTS = new Set([IND.ED, IND.ADM]);
const els = Object.fromEntries([...document.querySelectorAll('[id]')].map(el => [el.id, el]));
const [data, geo] = await Promise.all([fetch('data/health-data.json').then(r=>r.json()), fetch('data/nsw-lhds.geojson').then(r=>r.json())]);
const years = [...new Set(data.map(d=>d.year))].sort((a,b)=>+a.slice(0,4)-+b.slice(0,4));
const lhds = [...new Set(data.map(d=>d.LHD))].sort();
const indicators = [...new Set(data.map(d=>d.indicator))].sort();
const state = {year:'All',lhd:'All',indicator:IND.ED};

function fillSelect(el, values, first='All') { const options=first===''?values:[first,...values];el.innerHTML=options.map(v=>`<option>${v}</option>`).join(''); }
fillSelect(els.yearFilter,[...years].reverse()); fillSelect(els.lhdFilter,lhds); fillSelect(els.indicatorFilter,indicators,''); els.indicatorFilter.value=state.indicator;
const aggregate = (rows, indicator) => { const vals=rows.filter(d=>d.indicator===indicator).map(d=>d.value); return vals.length?(COUNTS.has(indicator)?vals.reduce((a,b)=>a+b,0):vals.reduce((a,b)=>a+b,0)/vals.length):null; };
const latestYear = (indicator,lhd=state.lhd) => { const yy=data.filter(d=>d.indicator===indicator&&(lhd==='All'||d.LHD===lhd)).map(d=>d.year).sort((a,b)=>+a.slice(0,4)-+b.slice(0,4)); return yy.at(-1); };
const effectiveYear = indicator => state.year!=='All'&&data.some(d=>d.year===state.year&&d.indicator===indicator&&(state.lhd==='All'||d.LHD===state.lhd))?state.year:latestYear(indicator);
const rowsFor=(indicator,{year=effectiveYear(indicator),lhd=state.lhd}={})=>data.filter(d=>d.indicator===indicator&&(year==='All'||d.year===year)&&(lhd==='All'||d.LHD===lhd));
const format=(v,ind,compact=false)=>v==null?'N/A':COUNTS.has(ind)?Intl.NumberFormat('en-AU',{notation:compact?'compact':'standard',maximumFractionDigits:0}).format(v):`${v.toFixed(1)}${ind===IND.WAIT?' min':ind===IND.ASTHMA?' /100k':ind===IND.SMOKE||ind==='%'?'%':''}`;
const short={ [IND.ED]:'ED presentations',[IND.ADM]:'Hospital admissions',[IND.WAIT]:'Avg. ED wait',[IND.ASTHMA]:'Asthma rate',[IND.SMOKE]:'Smoking prevalence' };

function renderKPIs(){
  const icons=['↗','✚','◷','≈','○'];
  els.kpiGrid.innerHTML=[IND.ED,IND.ADM,IND.WAIT,IND.ASTHMA,IND.SMOKE].map((ind,i)=>{const y=effectiveYear(ind),v=aggregate(rowsFor(ind,{year:y}),ind);return `<div class="kpi-card" style="--tint:${['#e5f2ee','#e8eff5','#fff0e9','#eceafa','#f1f2dd'][i]}"><div class="kpi-icon">${icons[i]}</div><div class="kpi-label">${short[ind]}</div><div class="kpi-value">${format(v,ind,true)}</div><div class="kpi-year">${y||'No reporting year'}</div></div>`}).join('');
}

const map=L.map('map',{zoomControl:false,scrollWheelZoom:false}).setView([-32.8,147],5); L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  attribution:'© OpenStreetMap contributors',
  subdomains:'abc',
  maxZoom:19
}).addTo(map);
let geoLayer;
function colorScale(v,min,max){const t=max===min?.5:(v-min)/(max-min); const a=[222,240,234],b=[15,111,105];return `rgb(${a.map((x,i)=>Math.round(x+(b[i]-x)*t)).join(',')})`;}
function renderMap(){
  if(geoLayer) geoLayer.remove(); const y=effectiveYear(state.indicator); const rows=rowsFor(state.indicator,{year:y,lhd:'All'}); const vals=rows.map(d=>d.value), min=Math.min(...vals),max=Math.max(...vals); const lookup=new Map(rows.map(d=>[`${d.LHD} Local Health District`,d.value]));
  geoLayer=L.geoJSON(geo,{style:f=>{const v=lookup.get(f.properties.lhd_name);return {fillColor:v==null?'#dfe5e2':colorScale(v,min,max),weight:state.lhd!=='All'&&f.properties.lhd_name===`${state.lhd} Local Health District`?3:1,color:'#fff',fillOpacity:.88};},onEachFeature:(f,l)=>{const name=f.properties.lhd_name.replace(' Local Health District',''),v=lookup.get(f.properties.lhd_name);l.bindTooltip(`<strong>${name}</strong><br>${short[state.indicator]}: ${format(v,state.indicator)}`,{sticky:true});l.on('click',()=>{state.lhd=name;els.lhdFilter.value=name;renderAll();});}}).addTo(map);
  if(state.lhd!=='All'){
    const feature=geoLayer.getLayers().find(l=>l.feature.properties.lhd_name===`${state.lhd} Local Health District`);
    if(feature) map.fitBounds(feature.getBounds(),{padding:[25,25],maxZoom:8});
  } else {
    map.fitBounds(geoLayer.getBounds(),{padding:[28,28],maxZoom:6});
  }
  els.legend.innerHTML=`<span>${format(min,state.indicator,true)}</span><span class="legend-ramp"></span><span>${format(max,state.indicator,true)}</span>`;
  els.mapCaption.textContent=`${short[state.indicator]} · ${y}${state.year!=='All'&&y!==state.year?` (latest available; ${state.year} has no matching data)`:''}`;
}

function positionTooltip(e){const box=els.tooltip.getBoundingClientRect(),left=Math.min(e.clientX+12,innerWidth-box.width-10),top=Math.min(e.clientY+12,innerHeight-box.height-10);els.tooltip.style.left=`${Math.max(10,left)}px`;els.tooltip.style.top=`${Math.max(10,top)}px`;}
function tooltip(e,html){els.tooltip.innerHTML=html;els.tooltip.style.display='block';positionTooltip(e);}
document.addEventListener('mousemove',e=>{if(els.tooltip.style.display==='block')positionTooltip(e);});
document.addEventListener('mouseover',e=>{const t=e.target.closest('[data-tip]');if(t)tooltip(e,t.dataset.tip)});document.addEventListener('mouseout',e=>{if(e.target.closest('[data-tip]'))els.tooltip.style.display='none'});

function group(ind,year='All'){const m=new Map();data.filter(d=>d.indicator===ind&&(year==='All'||d.year===year)).forEach(d=>{const k=d.LHD;m.set(k,[...(m.get(k)||[]),d.value])});return [...m].map(([LHD,vs])=>({LHD,value:COUNTS.has(ind)?vs.reduce((a,b)=>a+b,0):vs.reduce((a,b)=>a+b,0)/vs.length}));}
function bars(el,rows,labelKey='LHD',valueKey='value',indicator=state.indicator,negative=false){if(!rows.length){el.innerHTML='<div class="empty">No matching data available</div>';return;}const max=Math.max(...rows.map(r=>Math.abs(r[valueKey])));el.innerHTML=rows.map(r=>`<div class="bar-col"><span class="bar-value">${format(r[valueKey],indicator,true)}</span><div class="bar ${negative&&r[valueKey]<0?'negative':''}" style="height:${Math.max(3,Math.abs(r[valueKey])/max*235)}px" data-tip="<strong>${r[labelKey]}</strong><br>${format(r[valueKey],indicator)}"></div><span class="bar-label">${r[labelKey]}</span></div>`).join('');}
function renderRegional(){const y=effectiveYear(state.indicator),rows=group(state.indicator,y).sort((a,b)=>b.value-a.value);bars(els.rankingChart,rows);els.regionalSubtitle.textContent=`${short[state.indicator]} across NSW in ${y}.`;els.rankingExplanation.textContent=COUNTS.has(state.indicator)?`Ranks districts by the reported ${short[state.indicator].toLowerCase()} count in ${y}; taller bars represent more reported activity.`:`Ranks districts by their recorded ${short[state.indicator].toLowerCase()} in ${y}; taller bars represent higher values.`;const matrix=groupHeat();renderHeatmap(matrix);}
function groupHeat(){return lhds.map(lhd=>({lhd,values:years.map(year=>{const r=data.filter(d=>d.LHD===lhd&&d.year===year&&d.indicator===state.indicator);return aggregate(r,state.indicator)})}));}
function renderHeatmap(matrix){const vals=matrix.flatMap(r=>r.values).filter(v=>v!=null),min=Math.min(...vals),max=Math.max(...vals);els.heatmap.style.gridTemplateColumns=`150px repeat(${years.length},minmax(54px,1fr))`;els.heatmap.innerHTML=`<div></div>${years.map(y=>`<div class="heat-year">${y}</div>`).join('')}`+matrix.map(r=>`<div class="heat-label">${r.lhd}</div>${r.values.map((v,i)=>`<div class="heat-cell ${v==null?'missing':''}" style="background:${v==null?'#edf1ee':colorScale(v,min,max)}" ${v==null?'':`data-tip="<strong>${r.lhd}</strong><br>${years[i]} · ${format(v,state.indicator)}"`}>${v==null?'—':''}</div>`).join('')}`).join('');}

function svgLine(el,rows,indicator){if(!rows.length){el.innerHTML='<div class="empty">No matching trend data</div>';return;}const W=900,H=330,p={l:55,r:20,t:20,b:45},vals=rows.map(r=>r.value),min=Math.min(...vals)*.95,max=Math.max(...vals)*1.05,x=i=>p.l+i*(W-p.l-p.r)/Math.max(1,rows.length-1),y=v=>p.t+(max-v)*(H-p.t-p.b)/(max-min||1),pts=rows.map((r,i)=>`${x(i)},${y(r.value)}`).join(' ');el.innerHTML=`<svg class="chart-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><defs><linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#55b8a9" stop-opacity=".28"/><stop offset="1" stop-color="#55b8a9" stop-opacity="0"/></linearGradient></defs>${[0,.25,.5,.75,1].map(t=>`<line class="grid-line" x1="${p.l}" x2="${W-p.r}" y1="${p.t+t*(H-p.t-p.b)}" y2="${p.t+t*(H-p.t-p.b)}"/>`).join('')}<polygon class="trend-area" points="${p.l},${H-p.b} ${pts} ${W-p.r},${H-p.b}"/><polyline class="trend-line" points="${pts}"/>${rows.map((r,i)=>`<circle class="dot" cx="${x(i)}" cy="${y(r.value)}" r="5" data-tip="<strong>${r.year}</strong><br>${format(r.value,indicator)}"/><text class="axis-text" x="${x(i)}" y="${H-18}" text-anchor="middle">${r.year}</text>`).join('')}</svg>`;}
function signedBars(el,rows){if(!rows.length){el.innerHTML='<div class="empty">No consecutive-year comparison is available for these filters.</div>';return;}const max=Math.max(...rows.map(r=>Math.abs(r.value)),1);el.innerHTML=rows.map(r=>{const h=Math.max(3,Math.abs(r.value)/max*118),dir=r.value>=0?'up':'down';return `<div class="signed-col"><span class="signed-value ${dir}" style="--h:${h}px">${format(r.value,'%')}</span><div class="signed-bar ${dir}" style="height:${h}px" data-tip="<strong>${r.LHD}</strong><br>${r.previousYear} to ${r.year}<br>${format(r.value,'%')}"></div><span class="signed-label">${r.LHD}</span></div>`}).join('');}
function renderTrends(){
  const grouped=years.map(year=>({year,value:aggregate(rowsFor(state.indicator,{year,lhd:state.lhd}),state.indicator)})).filter(r=>r.value!=null);
  svgLine(els.trendChart,grouped,state.indicator);
  els.trendScope.textContent=state.lhd==='All'?'All NSW districts':state.lhd;
  els.trendSubtitle.textContent=`${short[state.indicator]} through every available reporting period.`;
  els.trendExplanation.textContent=COUNTS.has(state.indicator)&&state.lhd==='All'?`The line sums reported ${short[state.indicator].toLowerCase()} across all districts for each year.`:state.lhd==='All'?`The line shows the unweighted average ${short[state.indicator].toLowerCase()} across districts for each year.`:`The line shows the recorded ${short[state.indicator].toLowerCase()} for ${state.lhd}.`;
  const changes=[];
  lhds.forEach(lhd=>{const r=years.map(year=>({year,value:aggregate(rowsFor(state.indicator,{year,lhd}),state.indicator)})).filter(x=>x.value!=null);for(let i=1;i<r.length;i++){if(+r[i].year.slice(0,4)-+r[i-1].year.slice(0,4)===1&&r[i-1].value!==0)changes.push({LHD:lhd,value:(r[i].value-r[i-1].value)/r[i-1].value*100,year:r[i].year,previousYear:r[i-1].year});}});
  const validYears=[...new Set(changes.map(x=>x.year))].sort((a,b)=>+a.slice(0,4)-+b.slice(0,4));
  const comparisonYear=state.year==='All'?validYears.at(-1):state.year;
  let shown=changes.filter(c=>c.year===comparisonYear);
  if(state.lhd!=='All')shown=shown.filter(c=>c.LHD===state.lhd);
  signedBars(els.yoyChart,shown.sort((a,b)=>b.value-a.value));
  els.yoyPeriod.textContent=shown.length?`${shown[0].previousYear} → ${comparisonYear}`:`No comparison for ${comparisonYear}`;
}

function scatter(el,xInd,yInd){
  const commonYears=years.filter(year=>data.some(d=>d.year===year&&d.indicator===xInd)&&data.some(d=>d.year===year&&d.indicator===yInd));
  const requestedYear=state.year==='All'?'All':commonYears.includes(state.year)?state.year:commonYears.at(-1);
  const joined=[];
  data.filter(d=>d.indicator===xInd).forEach(x=>{if(requestedYear!=='All'&&x.year!==requestedYear)return;if(state.lhd!=='All'&&x.LHD!==state.lhd)return;const y=data.find(d=>d.indicator===yInd&&d.year===x.year&&d.LHD===x.LHD);if(y)joined.push({x:x.value,y:y.value,LHD:x.LHD,year:x.year});});
  if(!joined.length){el.innerHTML='<div class="empty">No matching records</div>';return {label:'No common period'};}
  const W=600,H=350,p={l:66,r:18,t:18,b:58},xmin=Math.min(...joined.map(d=>d.x))*.95,xmax=Math.max(...joined.map(d=>d.x))*1.05,ymin=Math.min(...joined.map(d=>d.y))*.95,ymax=Math.max(...joined.map(d=>d.y))*1.05,xf=v=>p.l+(v-xmin)/(xmax-xmin||1)*(W-p.l-p.r),yf=v=>H-p.b-(v-ymin)/(ymax-ymin||1)*(H-p.t-p.b),ticks=[0,.25,.5,.75,1];
  el.innerHTML=`<svg class="chart-svg" viewBox="0 0 ${W} ${H}">${ticks.map(t=>{const gy=p.t+t*(H-p.t-p.b),v=ymax-t*(ymax-ymin);return `<line class="grid-line" x1="${p.l}" x2="${W-p.r}" y1="${gy}" y2="${gy}"/><text class="axis-text" x="${p.l-8}" y="${gy+3}" text-anchor="end">${format(v,yInd,true)}</text>`}).join('')}${ticks.map(t=>{const gx=p.l+t*(W-p.l-p.r),v=xmin+t*(xmax-xmin);return `<text class="axis-text" x="${gx}" y="${H-p.b+18}" text-anchor="middle">${format(v,xInd,true)}</text>`}).join('')}<text class="axis-title" x="${(p.l+W-p.r)/2}" y="${H-8}" text-anchor="middle">${short[xInd]}</text><text class="axis-title" transform="translate(14 ${(p.t+H-p.b)/2}) rotate(-90)" text-anchor="middle">${short[yInd]}</text>${joined.map(d=>`<circle class="scatter-dot" cx="${xf(d.x)}" cy="${yf(d.y)}" r="6" data-tip="<strong>${d.LHD}</strong> · ${d.year}<br>${short[xInd]}: ${format(d.x,xInd)}<br>${short[yInd]}: ${format(d.y,yInd)}"/>`).join('')}</svg>`;
  return {label:requestedYear==='All'?`${commonYears[0]}–${commonYears.at(-1)}`:`${requestedYear}${state.year!==requestedYear?' · latest common':''}`};
}
function pairedBars(el,rows){if(!rows.length){el.innerHTML='<div class="empty">No matching records</div>';return;}const max=Math.max(...rows.flatMap(r=>[r.ed,r.adm]));el.innerHTML=rows.map(r=>`<div class="pair-col"><div class="pair-bar ed" style="height:${Math.max(3,r.ed/max*250)}px" data-tip="<strong>${r.LHD}</strong><br>ED presentations: ${format(r.ed,IND.ED)}"></div><div class="pair-bar adm" style="height:${Math.max(3,r.adm/max*250)}px" data-tip="<strong>${r.LHD}</strong><br>Hospital admissions: ${format(r.adm,IND.ADM)}"></div><span class="pair-label">${r.LHD}</span></div>`).join('');}
function renderRelationships(){
  const sa=scatter(els.smokingAsthma,IND.SMOKE,IND.ASTHMA);els.smokingAsthmaPeriod.textContent=sa.label;
  const ew=scatter(els.edWaiting,IND.ED,IND.WAIT);els.edWaitingPeriod.textContent=ew.label;
  const shared=years.filter(y=>data.some(d=>d.year===y&&d.indicator===IND.ED)&&data.some(d=>d.year===y&&d.indicator===IND.ADM));
  const y=state.year!=='All'&&shared.includes(state.year)?state.year:shared.at(-1);
  const rows=lhds.flatMap(lhd=>{const ed=aggregate(rowsFor(IND.ED,{year:y,lhd}),IND.ED),adm=aggregate(rowsFor(IND.ADM,{year:y,lhd}),IND.ADM);return ed!=null&&adm!=null?[{LHD:lhd,ed,adm}]:[];});
  pairedBars(els.edAdmissions,state.lhd==='All'?rows:rows.filter(r=>r.LHD===state.lhd));
  els.comparisonYear.textContent=`${y}${state.year!==y?' · latest common':''}`;
}

function renderAll(){els.heroYear.textContent=state.year==='All'?'Latest available':state.year;renderKPIs();renderMap();renderRegional();renderTrends();renderRelationships();els.updatedStamp.textContent=`${data.length.toLocaleString()} observations`;}
[els.yearFilter,els.lhdFilter,els.indicatorFilter].forEach(el=>el.addEventListener('change',()=>{state.year=els.yearFilter.value;state.lhd=els.lhdFilter.value;state.indicator=els.indicatorFilter.value;renderAll()}));
els.resetFilters.addEventListener('click',()=>{Object.assign(state,{year:'All',lhd:'All',indicator:IND.ED});els.yearFilter.value='All';els.lhdFilter.value='All';els.indicatorFilter.value=IND.ED;renderAll()});
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{document.querySelectorAll('.tab,.view').forEach(x=>x.classList.remove('active'));tab.classList.add('active');document.getElementById(tab.dataset.tab).classList.add('active');if(tab.dataset.tab==='overview')setTimeout(()=>map.invalidateSize(),50)}));
els.menuBtn.addEventListener('click',()=>{const open=document.querySelector('.sidebar').classList.toggle('open');els.menuBtn.setAttribute('aria-expanded',String(open));});document.addEventListener('click',e=>{if(innerWidth<780&&!e.target.closest('.sidebar')&&!e.target.closest('#menuBtn')){document.querySelector('.sidebar').classList.remove('open');els.menuBtn.setAttribute('aria-expanded','false');}});
renderAll();
