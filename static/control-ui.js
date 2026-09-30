/* ── Controle Interno e Controladoria · Rio Gestão ────────────────── */
(function() {
    'use strict';

    let currentTab = 'calendar';
    let currentMonth = new Date().getMonth() + 1;
    let currentYear = 2026;
    let selectedSphere = '';
    let selectedStatus = '';
    let selectedDimension = '';
    let selectedPower = '';

    function esc(s) {
        if (!s) return '';
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function fmtMoney(cents) {
        if (!cents && cents !== 0) return 'R$ 0,00';
        return (Number(cents) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    async function loadNotifications() {
        try {
            const res = await api('/control/notifications?unread_only=true');
            const countEl = document.getElementById('control-notif-count');
            const listEl = document.getElementById('control-notif-list');
            if (countEl) {
                countEl.textContent = res.unread_count || 0;
                countEl.style.display = res.unread_count > 0 ? 'inline-block' : 'none';
            }
            if (listEl) {
                if (!res.notifications || !res.notifications.length) {
                    listEl.innerHTML = '<div style="padding:16px;text-align:center;color:var(--muted);font-size:12px;">Nenhuma notificação não lida.</div>';
                } else {
                    listEl.innerHTML = res.notifications.map(n => `
                        <button type="button" class="control-notif-item unread" data-module-click="control-46" data-arg0="${ModulesUI.escape(n.id)}">
                            <div class="title">${esc(n.title)}</button>
                            <div class="msg">${esc(n.message)}</div>
                            <div class="time">${n.created_at}</div>
                        </div>
                    `).join('');
                }
            }
        } catch (e) {
            console.error('Erro ao carregar notificações:', e);
        }
    }

    window.toggleControlNotifications = function() {
        const dd = document.getElementById('control-notif-dropdown');
        if (dd) dd.classList.toggle('open');
    };

    window.markNotificationRead = async function(id) {
        try {
            await api(`/control/notifications/${id}/read`, 'PUT', {});
            loadNotifications();
        } catch (e) {
            toast(e.message, true);
        }
    };

    window.switchControlTab = async function(tab) {
        currentTab = tab;
        document.querySelectorAll('.control-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        const container = document.getElementById('control-tab-content');
        if (!container) return;
        container.innerHTML = '<div class="loading-panel"><div class="loader"></div>Carregando dados...</div>';

        if (tab === 'calendar') await renderCalendarTab(container);
        else if (tab === 'siconfi') await renderSiconfiTab(container);
        else if (tab === 'cauc') await renderCaucTab(container);
        else if (tab === 'agreements') await renderAgreementsTab(container);
        else if (tab === 'plans') await renderPlansTab(container);
        else if (tab === 'reports') await renderReportsTab(container);
        else if (tab === 'ibge') await renderIbgeTab(container);
    };

    // ── 1. Calendário de Obrigações ──────────────────────────────────────
    async function renderCalendarTab(container) {
        const [sumRes, calRes] = await Promise.all([
            api('/control/obligations/summary?entity=1&exercise=2026'),
            api(`/control/calendar?entity=1&exercise=2026&month=${currentMonth}${selectedSphere ? '&sphere='+selectedSphere : ''}${selectedStatus ? '&status='+selectedStatus : ''}`)
        ]);

        const s = sumRes.summary;
        const events = calRes.events;

        let html = `
            <div class="control-kpi-grid">
                <div class="control-kpi-card">
                    <div class="label">Total de Obrigações</div>
                    <div class="value">${s.total}</div>
                    <div class="sub">No exercício 2026</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Atendidas / Cumpridas</div>
                    <div class="value" style="color:#10b981;">${s.attended}</div>
                    <div class="sub">${s.compliance_rate}% de conformidade</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">A Vencer (Próximos 15 dias)</div>
                    <div class="value" style="color:#f59e0b;">${s.due_soon_15_days}</div>
                    <div class="sub">Acompanhamento contínuo</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Vencidas / Em Atraso</div>
                    <div class="value" style="color:#ef4444;">${s.overdue}</div>
                    <div class="sub">Exigem justificativa formal</div>
                </div>
            </div>

            <div class="control-calendar-wrap">
                <div class="control-calendar-toolbar">
                    <div class="control-calendar-filters">
                        <select id="ctrl-month-select" data-module-change="control-47" >
                            ${['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'].map((m, i) => `
                                <option value="${i+1}" ${currentMonth === i+1 ? 'selected' : ''}>${m} / 2026</option>
                            `).join('')}
                        </select>
                        <select id="ctrl-sphere-select" data-module-change="control-48" >
                            <option value="">Todas as Esferas</option>
                            <option value="Federal" ${selectedSphere==='Federal'?'selected':''}>Federal</option>
                            <option value="Estadual" ${selectedSphere==='Estadual'?'selected':''}>Estadual</option>
                            <option value="Municipal" ${selectedSphere==='Municipal'?'selected':''}>Municipal</option>
                        </select>
                        <button class="button small" data-module-click="control-49" >Carga Automática de Obrigações</button>
                    </div>
                    <div class="control-calendar-legend">
                        <span><span class="legend-dot" style="background:#10b981;"></span>Atendida</span>
                        <span><span class="legend-dot" style="background:#f59e0b;"></span>A Vencer</span>
                        <span><span class="legend-dot" style="background:#ef4444;"></span>Vencida</span>
                    </div>
                </div>

                <div class="control-calendar-grid">
                    ${['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'].map(d => `<div class="calendar-day-header">${d}</div>`).join('')}
                    ${buildCalendarCells(currentYear, currentMonth, events)}
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    function buildCalendarCells(year, month, events) {
        const firstDayIndex = new Date(year, month - 1, 1).getDay();
        const daysInMonth = new Date(year, month, 0).getDate();
        let cells = '';

        for (let i = 0; i < firstDayIndex; i++) {
            cells += `<div class="calendar-day-cell other-month"></div>`;
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayEvents = events.filter(e => e.due_date === dateStr);

            cells += `
                <div class="calendar-day-cell">
                    <span class="day-num">${day}</span>
                    ${dayEvents.map(e => `
                        <button type="button" class="calendar-event-chip" style="background:${e.color};" data-module-click="control-50" data-arg0="${ModulesUI.escape(e.id)}" title="${esc(e.title)} (${e.status})">
                            ${esc(e.obligation_code)}: ${esc(e.title)}
                        </button>
                    `).join('')}
                </div>
            `;
        }
        return cells;
    }

    window.changeCalendarMonth = function(m) {
        currentMonth = parseInt(m, 10);
        switchControlTab('calendar');
    };

    window.changeCalendarSphere = function(s) {
        selectedSphere = s;
        switchControlTab('calendar');
    };

    window.loadDefaultObligations = async function() {
        if (!confirm('Deseja executar a carga automática das obrigações legais federais, estaduais e municipais?')) return;
        try {
            const res = await api('/control/obligations/load-defaults', 'POST', { entity: 1, exercise: 2026 });
            toast(res.message);
            switchControlTab('calendar');
        } catch (e) {
            toast(e.message, true);
        }
    };

    // ── Modal de Detalhe da Ocorrência & Acompanhamentos ─────────────────
    window.openOccurrenceModal = async function(id) {
        try {
            const res = await api(`/control/occurrences/${id}`);
            const o = res.occurrence;

            let html = `
                <div style="margin-bottom:16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <h3 style="margin:0;font-size:16px;">${esc(o.title)}</h3>
                        <span class="badge ${o.status==='Atendida'?'badge-success':o.status==='Vencida'?'badge-danger':'badge-warning'}">${o.status}</span>
                    </div>
                    <p style="color:var(--muted);font-size:12px;margin:4px 0;"><strong>Código:</strong> ${esc(o.obligation_code)} · <strong>Esfera:</strong> ${esc(o.legislation_type)} · <strong>Assunto:</strong> ${esc(o.subject_group)}</p>
                    <p style="color:var(--muted);font-size:12px;margin:4px 0;"><strong>Vencimento:</strong> ${o.due_date} · <strong>Responsável:</strong> ${esc(o.owner_name)} (${esc(o.owner_email||'—')})</p>
                    <p style="font-size:12px;margin:8px 0;background:var(--surface);padding:8px;border-radius:6px;border:1px solid var(--line);">${esc(o.obligation_description)}</p>
                    ${o.delay_justification ? `<div style="background:rgba(239,68,68,0.08);border-left:3px solid #ef4444;padding:8px;font-size:12px;margin:8px 0;"><strong>Justificativa de Atraso:</strong> ${esc(o.delay_justification)}</div>` : ''}
                </div>

                <div class="form-section">
                    <h4>Ações Rápidas</h4>
                    <div style="display:flex;gap:10px;flex-wrap:wrap;margin:10px 0;">
                        ${o.status !== 'Atendida' ? `<button class="button primary small" data-module-click="control-51" data-arg0="${ModulesUI.escape(o.id)}">Encerramento Rápido</button>` : ''}
                        <button class="button small" data-module-click="control-52" data-arg0="${ModulesUI.escape(o.id)}" data-arg1="${ModulesUI.escape(o.owner_email)}">Enviar E-mail ao Responsável</button>
                        <button class="button small" data-module-click="control-53" data-arg0="${ModulesUI.escape(o.id)}">Inserir Acompanhamento / Justificativa</button>
                    </div>
                    <div id="occ-action-subform" style="margin-top:12px;"></div>
                </div>

                <div class="form-section">
                    <h4>Histórico de Acompanhamentos (${o.followups.length})</h4>
                    <div style="max-height:220px;overflow-y:auto;margin-top:8px;">
                        ${!o.followups.length ? '<p style="color:var(--muted);font-size:12px;">Nenhum acompanhamento registrado.</p>' : o.followups.map(f => `
                            <div class="comment" style="margin-bottom:8px;">
                                <strong>${esc(f.type)} · ${esc(f.author_name)}</strong>
                                <time>${f.created_at}</time>
                                <p style="white-space:pre-wrap;font-size:12px;margin-top:4px;">${esc(f.notes)}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            openModal(`Ocorrência #${o.id} - ${o.obligation_code}`, html);
        } catch (e) {
            toast(e.message, true);
        }
    };

    window.quickCloseOccurrence = async function(id) {
        if (!confirm('Deseja registrar o encerramento rápido desta ocorrência de obrigação?')) return;
        try {
            await api(`/control/occurrences/${id}/quick-close`, 'POST', { notes: 'Encerramento rápido homologado pelo Controle Interno.' });
            toast('Ocorrência encerrada com sucesso!');
            closeModal();
            switchControlTab('calendar');
        } catch (e) {
            toast(e.message, true);
        }
    };

    window.showEmailForm = function(id, defaultEmail) {
        const sub = document.getElementById('occ-action-subform');
        if (!sub) return;
        sub.innerHTML = `
            <div style="background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px;">
                <h5>Comunicação com o Responsável por E-mail</h5>
                <div class="form-grid" style="margin-top:8px;">
                    <label class="field"><span>Destinatário</span><input type="email" id="email-recip" value="${defaultEmail||''}" required></label>
                    <label class="field"><span>Assunto</span><input type="text" id="email-subject" value="Cobrança / Instruções sobre Obrigação Legal" required></label>
                    <label class="field full"><span>Instruções Livres para o Operador</span><textarea id="email-body" rows="3" placeholder="Escreva as instruções para atendimento desta ocorrência..." required></textarea></label>
                </div>
                <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;">
                    <button class="button small" data-module-click="control-54" >Cancelar</button>
                    <button class="button primary small" data-module-click="control-55" data-arg0="${ModulesUI.escape(id)}">Enviar e Anexar ao Histórico</button>
                </div>
            </div>
        `;
    };

    window.submitSendEmail = async function(id) {
        const recip = document.getElementById('email-recip').value;
        const subj = document.getElementById('email-subject').value;
        const body = document.getElementById('email-body').value;
        if (!recip || !body) {
            toast('Preencha o e-mail e a mensagem.', true);
            return;
        }
        try {
            const res = await api(`/control/occurrences/${id}/send-email`, 'POST', {
                recipient_email: recip,
                subject: subj,
                message_body: body
            });
            toast(res.message);
            openOccurrenceModal(id);
        } catch (e) {
            toast(e.message, true);
        }
    };

    window.showFollowupForm = function(id) {
        const sub = document.getElementById('occ-action-subform');
        if (!sub) return;
        sub.innerHTML = `
            <div style="background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px;">
                <h5>Novo Acompanhamento / Justificativa</h5>
                <div class="form-grid" style="margin-top:8px;">
                    <label class="field"><span>Tipo</span>
                        <select id="followup-type">
                            <option value="Comentário">Comentário</option>
                            <option value="Justificativa">Justificativa de Atraso</option>
                            <option value="Encerramento">Encerramento Formal</option>
                            <option value="Reabertura">Reabertura de Ocorrência</option>
                        </select>
                    </label>
                    <label class="field full"><span>Descrição / Parecer Técnico</span><textarea id="followup-notes" rows="3" placeholder="Detalhes do acompanhamento..." required></textarea></label>
                </div>
                <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;">
                    <button class="button small" data-module-click="control-56" >Cancelar</button>
                    <button class="button primary small" data-module-click="control-57" data-arg0="${ModulesUI.escape(id)}">Salvar Acompanhamento</button>
                </div>
            </div>
        `;
    };

    window.submitFollowup = async function(id) {
        const type = document.getElementById('followup-type').value;
        const notes = document.getElementById('followup-notes').value;
        if (!notes) {
            toast('Descrição é obrigatória.', true);
            return;
        }
        try {
            await api(`/control/occurrences/${id}/followup`, 'POST', { type, notes });
            toast('Acompanhamento registrado com sucesso!');
            openOccurrenceModal(id);
        } catch (e) {
            toast(e.message, true);
        }
    };

    // ── 2. Ranking SICONFI & STN ─────────────────────────────────────────
    async function renderSiconfiTab(container) {
        const res = await api(`/control/siconfi/ranking?entity=1&exercise=2026${selectedDimension?'&dimension='+selectedDimension:''}${selectedPower?'&power='+selectedPower:''}`);
        const d = res.data;

        let html = `
            <div class="control-kpi-grid">
                <div class="control-kpi-card">
                    <div class="label">Índice Geral de Qualidade STN</div>
                    <div class="value" style="color:#10b981;">${d.quality_score_pct}%</div>
                    <div class="sub">Ranking da Informação Contábil e Fiscal</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Regras em Conformidade</div>
                    <div class="value" style="color:#10b981;">${d.conforming_count}</div>
                    <div class="sub">Validadas na MSC do exercício</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Itens Não Conformes</div>
                    <div class="value" style="color:#ef4444;">${d.non_conforming_count}</div>
                    <div class="sub">Com Plano de Ação sugerido</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Total de Regras Ativas</div>
                    <div class="value">${d.total_rules}</div>
                    <div class="sub">Dimensões 1, 2, 3 e 4</div>
                </div>
            </div>

            <div class="control-siconfi-charts">
                <div class="siconfi-chart-card">
                    <h3>Dimensão 2 · Informações Contábeis</h3>
                    <p style="color:var(--muted);font-size:12px;margin:0 0 10px 0;">Balanço Patrimonial, DDR, VPA x VPD e ausência de contas invertidas.</p>
                    <div class="progress-bar-wrap">
                        <div class="progress-bar-green" style="width:${(d.dimension_2_chart.conforming/d.dimension_2_chart.total*100)||0}%;"></div>
                    </div>
                    <div class="chart-stats-row">
                        <span style="color:#10b981;"><b>${d.dimension_2_chart.conforming}</b> Em Conformidade</span>
                        <span style="color:#ef4444;"><b>${d.dimension_2_chart.non_conforming}</b> Não Conforme</span>
                    </div>
                </div>

                <div class="siconfi-chart-card">
                    <h3>Dimensão 3 · Informações Fiscais</h3>
                    <p style="color:var(--muted);font-size:12px;margin:0 0 10px 0;">Limites LRF (Pessoal 54%), MDE Educação 25%, ASPS Saúde 15% e Art. 42 LRF.</p>
                    <div class="progress-bar-wrap">
                        <div class="progress-bar-green" style="width:${(d.dimension_3_chart.conforming/d.dimension_3_chart.total*100)||0}%;"></div>
                    </div>
                    <div class="chart-stats-row">
                        <span style="color:#10b981;"><b>${d.dimension_3_chart.conforming}</b> Em Conformidade</span>
                        <span style="color:#ef4444;"><b>${d.dimension_3_chart.non_conforming}</b> Não Conforme</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="toolbar">
                    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                        <select data-module-change="control-58" >
                            <option value="">Todas as Dimensões</option>
                            <option value="2" ${selectedDimension==='2'?'selected':''}>Dimensão 2 (Contábil)</option>
                            <option value="3" ${selectedDimension==='3'?'selected':''}>Dimensão 3 (Fiscal)</option>
                            <option value="1" ${selectedDimension==='1'?'selected':''}>Dimensão 1 (Gestão)</option>
                            <option value="4" ${selectedDimension==='4'?'selected':''}>Dimensão 4 (Contábil x Fiscal)</option>
                        </select>
                        <select data-module-change="control-59" >
                            <option value="">Poder Executivo e Legislativo</option>
                            <option value="Executivo" ${selectedPower==='Executivo'?'selected':''}>Poder Executivo</option>
                            <option value="Legislativo" ${selectedPower==='Legislativo'?'selected':''}>Poder Legislativo</option>
                        </select>
                        <button class="button small" data-module-click="control-60" >Reprocessar Competência</button>
                        <button class="button small primary" data-module-click="control-61" >Nova Regra Específica</button>
                    </div>
                    <div style="font-size:11px;color:var(--muted);">
                        Legenda: <span style="color:#10b981;font-weight:700;">Verde = Conforme</span> · <span style="color:#ef4444;font-weight:700;">Vermelho = Não Conforme</span>
                    </div>
                </div>

                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>CÓDIGO</th>
                                <th>DIMENSÃO</th>
                                <th>DESCRIÇÃO DA VERIFICAÇÃO</th>
                                <th>INTERVALO</th>
                                <th>APURAÇÃO</th>
                                <th>SITUAÇÃO</th>
                                <th>AÇÕES</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${d.items.map(r => `
                                <tr>
                                    <td><b>${esc(r.rule_code)}</b></td>
                                    <td>Dimensão ${r.dimension} (${esc(r.power)})</td>
                                    <td>
                                        <strong>${esc(r.title)}</strong>
                                        <div style="font-size:11px;color:var(--muted);">${esc(r.description)}</div>
                                    </td>
                                    <td>${esc(r.interval_type)}</td>
                                    <td><small>${esc(r.verified_value||'Regular')}</small></td>
                                    <td>
                                        <span class="control-status-badge ${r.status==='Conforme'?'badge-conforme':'badge-nao-conforme'}">
                                            ${r.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div style="display:flex;gap:4px;">
                                            <button class="button small" data-module-click="control-62" data-arg0="${ModulesUI.escape(r.id)}" data-arg1="${ModulesUI.escape(r.rule_code)}" title="Duplicar regra">Duplicar</button>
                                            ${r.status === 'Não Conforme' ? `
                                                <button class="button small primary" data-module-click="control-63" data-arg0="${ModulesUI.escape(r.rule_code)}" data-arg1="${ModulesUI.escape(r.title)}">Plano de Ação</button>
                                            ` : ''}
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    window.changeSiconfiDimension = function(d) {
        selectedDimension = d;
        switchControlTab('siconfi');
    };

    window.changeSiconfiPower = function(p) {
        selectedPower = p;
        switchControlTab('siconfi');
    };

    window.reprocessSiconfiPeriod = async function() {
        if (!confirm('Deseja excluir a competência atual e reprocessar todas as validações com a base de regras vigentes?')) return;
        try {
            const res = await api('/control/siconfi/reprocess', 'POST', { entity: 1, exercise: 2026, period: '2026-01', delete_first: true });
            toast(res.message);
            switchControlTab('siconfi');
        } catch (e) {
            toast(e.message, true);
        }
    };

    window.duplicateSiconfiRule = async function(ruleId, ruleCode) {
        const newCode = prompt(`Informe o novo código para a regra duplicada a partir de ${ruleCode}:`, `${ruleCode}-V2`);
        if (!newCode) return;
        try {
            const res = await api('/control/siconfi/rules', 'POST', { action: 'duplicate', rule_id: ruleId, new_code: newCode });
            toast(res.message);
            switchControlTab('siconfi');
        } catch (e) {
            toast(e.message, true);
        }
    };

    window.openNewRuleModal = function() {
        openModal('Criar Regra Específica do SICONFI', `
            <form id="new-rule-form">
                <div class="form-grid">
                    <label class="field"><span>Código da Regra *</span><input type="text" id="nr-code" placeholder="Ex: STN-D2-CUSTOM" required></label>
                    <label class="field"><span>Título *</span><input type="text" id="nr-title" placeholder="Descrição suscinta da validação" required></label>
                    <label class="field"><span>Dimensão</span>
                        <select id="nr-dim">
                            <option value="2">Dimensão 2 (Contábil)</option>
                            <option value="3">Dimensão 3 (Fiscal)</option>
                            <option value="1">Dimensão 1 (Gestão)</option>
                            <option value="4">Dimensão 4 (Contábil x Fiscal)</option>
                        </select>
                    </label>
                    <label class="field"><span>Poder</span>
                        <select id="nr-power">
                            <option value="Executivo">Poder Executivo</option>
                            <option value="Legislativo">Poder Legislativo</option>
                        </select>
                    </label>
                    <label class="field full"><span>Detalhamento da Regra</span><textarea id="nr-desc" rows="2" placeholder="Critérios técnicos de validação"></textarea></label>
                </div>
                <div class="form-actions">
                    <button class="button primary" type="submit">Salvar Regra</button>
                </div>
            </form>
        `);
        document.getElementById('new-rule-form').onsubmit = async function(e) {
            e.preventDefault();
            try {
                await api('/control/siconfi/rules', 'POST', {
                    action: 'create',
                    rule_code: document.getElementById('nr-code').value,
                    title: document.getElementById('nr-title').value,
                    dimension: document.getElementById('nr-dim').value,
                    power: document.getElementById('nr-power').value,
                    description: document.getElementById('nr-desc').value
                });
                toast('Regra criada com sucesso!');
                closeModal();
                switchControlTab('siconfi');
            } catch (err) {
                toast(err.message, true);
            }
        };
    };

    // ── 3. Requisitos Fiscais do CAUC ───────────────────────────────────
    async function renderCaucTab(container) {
        const res = await api('/control/cauc?entity=1');
        const d = res.data;

        let html = `
            <div class="control-kpi-grid">
                <div class="control-kpi-card">
                    <div class="label">Taxa de Regularidade CAUC</div>
                    <div class="value" style="color:#10b981;">${d.regularity_rate}%</div>
                    <div class="sub">Cadastro Único de Convênios da STN</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Requisitos Adimplentes</div>
                    <div class="value" style="color:#10b981;">${d.adimplente_count}</div>
                    <div class="sub">Certidões válidas</div>
                </div>
                <div class="control-kpi-card">
                    <div class="label">Requisitos Inadimplentes</div>
                    <div class="value" style="color:#ef4444;">${d.inadimplente_count}</div>
                    <div class="sub">Pendências fiscais</div>
                </div>
            </div>

            <div class="panel">
                <div class="toolbar">
                    <span style="font-weight:700;color:var(--ink);">Requisitos Fiscais do CAUC (STN)</span>
                    <span class="muted" style="font-size:11px;">Identificação visual de cor (Verde = Adimplente, Vermelho = Inadimplente)</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>CÓDIGO</th>
                                <th>GRUPO DE REQUISITO</th>
                                <th>DESCRIÇÃO DO REQUISITO FISCAL</th>
                                <th>SITUAÇÃO</th>
                                <th>RESPONSÁVEL</th>
                                <th>VALIDADE</th>
                                <th>AÇÕES</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${d.items.map(it => `
                                <tr>
                                    <td><b>${esc(it.code)}</b></td>
                                    <td><small>${esc(it.group_name)}</small></td>
                                    <td>
                                        <strong>${esc(it.name)}</strong>
                                        <div style="font-size:11px;color:var(--muted);">${esc(it.description)}</div>
                                    </td>
                                    <td>
                                        <span class="control-status-badge ${it.status==='Adimplente'?'badge-conforme':'badge-nao-conforme'}">
                                            ${it.status}
                                        </span>
                                    </td>
                                    <td>
                                        ${esc(it.responsible_name)}
                                        <div style="font-size:10px;color:var(--muted);">${esc(it.responsible_email||'')}</div>
                                    </td>
                                    <td><small>${it.valid_until||'Contínuo'}</small></td>
                                    <td>
                                        <div style="display:flex;gap:4px;">
                                            <button class="button small" data-module-click="control-64" data-arg0="${ModulesUI.escape(it.code)}" data-arg1="${ModulesUI.escape(it.responsible_name)}" data-arg2="${ModulesUI.escape(it.responsible_email)}">Responsável</button>
                                            ${it.status !== 'Adimplente' ? `
                                                <button class="button small primary" data-module-click="control-65" data-arg0="${ModulesUI.escape(it.code)}" data-arg1="${ModulesUI.escape(it.name)}">Plano de Ação</button>
                                            ` : ''}
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    window.openCaucRespModal = function(code, name, email) {
        openModal(`Vincular Responsável ao Item ${code}`, `
            <form id="cauc-resp-form">
                <div class="form-grid">
                    <label class="field"><span>Nome do Responsável *</span><input type="text" id="cr-name" value="${name||''}" required></label>
                    <label class="field"><span>E-mail Institucional *</span><input type="email" id="cr-email" value="${email||''}" required></label>
                </div>
                <div class="form-actions">
                    <button class="button primary" type="submit">Salvar Responsável</button>
                </div>
            </form>
        `);
        document.getElementById('cauc-resp-form').onsubmit = async function(e) {
            e.preventDefault();
            try {
                await api('/control/cauc/responsible', 'PUT', {
                    code: code,
                    responsible_name: document.getElementById('cr-name').value,
                    responsible_email: document.getElementById('cr-email').value
                });
                toast('Responsável atualizado com sucesso!');
                closeModal();
                switchControlTab('cauc');
            } catch (err) {
                toast(err.message, true);
            }
        };
    };

    // ── 4. Convênios da STN ──────────────────────────────────────────────
    async function renderAgreementsTab(container) {
        const res = await api('/control/agreements?entity=1&exercise=2026');
        const d = res.data;

        let html = `
            <div class="panel">
                <div class="toolbar">
                    <span style="font-weight:700;color:var(--ink);">Extrato de Convênios da STN (Transferegov / SICONV)</span>
                    <span class="muted" style="font-size:11px;">Identificação de cor: Verde para Adimplente, Vermelho para Inadimplente</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>CONVÊNIO</th>
                                <th>CONCEDENTE</th>
                                <th>OBJETO DO CONVÊNIO</th>
                                <th>VALOR GLOBAL</th>
                                <th>VIGÊNCIA</th>
                                <th>SITUAÇÃO</th>
                                <th>RESPONSÁVEL</th>
                                <th>AÇÕES</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${d.items.map(a => `
                                <tr>
                                    <td><b>${esc(a.agreement_number)}</b><br><small class="muted">SICONV: ${esc(a.siconv_number||'—')}</small></td>
                                    <td>${esc(a.grantor)}</td>
                                    <td>${esc(a.object)}</td>
                                    <td>
                                        <b>${fmtMoney(a.total_amount)}</b>
                                        <div style="font-size:10px;color:var(--muted);">Contrapartida: ${fmtMoney(a.counterpart_amount)}</div>
                                    </td>
                                    <td><small>${a.start_date} a ${a.end_date}</small></td>
                                    <td>
                                        <span class="control-status-badge ${a.accountability_status==='Adimplente'?'badge-conforme':'badge-nao-conforme'}">
                                            ${a.accountability_status}
                                        </span>
                                    </td>
                                    <td>${esc(a.responsible_name)}</td>
                                    <td>
                                        <button class="button small" data-module-click="control-66" data-arg0="${ModulesUI.escape(a.agreement_number)}" data-arg1="${ModulesUI.escape(a.object)}">Plano de Ação</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    // ── 5. Planos de Ação ────────────────────────────────────────────────
    async function renderPlansTab(container) {
        const res = await api('/control/action-plans?entity=1&exercise=2026');
        const plans = res.plans;

        let html = `
            <div class="panel">
                <div class="toolbar">
                    <span style="font-weight:700;color:var(--ink);">Planos de Ação Corretiva (Fato · Causa · Ação)</span>
                    <button class="button small primary" data-module-click="control-67" >Novo Plano de Ação</button>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ITEM / ORIGEM</th>
                                <th>FATO APONTADO</th>
                                <th>CAUSA IDENTIFICADA</th>
                                <th>AÇÃO CORRETIVA PROPOSTA</th>
                                <th>RESPONSÁVEL / PRAZO</th>
                                <th>STATUS</th>
                                <th>AÇÕES</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${!plans.length ? `<tr><td colspan="7" class="empty">Nenhum plano de ação registrado.</td></tr>` : plans.map(p => `
                                <tr>
                                    <td><b>${esc(p.reference_id)}</b><br><small class="muted">${esc(p.source_module)}</small></td>
                                    <td><strong>${esc(p.title)}</strong><div style="font-size:11px;color:var(--muted);">${esc(p.fact)}</div></td>
                                    <td><small>${esc(p.cause)}</small></td>
                                    <td><small>${esc(p.corrective_action)}</small></td>
                                    <td>
                                        <b>${esc(p.responsible_name)}</b>
                                        <div style="font-size:10px;color:var(--muted);">Prazo: ${p.deadline}</div>
                                    </td>
                                    <td>
                                        <span class="control-status-badge ${p.status==='Concluído'?'badge-conforme':p.status==='Respondido'?'badge-pendente':'badge-nao-conforme'}">
                                            ${p.status}
                                        </span>
                                    </td>
                                    <td>
                                        <button class="button small" data-module-click="control-68" data-arg0="${ModulesUI.escape(p.id)}" data-arg1="${ModulesUI.escape(p.title)}">Responder / Avaliar</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    window.openActionPlanModal = function(refId, moduleSource, defaultTitle) {
        openModal('Novo Plano de Ação para Não Conformidade', `
            <form id="action-plan-form">
                <div class="form-grid">
                    <label class="field"><span>Módulo de Origem</span>
                        <select id="ap-module">
                            <option value="SICONFI" ${moduleSource==='SICONFI'?'selected':''}>SICONFI (Ranking STN)</option>
                            <option value="CAUC" ${moduleSource==='CAUC'?'selected':''}>CAUC (Requisitos Fiscais)</option>
                            <option value="Convenios" ${moduleSource==='Convenios'?'selected':''}>Convênios (STN / Transferegov)</option>
                            <option value="Obrigacao" ${moduleSource==='Obrigacao'?'selected':''}>Obrigação Legal em Atraso</option>
                        </select>
                    </label>
                    <label class="field"><span>Código de Referência *</span><input type="text" id="ap-ref" value="${esc(refId||'')}" required></label>
                    <label class="field full"><span>Título do Apontamento *</span><input type="text" id="ap-title" value="${esc(defaultTitle||'')}" required></label>
                    <label class="field full"><span>Fato Constatado *</span><textarea id="ap-fact" rows="2" placeholder="Descreva a ocorrência apontada como não conforme..." required></textarea></label>
                    <label class="field full"><span>Causa Apurada *</span><textarea id="ap-cause" rows="2" placeholder="Qual a origem/motivo que gerou a pendência?" required></textarea></label>
                    <label class="field full"><span>Ação Corretiva Estabelecida *</span><textarea id="ap-action" rows="2" placeholder="Quais providências devem ser adotadas?" required></textarea></label>
                    <label class="field"><span>Agente Responsável *</span><input type="text" id="ap-resp" placeholder="Nome do servidor" required></label>
                    <label class="field"><span>E-mail do Responsável</span><input type="email" id="ap-email" placeholder="Para envio de notificação"></label>
                    <label class="field"><span>Prazo Limite para Atendimento *</span><input type="date" id="ap-deadline" required></label>
                </div>
                <div class="form-actions">
                    <button class="button primary" type="submit">Registrar Plano e Notificar Responsável</button>
                </div>
            </form>
        `);
        document.getElementById('action-plan-form').onsubmit = async function(e) {
            e.preventDefault();
            try {
                await api('/control/action-plans', 'POST', {
                    source_module: document.getElementById('ap-module').value,
                    reference_id: document.getElementById('ap-ref').value,
                    title: document.getElementById('ap-title').value,
                    fact: document.getElementById('ap-fact').value,
                    cause: document.getElementById('ap-cause').value,
                    corrective_action: document.getElementById('ap-action').value,
                    responsible_name: document.getElementById('ap-resp').value,
                    responsible_email: document.getElementById('ap-email').value,
                    deadline: document.getElementById('ap-deadline').value
                });
                toast('Plano de ação registrado e responsável notificado!');
                closeModal();
                switchControlTab('plans');
            } catch (err) {
                toast(err.message, true);
            }
        };
    };

    window.openRespondPlanModal = function(id, title) {
        openModal(`Resposta ao Plano de Ação #${id}`, `
            <form id="respond-plan-form">
                <p><b>Item:</b> ${esc(title)}</p>
                <div class="form-grid">
                    <label class="field full"><span>Descritivo das Ações Tomadas *</span><textarea id="rp-notes" rows="4" placeholder="Detalhe as providências adotadas para sanar a pendência..." required></textarea></label>
                    <label class="field full"><span>Link do Documento Comprobatório / Evidência</span><input type="url" id="rp-evidence" placeholder="https://..."></label>
                </div>
                <div class="form-actions">
                    <button class="button primary" type="submit">Registrar Resposta e Notificar Controladoria</button>
                </div>
            </form>
        `);
        document.getElementById('respond-plan-form').onsubmit = async function(e) {
            e.preventDefault();
            try {
                await api(`/control/action-plans/${id}/respond`, 'POST', {
                    response_notes: document.getElementById('rp-notes').value,
                    response_evidence: document.getElementById('rp-evidence').value
                });
                toast('Resposta enviada com sucesso! A Controladoria foi alertada no painel.');
                closeModal();
                switchControlTab('plans');
                loadNotifications();
            } catch (err) {
                toast(err.message, true);
            }
        };
    };

    // ── 6. Relatórios Conclusivos Mensais ────────────────────────────────
    async function renderReportsTab(container) {
        const versionsRes = await api('/control/reports/conclusive/versions?entity=1&exercise=2026');
        const versions = versionsRes.versions;

        let html = `
            <div class="panel" style="margin-bottom:24px;">
                <div class="panel-head">
                    <div>
                        <h2>Emissão de Relatório Conclusivo do Controle Interno</h2>
                        <p>Gere e assine o parecer mensal consolidado ou por entidade (SICONFI, CAUC ou Convênios).</p>
                    </div>
                </div>
                <div class="panel-body">
                    <form id="conclusive-report-form">
                        <div class="form-grid">
                            <label class="field"><span>Tipo de Relatório</span>
                                <select id="cr-type">
                                    <option value="Geral">Relatório Conclusivo Geral</option>
                                    <option value="SICONFI">Avaliação de Qualidade SICONFI / MSC</option>
                                    <option value="CAUC">Regularidade Fiscal CAUC</option>
                                    <option value="Convenios">Extrato e Prestação de Convênios</option>
                                </select>
                            </label>
                            <label class="field"><span>Competência de Apuração</span><input type="month" id="cr-period" value="2026-01" required></label>
                            <label class="field"><span>Escopo</span>
                                <select id="cr-scope">
                                    <option value="Consolidado">Consolidado do Município</option>
                                    <option value="Executivo">Poder Executivo</option>
                                    <option value="Legislativo">Poder Legislativo</option>
                                </select>
                            </label>
                            <label class="field"><span>Título do Relatório *</span><input type="text" id="cr-title" value="Relatório Conclusivo do Controle Interno - Janeiro/2026" required></label>
                            <label class="field full"><span>Texto do Parecer Técnico (Editável pelo Usuário) *</span>
                                <textarea id="cr-opinion" rows="3" required>Com base nas verificações técnicas realizadas nos demonstrativos orçamentários e fiscais, manifestamo-nos pela conformidade dos atos de gestão praticados no período, observados os apontamentos dos planos de ação corretiva em andamento.</textarea>
                            </label>
                            <label class="field full"><span>Considerações Finais (Personalizável) *</span>
                                <textarea id="cr-conclusion" rows="3" required>Recomenda-se aos órgãos setoriais o cumprimento rigoroso dos prazos regulamentares para alimentação das bases da STN e manutenção contínua da adimplência do Município perante o CAUC.</textarea>
                            </label>
                        </div>
                        <div class="form-actions">
                            <button class="button primary" type="submit">Gerar, Assinar e Selar Relatório</button>
                        </div>
                    </form>
                </div>
            </div>

            <div class="panel">
                <div class="toolbar">
                    <span style="font-weight:700;color:var(--ink);">Histórico de Versões Armazenadas (Verificabilidade)</span>
                    <span class="muted" style="font-size:11px;">Múltiplas versões arquivadas com hash de integridade SHA-256</span>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>TÍTULO / TIPO</th>
                                <th>COMPETÊNCIA</th>
                                <th>VERSÃO</th>
                                <th>HASH SHA-256</th>
                                <th>EMISSOR</th>
                                <th>DATA DE SELAGEM</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${!versions.length ? `<tr><td colspan="6" class="empty">Nenhum relatório conclusivo selado até o momento.</td></tr>` : versions.map(v => `
                                <tr>
                                    <td><strong>${esc(v.title)}</strong><br><small class="muted">${esc(v.report_type)} · ${esc(v.scope_type)}</small></td>
                                    <td>${v.period}</td>
                                    <td><span class="report-version-badge">Versão ${v.version}</span></td>
                                    <td><span class="mono" style="font-size:10px;">${(v.hash_digest||'').substring(0, 16)}…</span></td>
                                    <td>${esc(v.created_by)}</td>
                                    <td><small>${v.created_at}</small></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container.innerHTML = html;

        document.getElementById('conclusive-report-form').onsubmit = async function(e) {
            e.preventDefault();
            try {
                const res = await api('/control/reports/conclusive', 'POST', {
                    report_type: document.getElementById('cr-type').value,
                    period: document.getElementById('cr-period').value,
                    scope_type: document.getElementById('cr-scope').value,
                    title: document.getElementById('cr-title').value,
                    opinion_text: document.getElementById('cr-opinion').value,
                    conclusion_text: document.getElementById('cr-conclusion').value,
                    selected_verifications: ['STN-D1-01', 'STN-D2-01', 'STN-D3-01'],
                    selected_occurrences: [1, 2, 3]
                });
                toast(res.message);
                switchControlTab('reports');
            } catch (err) {
                toast(err.message, true);
            }
        };
    }

    // ── 7. Dados do Município / IBGE ────────────────────────────────────
    async function renderIbgeTab(container) {
        const res = await api('/control/ibge?entity=1&exercise=2026');
        const d = res.data;

        let html = `
            <div class="panel">
                <div class="panel-head">
                    <div>
                        <h2>Dados do Município e Limites Constitucionais (Censo IBGE / LRF)</h2>
                        <p>Parâmetros populacionais e apuração dos limites da Lei de Responsabilidade Fiscal e Constituição Federal.</p>
                    </div>
                </div>
                <div class="panel-body">
                    <form id="ibge-form">
                        <div class="form-grid">
                            <label class="field"><span>Município</span><input type="text" value="${esc(d.municipio_nome)}" disabled></label>
                            <label class="field"><span>Código IBGE</span><input type="text" value="${esc(d.cod_ibge)}" disabled></label>
                            <label class="field"><span>População Oficial (Censo IBGE) *</span><input type="number" id="ibge-pop" value="${d.populacao}" required></label>
                            <label class="field"><span>Receita Corrente Líquida Anual (Centavos) *</span><input type="number" id="ibge-rcl" value="${d.receita_corrente_liquida}" required></label>
                            <label class="field"><span>Limite Despesa Pessoal Executivo (LRF %) *</span><input type="number" step="0.1" id="ibge-lim-exec" value="${d.limite_pessoal_executivo_pct}" required></label>
                            <label class="field"><span>Limite Despesa Pessoal Legislativo (LRF %) *</span><input type="number" step="0.1" id="ibge-lim-leg" value="${d.limite_pessoal_legislativo_pct}" required></label>
                            <label class="field"><span>Limite Repasse à Câmara (Art. 29-A CF %) *</span><input type="number" step="0.1" id="ibge-lim-cam" value="${d.limite_repasse_camara_pct}" required></label>
                        </div>

                        <div class="form-section">
                            <h4>Valores Limites Calculados em Reais (R$)</h4>
                            <div class="control-kpi-grid" style="margin-top:12px;">
                                <div class="control-kpi-card">
                                    <div class="label">Teto de Pessoal Executivo</div>
                                    <div class="value" style="font-size:18px;">${fmtMoney(d.limite_pessoal_executivo_valor)}</div>
                                    <div class="sub">54% da RCL</div>
                                </div>
                                <div class="control-kpi-card">
                                    <div class="label">Teto de Pessoal Legislativo</div>
                                    <div class="value" style="font-size:18px;">${fmtMoney(d.limite_pessoal_legislativo_valor)}</div>
                                    <div class="sub">6% da RCL</div>
                                </div>
                                <div class="control-kpi-card">
                                    <div class="label">Teto de Repasse ao Legislativo</div>
                                    <div class="value" style="font-size:18px;">${fmtMoney(d.limite_repasse_camara_valor)}</div>
                                    <div class="sub">7% da Receita de Tributos (Art. 29-A CF)</div>
                                </div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button class="button primary" type="submit">Salvar Dados do IBGE e Recalcular Limites</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        container.innerHTML = html;

        document.getElementById('ibge-form').onsubmit = async function(e) {
            e.preventDefault();
            try {
                await api('/control/ibge', 'PUT', {
                    populacao: document.getElementById('ibge-pop').value,
                    receita_corrente_liquida: document.getElementById('ibge-rcl').value,
                    limite_pessoal_executivo_pct: document.getElementById('ibge-lim-exec').value,
                    limite_pessoal_legislativo_pct: document.getElementById('ibge-lim-leg').value,
                    limite_repasse_camara_pct: document.getElementById('ibge-lim-cam').value
                });
                toast('Dados do IBGE e limites constitucionais atualizados com sucesso!');
                renderIbgeTab(container);
            } catch (err) {
                toast(err.message, true);
            }
        };
    }

    // ── Interceptação da Página ERP ──────────────────────────────────────
    const originalErpPage = erpPage;
    erpPage = async function(module) {
        if (module !== 'control') {
            return await originalErpPage(module);
        }

        const controlHtml = `
            <div class="control-container module-workspace">
                <div class="control-header">
                    <div class="control-title">
                        <h1>Controle Interno · Controladoria Geral</h1>
                        <p>Ambiente integrado de gestão de obrigações, SICONFI, CAUC, convênios, planos de ação e relatórios conclusivos.</p>
                    </div>
                    <div class="control-top-actions">
                        <div style="position:relative;">
                            <button class="control-bell-btn" data-module-click="control-69" >
                                Alertas
                                <span id="control-notif-count" class="control-bell-badge" style="display:none;">0</span>
                            </button>
                            <div id="control-notif-dropdown" class="control-notif-dropdown">
                                <div class="control-notif-head">
                                    <span>Notificações e Alertas</span>
                                    <button class="button small" data-module-click="control-70" >Fechar</button>
                                </div>
                                <div id="control-notif-list" class="control-notif-list"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="control-tabs">
                    <button class="control-tab-btn active" data-tab="calendar" data-module-click="control-71" >Calendário de Obrigações</button>
                    <button class="control-tab-btn" data-tab="siconfi" data-module-click="control-72" >Ranking SICONFI (STN)</button>
                    <button class="control-tab-btn" data-tab="cauc" data-module-click="control-73" >Requisitos CAUC</button>
                    <button class="control-tab-btn" data-tab="agreements" data-module-click="control-74" >Convênios STN</button>
                    <button class="control-tab-btn" data-tab="plans" data-module-click="control-75" >Planos de Ação</button>
                    <button class="control-tab-btn" data-tab="reports" data-module-click="control-76" >Relatórios Conclusivos</button>
                    <button class="control-tab-btn" data-tab="ibge" data-module-click="control-77" >Dados IBGE / Limites LRF</button>
                </div>

                <div id="control-tab-content">
                    <div class="loading-panel"><div class="loader"></div>Carregando painel de controle...</div>
                </div>
            </div>
        `;

        setTimeout(async () => {
            const container = document.getElementById('control-tab-content');
            if (container) {
                await renderCalendarTab(container);
                loadNotifications();
            }
        }, 50);

        return controlHtml;
    };

})();
