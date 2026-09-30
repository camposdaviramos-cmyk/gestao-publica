document.addEventListener('click',async event=>{
 const el=event.target.closest('[data-action]');if(!el||el.disabled)return;
 const action=el.dataset.action,id=Number(el.dataset.id);const row=state.rows.find(x=>x.id===id);
 try{
  if(action==='theme'){theme=theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme;try{localStorage.setItem('rio-theme',theme);}catch{}$$('[data-action=theme]').forEach(b=>b.innerHTML=icon(theme==='dark'?'sun':'moon'));}
  else if(action==='close-modal')closeModal();
  else if(action==='menu'){$('.sidebar').classList.toggle('open');$('.scrim').classList.toggle('open');}
  else if(action==='refresh'||action==='overview')await route();
  else if(action==='help')helpModal();
  else if(action==='search')searchModal();
  else if(action==='notifications')await notificationsModal();
  else if(action==='read-notifications'){await api('/notifications/read','POST',{});closeModal();pollNotifications();toast('Notificações marcadas como lidas.');}
  else if(action==='profile')openModal('Minha conta',`<div class="row-title"><span class="avatar">${esc(initials(state.me.user.name))}</span><div><h3>${esc(state.me.user.name)}</h3><p class="muted" style="font-size:12px">${esc(state.me.user.email)}</p></div></div><div class="form-actions">${button('Alterar senha','password','lock')}${button('Sair da conta','logout','logout')}</div>`);
  else if(action==='password')passwordModal();
  else if(action==='logout'){await api('/logout','POST',{});clearAccount();closeModal();showAuth(false);}
  else if(action==='new-budget')recordModal('budget');
  else if(action==='new-record')recordModal(state.route);
  else if(action==='edit-record'&&row)recordModal(state.route,row);
  else if(action==='view-record'&&row)await viewRecord(row);
  else if(action==='delete-record'&&row)openModal('Excluir registro',`${notice(`Confirme a exclusão de <strong>${esc(row.title)}</strong>. ${state.me.settings.dual_modules.includes(state.route)?'A operação será enviada para aprovação.':'Esta operação remove o registro da base.'}`,true)}<form id="delete-form" data-id="${id}" data-version="${row.version}" data-module="${state.route}"><label class="check"><input type="checkbox" required>Conferi o registro e confirmo a exclusão.</label>${formActions('Confirmar exclusão','trash')}</form>`);
  else if(action==='prev'||action==='next'){state.page+=action==='prev'?-1:1;await route();}
  else if(action==='new-user')userModal();
  else if(action==='edit-user')userModal(state.users.find(r=>r.id===id));
  else if(action==='new-group')groupModal();
  else if(action==='edit-group')groupModal(state.groups.find(r=>r.id===id));
  else if(action==='view-approval')approvalModal(state.approvals.find(r=>r.id===id));
  else if(action==='module-report'){state.report={module:state.route,from:'',to:''};location.hash='#/reports';}
  else if(action==='dashboard-export'){state.report={module:can('budget')?'budget':Object.keys(state.me.modules).find(m=>can(m)),from:'',to:''};location.hash='#/reports';}
  else if(action.startsWith('export-')){if(!state.report?.module)throw new Error('Consulte um relatório primeiro.');el.disabled=true;await download(`/reports/${state.report.module}?${new URLSearchParams({format:action.slice(7),from:state.report.from,to:state.report.to})}`);toast('Arquivo gerado.');}
  else if(action==='print')window.print();
  else if(action==='lesson')lessonModal(el.dataset.id);
  else if(action==='complete-lesson'){await api(`/training/${el.dataset.id}/complete`,'POST',{});closeModal();toast('Tutorial concluído.');await route();}
  else if(action==='backup'){el.disabled=true;const result=await api('/backups','POST',{});toast(result.message);await route();}
  else if(action==='download-backup'){el.disabled=true;await download('/backups/'+encodeURIComponent(el.dataset.name));toast('Backup pronto para download.');}
  else if(action==='run-script'){el.disabled=true;const result=await api(`/maintenance/${id}/run`,'POST',{});openModal('Rotina concluída',notice(esc(result.message))+`<p style="font-size:12px">Resultado: ${esc(result.result.length?result.result.flat().join(', '):'Execução concluída sem erros.')}</p>`);}
  else if(action==='shortcuts')await shortcutsModal();
  else if(action==='delete-shortcut'){await api('/shortcuts/'+id,'DELETE');await shortcutsModal();}
  else if(action==='activity')openModal('Atividade recente',activitiesHtml(state.dashboard?.activities||[]),'Últimas operações visíveis para seu perfil');
 }catch(error){toast(error.message,true);}finally{if(el.isConnected)el.disabled=false;}
});

document.addEventListener('submit',async event=>{
 const form=event.target;if(!(form instanceof HTMLFormElement))return;event.preventDefault();
 const data=new FormData(form);const values=Object.fromEntries(data);const submit=$('[type=submit]',form);const error=$('.form-error',form);if(error)error.textContent='';if(submit)submit.disabled=true;
 try{
  if(form.id==='auth-form'){
   if(form.dataset.setup==='true')await api('/setup','POST',{name:values.name,email:values.email,password:values.password,demo:data.has('demo')});
   const result=await api('/login','POST',{email:values.email,password:values.password});state.csrf=result.csrf;await loadAccount();
  }
  else if(form.id==='record-form'){
   const module=form.dataset.module;const fields={};for(const key of Object.keys(state.me.modules[module].fields))fields[key]=values[key]||'';
   if(module==='tickets'&&form.dataset.id)fields.priority=form.dataset.priority;
   const body={title:values.title,department:values.department,status:values.status,amount:values.amount||0,data:fields};if(form.dataset.id)body.version=Number(form.dataset.version);
   const result=await api('/records/'+module+(form.dataset.id?'/'+form.dataset.id:''),form.dataset.id?'PUT':'POST',body);closeModal();toast(result.message);await route();
  }
  else if(form.id==='delete-form'){const result=await api(`/records/${form.dataset.module}/${form.dataset.id}?version=${form.dataset.version}`,'DELETE');closeModal();toast(result.message);await route();}
  else if(form.id==='search-form'){state.q=values.q;state.page=1;await route();}
  else if(form.id==='approval-form'){const result=await api(`/approvals/${form.dataset.id}/decide`,'POST',values);closeModal();toast(result.message);await route();}
  else if(form.id==='user-form'){
   const body={...values,group_id:Number(values.group_id),active:data.has('active'),force_password:data.has('force_password'),schedule:data.has('restrict_schedule')?{days:data.getAll('days').map(Number),start:values.start,end:values.end}:{},permissions:collectPermissions(form,true)};
   const result=await api('/users'+(form.dataset.id?'/'+form.dataset.id:''),form.dataset.id?'PUT':'POST',body);closeModal();toast(result.message);await route();
  }
  else if(form.id==='group-form'){const result=await api('/groups'+(form.dataset.id?'/'+form.dataset.id:''),form.dataset.id?'PUT':'POST',{name:values.name,permissions:collectPermissions(form)});closeModal();toast(result.message);await route();}
  else if(form.id==='settings-form'){
   const body={...values,signature_required:data.has('signature_required'),signature_reports:data.getAll('signature_reports'),dual_modules:data.getAll('dual_modules'),holidays:values.holidays.split(/\s+/).filter(Boolean)};
   for(const name of ['min_password','max_attempts','lock_minutes','session_minutes'])body[name]=Number(values[name]);
   const result=await api('/settings','PUT',body);state.me=await api('/me');state.csrf=state.me.csrf;shell();await route();toast(result.message);
  }
  else if(form.id==='report-form'){state.report=values;await renderReport();}
  else if(form.id==='password-form'){
   if(values.password!==values.confirm)throw new Error('A confirmação de senha não confere.');const result=await api('/password','POST',{current:values.current,password:values.password});clearAccount();closeModal();showAuth(false);toast(result.message);
  }
  else if(form.id==='shortcut-form'){const result=await api('/shortcuts','POST',values);toast(result.message);await shortcutsModal();}
  else if(form.id==='comment-form'){const result=await api(`/tickets/${form.dataset.id}/comments`,'POST',values);toast(result.message);await viewRecord(state.rows.find(r=>r.id===Number(form.dataset.id)));}
 }catch(e){if(error&&error.isConnected)error.textContent=e.message;else toast(e.message,true);}finally{if(submit?.isConnected)submit.disabled=false;}
});
document.addEventListener('change',event=>{if(event.target.id==='status-filter'){state.filter=event.target.value;state.page=1;route();}if(event.target.id==='requirement-status')filterRequirements();});
document.addEventListener('input',event=>{
 const el=event.target;
 if(el.id==='requirement-search')filterRequirements();
 if(el.id==='page-search'){$$('[data-page]').forEach(a=>a.hidden=!a.dataset.page.includes(el.value.toLocaleLowerCase('pt-BR')));}
 if(el.id==='public-search'){let found=0;$$('[data-search]').forEach(a=>{const matches=a.dataset.search.includes(el.value.toLocaleLowerCase('pt-BR'));a.hidden=!matches;if(matches)found++;});$('#public-empty').hidden=found>0;}
 if(el.name==='password'&&$('#strength-bar')){const p=el.value;const special=[...p].filter(c=>!/[\p{L}\p{N}]/u.test(c)).length;const mixed=/\p{L}/u.test(p)&&/\d/.test(p);const strong=p.length>10&&special>1&&mixed;const medium=p.length>8&&special&&mixed;$('#strength-bar').style.cssText=`width:${strong?100:medium?65:p?30:0}%;background:var(--${strong?'accent':medium?'amber':'red'})`;$('#strength-label').textContent='Força da senha: '+(strong?'Forte':medium?'Média':'Fraca');}
});
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'&&state.me){event.preventDefault();searchModal();}});
window.addEventListener('hashchange',()=>{if(modal.open)closeModal();route();});
modal.addEventListener('click',event=>{if(event.target===modal){const r=modal.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeModal();}});
async function loadAccount(){state.me=await api('/me');state.csrf=state.me.csrf;prepareERP();shell();if(state.me.user.force_password){$('#main').innerHTML=heading('Atualize sua senha','Defina uma nova senha para acessar seu ambiente de trabalho.',button('Alterar senha','password','lock','primary'));passwordModal(true);}else await route();}
async function start(){try{if(location.pathname==='/portal'){await publicPage();return;}const status=await api('/status');if(status.setup_required){showAuth(true);return;}try{await loadAccount();}catch{state.me=null;showAuth(false);}}catch(e){$('#app').innerHTML=`<div class="boot">${icon('info')}<strong>Não foi possível conectar</strong><p>${esc(e.message)}</p><a class="button" href="/">Tentar novamente</a></div>`;}}
setInterval(()=>{if(!document.hidden)pollNotifications();},30000);
start();
