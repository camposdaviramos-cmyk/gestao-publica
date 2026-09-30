'use strict';
/* ── Obras Públicas · Interface e Gestão Integrada ─────────────────── */

async function worksProjectDetail(project) {
    const d = project.data;
    const contracted = Number(project.balances?.contracted_amount || d.estimated || 0);
    const measured = Number(project.balances?.measured_amount || 0);
    const paid = Number(project.balances?.paid || 0);
    const retention = Math.max(0, measured - paid);
    const pct = contracted > 0 ? Math.min(100, Math.round((measured / contracted) * 100)) : 0;
    
    // Buscar fotos e projeção
    let photos = [];
    let projection = [];
    try {
        const pRes = await api(`/works/projects/${project.id}/photos`);
        photos = pRes.items || [];
    } catch {}
    try {
        const prjRes = await api(`/works/projects/${project.id}/projection`);
        projection = prjRes.projection || [];
    } catch {}

    const mapsUrl = d.latitude && d.longitude ? `https://www.google.com/maps?q=${d.latitude},${d.longitude}` : '';

    return `
    <div class="works-overview-grid">
        <section class="panel">
            <div class="panel-head">
                <div>
                    <h2>${esc(project.code)} · ${esc(project.name)}</h2>
                    <p>${esc(d.address || 'Localização municipal não informada')}</p>
                </div>
                ${badge(project.state)}
            </div>
            <div class="panel-body">
                <dl class="detail-grid">
                    <div><dt>Responsável Técnico</dt><dd>${esc(d.engineer || '—')} (CREA: ${esc(d.registration || '—')})</dd></div>
                    <div><dt>Contrato / Licitação</dt><dd>${esc(d.contract || '—')}</dd></div>
                    <div><dt>Período de Execução</dt><dd>${date(d.start)} até ${date(d.end)}</dd></div>
                    <div><dt>Prazo de Retenção</dt><dd>${d.retention_days ? d.retention_days + ' dias pós-entrega' : 'Não informado'}</dd></div>
                </dl>
                <div style="margin-top:16px">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px">
                        <span><strong>Evolução Física da Obra</strong> · Medido vs Contratado</span>
                        <strong style="color:var(--accent)">${pct}% executado</strong>
                    </div>
                    <div class="progress-track" style="height:10px">
                        <span style="width:${pct}%;background:var(--accent)"></span>
                    </div>
                </div>
            </div>
        </section>

        <section class="works-map-card">
            <h3>${icon('target')}Localização e Mapa</h3>
            ${mapsUrl ? `
                <div class="works-coords">${icon('globe')}Lat: ${d.latitude}, Long: ${d.longitude}</div>
                <div class="works-map-placeholder">
                    <span>${icon('building')}Obra Georreferenciada</span>
                    <a href="${mapsUrl}" target="_blank" rel="noopener" class="button small">
                        ${icon('external')}Abrir no Google Maps
                    </a>
                </div>
            ` : `
                <div class="works-map-placeholder">
                    <span>Coordenadas de latitude/longitude não cadastradas</span>
                </div>
            `}
            <div style="display:flex;gap:6px;margin-top:auto">
                <button class="button small full" data-action="works-amend-modal" data-id="${project.id}">${icon('edit')}Aditivo</button>
                <button class="button small full" data-action="works-import-modal" data-id="${project.id}">${icon('download')}Importar Planilha</button>
            </div>
        </section>
    </div>

    <!-- Indicadores Financeiros da Obra -->
    <div class="works-indicators-grid">
        <article class="stat">
            <div class="stat-top"><span>Valor Contratado</span><span class="badge green">Total</span></div>
            <div class="stat-value">${money(contracted / 100)}</div>
            <div class="stat-bottom">${icon('arrow')}Orçamento base</div>
        </article>
        <article class="stat">
            <div class="stat-top"><span>Valor Medido</span><span class="badge blue">${pct}%</span></div>
            <div class="stat-value">${money(measured / 100)}</div>
            <div class="stat-bottom">${icon('arrow')}Aprovado pela fiscalização</div>
        </article>
        <article class="stat">
            <div class="stat-top"><span>Valor Pago</span><span class="badge green">Quitado</span></div>
            <div class="stat-value">${money(paid / 100)}</div>
            <div class="stat-bottom">${icon('arrow')}Medições liquidadas</div>
        </article>
        <article class="stat">
            <div class="stat-top"><span>Retenção Acumulada</span><span class="badge amber">Garantia</span></div>
            <div class="stat-value">${money(retention / 100)}</div>
            <div class="stat-bottom">${icon('shield')}Liberação pós-recebimento</div>
        </article>
    </div>

    <!-- Aportes Mensais e Curva Físico-Financeira -->
    ${projection.length ? `
    <section class="panel" style="margin-bottom:22px">
        <div class="panel-head">
            <div>
                <h2>Previsão de Aportes Mensais (Cronograma Físico-Financeiro)</h2>
                <p>Distribuição temporal dos recursos estimados ao longo dos meses da obra</p>
            </div>
            <button class="button small" data-action="works-export-funding" data-id="${project.id}">${icon('download')}Exportar Aportes (PDF)</button>
        </div>
        <div class="table-wrap">
            <table>
                <thead><tr><th>COMPETÊNCIA</th><th>APORTE PREVISTO</th><th>ACUMULADO PREVISTO</th><th>AVANÇO (%)</th></tr></thead>
                <tbody>
                    ${projection.map(p => `
                        <tr>
                            <td class="mono"><strong>${esc(p.period)}</strong></td>
                            <td class="mono">${money(p.amount / 100)}</td>
                            <td class="mono">${money(p.cumulative / 100)}</td>
                            <td class="mono"><span class="badge green">${p.percent}%</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    </section>
    ` : ''}

    <!-- Galeria de Fotos Aprovadas nos Diários -->
    <section class="panel">
        <div class="panel-head">
            <div>
                <h2>Fotos dos Diários de Obra</h2>
                <p>Registros fotográficos acompanhados e aprovados pelos fiscais da prefeitura</p>
            </div>
            <div class="heading-actions">
                <button class="button small" data-action="works-report-stoppages" data-id="${project.id}">${icon('file')}Relatório de Paralisações (PDF)</button>
            </div>
        </div>
        <div class="panel-body">
            ${photos.length ? `
                <div class="works-photos-grid">
                    ${photos.map(ph => `
                        <div class="works-photo-card">
                            <div class="works-photo-thumb">
                                <span style="font-size:32px">📷</span>
                            </div>
                            <div class="works-photo-meta">
                                <div class="works-photo-caption">${esc(ph.caption || ph.filename)}</div>
                                <small class="muted">Diário #${esc(ph.diary_code)} · ${date(ph.created_at)}</small>
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">
                                    ${ph.approved ? '<span class="badge green">Aprovada</span>' : `<button class="button small" data-action="works-approve-photo" data-id="${ph.id}">Aprovar</button>`}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : empty('Nenhuma foto anexada', 'As fotos registradas nos diários de obras aparecerão aqui após inclusão.')}
        </div>
    </section>
    `;
}

/* ── Modais de Ação de Obras ──────────────────────────────────────── */

function worksImportSpreadsheetModal(projectId) {
    openModal('Importar Planilha Orçamentária Base', `
        <form id="works-import-form" data-id="${projectId}">
            <div class="form-grid">
                ${field('bdi_linear', 'BDI Linear Padrão (%)', '0', 'number', 'step="0.01" min="0" max="100"')}
                ${field('discount_linear', 'Desconto Linear Padrão (%)', '0', 'number', 'step="0.01" min="0" max="100"')}
            </div>
            <div class="field full" style="margin-top:14px">
                <label>Itens da Planilha (Cole em formato JSON ou CSV: código;descrição;unidade;quantidade;preço unitário em centavos)
                    <textarea name="raw_content" rows="8" placeholder="ITEM-001;Serviços Preliminares;m2;100;4500\nITEM-002;Estrutura e Fundações;m3;50;12000" required></textarea>
                </label>
            </div>
            ${formActions('Importar Itens da Planilha', 'download')}
        </form>
    `, 'Definição da referência inicial de custos e itens da obra');
}

function worksAmendModal(projectId) {
    openModal('Aditivo de Obra', `
        <form id="works-amend-form" data-id="${projectId}">
            <div class="form-grid">
                ${selectField('type', 'Tipo de Aditivo', ['Prazo', 'Valor'])}
                ${field('new_end', 'Nova Data de Término (para aditivo de prazo)', '', 'date')}
                ${field('amount', 'Valor Adicional em centavos (para aditivo de valor)', '0', 'number')}
            </div>
            ${textField('justification', 'Justificativa do Aditivo *', '', 'required minlength="5"')}
            ${formActions('Salvar Termo Aditivo', 'check')}
        </form>
    `, 'Acréscimo de prazo ou de valor com base em parecer técnico');
}
