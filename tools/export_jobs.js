// Usage: node export_jobs.js data/hsk4a.js ... > jobs.json
// Turns question data into a list of audio jobs: {out, speed, segs:[{v:'F'|'M'|'N'|'P', t, pause}]}
const fs=require('fs'), vm=require('vm');
const ctx={window:{}}; ctx.HSK_SETS=ctx.window.HSK_SETS=[]; ctx.HSK_PRACTICE=ctx.window.HSK_PRACTICE=[]; vm.createContext(ctx);
for(const f of process.argv.slice(2)) vm.runInContext(fs.readFileSync(f,'utf8'),ctx);
const SPEED={4:0.92,5:0.96,6:1.0};
function lines(script, narrator){
  return script.split('\n').filter(Boolean).map(l=>{
    let m=l.match(/^(男|女|问)：(.*)$/);
    if(!m) return {v:narrator,t:l,pause:0.5};
    return {v:m[1]==='男'?'M':m[1]==='女'?'F':'N', t:m[2], pause:m[1]==='问'?0.8:0.45};
  });
}
const jobs=[];
for(const s of [...ctx.HSK_SETS, ...ctx.HSK_PRACTICE]){
  const sp=SPEED[s.level], dir=s.id; let gi=0;
  for(const sec of s.sections) for(const p of sec.parts){
    if(p.type==='tf') for(const it of p.items) jobs.push({out:`${dir}/${it.id}.mp3`,speed:sp,segs:[...lines(it.script,'P'),{v:'N',t:it.stem,pause:1.0}]});
    if(p.type==='lmc') for(const it of p.items) jobs.push({out:`${dir}/${it.id}.mp3`,speed:sp,segs:lines(it.script,'P')});
    if(p.type==='lgroup') for(const g of p.groups){
      gi++; const nar = gi%2? 'P':'Q';
      const segs=lines(g.script,nar);
      for(const it of g.items){ const n=it.id.replace(/\D/g,''); segs.push({v:'N',t:`第${n}题：${it.q}`,pause:1.4}); }
      jobs.push({out:`${dir}/${g.id}.mp3`,speed:sp,segs});
    }
    if(p.type==='repeat'||p.type==='read') for(const it of p.items) jobs.push({out:`${dir}/${it.id}.mp3`,speed:sp*0.95,segs:[{v:'Q',t:it.text,pause:0.3}]});
    if(p.type==='retell') for(const it of p.items) jobs.push({out:`${dir}/${it.id}.mp3`,speed:sp*0.95,segs:lines(it.script,'P')});
    if(p.type==='speak'||p.type==='retell') for(const it of p.items) if(it.sample) jobs.push({out:`${dir}/${it.id}_sample.mp3`,speed:sp,segs:[{v:'Q',t:it.sample,pause:0.3}]});
  }
}
process.stdout.write(JSON.stringify(jobs,null,1));
