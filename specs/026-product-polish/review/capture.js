const {chromium}=require('playwright');const path=require('path');
const OUT=process.argv[2]||'specs/026-product-polish/review/shots';
(async()=>{const b=await chromium.launch();const out={};
for(const page of ['index.html','demo-report.html'])for(const w of [1280,390])for(const scheme of ['light','dark']){
 const ctx=await b.newContext({viewport:{width:w,height:900},colorScheme:scheme,deviceScaleFactor:1});const p=await ctx.newPage();
 const net=[],errs=[];p.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:'))net.push(r.url())});p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});p.on('pageerror',e=>errs.push(String(e)));
 await p.goto('file://'+path.resolve('docs/'+page));await p.waitForTimeout(400);
 const info=await p.evaluate(()=>{const de=document.documentElement;const wide=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>de.clientWidth+1&&getComputedStyle(e).position!=='fixed'}).filter(e=>{let a=e.parentElement;while(a){const s=getComputedStyle(a);if(/auto|scroll|hidden/.test(s.overflowX))return false;a=a.parentElement}return true}).slice(0,8).map(e=>e.tagName+'.'+e.className+' '+Math.round(e.getBoundingClientRect().right));
  const small=[...document.querySelectorAll('body *')].filter(e=>e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())&&e.getClientRects().length).map(e=>parseFloat(getComputedStyle(e).fontSize)).filter(s=>s<12).length;
  return {scrollW:de.scrollWidth,clientW:de.clientWidth,height:de.scrollHeight,wide,small}});
 const n=`${page.replace('.html','')}-${scheme}-${w}`;out[n]={...info,net,errs};
 await p.screenshot({path:OUT+`/${n}.png`,fullPage:page==='index.html'});await ctx.close();}
console.log(JSON.stringify(out,null,1));await b.close();})();
