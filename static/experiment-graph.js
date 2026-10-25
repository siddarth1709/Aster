(() => {
  const root = document.querySelector('.aster-graph');
  if (!root) return;
  const DATA = JSON.parse(root.dataset.graph || '{}');
  root.dataset.graphRuntime = 'ready';
  const canvas = root.querySelector('.graph-canvas');
  const ctx = canvas.getContext('2d');
  const stage = root.querySelector('.graph-stage');
  const inspector = root.querySelector('.graph-inspector');
  const search = root.querySelector('#graph-search');
  const nodes = DATA.nodes.map((node,index) => {
    const angle = index * 2.399963229728653;
    const radius = node.kind === 'experiment' ? 65 + Math.sqrt(index + 1) * 20 : 155 + Math.sqrt(index + 1) * 14;
    return {...node,x:Math.cos(angle)*radius,y:Math.sin(angle)*radius,vx:0,vy:0,r:node.kind==='experiment'?10:Math.min(8,5+Math.sqrt(node.count||1)),fixed:false};
  });
  const byId = new Map(nodes.map(node => [node.id,node]));
  const indexById = new Map(nodes.map((node,index)=>[node.id,index]));
  const edges = DATA.edges.filter(edge => byId.has(edge.source) && byId.has(edge.target));
  const adjacency = new Map(nodes.map(node => [node.id,new Set()]));
  for (const edge of edges) { adjacency.get(edge.source)?.add(edge.target); adjacency.get(edge.target)?.add(edge.source); }
  const camera = {scale:1,tx:0,ty:0};
  let selected = null, hovered = null, isolate = false, query = '', moving = true, pointer = null;
  const dpr = Math.min(window.devicePixelRatio||1,2);
  const colors = {experiment:'#65d6ff',tag:'#a896ff',pattern:'#56dfb6',metric:'#ffbe72',model:'#75a8ff',dataset:'#65c6c8',framework:'#89d19c'};
  const escapeHtml = value => String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  function resize(){const rect=stage.getBoundingClientRect();canvas.width=Math.max(1,Math.round(rect.width*dpr));canvas.height=Math.max(1,Math.round(rect.height*dpr));root.dataset.canvasReady='true';draw();}
  function screenPoint(node){return {x:canvas.clientWidth/2+camera.tx+node.x*camera.scale,y:canvas.clientHeight/2+camera.ty+node.y*camera.scale};}
  function draw(){
    const w=canvas.clientWidth,h=canvas.clientHeight;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
    ctx.save();ctx.translate(w/2+camera.tx,h/2+camera.ty);ctx.scale(camera.scale,camera.scale);
    const focusedNeighbors=selected&&isolate?adjacency.get(selected.id):null;
    for(const edge of edges){
      const a=byId.get(edge.source),b=byId.get(edge.target);if(!a||!b)continue;
      const faded=Boolean(focusedNeighbors&&edge.source!==selected.id&&edge.target!==selected.id);
      const active=selected&&(edge.source===selected.id||edge.target===selected.id);
      ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
      ctx.strokeStyle=faded?'rgba(130,142,164,.035)':edge.kind==='lineage'?(active?'rgba(100,210,255,.88)':'rgba(77,179,225,.42)'):(active?'rgba(168,150,255,.78)':'rgba(168,150,255,.27)');
      ctx.lineWidth=(active?1.8:1)/camera.scale;
      ctx.setLineDash(edge.kind==='lineage'?[]:[4/camera.scale,6/camera.scale]);ctx.stroke();ctx.setLineDash([]);
      if(edge.kind==='lineage'&&!faded){const angle=Math.atan2(b.y-a.y,b.x-a.x),len=b.r+2;const x=b.x-Math.cos(angle)*len,y=b.y-Math.sin(angle)*len;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x-Math.cos(angle-.48)*7/camera.scale,y-Math.sin(angle-.48)*7/camera.scale);ctx.lineTo(x-Math.cos(angle+.48)*7/camera.scale,y-Math.sin(angle+.48)*7/camera.scale);ctx.closePath();ctx.fillStyle=active?'#8fe3ff':'#56bde9';ctx.fill();}
    }
    for(const node of nodes){
      const isSelected=selected?.id===node.id,isHovered=hovered?.id===node.id;
      const isNeighbor=selected&&(node.id===selected.id||focusedNeighbors?.has(node.id));
      const match=!query||node.label.toLowerCase().includes(query);
      const dim=(focusedNeighbors&&!isNeighbor)||(!match&&query);
      const color=colors[node.kind]||'#a896ff';
      const radius=node.r*(isSelected?1.42:isHovered?1.2:1);
      ctx.globalAlpha=dim?.12:1;
      if(isSelected||isHovered||node.kind==='experiment'){ctx.beginPath();ctx.arc(node.x,node.y,radius+5/camera.scale,0,Math.PI*2);ctx.fillStyle=isSelected?'rgba(100,210,255,.12)':`rgba(${node.kind==='metric'?'255,190,114':'100,210,255'},.075)`;ctx.fill();}
      ctx.beginPath();ctx.arc(node.x,node.y,radius,0,Math.PI*2);ctx.fillStyle=node.kind==='experiment'?'#111c29':'#121823';ctx.fill();ctx.lineWidth=(isSelected?2.2:1.45)/camera.scale;ctx.strokeStyle=color;ctx.stroke();
      if(node.kind==='experiment'){ctx.beginPath();ctx.arc(node.x,node.y,2.4/camera.scale,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();}
      const showLabel=isSelected||isHovered||(node.kind!=='experiment'&&camera.scale>.72)||(node.kind==='experiment'&&camera.scale>.95);
      if(showLabel){const text=node.label.length>24?node.label.slice(0,22)+'…':node.label;ctx.font=`${isSelected?'600':'500'} ${Math.max(10,11/camera.scale)}px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif`;ctx.textAlign='center';ctx.textBaseline='top';ctx.fillStyle=dim?'rgba(193,204,222,.25)':isSelected?'#f4f8ff':'#c7d1e0';ctx.fillText(text,node.x,node.y+radius+6/camera.scale);}
      ctx.globalAlpha=1;
    }
    ctx.restore();
  }
  function fit(){if(!nodes.length)return;let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;for(const node of nodes){minX=Math.min(minX,node.x);maxX=Math.max(maxX,node.x);minY=Math.min(minY,node.y);maxY=Math.max(maxY,node.y);}const pad=100;camera.scale=Math.max(.32,Math.min(1.65,(canvas.clientWidth-pad*2)/Math.max(1,maxX-minX),(canvas.clientHeight-pad*2)/Math.max(1,maxY-minY)));camera.tx=-(minX+maxX)*camera.scale/2;camera.ty=-(minY+maxY)*camera.scale/2;draw();}
  function describe(node){
    if(!node){inspector.innerHTML='<div class="inspector-empty">Select a node to inspect its experiment, metrics, memory, and relationships.</div>';return;}
    if(node.kind!=='experiment'){
      const members=(node.members||[]).map(member=>`<p>• ${escapeHtml(member.title)}</p>`).join('');
      const samples=(node.samples||[]).map(sample=>`<p><b>${escapeHtml(sample.title)}:</b> ${escapeHtml(sample.value)}</p>`).join('');
      const memberCount=(node.members||[]).length;
      inspector.innerHTML=`<p class="inspector-kicker">${escapeHtml(node.kind)} concept · ${memberCount} experiment${memberCount===1?'':'s'}</p><h3 class="inspector-title">${escapeHtml(node.label)}</h3>${node.summary?`<div class="inspector-section"><h4>About this concept</h4><p>${escapeHtml(node.summary)}</p></div>`:''}<div class="inspector-section"><h4>Connected experiments</h4>${members||'<p>No experiments use this concept yet.</p>'}</div>${samples?`<div class="inspector-section"><h4>Observed metric values</h4>${samples}</div>`:''}`;return;
    }
    const details=[['Hypothesis',node.hypothesis],['Setup',node.setup],['Results',node.results],['Insights',node.insights],['Next steps',node.next_steps],['Research memory',node.memory]];
    const sections=details.filter(([,value])=>String(value||'').trim()).map(([title,value])=>`<div class="inspector-section"><h4>${title}</h4><p>${escapeHtml(value)}</p></div>`).join('');
    const tags=(node.tags||[]).map(tag=>`<span class="inspector-chip">${escapeHtml(tag)}</span>`).join('');
    const context=[['Model',node.model],['Dataset',node.dataset],['Framework',node.framework]].filter(([,value])=>value).map(([label,value])=>`<p><b>${label}:</b> ${escapeHtml(value)}</p>`).join('');
    const metrics=Object.entries(node.metrics||{}).map(([name,value])=>`<p><b>${escapeHtml(name)}:</b> ${escapeHtml(typeof value==='string'?value:JSON.stringify(value))}</p>`).join('');
    const active=Object.entries(node.involvement||{}).filter(([,value])=>value===true).map(([key])=>key.replaceAll('_',' ')).join(' · ');
    inspector.innerHTML=`<p class="inspector-kicker">Experiment · ${escapeHtml(node.date||'Date unavailable')}</p><h3 class="inspector-title">${escapeHtml(node.label)}</h3>${tags?`<div>${tags}</div>`:''}${context?`<div class="inspector-section"><h4>Run context</h4>${context}</div>`:''}${active?`<div class="inspector-section"><h4>Involvement</h4><p>${escapeHtml(active)}</p></div>`:''}${metrics?`<div class="inspector-section"><h4>Metrics</h4>${metrics}</div>`:''}${sections}<a class="inspector-link" href="?open_experiment=${encodeURIComponent(node.id.slice('experiment:'.length))}">Open experiment details <span aria-hidden="true">↗</span></a>`;
  }
  function hit(x,y){const world={x:(x-canvas.clientWidth/2-camera.tx)/camera.scale,y:(y-canvas.clientHeight/2-camera.ty)/camera.scale};for(let i=nodes.length-1;i>=0;i--){const node=nodes[i];if(Math.hypot(node.x-world.x,node.y-world.y)<node.r+9/camera.scale)return node;}return null;}
  function eventPoint(event){const rect=canvas.getBoundingClientRect();return{x:event.clientX-rect.left,y:event.clientY-rect.top};}
  canvas.addEventListener('pointerdown',event=>{const p=eventPoint(event),node=hit(p.x,p.y);pointer={x:event.clientX,y:event.clientY,tx:camera.tx,ty:camera.ty,node,moved:false,lastX:0,lastY:0};canvas.setPointerCapture(event.pointerId);if(node){selected=node;describe(node);draw();}});
  canvas.addEventListener('pointermove',event=>{const p=eventPoint(event);if(pointer){const dx=event.clientX-pointer.x,dy=event.clientY-pointer.y;if(Math.abs(dx)+Math.abs(dy)>3)pointer.moved=true;if(pointer.node&&pointer.moved){pointer.node.x+=(dx-pointer.lastX||0)/camera.scale;pointer.node.y+=(dy-pointer.lastY||0)/camera.scale;pointer.lastX=dx;pointer.lastY=dy;pointer.node.vx=pointer.node.vy=0;}else if(pointer.moved){camera.tx=pointer.tx+dx;camera.ty=pointer.ty+dy;}draw();return;}const node=hit(p.x,p.y);if(node!==hovered){hovered=node;canvas.style.cursor=node?'pointer':'grab';draw();}});
  canvas.addEventListener('pointerup',()=>{if(pointer){if(pointer.node&&pointer.moved){const dragged=pointer.node;dragged.fixed=true;window.setTimeout(()=>{dragged.fixed=false;start();},600);}pointer=null;}});
  canvas.addEventListener('pointercancel',()=>{pointer=null;});
  canvas.addEventListener('wheel',event=>{event.preventDefault();const old=camera.scale,factor=Math.exp(-event.deltaY*.001);camera.scale=Math.max(.32,Math.min(2.6,old*factor));camera.tx=(camera.tx+canvas.clientWidth/2)*(camera.scale/old)-canvas.clientWidth/2;camera.ty=(camera.ty+canvas.clientHeight/2)*(camera.scale/old)-canvas.clientHeight/2;draw();},{passive:false});
  root.querySelector('#graph-fit').addEventListener('click',fit);
  root.querySelector('#graph-focus').addEventListener('click',event=>{isolate=!isolate;event.currentTarget.setAttribute('aria-pressed',String(isolate));event.currentTarget.textContent=isolate?'Show full graph':'Focus neighborhood';draw();});
  root.querySelector('#graph-reset').addEventListener('click',()=>{selected=null;isolate=false;root.querySelector('#graph-focus').setAttribute('aria-pressed','false');root.querySelector('#graph-focus').textContent='Focus neighborhood';describe(null);fit();});
  search.addEventListener('input',()=>{query=search.value.trim().toLowerCase();draw();if(query){const exact=nodes.find(node=>node.label.toLowerCase().includes(query));if(exact){selected=exact;describe(exact);}}});
  function start(){if(moving)return;moving=true;requestAnimationFrame(step);}
  function step(){
    if(!moving)return;
    const forces=nodes.map(()=>({x:0,y:0}));
    for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j],dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy+1,d=Math.sqrt(d2),strength=5200/d2,fx=dx/d*strength,fy=dy/d*strength;forces[i].x-=fx;forces[i].y-=fy;forces[j].x+=fx;forces[j].y+=fy;}
    for(const edge of edges){const a=byId.get(edge.source),b=byId.get(edge.target),ia=indexById.get(edge.source),ib=indexById.get(edge.target);if(!a||!b||ia===undefined||ib===undefined)continue;const dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,target=edge.kind==='lineage'?150:112,force=(d-target)*.0032,fx=dx/d*force,fy=dy/d*force;forces[ia].x+=fx;forces[ia].y+=fy;forces[ib].x-=fx;forces[ib].y-=fy;}
    let energy=0;for(let i=0;i<nodes.length;i++){const node=nodes[i];if(node.fixed)continue;const force=forces[i];force.x-=node.x*.0011;force.y-=node.y*.0011;node.vx=(node.vx+force.x)*.84;node.vy=(node.vy+force.y)*.84;node.x+=node.vx;node.y+=node.vy;energy+=node.vx*node.vx+node.vy*node.vy;}
    draw();if(energy/nodes.length<.012){moving=false;return;}requestAnimationFrame(step);
  }
  new ResizeObserver(resize).observe(stage);resize();if(nodes.length){requestAnimationFrame(step);window.setTimeout(fit,350);}
})();
