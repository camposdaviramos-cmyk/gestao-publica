CREATE TABLE IF NOT EXISTS esocial_batches (
 id INTEGER PRIMARY KEY,entity_id INTEGER NOT NULL REFERENCES erp_entities(id),environment TEXT NOT NULL,
 group_number INTEGER NOT NULL,config_version INTEGER NOT NULL,parameters TEXT NOT NULL,
 state TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,encrypted_xml BLOB NOT NULL,xml_hash TEXT NOT NULL,
 certificate_hash TEXT NOT NULL,protocol TEXT,encrypted_response BLOB,response_summary TEXT NOT NULL DEFAULT '{}',
 created_by INTEGER NOT NULL REFERENCES users(id),approved_by INTEGER REFERENCES users(id),
 created_at TEXT NOT NULL,updated_at TEXT NOT NULL,next_query_at TEXT,last_message TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS esocial_batch_context ON esocial_batches(entity_id,environment,id DESC);
CREATE TABLE IF NOT EXISTS esocial_events (
 id INTEGER PRIMARY KEY,batch_id INTEGER NOT NULL REFERENCES esocial_batches(id),event_id TEXT NOT NULL,event_type TEXT NOT NULL,
 response_code TEXT,receipt TEXT,description TEXT,UNIQUE(batch_id,event_id)
);
CREATE INDEX IF NOT EXISTS esocial_event_identity ON esocial_events(event_id,batch_id);
CREATE TABLE IF NOT EXISTS esocial_history (
 id INTEGER PRIMARY KEY,batch_id INTEGER NOT NULL REFERENCES esocial_batches(id),action TEXT NOT NULL,details TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS esocial_batch_source_immutable BEFORE UPDATE ON esocial_batches
WHEN OLD.entity_id<>NEW.entity_id OR OLD.environment<>NEW.environment OR OLD.group_number<>NEW.group_number OR OLD.config_version<>NEW.config_version OR OLD.parameters<>NEW.parameters OR OLD.encrypted_xml<>NEW.encrypted_xml OR OLD.xml_hash<>NEW.xml_hash OR OLD.certificate_hash<>NEW.certificate_hash OR OLD.created_by<>NEW.created_by OR OLD.created_at<>NEW.created_at
BEGIN SELECT RAISE(ABORT,'Lote eSocial imutável'); END;
CREATE TRIGGER IF NOT EXISTS esocial_batch_no_delete BEFORE DELETE ON esocial_batches BEGIN SELECT RAISE(ABORT,'Lote eSocial preservado'); END;
CREATE TRIGGER IF NOT EXISTS esocial_event_source_immutable BEFORE UPDATE ON esocial_events WHEN OLD.batch_id<>NEW.batch_id OR OLD.event_id<>NEW.event_id OR OLD.event_type<>NEW.event_type BEGIN SELECT RAISE(ABORT,'Identidade do evento imutável'); END;
CREATE TRIGGER IF NOT EXISTS esocial_event_no_delete BEFORE DELETE ON esocial_events BEGIN SELECT RAISE(ABORT,'Evento preservado'); END;
CREATE TRIGGER IF NOT EXISTS esocial_history_no_update BEFORE UPDATE ON esocial_history BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TRIGGER IF NOT EXISTS esocial_history_no_delete BEFORE DELETE ON esocial_history BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;

CREATE TABLE IF NOT EXISTS esocial_responses(id INTEGER PRIMARY KEY,batch_id INTEGER NOT NULL REFERENCES esocial_batches(id),operation TEXT NOT NULL,code INTEGER NOT NULL,sha256 TEXT NOT NULL,encrypted_xml BLOB NOT NULL,created_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS esocial_response_no_update BEFORE UPDATE ON esocial_responses BEGIN SELECT RAISE(ABORT,'Retorno eSocial imutável'); END;
CREATE TRIGGER IF NOT EXISTS esocial_response_no_delete BEFORE DELETE ON esocial_responses BEGIN SELECT RAISE(ABORT,'Retorno eSocial preservado'); END;
