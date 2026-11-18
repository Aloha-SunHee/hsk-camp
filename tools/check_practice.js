const fs=require('fs'),vm=require('vm');const ctx={window:{}};ctx.HSK_SETS=ctx.window.HSK_SETS=[];vm.createContext(ctx);
for(const f of fs.readdirSync('data/practice').sort()) vm.runInContext(fs.readFileSync('data/practice/'+f,'utf8'),ctx);
const L='ABCDEF'; let errs=0; const E=(s,m)=>{errs++;console.log('ERR',s,m)};
const norm=s=>s.replace(/[\s。，、？！]/g,''); const BAD=/第[一二三四]部分|[●○■]|参考答案|试题|听力材料|请选择正确答案|____|\(\s*\)|题选项/;
for(const s of ctx.HSK_SETS){ const ids=new Set(), dist={};
 for(const sec of s.sections) for(const p of sec.parts){
  for(const g of (p.groups||[])){ for(const k of ['script','passage']) if(g[k]!=null){ if(!g[k].trim()) E(s.id,'empty '+k+' '+g.id); if(BAD.test(g[k])) E(s.id,'junk in '+g.id+': '+g[k].match(BAD)[0]); }
    if(g.bank) for(const v of Object.values(g.bank)) if(BAD.test(v)||!v) E(s.id,'bank '+g.id+' '+v); }
  const items=p.groups?p.groups.flatMap(g=>g.items.map(it=>({it,g}))):p.items.map(it=>({it,g:null}));
  for(const {it,g} of items){
   if(ids.has(it.id)) E(s.id,'dup '+it.id); ids.add(it.id);
   const strs=[it.script,it.stem,it.q,it.passage,it.text,...(it.opts||[]),...(it.segs||[])].filter(x=>x!=null);
   for(const x of strs) if(BAD.test(x)) E(s.id,'junk '+it.id+': '+x.slice(0,60));
   if(it.opts){ if(!['error','multi','cloze'].includes(p.type) && it.opts.length!==4) E(s.id,'nopts '+it.id+' '+it.opts.length);
     if(it.opts.length!==4) E(s.id,'nopts '+it.id+' '+it.opts.length);
     if(!L.slice(0,it.opts.length).includes(it.ans)) E(s.id,'ans '+it.id+' '+it.ans); if(new Set(it.opts).size!==it.opts.length) E(s.id,'dupopt '+it.id);
     if(it.opts.some(o=>!o||o.length>60)) E(s.id,'optlen '+it.id); dist[it.ans]=(dist[it.ans]||0)+1; }
   if(p.type==='tf'&&!['√','×'].includes(it.ans)) E(s.id,'tf '+it.id);
   if(['tf','lmc'].includes(p.type)&&!it.script) E(s.id,'noscript '+it.id);
   if(p.type==='lgroup'&&!it.q) E(s.id,'noq '+it.id);
   if(p.type==='bank'&&(!p.bank[it.ans]||!it.text.includes('（　　）'))) E(s.id,'bank '+it.id);
   if(p.type==='order'&&([...it.ans].sort().join('')!=='ABC'||it.segs.length!==3)) E(s.id,'order '+it.id);
   if(p.type==='sentfill'&&!g.bank[it.ans]) E(s.id,'sentfill '+it.id);
   if((p.type==='cloze'||p.type==='sentfill')&&!g.passage.includes('（'+it.id+'）')) E(s.id,'marker '+it.id);
   if(p.type==='multi'&&!it.text.includes('＿＿＿')) E(s.id,'multi blank '+it.id);
   if(p.type==='arrange') for(const a of it.ans) if([...norm(a)].sort().join('')!==[...it.words.join('')].sort().join('')) E(s.id,'arrange '+it.id+' '+a+' | '+it.words.join(' '));
   if(p.type==='picture'&&(!it.word||!it.sample)) E(s.id,'pic '+it.id);
   if(['essay','summary'].includes(p.type)&&!it.sample) E(s.id,'sample '+it.id);
  }}
 const exp={4:100,5:100,6:101}[s.level]; if(ids.size!==exp) E(s.id,'count '+ids.size);
 console.log(s.id, ids.size, JSON.stringify(dist));
}
console.log('errors',errs);
