'use strict';
let esocialCurrent=null;
function esocialContext(){return {entity:Number(integrationState.entity),environment:integrationState.environment};}
async function esocialList(){
 const c=esocialContext(),r=await api('/esocial/batches?'+new URLSearchParams(c));
 openModal('eSocial · eventos e recibos',notice('Ambiente: '+(c.environment==='producao'?'PRODUÇÃO':'Produção restrita / homologação')+'. Prepare XMLs S-1.3, revise com outro administrador e transmita. A aceitação de cada evento aparece após a consulta de processamento.')+'<div class="int-actions"><button class="button primary" data-action="eso-new">Preparar lote de eventos</button></div><div class="int-history">'+(r.items.map(i=>`<article><strong>Lote #${i.id} · ${esc(i.state)}</strong><p>Grupo ${i.group_number} · ${date(i.created_at,true)}</p><p>${esc(i.protocol||'Protocolo ainda não recebido')}</p><button class="button" data-action="eso-detail" data-id="${i.id}">Eventos e histórico</button></article>`).join('')||'<p>Nenhum lote preparado neste ambiente.</p>')+'</div>','Entidade selecionada · dados protegidos');
}
function esocialNew(){
 openModal('Preparar lote eSocial',`<form id="eso-prepare">${notice('Selecione de 1 a 50 XMLs individuais sem assinatura, do mesmo empregador, ambiente e grupo. Limite do painel: 700 KB somados. O certificado A1 configurado assinará os eventos após a validação nos esquemas oficiais.')}<label class="field"><span>Eventos XML S-1.3</span><input type="file" name="events" accept=".xml,application/xml,text/xml" multiple required><small>Grupos: 1 — tabelas; 2 — não periódicos; 3 — periódicos.</small></label><label class="check"><input type="checkbox" name="confirm" required>Conferi o empregador e o ambiente dos eventos.</label><div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">Validar e assinar lote</button></div></form>`,'Nenhum envio ocorre nesta etapa');
}
async function esocialDetail(id){
 const d=await api('/esocial/batches/'+id);esocialCurrent=d.item;const i=d.item,canWrite=can('people','write');
 let actions=`<button class="button" data-action="eso-download" data-kind="xml" data-id="${i.id}">Baixar XML assinado</button>`;
 if(Object.keys(i.response_summary).length)actions+=`<button class="button" data-action="eso-download" data-kind="response" data-id="${i.id}">Baixar retorno oficial</button>`;
 if(i.state==='Preparado'&&can('people','approve'))actions+='<button class="button primary" data-action="eso-approve">Aprovar revisão</button>';
 if(['Aprovado','Falha de conexão'].includes(i.state)&&canWrite)actions+='<button class="button primary" data-action="eso-send">Transmitir lote</button>';
 if(['Preparado','Aprovado','Falha de conexão'].includes(i.state)&&canWrite)actions+='<button class="button" data-action="eso-cancel">Cancelar lote</button>';
 if(['Recebido','Processando','Processado','Processado com ocorrências','Resultado incerto'].includes(i.state)&&canWrite)actions+='<button class="button" data-action="eso-query">Consultar processamento</button>';
 if(['Rejeitado','Processado com ocorrências'].includes(i.state)&&canWrite)actions+='<button class="button" data-action="eso-new">Preparar XMLs corrigidos</button>';
 if(i.state==='Enviando'&&canWrite)actions+='<button class="button" data-action="eso-recover">Registrar envio interrompido</button>';
 openModal('Lote eSocial #'+i.id,notice(i.state+' · '+(i.environment==='producao'?'PRODUÇÃO':'Homologação'))+`<p>${esc(i.last_message)}</p><p>Protocolo: <strong>${esc(i.protocol||'Aguardando recepção')}</strong></p><p class="int-digest">SHA-256: ${esc(i.xml_hash)}</p><div class="int-actions">${actions}</div><h3>Eventos</h3><div class="int-history">${d.events.map(e=>`<article><strong>${esc(e.event_type)}</strong><p class="int-digest">${esc(e.event_id)}</p><p>${esc(e.status)} · ${esc(e.response_code||'')} ${esc(e.description||'')}</p><p>Recibo: ${esc(e.receipt||'Ainda não recebido')}</p></article>`).join('')}</div><h3>Retornos preservados</h3><div class="int-actions">${d.responses.map(r=>`<button class="button" data-action="eso-response" data-id="${r.id}">${r.operation==='send'?'Recepção':'Processamento'} · ${esc(r.code)} · ${date(r.created_at,true)}</button>`).join('')||'<p>Nenhum retorno recebido.</p>'}</div><h3>Histórico</h3><div class="int-history">${d.history.map(h=>`<article><strong>${esc(h.action)}</strong><p>${esc(h.actor)} · ${date(h.created_at,true)}</p><p>${esc(JSON.parse(h.details).message||JSON.parse(h.details).reason||'')}</p></article>`).join('')}</div>`,'Grupo '+i.group_number+' · configuração versão '+i.config_version);
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-action^="eso-"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();if(b.disabled)return;b.disabled=true;
 try{
  const action=b.dataset.action;
  if(action==='eso-list')await esocialList();
  if(action==='eso-new')esocialNew();
  if(action==='eso-detail')await esocialDetail(b.dataset.id);
  if(action==='eso-response')await download('/esocial/responses/'+b.dataset.id+'/download');
  if(action==='eso-download')await download('/esocial/batches/'+b.dataset.id+'/download/'+b.dataset.kind);
  if(action==='eso-approve'||action==='eso-recover'){const r=await api('/esocial/batches/'+esocialCurrent.id+'/'+action.slice(4),'POST',{version:esocialCurrent.version});toast(r.message);await esocialDetail(esocialCurrent.id);}
  if(['eso-send','eso-cancel','eso-query'].includes(action)){
   const op=action.slice(4),i=esocialCurrent;
   const content=op==='send'?notice('O envio é uma operação externa. Digite '+(i.environment==='producao'?'ENVIAR PARA PRODUCAO':'ENVIAR PARA HOMOLOGACAO')+' para confirmar.')+field('confirmation','Confirmação de transmissão','','text','required autocomplete="off"'):op==='cancel'?textField('reason','Motivo do cancelamento','','required minlength="10" maxlength="1000"'):notice('A consulta preserva o XML e os recibos. O tempo de espera informado pelo serviço é respeitado.')+(i.protocol?'<p>Protocolo: '+esc(i.protocol)+'</p>':field('protocol','Protocolo localizado no portal eSocial','','text','required maxlength="23"'));
   openModal(op==='send'?'Transmitir ao eSocial':op==='cancel'?'Cancelar lote':'Consultar retorno',`<form id="eso-operation" data-operation="${op}" data-id="${i.id}" data-version="${i.version}">${content}<div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">${op==='send'?'Confirmar transmissão':op==='cancel'?'Confirmar cancelamento':'Consultar'}</button></div></form>`);
  }
 }catch(error){toast(error.message,true);}finally{b.disabled=false;}
},true);
document.addEventListener('submit',async e=>{
 const f=e.target;if(!f.id.startsWith('eso-'))return;e.preventDefault();e.stopImmediatePropagation();const b=$('[type=submit]',f);if(b.disabled)return;b.disabled=true;
 try{
  const fd=new FormData(f);
  if(f.id==='eso-prepare'){
   const files=[...f.elements.events.files];if(!files.length||files.length>50||files.reduce((n,x)=>n+x.size,0)>700000)throw new Error('Selecione de 1 a 50 XMLs, até 700 KB somados.');
   const events=await Promise.all(files.map(x=>x.text()));const r=await api('/esocial/batches','POST',{...esocialContext(),events});toast(r.message);await esocialDetail(r.id);
  }
  if(f.id==='eso-operation'){const r=await api('/esocial/batches/'+f.dataset.id+'/'+f.dataset.operation,'POST',{version:Number(f.dataset.version),...Object.fromEntries(fd)});toast(r.message,r.success===false);await esocialDetail(f.dataset.id);}
 }catch(error){$('.form-error',f).textContent=error.message;}finally{b.disabled=false;}
},true);
const clearEsocial=clearAccount;
clearAccount=function(){esocialCurrent=null;return clearEsocial();};
