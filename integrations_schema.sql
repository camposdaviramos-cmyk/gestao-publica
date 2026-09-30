CREATE TABLE IF NOT EXISTS integration_configs (
 entity_id INTEGER NOT NULL REFERENCES erp_entities(id), provider TEXT NOT NULL,
 environment TEXT NOT NULL CHECK(environment IN ('homologacao','producao')),
 enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
 parameters TEXT NOT NULL DEFAULT '{}', encrypted_secrets TEXT NOT NULL,
 certificate_meta TEXT NOT NULL DEFAULT '{}', version INTEGER NOT NULL DEFAULT 1,
 updated_by INTEGER NOT NULL REFERENCES users(id), updated_at TEXT NOT NULL,
 PRIMARY KEY(entity_id,provider,environment)
);
CREATE TABLE IF NOT EXISTS integration_checks (
 id INTEGER PRIMARY KEY, entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
 provider TEXT NOT NULL, environment TEXT NOT NULL, operation TEXT NOT NULL,
 success INTEGER NOT NULL, message TEXT NOT NULL, duration_ms INTEGER NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS integration_checks_context ON integration_checks(entity_id,provider,environment,id DESC);
CREATE TABLE IF NOT EXISTS integration_jobs (
 id INTEGER PRIMARY KEY, entity_id INTEGER NOT NULL REFERENCES erp_entities(id),
 provider TEXT NOT NULL, environment TEXT NOT NULL,
 source_id INTEGER NOT NULL REFERENCES erp_objects(id), source_version INTEGER NOT NULL, source_fingerprint TEXT NOT NULL,
 operation TEXT NOT NULL, payload TEXT NOT NULL, encrypted_document TEXT NOT NULL,
 document_title TEXT NOT NULL, document_type INTEGER NOT NULL,
 digest TEXT NOT NULL, config_version INTEGER NOT NULL,
 state TEXT NOT NULL DEFAULT 'Preparado', version INTEGER NOT NULL DEFAULT 1,
 created_by INTEGER NOT NULL REFERENCES users(id), approved_by INTEGER REFERENCES users(id),
 receipt TEXT NOT NULL DEFAULT '{}', message TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(entity_id,provider,environment,digest)
);
CREATE INDEX IF NOT EXISTS integration_jobs_context ON integration_jobs(entity_id,environment,id DESC);
CREATE TABLE IF NOT EXISTS integration_job_events (
 id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES integration_jobs(id),
 state TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES users(id),
 detail TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS integration_events_no_update BEFORE UPDATE ON integration_job_events BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TRIGGER IF NOT EXISTS integration_events_no_delete BEFORE DELETE ON integration_job_events BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TRIGGER IF NOT EXISTS integration_checks_no_update BEFORE UPDATE ON integration_checks BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TRIGGER IF NOT EXISTS integration_checks_no_delete BEFORE DELETE ON integration_checks BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TRIGGER IF NOT EXISTS integration_jobs_snapshot BEFORE UPDATE OF entity_id,provider,environment,source_id,source_version,source_fingerprint,operation,payload,encrypted_document,document_title,document_type,digest,config_version,created_by ON integration_jobs BEGIN SELECT RAISE(ABORT,'Pacote imutável'); END;
