'use strict';
function integrationObjectDetails(d){
 let html='';
 if(d.siconfi){const r=d.siconfi.data;html+=`<div class="form-section"><h3>Extrato oficial do Siconfi</h3><dl class="detail-grid"><div><dt>Instituição</dt><dd>${esc(r.instituicao)}</dd></div><div><dt>Declaração e período</dt><dd>${esc(r.entregavel)} · ${r.periodo}/${r.exercicio}</dd></div><div><dt>Status externo</dt><dd>${esc(r.status_relatorio||'Não informado pelo Siconfi')}</dd></div><div><dt>Última sincronização</dt><dd>${date(d.siconfi.updated_at,true)}</dd></div></dl><p class="muted">O status externo não encerra automaticamente a obrigação local.</p></div>`;}
 if(d.pncp){html+='<div class="form-section"><h3>Publicações PNCP</h3>'+d.pncp.map(j=>{
  const receipt=JSON.parse(j.receipt),url=receipt.location||'';let link='';
  if(/^https:\/\/(treina\.)?pncp\.gov\.br\/api\/pncp\/v1\/orgaos\/[A-Z0-9]{14}\/(compras|contratos)\/\d{4}\/\d+$/.test(url))link=`<a class="button" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Consultar recibo oficial ${icon('external')}</a>`;
  return `<article class="comment"><strong>${esc(j.state)} · ${intEnv(j.environment)}</strong><p>${date(j.updated_at,true)}</p>${link}${accessible('integrations')?intButton('Revisar pacote','job',`data-id="${j.id}"`):''}</article>`;
 }).join('')+(d.pncp.length?'':'<p class="muted">Nenhuma publicação preparada para este cadastro.</p>')+(accessible('integrations')&&can('procurement','write')?intButton('Preparar publicação no PNCP','prepare',`data-id="${d.item.id}"`):'')+'</div>';}
 return html;
}
