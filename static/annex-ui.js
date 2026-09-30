'use strict';
/* ── Anexo III · Estado ─────────────────────────────────────────── */
const annexState={items:[],filtered:[],page:1,limit:50,q:'',module:'',status:'',view:'list'};
const annexNormalize=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const annexModuleNames={
 general:'Características gerais do sistema',
 cloud:'Provedor em nuvem (cloud computing)',
 finance:'Administração orçamentária, financeira e contabilidade',
 control:'Controle interno',
 people:'Gestão de recursos humanos',
 procurement:'Compras e contratos',
 auction:'Pregão eletrônico',
 inventory:'Gestão de estoque',
 assets:'Patrimônio',
 fleet:'Gestão de frotas',
 social:'Assistência social',
 works:'Obras públicas',
 bi:'Painel do gestor · BI',
 transparency:'Portal de transparência',
};
const annexStatusColor={
 'Implementado':'green',
 'Parcial':'amber',
 'Não implementado':'red',
 'Dependência externa':'',
 'Não comprovado':'amber',
};

/* ── Filtrar ─────────────────────────────────────────────────────── */
function annexFilter(){
 const q=annexNormalize(annexState.q).trim();
 annexState.filtered=annexState.items.filter(r=>(
  (!annexState.module||r.module===annexState.module)&&
  (!annexState.status||r.status===annexState.status)&&
  (!q||r.search.includes(q))
 ));
 const maxPage=Math.max(1,Math.ceil(annexState.filtered.length/annexState.limit));
 annexState.page=Math.min(annexState.page,maxPage);
}

/* ── Calcular estatísticas ───────────────────────────────────────── */
function annexStats(items){
 const counts={};
 for(const r of items) counts[r.status]=(counts[r.status]||0)+1;
 const total=items.length||1;
 const impl=counts['Implementado']||0;
 const parc=counts['Parcial']||0;
 const nImpl=counts['Não implementado']||0;
 const dep=counts['Dependência externa']||0;
 const unverified=counts['Não comprovado']||0;
 const pct=Math.round(impl/total*1000)/10;
 return {counts,total,impl,parc,nImpl,dep,unverified,pct};
}

/* ── Cards de estatísticas ───────────────────────────────────────── */
function annexStatsPanel(st){
 const statCard=(label,value,cls,desc)=>`<article class="stat annex-stat">
  <div class="stat-top"><span>${label}</span><span class="badge ${cls}">${value}</span></div>
  <div class="stat-value">${value}</div>
  <div class="stat-bottom">${icon('arrow')}${desc}</div>
 </article>`;
 return `<div class="stats annex-stats-grid">
  ${statCard('Implementado',st.impl,'green','Requisito atendido pela solução')}
  ${statCard('Parcial',st.parc,'amber','Atendimento incompleto ou com ressalvas')}
  ${statCard('Não implementado',st.nImpl,'red','Pendente de desenvolvimento')}
  ${statCard('Dependência externa',st.dep,'','Infraestrutura, nuvem ou integração')}
  ${statCard('Não comprovado',st.unverified,'amber','Validação de aceite ainda pendente')}
 </div>
 <section class="panel annex-progress-panel">
  <div class="panel-body annex-progress-body">
   <div class="annex-progress-header">
    <span><strong>Requisitos registrados como implementados</strong> · Sem crédito parcial; não equivale à aprovação da POC</span>
    <strong class="annex-pct">${st.pct}%</strong>
   </div>
   <div class="progress-track annex-track">
    <span style="width:${Math.round((st.impl/st.total)*100)}%;background:var(--accent)"></span>
    
   </div>
   <div class="annex-progress-legend">
    <span class="annex-leg annex-leg-impl">${number(st.impl)} implementados</span>
    <span class="annex-leg annex-leg-parc">${number(st.parc)} parciais</span>
    <span class="annex-leg annex-leg-no">${number(st.nImpl)} pendentes</span>
    <span class="annex-leg">${number(st.dep)} externos</span><span class="annex-leg">${number(st.unverified)} não comprovados</span>
   </div>
  </div>
 </section>`;
}

/* ── Painel por módulo ───────────────────────────────────────────── */
function annexModulePanel(items){
 const byModule={};
 for(const r of items){
  if(!byModule[r.module])byModule[r.module]={label:annexModuleNames[r.module]||r.module,impl:0,parc:0,nImpl:0,dep:0,unverified:0,total:0};
  byModule[r.module].total++;
  if(r.status==='Implementado')byModule[r.module].impl++;
  else if(r.status==='Parcial')byModule[r.module].parc++;
  else if(r.status==='Não implementado')byModule[r.module].nImpl++;
  else if(r.status==='Dependência externa')byModule[r.module].dep++;
  else byModule[r.module].unverified++;
 }
 const rows=Object.entries(byModule).map(([key,m])=>{
  const pct=Math.round(m.impl/m.total*1000)/10;
  const minimum=key==='cloud'?100:90;
  const color=pct>=minimum?'var(--accent)':'var(--amber)';
  return `<tr class="annex-mod-row" data-module="${key}" style="cursor:pointer">
   <td><strong>${esc(m.label)}</strong><small>${esc(key)}</small></td>
   <td><div class="progress-track" style="width:120px;height:6px"><span style="width:${pct}%;background:${color}"></span></div></td>
   <td class="mono" style="color:${color};font-weight:600">${pct}%</td>
   <td><span class="badge green">${m.impl}</span></td>
   <td><span class="badge amber">${m.parc}</span></td>
   <td><span class="badge red">${m.nImpl}</span></td>
   <td>${m.unverified}</td><td>${m.dep}</td><td class="mono">${m.total}</td>
   <td><button class="button small" data-action="ann-module" data-module="${key}">${icon('filter')}Filtrar</button></td>
  </tr>`;
 });
 return `<section class="panel" style="margin-bottom:22px">
  <div class="panel-head"><div><h2>Cobertura por área do edital</h2><p>Percentual sem crédito parcial. Mínimos do edital: 90% por módulo e gerais; 100% nuvem. A homologação depende dos testes de aceite.</p></div></div>
  <div class="table-wrap"><table>
   <thead><tr><th>ÁREA / MÓDULO</th><th>PROGRESSO</th><th>%</th><th>IMPLEMENTADO</th><th>PARCIAL</th><th>PENDENTE</th><th>NÃO COMPROVADO</th><th>EXTERNO</th><th>TOTAL</th><th></th></tr></thead>
   <tbody>${rows.join('')}</tbody>
  </table></div>
 </section>`;
}

/* ── Linhas de requisitos ────────────────────────────────────────── */
function annexRows(){
 const start=(annexState.page-1)*annexState.limit;
 const slice=annexState.filtered.slice(start,start+annexState.limit);
 if(!slice.length)return empty('Nenhum requisito encontrado','Ajuste a busca ou os filtros para ver os requisitos do Anexo III.');
 return slice.map(r=>`<details class="erp-requirement">
  <summary>
   <span class="annex-req-key">${esc(r.key)}</span>
   ${badge(r.status)}
   <span class="annex-req-module">${esc(annexModuleNames[r.module]||r.module)}</span>
   <span class="annex-req-page">Pág. ${r.page}</span>
  </summary>
  <div class="annex-req-body">
   <p class="erp-clause">${esc(r.text)}</p>
   <dl class="annex-dl">
    <dt>${icon('clock')}Situação anterior</dt><dd>${esc(r.before)||'—'}</dd>
    <dt>${icon('check')}Cobertura atual / pendências</dt><dd>${esc(r.coverage)||'—'}</dd>
   </dl>
  </div>
 </details>`).join('');
}

/* ── Paginação ───────────────────────────────────────────────────── */
function annexPagination(){
 const n=annexState.filtered.length,start=n?(annexState.page-1)*annexState.limit+1:0,end=Math.min(n,annexState.page*annexState.limit);
 return `<span aria-live="polite">${number(start)}–${number(end)} de ${number(n)} requisitos · página ${annexState.page}</span>
 <div>
  <button class="button small" data-action="ann-prev" ${annexState.page===1?'disabled':''}>Anterior</button>
  <button class="button small" data-action="ann-next" ${end>=n?'disabled':''}>Próxima</button>
 </div>`;
}

/* ── Render principal ────────────────────────────────────────────── */
function annexRender(){
 annexFilter();
 const list=$('#erp-annex-list');
 if(!list)return;
 list.innerHTML=annexRows();
 const pg=$('#annex-pagination');
 if(pg)pg.innerHTML=annexPagination();
}

/* ── Exportar CSV ────────────────────────────────────────────────── */
function annexExportCsv(){
 const items=annexState.filtered;
 const header=['Chave','Módulo','Item','Página PDF','Situação','Texto','Cobertura','Antes'];
 const rows=[header,...items.map(r=>[r.key,annexModuleNames[r.module]||r.module,r.item,r.page,r.status,r.text,r.coverage,r.before])];
 const csv=rows.map(r=>r.map(v=>'"'+String(v||'').replace(/"/g,'""')+'"').join(';')).join('\n');
 const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob);const a=document.createElement('a');
 a.href=url;a.download='anexo-iii-conformidade.csv';a.click();
 setTimeout(()=>URL.revokeObjectURL(url),10000);
 toast('Matriz exportada em CSV.');
}

function devPhasesCardHtml(){
 return `<aside class="dev-phases-card" aria-label="Fases de desenvolvimento">
  <div class="dev-phases-head">
   <div>
    <span class="dev-phases-eyebrow">Roteiro de execução</span>
    <h3 class="dev-phases-title">Fases de desenvolvimento</h3>
   </div>
   <div class="dev-phases-badge" title="Progresso geral: 75%">
    <span class="phase-current-label">Fase atual:</span>
    <strong class="phase-current-val">3/4</strong>
   </div>
  </div>
  <div class="dev-phases-bar" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">
   <span class="dev-phases-fill" style="width:75%"></span>
  </div>
  <ul class="dev-phases-list">
   <li class="dev-phase-item completed">
    <span class="phase-icon" aria-hidden="true">✓</span>
    <span class="phase-name"><strong>Fase 1:</strong> Estrutura</span>
    <span class="phase-tag completed">( Concluída )</span>
   </li>
   <li class="dev-phase-item completed">
    <span class="phase-icon" aria-hidden="true">✓</span>
    <span class="phase-name"><strong>Fase 2:</strong> Implementação</span>
    <span class="phase-tag completed">( Concluída )</span>
   </li>
   <li class="dev-phase-item active">
    <span class="phase-icon pulse" aria-hidden="true">●</span>
    <span class="phase-name"><strong>Fase 3:</strong> Auditoria &amp; correções</span>
    <span class="phase-tag active">( Em andamento )</span>
   </li>
   <li class="dev-phase-item pending">
    <span class="phase-icon" aria-hidden="true">○</span>
    <span class="phase-name"><strong>Fase 4:</strong> Relatório final</span>
    <span class="phase-tag pending">( Aguardando início )</span>
   </li>
  </ul>
 </aside>`;
}

/* ── Página principal ────────────────────────────────────────────── */
async function annexPage(){
 const d=await api('/erp/annex');
 annexState.items=d.items.map(r=>({...r,search:annexNormalize([r.key,r.module,r.text,r.status,r.coverage,r.before].join(' '))}));
 annexState.page=1;
 annexFilter();

 const st=annexStats(d.items);
 const modules=[...new Set(d.items.map(r=>r.module))];
 const statuses=[...new Set(d.items.map(r=>r.status))];

 const filterBar=`<section class="panel">
  <div class="toolbar">
   <form id="annex-search-form" class="input-search">
    ${icon('search')}
    <input id="erp-annex-search" name="q" aria-label="Buscar requisito" placeholder="Buscar código, texto ou cobertura…" value="${esc(annexState.q)}">
    <button class="icon-btn" type="submit" aria-label="Buscar">${icon('arrow')}</button>
   </form>
   <label class="field" style="margin:0;min-width:0">
    <select id="annex-module" class="control" aria-label="Filtrar por área" style="min-width:200px">
     <option value="">Todas as áreas</option>
     ${modules.map(m=>`<option value="${esc(m)}" ${annexState.module===m?'selected':''}>${esc(annexModuleNames[m]||m)}</option>`).join('')}
    </select>
   </label>
   <label class="field" style="margin:0;min-width:0">
    <select id="annex-status" class="control" aria-label="Filtrar por situação" style="min-width:175px">
     <option value="">Todas as situações</option>
     ${statuses.map(s=>`<option value="${esc(s)}" ${annexState.status===s?'selected':''}>${esc(s)}</option>`).join('')}
    </select>
   </label>
   <span class="count">${number(d.items.length)} requisitos</span>
   <button class="button" data-action="ann-csv" style="margin-left:auto">${icon('download')}Exportar CSV</button>
   <button class="button ${annexState.view==='modules'?'primary':''}" data-action="ann-view-modules" title="Visão por módulo">${icon('grid')}Por área</button>
   <button class="button ${annexState.view==='list'?'primary':''}" data-action="ann-view-list" title="Visão de lista">${icon('file')}Requisitos</button>
  </div>
 </section>`;

 const html=heading('Anexo III · Rastreabilidade de conformidade',
  'Requisitos extraídos do Edital PE 552/2026 e comparação com a implementação atual.',
  devPhasesCardHtml(),
  'PROVA DE CONCEITO')+
  notice(esc(d.note),true)+
  (d.audit?.ui_remediation?.items ? `<section class="panel" style="margin-bottom:22px" id="annex-remediation"><div class="panel-head"><div><h2>Andamento das correções prioritárias</h2><p>${esc(d.audit.ui_remediation.updated_at || '')} · Design e funcionamento das telas; aceite integral dos requisitos continua separado.</p></div></div><div class="table-wrap"><table><thead><tr><th>Módulo</th><th>Situação da entrega</th><th>Correções e evidências</th><th>Pendências</th></tr></thead><tbody>${d.audit.ui_remediation.items.map(row=>`<tr><td><strong>${esc(annexModuleNames[row.module] || row.module)}</strong></td><td><span class="badge green">${esc(row.status)}</span></td><td>${esc(row.completed)}</td><td>${esc(row.pending)}</td></tr>`).join('')}</tbody></table></div></section>` : '')+
  annexStatsPanel(st)+
  filterBar+
  (annexState.view==='modules'?annexModulePanel(d.items):`<div id="annex-module-panel"></div>`)+
  `<div id="annex-view-area">
   <section class="panel" style="margin-bottom:22px" id="annex-list-panel">
    <div class="panel-head"><div>
     <h2>Requisitos do Anexo III</h2>
     <p id="annex-list-subtitle">Exibindo todos os ${number(annexState.filtered.length)} requisitos filtrados</p>
    </div></div>
    <div id="erp-annex-list">${annexRows()}</div>
    <div class="pagination" id="annex-pagination">${annexPagination()}</div>
   </section>
  </div>`;

 return html;
}

/* ── Eventos ─────────────────────────────────────────────────────── */
document.addEventListener('input',e=>{
 if(e.target.id==='erp-annex-search'){annexState.q=e.target.value;annexState.page=1;annexRender();}
});
document.addEventListener('change',e=>{
 if(e.target.id==='annex-module'){annexState.module=e.target.value;annexState.page=1;annexRender();}
 if(e.target.id==='annex-status'){annexState.status=e.target.value;annexState.page=1;annexRender();}
});
document.addEventListener('submit',e=>{
 if(e.target.id==='annex-search-form'){e.preventDefault();e.stopPropagation();annexState.q=$('#erp-annex-search').value;annexState.page=1;annexRender();}
},true);
document.addEventListener('click',e=>{
 const b=e.target.closest('[data-action^="ann-"]');if(!b||b.disabled)return;
 e.preventDefault();e.stopImmediatePropagation();
 const action=b.dataset.action;
 if(action==='ann-next'){annexState.page++;annexRender();$('#erp-annex-list')?.scrollIntoView({block:'start'});}
 else if(action==='ann-prev'){annexState.page--;annexRender();$('#erp-annex-list')?.scrollIntoView({block:'start'});}
 else if(action==='ann-csv'){annexExportCsv();}
 else if(action==='ann-view-modules'){
  annexState.view='modules';
  const area=$('#annex-view-area');
  const mp=$('#annex-module-panel');
  if(area){
   const all=annexState.items;
   if(mp)mp.innerHTML=annexModulePanel(all);
   else if(area.previousElementSibling)area.previousElementSibling.insertAdjacentHTML('afterend',`<div id="annex-module-panel">${annexModulePanel(all)}</div>`);
  }
  $$('[data-action^="ann-view-"]').forEach(x=>x.classList.toggle('primary',x.dataset.action===action));
 }
 else if(action==='ann-view-list'){
  annexState.view='list';
  const mp=$('#annex-module-panel');
  if(mp)mp.innerHTML='';
  $$('[data-action^="ann-view-"]').forEach(x=>x.classList.toggle('primary',x.dataset.action===action));
 }
 else if(action==='ann-module'){
  const mod=b.dataset.module;
  annexState.module=mod;
  annexState.page=1;
  // Atualizar select
  const sel=$('#annex-module');
  if(sel)sel.value=mod;
  annexRender();
  // Scroll para lista
  $('#erp-annex-list')?.scrollIntoView({block:'start'});
 }
},true);

/* ── Integração com clearAccount ─────────────────────────────────── */
const _clearAnnex=clearAccount;
clearAccount=function(){
 Object.assign(annexState,{items:[],filtered:[],page:1,q:'',module:'',status:'',view:'list'});
 return _clearAnnex();
};
