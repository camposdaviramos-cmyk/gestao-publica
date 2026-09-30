'use strict';
let siconfiRows=[];
async function siconfiPage(){
 const d=await api(`/integrations/siconfi/reports?entity=${integrationState.entity}&exercise=${erpState.exercise}`);siconfiRows=d.items;
 openModal('Extrato Siconfi · agenda',notice('Confira a instituição antes de vincular. O extrato pode trazer Prefeitura e Câmara. Sincronizar atualiza o status externo; o encerramento da obrigação continua sob análise do responsável.')+`<div class="int-actions"><button class="button primary" data-action="sic-sync">Sincronizar extrato oficial</button></div><div class="int-history">${d.items.map(r=>`<article><strong>${esc(r.data.entregavel)} · ${r.data.exercicio} / ${r.data.periodo}</strong><p>${esc(r.data.instituicao)}</p><p>Status: ${esc(r.data.status_relatorio||'Não informado pelo Siconfi')} · ${date(r.data.data_status,true)}</p>${r.occurrence_id?`<small>Vinculado à ocorrência #${r.occurrence_id}</small>`:`<button class="button" data-action="sic-link" data-id="${r.id}">Vincular à agenda</button>`}</article>`).join('')||'<p>Nenhum extrato sincronizado neste exercício.</p>'}</div>`,'Dados oficiais · '+erpState.exercise);
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-action^="sic-"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();if(b.disabled)return;b.disabled=true;
 try{
  if(b.dataset.action==='sic-reports')await siconfiPage();
  if(b.dataset.action==='sic-sync'){const r=await api('/integrations/siconfi/sync','POST',{entity:Number(integrationState.entity)});erpState.exercise=r.exercise;toast(r.message);await siconfiPage();}
  if(b.dataset.action==='sic-link'){
   const r=siconfiRows.find(r=>r.id===Number(b.dataset.id));integrationState.siconfiReport=r;
   openModal('Vincular à agenda',`<form id="sic-search"><p>${esc(r.data.instituicao)} · ${esc(r.data.entregavel)} · ${r.data.periodo}/${r.data.exercicio}</p>${field('q','Buscar ocorrência por código ou título','','search')}<div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">Buscar ocorrências</button></div></form><div id="sic-results"></div>`);
  }
  if(b.dataset.action==='sic-confirm'){
   const r=integrationState.siconfiReport;const result=await api(`/integrations/siconfi/reports/${r.id}/link`,'PUT',{version:r.version,occurrence_id:Number(b.dataset.id),confirm_institution:r.data.instituicao});toast(result.message);await siconfiPage();
  }
 }catch(error){toast(error.message,true);}finally{b.disabled=false;}
},true);
document.addEventListener('submit',async e=>{
 if(e.target.id!=='sic-search')return;e.preventDefault();e.stopImmediatePropagation();const f=e.target,b=$('[type=submit]',f);if(b.disabled)return;b.disabled=true;
 try{const r=integrationState.siconfiReport,d=await api(`/erp/control/occurrences?entity=${integrationState.entity}&exercise=${r.exercise}&q=${encodeURIComponent(new FormData(f).get('q'))}&limit=100`);$('#sic-results').innerHTML=notice('Ao confirmar o vínculo, você declara que a instituição e o período do relatório correspondem à obrigação selecionada.')+d.items.map(o=>`<article class="int-source-row"><span>${esc(o.code)} · ${esc(o.name)} · ${date(o.data.due_date)}</span><button class="button" data-action="sic-confirm" data-id="${o.id}">Confirmar vínculo</button></article>`).join('')+(!d.items.length?notice('Nenhuma ocorrência encontrada.'):'');}
 catch(error){$('.form-error',f).textContent=error.message;}finally{b.disabled=false;}
},true);

const siconfiClear=clearAccount;clearAccount=function(){siconfiRows=[];siconfiClear();};
