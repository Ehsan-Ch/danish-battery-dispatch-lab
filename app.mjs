import {labels,scaleTotals,intervalCash,cumulative,csv} from './core.mjs';
const $=id=>document.getElementById(id),fmt=(n,d=0)=>new Intl.NumberFormat('en-GB',{maximumFractionDigits:d,minimumFractionDigits:d}).format(n),money=n=>`${n<0?'−':''}€${fmt(Math.abs(n),0)}`;
let report,currentDay;
function lineChart(id,series,{min,max,ticks,unit='',bars=false}={}){
  const el=$(id),[, ,W,H]=el.getAttribute('viewBox').split(' ').map(Number);
  const left=48,right=15,top=14,bottom=28,w=W-left-right,h=H-top-bottom;
  const values=series.flatMap(s=>s.values),n=Math.max(...series.map(s=>s.values.length));
  min=min??Math.min(0,...values);max=max??Math.max(0,...values);if(max-min<1e-9)max=min+1;
  const x=i=>left+i*w/(n-1||1),y=v=>top+(max-v)*h/(max-min),esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;');
  let svg=`<title>${esc(el.getAttribute('aria-label'))}</title>`;
  for(let i=0;i<=4;i++){const value=min+(max-min)*i/4,Y=y(value);svg+=`<line x1="${left}" x2="${W-right}" y1="${Y}" y2="${Y}" stroke="#e0e4d8"/><text x="${left-8}" y="${Y+4}" text-anchor="end" fill="#687064" font-size="11">${fmt(value,Math.abs(max-min)<5?1:0)}</text>`;}
  if(unit)svg+=`<text x="${left}" y="10" fill="#687064" font-size="9">${esc(unit)}</text>`;
  for(const s of series){
    if(bars){const bw=w/n;svg+=s.values.map((v,i)=>`<rect x="${left+i*bw}" y="${Math.min(y(0),y(v))}" width="${Math.max(.5,bw-1)}" height="${Math.abs(y(v)-y(0))}" fill="${s.color}"/>`).join('');}
    else{svg+=`<polyline fill="none" stroke="${s.color}" stroke-width="${s.width||2.5}" ${s.dash?'stroke-dasharray="6 4"':''} points="${s.values.map((v,i)=>`${x(i)},${y(v)}`).join(' ')}"/>`;}
  }
  for(const t of ticks||[])svg+=`<text x="${x(t.index)}" y="${H-6}" text-anchor="middle" fill="#687064" font-size="11">${esc(t.label)}</text>`;
  el.innerHTML=svg;
}
function render(){
  const area=$('area').value,policy=$('policy').value,scale=Number($('scale').value),days=report.days.filter(d=>d.area===area);
  const day=days.find(d=>d.day===$('day').value)||days[0];currentDay=day;
  const s=day.policies[policy],totals=scaleTotals(s.totals,scale),all=report.summary[area],chosen=all[policy];
  $('context').textContent=`Decision: ${day.issue.slice(0,10)} at 10:00 Europe/Copenhagen · ${policy==='hindsight'?'HINDSIGHT ONLY: actual delivery prices used for optimization':policy==='idle'?'No charging or discharging':`Planning input: ${policy==='weekly'?'weekly seasonal':report.selected_models[area]} forecast`} · ${scale} MW / ${2*scale} MWh`;
  $('net').textContent=money(chosen.net*scale);$('difference').textContent=money((chosen.net-all.weekly.net)*scale);
  $('loss').textContent=fmt(chosen.loss_mwh*scale,1)+' MWh';$('cycles').textContent=fmt(chosen.cycles,1);
  $('finding').textContent=`The frozen forecast trails the weekly forecast by ${money((all.weekly.net-all.selected.net)*scale)} over this period in ${area}. Lower price error in the earlier forecast benchmark did not translate into better battery cash flow. These are simulated operating cash flows, before capital cost and omitted tariffs.`;
  const ticks=[0,24,48,72,95].map(i=>({index:i,label:day.local[i].slice(11,16)}));
  const planning=policy==='hindsight'?day.actual:day.forecast[policy];
  lineChart('price-chart',[{values:day.actual,color:'#263026'},...(planning?[{values:planning,color:'#d65b32',dash:true}]:[])],{ticks,unit:'EUR / MWh'});
  lineChart('power-chart',[{values:s.charge.map(x=>-x*scale),color:'#3d613c'},{values:s.discharge.map(x=>x*scale),color:'#d65b32'}],{min:-scale,max:scale,ticks,bars:true});
  lineChart('soc-chart',[{values:s.soc.map(x=>x*scale),color:'#3d613c'}],{min:0,max:2*scale,ticks:[{index:0,label:'00:00'},{index:24,label:'06:00'},{index:48,label:'12:00'},{index:72,label:'18:00'},{index:96,label:'24:00'}]});
  $('daily-stats').innerHTML=[['Grid import',fmt(totals.import_mwh,2)+' MWh'],['Grid export',fmt(totals.export_mwh,2)+' MWh'],['Daily net cash flow',money(totals.net)],['Energy lost',fmt(totals.loss_mwh,2)+' MWh']].map(([k,v])=>`<div><span>${k}</span><strong>${v}</strong></div>`).join('');
  lineChart('cash-chart',[{values:[0,...cumulative(days.map(d=>d.policies.hindsight.totals.net*scale))],color:'#a4b49b',dash:true},{values:[0,...cumulative(days.map(d=>d.policies.weekly.totals.net*scale))],color:'#d65b32'},{values:[0,...cumulative(days.map(d=>d.policies[policy].totals.net*scale))],color:'#263026',width:3}],{ticks:[{index:0,label:'1 Jul'},{index:31,label:'1 Aug'},{index:62,label:'1 Sep'},{index:92,label:'30 Sep'}]});
  $('waterfall').innerHTML=[['Gross energy cash flow',totals.gross],['Grid throughput fee',-totals.fee],['Cell wear allowance',-totals.wear],['Net cash flow',totals.net]].map(([k,v])=>`<div class="cash-row"><span>${k}</span><strong>${money(v)}</strong></div>`).join('');
  $('comparison').innerHTML=Object.entries(labels).map(([key,label])=>{const r=all[key];return `<tr class="${key===policy?'active-row':''}"><td>${label}</td><td>${money(r.net*scale)}</td><td>${r.profitable_days} / 92</td><td>${money(r.worst_day_eur*scale)}</td><td>${fmt(r.cycles,1)}</td></tr>`;}).join('');
  $('journal').innerHTML=intervalCash(day,policy,scale).map((r,i)=>`<tr><td>${r.local.slice(11,16)}</td><td>${fmt(day.actual[i],2)}</td><td>${fmt(r.charge,3)}</td><td>${fmt(r.discharge,3)}</td><td>${fmt(r.soc,3)}</td><td>${fmt(r.net,2)}</td></tr>`).join('');
}
async function init(){
  try{
    const response=await fetch('reports/results.json');if(!response.ok)throw new Error(`Report request failed (${response.status})`);
    report=await response.json();if(report.days.length!==184)throw new Error('Incomplete replay data');
    $('day').innerHTML=report.days.filter(d=>d.area==='DK1').map(d=>`<option value="${d.day}">${d.day}</option>`).join('');
    for(const id of ['area','policy','day','scale'])$(id).addEventListener('change',render);
    $('download').addEventListener('click',()=>{
      const policy=$('policy').value,scale=Number($('scale').value);
      const rows=intervalCash(currentDay,policy,scale).map((r,i)=>({area:currentDay.area,day:currentDay.day,policy,asset_mw:scale,asset_mwh:2*scale,issue_utc:currentDay.issue,delivery_utc:r.utc,delivery_local:r.local,actual_eur_mwh:currentDay.actual[i],charge_mw:r.charge,discharge_mw:r.discharge,soc_end_mwh:r.soc,gross_eur:r.gross,fee_eur:r.fee,wear_eur:r.wear,net_eur:r.net}));
      const url=URL.createObjectURL(new Blob([csv(rows)],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=`cellar-${currentDay.area}-${currentDay.day}-${policy}-${scale}MW.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    render();$('loading').hidden=true;$('dashboard').hidden=false;
  }catch(e){$('loading').hidden=true;$('error').hidden=false;$('error').textContent=`Could not load the replay. Serve this repository over HTTP or use the public preview. ${e.message}`;}
}
init();
