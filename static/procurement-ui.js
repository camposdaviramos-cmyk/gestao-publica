/* ── Compras, Licitações e Contratos · Rio Gestão ────────────────── */
(function() {
    'use strict';

    function fmtMoney(cents) {
        if (!cents && cents !== 0) return 'R$ 0,00';
        const val = Number(cents) / 100;
        return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    function esc(s) {
        if (!s) return '';
        return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    async function checkSrpAlerts(terms, targetEl) {
        if (!targetEl || !terms || !terms.length) return;
        try {
            const res = await fetch(`/api/procurement/check-srp-alerts?terms=${encodeURIComponent(terms.join(','))}`);
            if (!res.ok) return;
            const data = await res.json();
            if (!data.has_active_srp) {
                targetEl.innerHTML = '';
                return;
            }
            let html = `
                <div class="proc-srp-alert-banner">
                    <span class="proc-srp-alert-icon">⚠️</span>
                    <div class="proc-srp-alert-details">
                        <b>Atenção:</b> Existem Atas de Registro de Preços vigentes para os itens requisitados:
                        <ul style="margin: 6px 0 0 16px; padding: 0;">
            `;
            data.alerts.forEach(a => {
                html += `<li><b>${esc(a.agreement_code)}:</b> ${esc(a.description)} — Saldo disponível: <b>${a.available_quantity} ${esc(a.unit)}</b> (${fmtMoney(a.unit_price)}/un) com ${esc(a.supplier_name)}.</li>`;
            });
            html += `</ul></div>`;
            targetEl.innerHTML = html;
        } catch (e) {
            console.error('Erro ao verificar SRP:', e);
        }
    }

    async function renderSupplierCompliance(supplierId, targetEl) {
        if (!targetEl || !supplierId) return;
        try {
            const res = await fetch(`/api/procurement/suppliers/${supplierId}/compliance`);
            if (!res.ok) return;
            const data = await res.json();
            
            let html = `
                <div class="proc-card">
                    <div class="proc-card-header">
                        <span class="proc-card-title">🛡️ Regularidade Fiscal e Trabalhista (CNDs)</span>
                        <span class="proc-bid-badge ${data.compliant ? 'proc-bid-winner' : 'proc-cnd-expired'}" style="padding: 4px 8px;">
                            ${data.compliant ? '✓ Habilitado / Regular' : '✕ Pendência Fiscal / Sanção'}
                        </span>
                    </div>
            `;
            
            if (data.blocked && data.reason) {
                html += `
                    <div style="background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.3); border-radius: 6px; padding: 10px; color: #dc2626; font-size: 13px;">
                        <b>Bloqueio:</b> ${esc(data.reason)}
                    </div>
                `;
            }
            
            html += `<div class="proc-cnd-grid">`;
            const certTypes = ['Federal/INSS', 'Estadual', 'Municipal', 'Trabalhista CNDT', 'FGTS'];
            certTypes.forEach(t => {
                const c = data.certificates ? data.certificates[t] : null;
                let cls = 'proc-cnd-expired';
                let statusTxt = 'Não cadastrada';
                let expTxt = '—';
                
                if (c) {
                    expTxt = c.expiration_date;
                    if (data.expired_certificates && data.expired_certificates.includes(t)) {
                        cls = 'proc-cnd-expired';
                        statusTxt = 'Vencida';
                    } else if (data.expiring_soon && data.expiring_soon.some(x => x.type === t)) {
                        cls = 'proc-cnd-warning';
                        statusTxt = 'Vence em breve';
                    } else {
                        cls = 'proc-cnd-valid';
                        statusTxt = 'Válida';
                    }
                }
                
                html += `
                    <div class="proc-cnd-item ${cls}">
                        <div class="proc-cnd-label">${esc(t)}</div>
                        <div class="proc-cnd-val">${esc(statusTxt)}</div>
                        <div style="font-size: 11px; color: var(--muted);">Validade: ${esc(expTxt)}</div>
                    </div>
                `;
            });
            html += `</div></div>`;
            targetEl.innerHTML = html;
        } catch (e) {
            console.error('Erro ao consultar regularidade:', e);
        }
    }

    async function renderContractFinancialSummary(contractId, targetEl) {
        if (!targetEl || !contractId) return;
        try {
            const res = await fetch(`/api/procurement/contracts/${contractId}/financial-summary`);
            if (!res.ok) return;
            const data = await res.json();
            
            const pct = data.current_amount ? Math.min(100, Math.round((data.total_committed / data.current_amount) * 100)) : 0;
            
            let html = `
                <div class="proc-card">
                    <div class="proc-card-header">
                        <span class="proc-card-title">📊 Acompanhamento Financeiro do Contrato</span>
                        <span style="font-size: 12px; color: var(--muted);">Contrato: <b>${esc(data.contract_code)}</b></span>
                    </div>
                    <div class="proc-finance-bar-wrap">
                        <div class="proc-finance-meta">
                            <span>Empenhado: <b>${fmtMoney(data.total_committed)}</b> (${pct}%)</span>
                            <span>Valor Atual: <b>${fmtMoney(data.current_amount)}</b></span>
                        </div>
                        <div class="proc-finance-bar">
                            <div class="proc-finance-fill" style="width: ${pct}%;"></div>
                        </div>
                        <div class="proc-finance-meta">
                            <span>Saldo a empenhar: <b>${fmtMoney(data.uncommitted_balance)}</b></span>
                            <span>Empenhos vinculados: <b>${data.commitments_count}</b></span>
                        </div>
                    </div>
                </div>
            `;
            targetEl.innerHTML = html;
        } catch (e) {
            console.error('Erro no resumo financeiro:', e);
        }
    }

    window.ProcurementUI = {
        checkSrpAlerts,
        renderSupplierCompliance,
        renderContractFinancialSummary,
        fmtMoney
    };
})();
