/* Logical edge metadata drives both diagram focus and accessible flow navigation. */
(() => {
  const escape=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const colors={incoming:'#2469a2',outgoing:'#26764f',both:'#79569b'};
  const routingCache=new WeakMap();
  function routingGrid(c){
    if(routingCache.has(c))return routingCache.get(c);
    const pad=3,stub=4,offsets=[-12,0,12], xs=new Set(),ys=new Set(),ports=new Map();
    const boxes=c.nodes.map(n=>({left:n.x-pad,right:n.x+n.w+pad,top:n.y-pad,bottom:n.y+n.h+pad}));
    for(const n of c.nodes){
      const cx=n.x+n.w/2,cy=n.y+n.h/2,list=[];
      for(const offset of offsets){
        list.push({x:n.x-stub,y:cy+offset,ax:n.x,ay:cy+offset,axis:0,vx:-1,vy:0,offset});
        list.push({x:n.x+n.w+stub,y:cy+offset,ax:n.x+n.w,ay:cy+offset,axis:0,vx:1,vy:0,offset});
        list.push({x:cx+offset,y:n.y-stub,ax:cx+offset,ay:n.y,axis:1,vx:0,vy:-1,offset});
        list.push({x:cx+offset,y:n.y+n.h+stub,ax:cx+offset,ay:n.y+n.h,axis:1,vx:0,vy:1,offset});
      }
      ports.set(n.id,list);list.forEach(p=>{xs.add(p.x);ys.add(p.y);});
    }
    xs.add(Math.min(...c.nodes.map(n=>n.x))-20);xs.add(Math.max(...c.nodes.map(n=>n.x+n.w))+20);
    ys.add(Math.min(...c.nodes.map(n=>n.y))-20);ys.add(Math.max(...c.nodes.map(n=>n.y+n.h))+35);
    const xx=[...xs].sort((a,b)=>a-b),yy=[...ys].sort((a,b)=>a-b),points=[],lookup=new Map();
    for(const y of yy)for(const x of xx){if(!boxes.some(b=>x>b.left&&x<b.right&&y>b.top&&y<b.bottom)){lookup.set(`${x},${y}`,points.length);points.push({x,y,links:[]});}}
    const clear=(a,b)=>!boxes.some(r=>a.y===b.y?a.y>r.top&&a.y<r.bottom&&Math.max(a.x,b.x)>r.left&&Math.min(a.x,b.x)<r.right:a.x>r.left&&a.x<r.right&&Math.max(a.y,b.y)>r.top&&Math.min(a.y,b.y)<r.bottom);
    for(const group of [yy.map(y=>xx.map(x=>lookup.get(`${x},${y}`)).filter(i=>i!==undefined)),xx.map(x=>yy.map(y=>lookup.get(`${x},${y}`)).filter(i=>i!==undefined))]){
      for(const line of group)for(let j=1;j<line.length;j++){const a=line[j-1],b=line[j];if(clear(points[a],points[b])){const axis=points[a].y===points[b].y?0:1,weight=Math.abs(points[a].x-points[b].x)+Math.abs(points[a].y-points[b].y);points[a].links.push({to:b,axis,weight});points[b].links.push({to:a,axis,weight});}}
    }
    ports.forEach((list,id)=>ports.set(id,list.filter(p=>lookup.has(`${p.x},${p.y}`)).map(p=>({...p,index:lookup.get(`${p.x},${p.y}`)}))));
    const grid={points,ports,paths:new Map()};routingCache.set(c,grid);return grid;
  }
  function route(c,p){
    if(p[0])return p[0];
    const grid=routingGrid(c),key=`${p[2]}:${p[3]}:${p[1]}`;
    if(grid.paths.has(key))return grid.paths.get(key);
    const from=c.nodes.find(n=>n.id===p[2]),to=c.nodes.find(n=>n.id===p[3]);
    if(!from||!to)throw new Error(`${c.label}: unknown edge endpoint`);
    const preferred=p[1]==='request'?-12:p[1]==='data'?12:0;
    const penalty=(port,source,target)=>{const dot=port.vx*(target.x+target.w/2-source.x-source.w/2)+port.vy*(target.y+target.h/2-source.y-source.h/2);return (dot<0?55:dot===0?22:0)+(port.offset===preferred?0:8);};
    const dist=new Float64Array(grid.points.length*2).fill(Infinity),parents=new Int32Array(dist.length).fill(-1),seeds=new Map(),ends=new Map(),heap=[];
    const push=item=>{heap.push(item);let i=heap.length-1;while(i){const parent=(i-1)>>1;if(heap[parent].cost<=item.cost)break;heap[i]=heap[parent];i=parent;}heap[i]=item;};
    const pop=()=>{const first=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let j=i*2+1;if(j+1<heap.length&&heap[j+1].cost<heap[j].cost)j++;if(heap[j].cost>=last.cost)break;heap[i]=heap[j];i=j;}heap[i]=last;}return first;};
    for(const port of grid.ports.get(from.id)){const state=port.index*2+port.axis,cost=4+penalty(port,from,to);if(cost<dist[state]){dist[state]=cost;seeds.set(state,port);push({state,cost});}}
    for(const port of grid.ports.get(to.id)){const list=ends.get(port.index)||[];list.push(port);ends.set(port.index,list);}
    let best=Infinity,finish=null;
    while(heap.length){const {state,cost}=pop();if(cost!==dist[state])continue;if(cost>=best)break;const index=state>>1,axis=state%2;
      for(const port of ends.get(index)||[]){const total=cost+4+penalty(port,to,from)+(axis===port.axis?0:20);if(total<best){best=total;finish={state,port};}}
      for(const link of grid.points[index].links){const next=link.to*2+link.axis,value=cost+link.weight+(axis===link.axis?0:20);if(value<dist[next]){dist[next]=value;parents[next]=state;push({state:next,cost:value});}}
    }
    if(!finish)throw new Error(`${c.label}: cannot route ${from.id} → ${to.id}`);
    const coords=[];let cursor=finish.state;
    while(parents[cursor]!==-1){coords.push(grid.points[cursor>>1]);cursor=parents[cursor];}
    const start=seeds.get(cursor);coords.push(grid.points[cursor>>1],{x:start.ax,y:start.ay});coords.reverse();coords.push({x:finish.port.ax,y:finish.port.ay});
    const compact=coords.filter((point,i)=>i===0||i===coords.length-1||!((coords[i-1].x===point.x&&point.x===coords[i+1].x)||(coords[i-1].y===point.y&&point.y===coords[i+1].y)));
    const path=compact.map((point,i)=>`${i?'L':'M'}${point.x} ${point.y}`).join('');grid.paths.set(key,path);return path;
  }
  function markers(id,baseColor='#577568',size=8){
    const pixels=size*2;
    return [['',baseColor],...Object.entries(colors).map(([name,color])=>[`-${name}`,color])].map(([suffix,color])=>`<marker id="${id}${suffix}" markerUnits="userSpaceOnUse" markerWidth="${pixels}" markerHeight="${pixels}" refX="${pixels}" refY="${pixels/2}" orient="auto"><path d="M0 0L${pixels} ${pixels/2}L0 ${pixels}" fill="${color}"/></marker>`).join('');
  }
  function connections(c,id){
    return {incoming:c.paths.filter(p=>p[3]===id).map(edge=>({edge,node:c.nodes.find(n=>n.id===edge[2])})),outgoing:c.paths.filter(p=>p[2]===id).map(edge=>({edge,node:c.nodes.find(n=>n.id===edge[3])}))};
  }
  function apply(scope,c,id,focused=true){
    const edges=connections(c,id), up=new Set(edges.incoming.map(e=>e.node?.id)),down=new Set(edges.outgoing.map(e=>e.node?.id));
    scope.querySelectorAll('svg[data-connection-map]').forEach(svg=>{svg.classList.toggle('connection-focus',focused);});
    scope.querySelectorAll('[data-component]').forEach(el=>{
      const key=el.dataset.component, incoming=focused&&up.has(key)&&key!==id, outgoing=focused&&down.has(key)&&key!==id;
      el.classList.toggle('is-upstream',incoming);el.classList.toggle('is-downstream',outgoing);el.classList.toggle('is-both',incoming&&outgoing);
      el.classList.toggle('is-muted',focused&&key!==id&&!incoming&&!outgoing);
    });
    scope.querySelectorAll('[data-from][data-to]').forEach(el=>{
      const incoming=focused&&el.dataset.to===id,outgoing=focused&&el.dataset.from===id;
      el.classList.toggle('is-incoming',incoming);el.classList.toggle('is-outgoing',outgoing);el.classList.toggle('is-muted',focused&&!incoming&&!outgoing);
      const variant=incoming&&outgoing?'both':incoming?'incoming':outgoing?'outgoing':'';
      el.setAttribute('marker-end',`url(#${el.dataset.marker}${variant?'-'+variant:''})`);
    });
    return edges;
  }
  function html(c,id,attribute){
    const edgeGroups=connections(c,id);
    return `<div class="selected-connections" aria-label="Connections for selected component">${[['incoming','Receives from','upstream'],['outgoing','Sends to','downstream']].map(([key,title,direction])=>{
      const grouped=new Map();
      edgeGroups[key].filter(e=>e.node&&e.node.id!==id).forEach(({edge,node})=>{const item=grouped.get(node.id)||{node,labels:[]};item.labels.push(edge[4]||edge[1]);grouped.set(node.id,item);});
      return `<div class="connection-group ${key}"><span>${title} <b>${grouped.size}</b></span><div>${grouped.size?[...grouped.values()].map(({node,labels})=>`<button ${attribute}="${node.id}" aria-label="Select ${direction}: ${escape(node.title.replaceAll('|',' '))}"><strong>${escape(node.title.replaceAll('|',' '))}</strong><small>${escape([...new Set(labels)].join(' · '))}</small></button>`).join(''):`<p>${key==='incoming'?'Source / entry component':'Terminal component in this view'}</p>`}</div></div>`;
    }).join('')}</div>`;
  }
  function key(){return `<div class="connection-key" aria-label="Selection highlight colors"><span><i></i>Selected</span><span><i class="incoming"></i>Incoming</span><span><i class="outgoing"></i>Outgoing</span><span><i class="both"></i>Both directions</span></div>`;}
  function validate(c){
    const ids=new Set(c.nodes.map(n=>n.id));
    if(ids.size!==c.nodes.length)throw new Error(`${c.label}: duplicate component ID`);
    c.paths.forEach((p,i)=>{if(!ids.has(p[2])||!ids.has(p[3])||!p[4])throw new Error(`${c.label}: edge ${i+1} needs valid from/to IDs and a label`);});
    const connected=new Set(c.paths.flatMap(p=>[p[2],p[3]]));
    for(const id of ids)if(!connected.has(id))throw new Error(`${c.label}: disconnected component ${id}`);
  }
  window.diagramGraph={markers,connections,apply,html,validate,route,key};
})();
