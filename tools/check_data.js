const fs=require('fs'),vm=require('vm');const ctx={window:{}};ctx.HSK_SETS=ctx.window.HSK_SETS=[];vm.createContext(ctx);
for(const f of fs.readdirSync('data').sort()) vm.runInContext(fs.readFileSync('data/'+f,'utf8'),ctx);
const L='ABCDEF'; let errs=0; const E=(s,m)=>{errs++;console.log('ERR',s,m)};
const norm=s=>s.replace(/[\s。，、？！]/g,'');
for(const s of ctx.HSK_SETS){
  const ids=new Set(), dist={}; let nObj=0;
  for(const sec of s.sections) for(const p of sec.parts){
    const items=p.groups?p.groups.flatMap(g=>g.items.map(it=>({it,g}))):p.items.map(it=>({it,g:null}));
    for(const {it,g} of items){
      if(ids.has(it.id)) E(s.id,'dup '+it.id); ids.add(it.id);
      if(!it.id.startsWith(sec.key)) E(s.id,'prefix '+it.id);
      if(it.opts){ if(!L.slice(0,it.opts.length).includes(it.ans)) E(s.id,'ans out of range '+it.id); if(new Set(it.opts).size!==it.opts.length) E(s.id,'dup opt '+it.id); dist[it.ans]=(dist[it.ans]||0)+1; nObj++; }
      if(p.type==='tf'&&!['√','×'].includes(it.ans)) E(s.id,'tf '+it.id);
      if(p.type==='bank'&&!p.bank[it.ans]) E(s.id,'bank '+it.id);
      if(p.type==='bank'&&!it.text.includes('（　　）')) E(s.id,'bank blank '+it.id);
      if(p.type==='order'&&[...it.ans].sort().join('')!=='ABC') E(s.id,'order '+it.id);
      if(p.type==='sentfill'&&!g.bank[it.ans]) E(s.id,'sentfill '+it.id);
      if((p.type==='cloze'||p.type==='sentfill')&&!g.passage.includes('（'+it.id+'）')) E(s.id,'marker '+it.id);
      if(p.type==='arrange') for(const a of it.ans) if([...norm(a)].sort().join('')!==[...it.words.join('')].sort().join('')) E(s.id,'arrange chars '+it.id+' '+a);
      if(p.type==='lgroup'&&!it.q) E(s.id,'q '+it.id);
      if((OBJ=['tf','lmc','lgroup','bank','order','rmc','rgroup','cloze','error','multi','sentfill','arrange']).includes(p.type)&&!it.exp) E(s.id,'no exp '+it.id);
    }
    if(p.type==='sentfill') for(const g of p.groups){ const a=g.items.map(i=>i.ans); if(new Set(a).size!==a.length) E(s.id,'sentfill dup'); }
    if(p.type==='bank'){ const a=p.items.map(i=>i.ans); if(new Set(a).size!==a.length) E(s.id,'bank dup'); }
  }
  console.log(s.id, 'items', ids.size, 'mc', nObj, JSON.stringify(dist));
}
console.log('errors', errs);
