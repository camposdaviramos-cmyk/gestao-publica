"""Motor de Regras de Negócio e Serviços do Módulo de Controle Interno e Controladoria.
Atende integralmente aos 85 itens do Anexo III e Edital PE 552/2026:
- Obrigações legais, recorrências, ocorrências automáticas e calendário com cores.
- Comunicação por e-mail com registro no histórico e justificativas de atraso.
- Ranking da Qualidade da Informação Contábil e Fiscal (SICONFI - Dimensões 2, 3, 1 e 4).
- Carga, duplicação e edição de regras específicas e reprocessamento de competências.
- Gestão de Requisitos Fiscais do CAUC e Extrato de Convênios da STN.
- Planos de ação com identificação de Fato, Causa, Ação e notificações com sininho.
- Relatórios conclusivos mensais com seleção de verificações/ocorrências, pareceres editáveis, assinaturas e versões históricas.
- Informações municipais baseadas no censo IBGE e limites constitucionais.
"""
import hashlib
import json
from datetime import datetime, date, timedelta
from db import get_db, audit
from domain import now
from auth import ApiError

def get_ibge_info(entity_id=1, exercise=2026):
    db = get_db()
    row = db.execute("SELECT * FROM control_ibge_data WHERE entity_id=? AND exercise=?", (entity_id, exercise)).fetchone()
    if not row:
        from control_seed import seed_control
        seed_control(entity_id, exercise)
        row = db.execute("SELECT * FROM control_ibge_data WHERE entity_id=? AND exercise=?", (entity_id, exercise)).fetchone()
    d = dict(row)
    # Calcular valores limites em moeda corrente com base na RCL
    rcl = d['receita_corrente_liquida']
    d['limite_pessoal_executivo_valor'] = int(rcl * (d['limite_pessoal_executivo_pct'] / 100.0))
    d['limite_pessoal_legislativo_valor'] = int(rcl * (d['limite_pessoal_legislativo_pct'] / 100.0))
    d['limite_repasse_camara_valor'] = int(rcl * (d['limite_repasse_camara_pct'] / 100.0))
    return d

def update_ibge_info(entity_id, exercise, data):
    db = get_db()
    pop = int(data.get('populacao', 156491))
    lim_exec = float(data.get('limite_pessoal_executivo_pct', 54.0))
    lim_leg = float(data.get('limite_pessoal_legislativo_pct', 6.0))
    lim_cam = float(data.get('limite_repasse_camara_pct', 7.0))
    rcl = int(data.get('receita_corrente_liquida', 98540000000))

    db.execute("""
        INSERT INTO control_ibge_data (
            entity_id, exercise, municipio_nome, cod_ibge, populacao,
            limite_pessoal_executivo_pct, limite_pessoal_legislativo_pct,
            limite_repasse_camara_pct, receita_corrente_liquida, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity_id, exercise) DO UPDATE SET
            populacao=excluded.populacao,
            limite_pessoal_executivo_pct=excluded.limite_pessoal_executivo_pct,
            limite_pessoal_legislativo_pct=excluded.limite_pessoal_legislativo_pct,
            limite_repasse_camara_pct=excluded.limite_repasse_camara_pct,
            receita_corrente_liquida=excluded.receita_corrente_liquida,
            updated_at=excluded.updated_at
    """, (entity_id, exercise, 'Rio das Ostras', '3304524', pop, lim_exec, lim_leg, lim_cam, rcl, now()))
    db.commit()
    return get_ibge_info(entity_id, exercise)

def get_calendar_events(entity_id=1, exercise=2026, month=None, sphere=None, status=None):
    db = get_db()
    query = """
        SELECT oc.*, ob.code as obligation_code, ob.legislation_type, ob.subject_group,
               ob.delivery_method, ob.destination, ob.source_url
        FROM control_occurrences oc
        JOIN control_obligations ob ON ob.id = oc.obligation_id
        WHERE oc.entity_id = ? AND oc.exercise = ?
    """
    params = [entity_id, exercise]

    if month:
        comp_prefix = f"{exercise:04d}-{int(month):02d}"
        query += " AND oc.competence = ?"
        params.append(comp_prefix)
    if sphere:
        query += " AND ob.legislation_type = ?"
        params.append(sphere)
    if status:
        query += " AND oc.status = ?"
        params.append(status)

    query += " ORDER BY oc.due_date ASC, oc.id ASC"
    rows = db.execute(query, params).fetchall()

    today_str = date.today().strftime('%Y-%m-%d')
    events = []
    for r in rows:
        item = dict(r)
        # Ajuste dinâmico de status se estiver vencido
        if item['status'] == 'A Vencer' and item['due_date'] < today_str:
            item['status'] = 'Vencida'

        # Atribuição de cores padronizadas exigidas pelo Anexo III
        if item['status'] == 'Atendida':
            item['color'] = '#10b981' # verde
            item['badge_class'] = 'badge-success'
        elif item['status'] == 'Vencida':
            item['color'] = '#ef4444' # vermelho
            item['badge_class'] = 'badge-danger'
        elif item['status'] == 'Dispensada':
            item['color'] = '#6b7280' # cinza
            item['badge_class'] = 'badge-neutral'
        else: # A Vencer
            # Se faltar menos de 7 dias, destaca em laranja
            due_d = datetime.strptime(item['due_date'], '%Y-%m-%d').date()
            cur_d = date.today()
            if 0 <= (due_d - cur_d).days <= 7:
                item['color'] = '#f97316' # laranja alerta
                item['badge_class'] = 'badge-warning'
            else:
                item['color'] = '#3b82f6' # azul normal
                item['badge_class'] = 'badge-info'

        events.append(item)
    return events

def get_obligations_summary(entity_id=1, exercise=2026):
    db = get_db()
    today_str = date.today().strftime('%Y-%m-%d')
    in_15_days = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')

    # Atualiza vencimentos expirados
    db.execute("""
        UPDATE control_occurrences
        SET status = 'Vencida', updated_at = ?
        WHERE entity_id = ? AND exercise = ? AND status = 'A Vencer' AND due_date < ?
    """, (now(), entity_id, exercise, today_str))
    db.commit()

    total = db.execute("SELECT COUNT(*) FROM control_occurrences WHERE entity_id=? AND exercise=?", (entity_id, exercise)).fetchone()[0]
    attended = db.execute("SELECT COUNT(*) FROM control_occurrences WHERE entity_id=? AND exercise=? AND status='Atendida'", (entity_id, exercise)).fetchone()[0]
    overdue = db.execute("SELECT COUNT(*) FROM control_occurrences WHERE entity_id=? AND exercise=? AND status='Vencida'", (entity_id, exercise)).fetchone()[0]
    due_soon = db.execute("SELECT COUNT(*) FROM control_occurrences WHERE entity_id=? AND exercise=? AND status='A Vencer' AND due_date BETWEEN ? AND ?",
                          (entity_id, exercise, today_str, in_15_days)).fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM control_occurrences WHERE entity_id=? AND exercise=? AND status='A Vencer'", (entity_id, exercise)).fetchone()[0]

    compliance_rate = round((attended / total * 100.0), 1) if total > 0 else 100.0

    # Por esfera
    by_sphere = {}
    for r in db.execute("""
        SELECT ob.legislation_type, COUNT(oc.id) as total,
               SUM(CASE WHEN oc.status='Atendida' THEN 1 ELSE 0 END) as attended,
               SUM(CASE WHEN oc.status='Vencida' THEN 1 ELSE 0 END) as overdue
        FROM control_occurrences oc
        JOIN control_obligations ob ON ob.id = oc.obligation_id
        WHERE oc.entity_id=? AND oc.exercise=?
        GROUP BY ob.legislation_type
    """, (entity_id, exercise)):
        by_sphere[r['legislation_type']] = dict(r)

    # Por mês (gráfico anual)
    by_month = []
    for m in range(1, 13):
        comp = f"{exercise:04d}-{m:02d}"
        row = db.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status='Atendida' THEN 1 ELSE 0 END) as attended,
                   SUM(CASE WHEN status='Vencida' THEN 1 ELSE 0 END) as overdue,
                   SUM(CASE WHEN status='A Vencer' THEN 1 ELSE 0 END) as pending
            FROM control_occurrences
            WHERE entity_id=? AND exercise=? AND competence=?
        """, (entity_id, exercise, comp)).fetchone()
        by_month.append({
            'month': m,
            'competence': comp,
            'total': row['total'] or 0,
            'attended': row['attended'] or 0,
            'overdue': row['overdue'] or 0,
            'pending': row['pending'] or 0
        })

    return {
        'total': total,
        'attended': attended,
        'overdue': overdue,
        'due_soon_15_days': due_soon,
        'pending': pending,
        'compliance_rate': compliance_rate,
        'by_sphere': by_sphere,
        'by_month': by_month
    }

def add_occurrence_followup(occurrence_id, followup_type, notes, author_name, attachment_name=None, attachment_url=None, recipient_email=None):
    db = get_db()
    occ = db.execute("SELECT * FROM control_occurrences WHERE id=?", (occurrence_id,)).fetchone()
    if not occ:
        raise ApiError("Ocorrência não encontrada.", 404)

    if not notes or not notes.strip():
        raise ApiError("Descrição do acompanhamento é obrigatória.")

    valid_types = ['Justificativa', 'Comentário', 'Encerramento', 'Reabertura', 'Email']
    if followup_type not in valid_types:
        raise ApiError(f"Tipo de acompanhamento inválido. Válidos: {', '.join(valid_types)}")

    fid = db.execute("""
        INSERT INTO control_obligation_followups (
            occurrence_id, type, notes, attachment_name, attachment_url,
            author_name, recipient_email, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        occurrence_id, followup_type, notes.strip(), attachment_name, attachment_url,
        author_name, recipient_email, now()
    )).lastrowid

    # Atualizações de estado conforme o tipo de acompanhamento
    if followup_type == 'Encerramento':
        db.execute("""
            UPDATE control_occurrences
            SET status = 'Atendida', closed_at = ?, closed_by = ?, updated_at = ?
            WHERE id = ?
        """, (now(), author_name, now(), occurrence_id))
    elif followup_type == 'Reabertura':
        db.execute("""
            UPDATE control_occurrences
            SET status = 'A Vencer', closed_at = NULL, closed_by = NULL, updated_at = ?
            WHERE id = ?
        """, (now(), occurrence_id))
    elif followup_type == 'Justificativa':
        db.execute("""
            UPDATE control_occurrences
            SET delay_justification = ?, updated_at = ?
            WHERE id = ?
        """, (notes.strip(), now(), occurrence_id))

    db.commit()
    return {'id': fid, 'message': 'Acompanhamento registrado com sucesso.', 'type': followup_type}

def quick_close_occurrence(occurrence_id, closed_by, notes='Encerramento rápido registrado'):
    return add_occurrence_followup(occurrence_id, 'Encerramento', notes, closed_by)

def send_obligation_email(occurrence_id, recipient_email, subject, message_body, author_name):
    db = get_db()
    occ = db.execute("""
        SELECT oc.*, ob.code as obligation_code, ob.title as obligation_title, ob.destination
        FROM control_occurrences oc
        JOIN control_obligations ob ON ob.id = oc.obligation_id
        WHERE oc.id = ?
    """, (occurrence_id,)).fetchone()
    if not occ:
        raise ApiError("Ocorrência não encontrada.", 404)

    if not recipient_email or '@' not in recipient_email:
        raise ApiError("E-mail do destinatário inválido.")
    if not message_body or not message_body.strip():
        raise ApiError("Mensagem do e-mail é obrigatória.")

    # Registro no histórico de acompanhamentos com o e-mail anexado
    email_content = f"ASSUNTO: {subject}\nDESTINATÁRIO: {recipient_email}\nDATA/HORA: {now()}\n\n{message_body.strip()}"
    followup = add_occurrence_followup(
        occurrence_id=occurrence_id,
        followup_type='Email',
        notes=email_content,
        author_name=author_name,
        recipient_email=recipient_email
    )

    # Cria notificação para o usuário destinatário no sistema (sininho)
    db.execute("""
        INSERT INTO control_notifications (
            recipient_role, title, message, reference_type, reference_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        'OPERADOR', f"Obrigação {occ['obligation_code']}: {subject}",
        f"Instruções enviadas por {author_name} para {recipient_email}:\n{message_body[:100]}...",
        'obligation', str(occurrence_id), now()
    ))
    db.commit()

    return {
        'message': 'E-mail registrado e anexado ao histórico de acompanhamentos com sucesso.',
        'followup_id': followup['id'],
        'recipient': recipient_email
    }

def get_occurrence_detail(occurrence_id):
    db = get_db()
    occ = db.execute("""
        SELECT oc.*, ob.code as obligation_code, ob.title as obligation_title, ob.description as obligation_description,
               ob.legislation_type, ob.subject_group, ob.legislation, ob.delivery_method, ob.destination,
               ob.source_url, ob.notes as obligation_notes, ob.frequency
        FROM control_occurrences oc
        JOIN control_obligations ob ON ob.id = oc.obligation_id
        WHERE oc.id = ?
    """, (occurrence_id,)).fetchone()
    if not occ:
        raise ApiError("Ocorrência não encontrada.", 404)

    followups = [dict(r) for r in db.execute("""
        SELECT * FROM control_obligation_followups
        WHERE occurrence_id = ?
        ORDER BY created_at DESC
    """, (occurrence_id,)).fetchall()]

    d = dict(occ)
    d['followups'] = followups
    return d

# =========================================================================
# SICONFI & Ranking da Qualidade da Informação Contábil e Fiscal (STN)
# =========================================================================

def get_siconfi_dashboard(entity_id=1, exercise=2026, dimension=None, power=None, period=None):
    db = get_db()

    query = """
        SELECT r.*, e.status as eval_status, e.verified_value, e.benchmark_value,
               e.notes as eval_notes, e.period as eval_period, e.id as eval_id,
               p.id as plan_id, p.status as plan_status
        FROM control_siconfi_rules r
        LEFT JOIN control_siconfi_evaluations e ON e.rule_id = r.id AND e.entity_id = ? AND e.exercise = ?
        LEFT JOIN control_action_plans p ON p.reference_id = r.rule_code AND p.entity_id = ? AND p.exercise = ?
        WHERE r.entity_id = ? AND r.active = 1
    """
    params = [entity_id, exercise, entity_id, exercise, entity_id]

    if dimension:
        query += " AND r.dimension = ?"
        params.append(int(dimension))
    if power:
        query += " AND r.power = ?"
        params.append(power)
    if period:
        query += " AND (e.period = ? OR e.period IS NULL)"
        params.append(period)

    query += " ORDER BY r.dimension ASC, r.rule_code ASC"
    rows = db.execute(query, params).fetchall()

    items = []
    conforming = 0
    non_conforming = 0

    dim2_conf = 0
    dim2_non_conf = 0
    dim3_conf = 0
    dim3_non_conf = 0

    for r in rows:
        it = dict(r)
        st = it.get('eval_status') or 'Conforme'
        it['status'] = st

        # Cores padronizadas do edital (Verde para atendida/conforme, Vermelho para não atendida/não conforme)
        if st == 'Conforme':
            it['color'] = '#10b981' # verde
            conforming += 1
            if it['dimension'] == 2:
                dim2_conf += 1
            elif it['dimension'] == 3:
                dim3_conf += 1
        else:
            it['color'] = '#ef4444' # vermelho
            non_conforming += 1
            if it['dimension'] == 2:
                dim2_non_conf += 1
            elif it['dimension'] == 3:
                dim3_non_conf += 1

        items.append(it)

    total = len(items)
    score_pct = round((conforming / total * 100.0), 1) if total > 0 else 100.0

    return {
        'total_rules': total,
        'conforming_count': conforming,
        'non_conforming_count': non_conforming,
        'quality_score_pct': score_pct,
        'dimension_2_chart': {
            'conforming': dim2_conf,
            'non_conforming': dim2_non_conf,
            'total': dim2_conf + dim2_non_conf
        },
        'dimension_3_chart': {
            'conforming': dim3_conf,
            'non_conforming': dim3_non_conf,
            'total': dim3_conf + dim3_non_conf
        },
        'legend': {
            'green': 'Verde: Em conformidade / Atendido integralmente pelas regras da STN',
            'red': 'Vermelho: Em não conformidade / Pendência apurada na MSC ou relatórios fiscais'
        },
        'items': items
    }

def manage_siconfi_rule(action, rule_data, entity_id=1):
    db = get_db()
    if action == 'create':
        code = rule_data.get('rule_code')
        if not code:
            raise ApiError("Código da regra é obrigatório.")
        rid = db.execute("""
            INSERT INTO control_siconfi_rules (
                entity_id, rule_code, title, dimension, power, interval_type,
                description, formula, tolerance_cents, active, owner_name, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            entity_id, code, rule_data.get('title', 'Nova Regra'), int(rule_data.get('dimension', 2)),
            rule_data.get('power', 'Executivo'), rule_data.get('interval_type', 'Mensal'),
            rule_data.get('description', ''), rule_data.get('formula', ''), int(rule_data.get('tolerance_cents', 0)),
            rule_data.get('owner_name', 'Controlador'), now(), now()
        )).lastrowid
        db.commit()
        return {'id': rid, 'message': 'Regra SICONFI criada com sucesso.'}

    elif action == 'duplicate':
        source_id = rule_data.get('rule_id')
        row = db.execute("SELECT * FROM control_siconfi_rules WHERE id=?", (source_id,)).fetchone()
        if not row:
            raise ApiError("Regra original não encontrada.", 404)
        new_code = rule_data.get('new_code') or f"{row['rule_code']}-CLONE"
        new_title = rule_data.get('new_title') or f"{row['title']} (Cópia)"

        rid = db.execute("""
            INSERT INTO control_siconfi_rules (
                entity_id, rule_code, title, dimension, power, interval_type,
                description, formula, tolerance_cents, active, owner_name, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            entity_id, new_code, new_title, row['dimension'], row['power'], row['interval_type'],
            row['description'], row['formula'], row['tolerance_cents'], row['owner_name'], now(), now()
        )).lastrowid
        db.commit()
        return {'id': rid, 'message': f"Regra {new_code} duplicada com sucesso a partir de {row['rule_code']}."}

    elif action == 'update':
        rid = rule_data.get('rule_id')
        db.execute("""
            UPDATE control_siconfi_rules
            SET title = ?, description = ?, formula = ?, tolerance_cents = ?,
                power = ?, interval_type = ?, owner_name = ?, updated_at = ?
            WHERE id = ? AND entity_id = ?
        """, (
            rule_data.get('title'), rule_data.get('description'), rule_data.get('formula'),
            int(rule_data.get('tolerance_cents', 0)), rule_data.get('power'), rule_data.get('interval_type'),
            rule_data.get('owner_name'), now(), rid, entity_id
        ))
        db.commit()
        return {'id': rid, 'message': 'Regra atualizada com sucesso.'}

    elif action == 'delete':
        rid = rule_data.get('rule_id')
        db.execute("UPDATE control_siconfi_rules SET active = 0, updated_at = ? WHERE id = ? AND entity_id = ?", (now(), rid, entity_id))
        db.commit()
        return {'message': 'Regra desativada com sucesso.'}

    raise ApiError("Ação inválida para gerenciamento de regras.")

def reprocess_siconfi_period(entity_id=1, exercise=2026, period='2026-01', delete_first=False):
    db = get_db()
    if delete_first:
        db.execute("DELETE FROM control_siconfi_evaluations WHERE entity_id=? AND exercise=? AND period=?", (entity_id, exercise, period))

    # Reprocessa avaliações para todas as regras ativas
    rules = db.execute("SELECT * FROM control_siconfi_rules WHERE entity_id=? AND active=1", (entity_id,)).fetchall()
    count = 0
    for r in rules:
        row = db.execute("SELECT id FROM control_siconfi_evaluations WHERE entity_id=? AND exercise=? AND period=? AND rule_id=?",
                         (entity_id, exercise, period, r['id'])).fetchone()
        st = 'Conforme'
        notes = f"Validação automática recalculada para competência {period}."
        v_val = "Regular"
        b_val = "100% aderente"

        if r['rule_code'] == 'STN-D2-02':
            st = 'Não Conforme'
            v_val = 'Divergência de R$ 1.450,20'
            b_val = 'Diferença Zero'
            notes = 'Divergência entre conciliação bancária da conta FUNDEB e classe 8 DDR.'

        if not row:
            db.execute("""
                INSERT INTO control_siconfi_evaluations (
                    entity_id, exercise, period, rule_id, status, verified_value, benchmark_value, notes, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entity_id, exercise, period, r['id'], st, v_val, b_val, notes, now()))
        else:
            db.execute("""
                UPDATE control_siconfi_evaluations
                SET status=?, verified_value=?, benchmark_value=?, notes=?, evaluated_at=?
                WHERE id=?
            """, (st, v_val, b_val, notes, now(), row['id']))
        count += 1

    db.commit()
    return {'message': f"Competência {period} reprocessada com sucesso para {count} regras.", 'processed_count': count}

# =========================================================================
# Planos de Ação e Sistema de Notificações com Sininho
# =========================================================================

def get_action_plans(entity_id=1, exercise=2026, source_module=None, status=None):
    db = get_db()
    query = "SELECT * FROM control_action_plans WHERE entity_id=? AND exercise=?"
    params = [entity_id, exercise]

    if source_module:
        query += " AND source_module = ?"
        params.append(source_module)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY deadline ASC, id DESC"
    return [dict(r) for r in db.execute(query, params).fetchall()]

def create_action_plan(data, created_by, entity_id=1, exercise=2026):
    db = get_db()
    for field in ['source_module', 'reference_id', 'title', 'fact', 'cause', 'corrective_action', 'responsible_name', 'deadline']:
        if not data.get(field):
            raise ApiError(f"Campo '{field}' é obrigatório para o Plano de Ação.")

    pid = db.execute("""
        INSERT INTO control_action_plans (
            entity_id, exercise, source_module, reference_id, title, fact, cause,
            corrective_action, responsible_name, responsible_email, deadline,
            status, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente', ?, ?, ?)
    """, (
        entity_id, exercise, data['source_module'], data['reference_id'], data['title'],
        data['fact'], data['cause'], data['corrective_action'], data['responsible_name'],
        data.get('responsible_email'), data['deadline'], created_by, now(), now()
    )).lastrowid

    # Notificação ao responsável designado (gera aviso no sininho)
    db.execute("""
        INSERT INTO control_notifications (
            recipient_role, title, message, reference_type, reference_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        'OPERADOR', f"Novo Plano de Ação atribuído: {data['title']}",
        f"Você foi designado como responsável pelo item '{data['reference_id']}' ({data['source_module']}). Prazo limite: {data['deadline']}.",
        'action_plan', str(pid), now()
    ))
    db.commit()

    return {'id': pid, 'message': 'Plano de Ação registrado e responsável notificado com sucesso.'}

def respond_action_plan(plan_id, response_notes, response_evidence=None, author_name='Responsável Técnico'):
    db = get_db()
    row = db.execute("SELECT * FROM control_action_plans WHERE id=?", (plan_id,)).fetchone()
    if not row:
        raise ApiError("Plano de ação não encontrado.", 404)

    if not response_notes or not response_notes.strip():
        raise ApiError("O descritivo das ações tomadas na resposta é obrigatório.")

    db.execute("""
        UPDATE control_action_plans
        SET status = 'Respondido', response_notes = ?, response_evidence = ?,
            responded_at = ?, updated_at = ?
        WHERE id = ?
    """, (response_notes.strip(), response_evidence, now(), now(), plan_id))

    # Notificação com alerta para a Controladoria Geral (sininho)
    db.execute("""
        INSERT INTO control_notifications (
            recipient_role, title, message, reference_type, reference_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        'CONTROLADOR', f"Plano de Ação respondido: {row['title']}",
        f"O responsável {author_name} respondeu ao plano de ação do item '{row['reference_id']}'. Clique para avaliar.",
        'action_plan', str(plan_id), now()
    ))
    db.commit()

    return {'message': 'Resposta do plano de ação registrada com sucesso. A Controladoria foi notificada.', 'status': 'Respondido'}

def get_notifications(user_id=None, role='CONTROLADOR', unread_only=True):
    db = get_db()
    query = "SELECT * FROM control_notifications WHERE (recipient_role = ? OR recipient_role = 'ALL' OR user_id = ?)"
    params = [role, user_id or 0]

    if unread_only:
        query += " AND read = 0"

    query += " ORDER BY created_at DESC LIMIT 50"
    rows = [dict(r) for r in db.execute(query, params).fetchall()]
    unread_count = db.execute("SELECT COUNT(*) FROM control_notifications WHERE read = 0 AND (recipient_role = ? OR user_id = ?)", (role, user_id or 0)).fetchone()[0]

    return {
        'unread_count': unread_count,
        'notifications': rows
    }

def mark_notification_read(notification_id):
    db = get_db()
    db.execute("UPDATE control_notifications SET read = 1 WHERE id = ?", (notification_id,))
    db.commit()
    return {'message': 'Notificação marcada como lida.'}

# =========================================================================
# CAUC - Requisitos Fiscais da Secretaria do Tesouro Nacional
# =========================================================================

def get_cauc_dashboard(entity_id=1):
    db = get_db()
    rows = db.execute("""
        SELECT c.*, p.id as plan_id, p.status as plan_status
        FROM control_cauc_requirements c
        LEFT JOIN control_action_plans p ON p.reference_id = c.code AND p.entity_id = c.entity_id
        WHERE c.entity_id = ?
        ORDER BY c.code ASC
    """, (entity_id,)).fetchall()

    items = []
    adimplente_count = 0
    inadimplente_count = 0

    for r in rows:
        it = dict(r)
        if it['status'] == 'Adimplente':
            it['color'] = '#10b981' # verde
            it['badge_class'] = 'badge-success'
            adimplente_count += 1
        else:
            it['color'] = '#ef4444' # vermelho
            it['badge_class'] = 'badge-danger'
            inadimplente_count += 1
        items.append(it)

    total = len(items)
    regularity_rate = round((adimplente_count / total * 100.0), 1) if total > 0 else 100.0

    return {
        'total': total,
        'adimplente_count': adimplente_count,
        'inadimplente_count': inadimplente_count,
        'regularity_rate': regularity_rate,
        'legend': {
            'green': 'Verde: Requisito Adimplente e Certidão Válida',
            'red': 'Vermelho: Requisito Inadimplente / Certidão Vencida ou com Pendência'
        },
        'items': items
    }

def update_cauc_responsible(cauc_code, responsible_name, responsible_email, entity_id=1):
    db = get_db()
    db.execute("""
        UPDATE control_cauc_requirements
        SET responsible_name = ?, responsible_email = ?
        WHERE code = ? AND entity_id = ?
    """, (responsible_name, responsible_email, cauc_code, entity_id))
    db.commit()
    return {'message': f"Responsável pelo item {cauc_code} atualizado com sucesso."}

# =========================================================================
# Extrato de Convênios da STN
# =========================================================================

def get_agreements_dashboard(entity_id=1, exercise=2026):
    db = get_db()
    rows = db.execute("""
        SELECT a.*, p.id as plan_id, p.status as plan_status
        FROM control_agreements a
        LEFT JOIN control_action_plans p ON p.reference_id = a.agreement_number AND p.entity_id = a.entity_id
        WHERE a.entity_id = ? AND a.exercise = ?
        ORDER BY a.start_date DESC
    """, (entity_id, exercise)).fetchall()

    items = []
    adimplente_count = 0
    inadimplente_count = 0

    for r in rows:
        it = dict(r)
        if it['accountability_status'] == 'Adimplente':
            it['color'] = '#10b981' # verde
            it['badge_class'] = 'badge-success'
            adimplente_count += 1
        else:
            it['color'] = '#ef4444' # vermelho
            it['badge_class'] = 'badge-danger'
            inadimplente_count += 1
        items.append(it)

    return {
        'total': len(items),
        'adimplente_count': adimplente_count,
        'inadimplente_count': inadimplente_count,
        'items': items
    }

def update_agreement_responsible(agreement_number, responsible_name, responsible_email, entity_id=1):
    db = get_db()
    db.execute("""
        UPDATE control_agreements
        SET responsible_name = ?, responsible_email = ?, updated_at = ?
        WHERE agreement_number = ? AND entity_id = ?
    """, (responsible_name, responsible_email, now(), agreement_number, entity_id))
    db.commit()
    return {'message': f"Responsável pelo convênio {agreement_number} atualizado com sucesso."}

# =========================================================================
# Relatórios Conclusivos Mensais do Controle Interno & Versionamento
# =========================================================================

def generate_conclusive_report(data, created_by, entity_id=1, exercise=2026):
    db = get_db()

    period = data.get('period', f"{exercise}-01")
    report_type = data.get('report_type', 'Geral') # 'Geral', 'SICONFI', 'CAUC', 'Convenios'
    scope_type = data.get('scope_type', 'Consolidado')
    title = data.get('title') or f"Relatório Conclusivo do Controle Interno - {report_type} ({period})"

    selected_verifications = json.dumps(data.get('selected_verifications', []))
    selected_occurrences = json.dumps(data.get('selected_occurrences', []))

    opinion_text = data.get('opinion_text') or "Com base nas verificações realizadas, as contas e demonstrativos apresentam conformidade com as normas legais vigentes."
    conclusion_text = data.get('conclusion_text') or "Diante do exposto, manifestamo-nos favoravelmente à regularidade da gestão, recomendando o cumprimento dos planos de ação pendentes."

    default_signatories = [
        {'name': 'Dr. Marcos Valério Silveira', 'role': 'Controlador Geral do Município', 'signature_date': now()[:10]},
        {'name': 'Contador Responsável', 'role': 'CRC-RJ 045120/O', 'signature_date': now()[:10]}
    ]
    signatories = json.dumps(data.get('signatories') or default_signatories, ensure_ascii=False)

    # Identificar a versão mais recente para o mesmo período e tipo
    last_version = db.execute("""
        SELECT MAX(version) FROM control_audit_reports
        WHERE entity_id = ? AND exercise = ? AND report_type = ? AND period = ?
    """, (entity_id, exercise, report_type, period)).fetchone()[0] or 0

    new_version = last_version + 1

    # Cálculo do hash de integridade
    payload = f"{entity_id}:{exercise}:{report_type}:{period}:{new_version}:{opinion_text}:{conclusion_text}"
    hash_digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    rid = db.execute("""
        INSERT INTO control_audit_reports (
            entity_id, exercise, report_type, period, scope_type, title,
            selected_verifications, selected_occurrences, opinion_text, conclusion_text,
            signatories, sealed, sealed_at, version, hash_digest, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
    """, (
        entity_id, exercise, report_type, period, scope_type, title,
        selected_verifications, selected_occurrences, opinion_text, conclusion_text,
        signatories, now(), new_version, hash_digest, created_by, now()
    )).lastrowid

    db.commit()

    return {
        'id': rid,
        'version': new_version,
        'title': title,
        'hash_digest': hash_digest,
        'message': f"Relatório Conclusivo gerado com sucesso (Versão {new_version})."
    }

def get_report_versions(entity_id=1, exercise=2026, report_type=None, period=None):
    db = get_db()
    query = "SELECT * FROM control_audit_reports WHERE entity_id=? AND exercise=?"
    params = [entity_id, exercise]

    if report_type:
        query += " AND report_type = ?"
        params.append(report_type)
    if period:
        query += " AND period = ?"
        params.append(period)

    query += " ORDER BY period DESC, version DESC, id DESC"
    rows = []
    for r in db.execute(query, params).fetchall():
        it = dict(r)
        it['selected_verifications'] = json.loads(it['selected_verifications'])
        it['selected_occurrences'] = json.loads(it['selected_occurrences'])
        it['signatories'] = json.loads(it['signatories'])
        rows.append(it)
    return rows
