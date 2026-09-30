'use strict';
async function directoryBindings(){
 const [bindings,users]=await Promise.all([api('/integrations/ldap/bindings?entity='+integrationState.entity),api('/users')]);
 openModal('Usuários do diretório',notice('O usuário entra com o e-mail cadastrado no sistema e a senha do AD/LDAP. Não há fallback para senha local. Mantenha uma conta administrativa local para recuperação.')+`<form id="ent-binding"><div class="form-grid">${selectField('user_id','Conta local',users.items.filter(u=>u.id!==state.me.user.id).map(u=>[u.id,u.name+' · '+u.email]))}${field('login_name','Identidade no diretório','','text','required maxlength="200"')}</div><div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">Vincular conta</button></div></form><div class="int-history">${bindings.items.map(b=>`<article><strong>${esc(b.name)}</strong><p>${esc(b.email)} → ${esc(b.login_name)}</p><button class="button" data-action="ent-unbind" data-id="${b.user_id}">Remover vínculo</button></article>`).join('')||'<p>Nenhuma conta vinculada.</p>'}</div>`,'Entidade selecionada · LDAPS/StartTLS');
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-action^="ent-"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();if(b.disabled)return;b.disabled=true;
 try{
  if(b.dataset.action==='ent-bindings')await directoryBindings();
  if(b.dataset.action==='ent-unbind'){openModal('Remover autenticação LDAP',`<form id="ent-unbind" data-id="${b.dataset.id}">${notice('A conta voltará à autenticação local. Todas as sessões serão encerradas. Redefina a senha local antes de entregá-la ao usuário.')}<div class="form-actions"><button class="button primary" type="submit">Confirmar remoção</button></div><div class="form-error" role="alert"></div></form>`);}
  if(b.dataset.action==='ent-sign'){openModal('Assinar documento',`<form id="ent-sign" data-id="${b.dataset.id}" data-object="${b.dataset.object}">${notice('O arquivo será assinado com o certificado institucional desta entidade. O original e a versão assinada permanecerão preservados.')}<label class="check"><input name="confirm" type="checkbox" required>Conferi o documento e autorizo sua assinatura institucional.</label><div class="form-error" role="alert"></div><div class="form-actions"><button class="button primary" type="submit">Assinar documento</button></div></form>`);}
  if(b.dataset.action==='ent-download')await download('/signatures/'+b.dataset.id+'/download');
 }catch(error){toast(error.message,true);}finally{b.disabled=false;}
},true);
document.addEventListener('submit',async e=>{
 const f=e.target;if(!f.id.startsWith('ent-'))return;e.preventDefault();e.stopImmediatePropagation();const b=$('[type=submit]',f);if(b.disabled)return;b.disabled=true;
 try{const fd=new FormData(f);
  if(f.id==='ent-binding'){const r=await api('/integrations/ldap/bindings/'+fd.get('user_id'),'PUT',{entity:Number(integrationState.entity),login_name:fd.get('login_name')});toast(r.message);await directoryBindings();}
  if(f.id==='ent-unbind'){const r=await api('/integrations/ldap/bindings/'+f.dataset.id,'DELETE');toast(r.message);await directoryBindings();}
  if(f.id==='ent-sign'){const r=await api('/erp/attachments/'+f.dataset.id+'/sign','POST',{confirm:fd.get('confirm')==='on'});toast(r.message);await erpView(f.dataset.object);}
 }catch(error){$('.form-error',f).textContent=error.message;}finally{b.disabled=false;}
},true);
const enterpriseDetails=integrationObjectDetails;
integrationObjectDetails=function(d){let html=enterpriseDetails(d);if(d.attachments?.length&&can(d.item.module,'write'))html+='<div class="form-section"><h3>Assinatura institucional</h3><div class="int-actions">'+d.attachments.map(a=>`<button class="button" data-action="ent-sign" data-id="${a.id}" data-object="${d.item.id}">Assinar ${esc(a.name)}</button>`).join('')+'</div></div>';if(d.signatures?.length)html+='<div class="form-section"><h3>Versões assinadas</h3>'+d.signatures.map(s=>{const m=JSON.parse(s.metadata);return `<article class="comment"><strong>${esc(s.name)}</strong><p>${esc(m.profile)} · ${date(s.created_at,true)}</p><p class="int-digest">${esc(m.subject)}<br>SHA-256: ${esc(m.original_sha256)}</p><button class="button" data-action="ent-download" data-id="${s.id}">Baixar assinado</button></article>`;}).join('')+'</div>';return html;};
