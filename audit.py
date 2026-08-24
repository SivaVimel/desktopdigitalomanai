#!/usr/bin/env python3
"""Universal layout audit.

Walks the whole reel at many viewport sizes and asserts two things that must
hold on every device: no two words of a line may overlap, and nothing may sit
outside the frame. Between passes it fires the height-only resize a phone
produces when its address bar slides, which is what used to zero every
measurement and stack the words on one point.
"""
import sys
from playwright.sync_api import sync_playwright

SIZES = [("iPhone SE",320,568),("Galaxy S8",360,740),("iPhone 12",390,844),
         ("iPhone Pro Max",430,932),("phablet",480,800),("iPad mini",768,1024),
         ("iPad",834,1112),("iPad Pro",1024,1366),("laptop",1280,800),
         ("desktop",1440,900),("full HD",1920,1080),("wide",2560,1440),
         # landscape phones: very short frames, where stacked text can collide
         ("SE landscape",568,320),("phone landscape",740,360),("12 landscape",844,390)]
STEPS = 26

DETECT = """() => {
  const bad=[];
  // measure the text's ink, not the element box: most of these are
  // full-width absolutely-positioned centring boxes
  const ink = e => { const r=document.createRange(); r.selectNodeContents(e);
                     const b=r.getBoundingClientRect(); r.detach&&r.detach(); return b; };
  const vw=innerWidth, vh=innerHeight;
  for(const o of LINES){
    const vis=[];
    o.spans.forEach((s,i)=>{
      if(parseFloat(s.style.opacity||0) < .55) return;
      const r=s.getBoundingClientRect();
      if(r.width<=0 || r.bottom<0 || r.top>vh) return;
      vis.push({i, r, t:s.textContent.trim()});
    });
    for(let a=0;a<vis.length;a++){
      const A=vis[a].r;
      if(A.left < -2 || A.right > vw+2)
        bad.push({kind:'overflow', word:vis[a].t, left:Math.round(A.left), right:Math.round(A.right)});
      for(let b=a+1;b<vis.length;b++){
        const B=vis[b].r;
        const ox=Math.min(A.right,B.right)-Math.max(A.left,B.left);
        const oy=Math.min(A.bottom,B.bottom)-Math.max(A.top,B.top);
        if(ox > Math.min(A.width,B.width)*.34 && oy > Math.min(A.height,B.height)*.55)
          bad.push({kind:'overlap', a:vis[a].t, b:vis[b].t, ox:Math.round(ox)});
      }
    }
  }
  // stacked text blocks (headline / figure / caption / close stack) must stay
  // inside the frame and must not run into each other on short screens
  const stages=[...document.querySelectorAll('.stage')]
    .filter(s=>s.style.display!=='none' && parseFloat(s.style.opacity||0)>.6);
  for(const st of stages){
    const blocks=[...st.querySelectorAll('div,a')].filter(e=>{
      // orbiting decor is meant to drift past the frame edge, like the film's
      // objects flying past camera — only anchored text must stay inside
      if(e.closest('.chipf,.ico,.card,.orb,.win,.app,.term')) return false;
      // a reveal clips its own text on purpose (the wordmark types out of an
      // animated width); .stage clips to the viewport, which is not a defect
      for(let a=e; a && !a.classList.contains('stage'); a=a.parentElement){
        const cs=getComputedStyle(a);
        if(cs.overflowX!=='visible'||cs.overflowY!=='visible') return false;
      }
      if(e.classList.contains('line')||e.classList.contains('w')) return false;
      if(e.querySelector('div,a,img,svg')) return false;      // leaves only
      if(!e.textContent.trim()) return false;
      if(parseFloat(getComputedStyle(e).opacity) < .55) return false;
      const r=ink(e);
      return r.width>0 && r.height>0 && r.bottom>0 && r.top<vh;
    }).map(e=>({e, r:ink(e), t:e.textContent.trim().slice(0,22)}));
    for(let a=0;a<blocks.length;a++){
      const A=blocks[a].r;
      if(A.left<-2 || A.right>vw+2)
        bad.push({kind:'block-overflow', word:blocks[a].t,
                  left:Math.round(A.left), right:Math.round(A.right)});
      for(let b=a+1;b<blocks.length;b++){
        const B=blocks[b].r;
        if(blocks[a].e.contains(blocks[b].e)||blocks[b].e.contains(blocks[a].e)) continue;
        const ox=Math.min(A.right,B.right)-Math.max(A.left,B.left);
        const oy=Math.min(A.bottom,B.bottom)-Math.max(A.top,B.top);
        if(ox>Math.min(A.width,B.width)*.34 && oy>Math.min(A.height,B.height)*.55)
          bad.push({kind:'block-overlap', a:blocks[a].t, b:blocks[b].t, oy:Math.round(oy)});
      }
    }
  }
  return bad;
}"""

fails = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome",
                          args=["--no-sandbox","--hide-scrollbars"])
    for name,w,h in SIZES:
        pg = b.new_page(viewport={"width":w,"height":h})
        pg.goto("http://127.0.0.1:8899/index.html", wait_until="load")
        pg.wait_for_function("document.body.dataset.ready==='1'", timeout=45000)
        issues=[]
        for i in range(STEPS+1):
            fr=i/STEPS
            pg.evaluate("f=>window.scrollTo(0,Math.round(f*(document.documentElement.scrollHeight-innerHeight)))", fr)
            pg.wait_for_timeout(240)
            # a phone's address bar slides mid-scroll: height-only resize
            if i in (6, 13, 20):
                pg.set_viewport_size({"width":w,"height":h-60 if i%2 else h})
                pg.wait_for_timeout(320)
            for it in pg.evaluate(DETECT):
                it["at"]=round(fr,2); issues.append(it)
        ovf = pg.evaluate("document.documentElement.scrollWidth>innerWidth+1")
        pg.close()
        if issues or ovf:
            fails += 1
            print(f"FAIL {name:14s} {w}x{h}  h-scroll={ovf}  {len(issues)} issue(s)")
            for it in issues[:4]: print("      ", it)
        else:
            print(f"  ok {name:14s} {w}x{h}")
    b.close()
print("\nRESULT:", "all clean" if fails==0 else f"{fails} viewport(s) with problems")
sys.exit(1 if fails else 0)
