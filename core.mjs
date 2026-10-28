export const labels = {selected:'Frozen forecast',weekly:'Weekly forecast',idle:'Idle battery',hindsight:'Perfect-price hindsight'};
export function scaleTotals(t,scale=1) {
  if(!Number.isFinite(scale)||scale<=0) throw new Error('Invalid asset scale');
  return Object.fromEntries(Object.entries(t).map(([k,v])=>[k,k==='cycles'?v:v*scale]));
}
export function intervalCash(day,policy,scale=1) {
  if(!Number.isFinite(scale)||scale<=0) throw new Error('Invalid asset scale');
  const p=day.policies[policy];
  return day.actual.map((price,i)=>{
    const charge=p.charge[i]*scale,discharge=p.discharge[i]*scale;
    const gross=(discharge-charge)*.25*price,fee=(charge+discharge)*.25*2,wear=discharge*.25/.95*8;
    return {utc:day.utc[i],local:day.local[i],charge,discharge,soc:p.soc[i+1]*scale,gross,fee,wear,net:gross-fee-wear};
  });
}
export function cumulative(values){let s=0;return values.map(x=>s+=x);}
export function csv(rows){
  if(!rows.length)return '';
  const keys=Object.keys(rows[0]),escape=v=>'"'+String(v??'').replaceAll('"','""')+'"';
  return [keys.map(escape).join(','),...rows.map(row=>keys.map(k=>escape(row[k])).join(','))].join('\r\n');
}
