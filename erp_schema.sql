CREATE TABLE IF NOT EXISTS erp_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS erp_entities(id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, cnpj TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS erp_entity_access(user_id INTEGER NOT NULL REFERENCES users(id),entity_id INTEGER NOT NULL REFERENCES erp_entities(id),PRIMARY KEY(user_id,entity_id));
CREATE TABLE IF NOT EXISTS erp_objects(
 id INTEGER PRIMARY KEY,entity_id INTEGER NOT NULL REFERENCES erp_entities(id),exercise INTEGER NOT NULL,
 module TEXT NOT NULL,kind TEXT NOT NULL,code TEXT NOT NULL,name TEXT NOT NULL,data TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'Rascunho',version INTEGER NOT NULL DEFAULT 1,deleted INTEGER NOT NULL DEFAULT 0,
 created_by INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
 UNIQUE(entity_id,exercise,module,kind,code)
);
CREATE INDEX IF NOT EXISTS erp_objects_query ON erp_objects(entity_id,exercise,module,kind,deleted,id DESC);
CREATE TABLE IF NOT EXISTS erp_links(source_id INTEGER NOT NULL REFERENCES erp_objects(id),field TEXT NOT NULL,target_id INTEGER NOT NULL REFERENCES erp_objects(id),PRIMARY KEY(source_id,field));
CREATE INDEX IF NOT EXISTS erp_links_target ON erp_links(target_id,field);
CREATE TABLE IF NOT EXISTS erp_events(id INTEGER PRIMARY KEY,object_id INTEGER NOT NULL REFERENCES erp_objects(id),operation TEXT NOT NULL,payload TEXT NOT NULL,actor INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS erp_events_object ON erp_events(object_id,id);
CREATE TRIGGER IF NOT EXISTS erp_events_no_update BEFORE UPDATE ON erp_events BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TRIGGER IF NOT EXISTS erp_events_no_delete BEFORE DELETE ON erp_events BEGIN SELECT RAISE(ABORT,'Histórico imutável'); END;
CREATE TABLE IF NOT EXISTS erp_balances(object_id INTEGER NOT NULL REFERENCES erp_objects(id),name TEXT NOT NULL,value INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(object_id,name));
CREATE TABLE IF NOT EXISTS erp_stock(warehouse_id INTEGER NOT NULL REFERENCES erp_objects(id),material_id INTEGER NOT NULL REFERENCES erp_objects(id),quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),value INTEGER NOT NULL DEFAULT 0 CHECK(value>=0),PRIMARY KEY(warehouse_id,material_id));
CREATE TABLE IF NOT EXISTS erp_stock_ledger(id INTEGER PRIMARY KEY,source_id INTEGER NOT NULL REFERENCES erp_objects(id),warehouse_id INTEGER NOT NULL REFERENCES erp_objects(id),material_id INTEGER NOT NULL REFERENCES erp_objects(id),date TEXT NOT NULL,quantity INTEGER NOT NULL,value INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS erp_ledger(id INTEGER PRIMARY KEY,source_id INTEGER NOT NULL REFERENCES erp_objects(id),entity_id INTEGER NOT NULL REFERENCES erp_entities(id),exercise INTEGER NOT NULL,date TEXT NOT NULL,account_id INTEGER NOT NULL REFERENCES erp_objects(id),debit INTEGER NOT NULL DEFAULT 0 CHECK(debit>=0),credit INTEGER NOT NULL DEFAULT 0 CHECK(credit>=0),reversal INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,CHECK((debit=0 AND credit>=0) OR (credit=0 AND debit>=0)));
CREATE INDEX IF NOT EXISTS erp_ledger_report ON erp_ledger(entity_id,exercise,date,account_id);
CREATE TABLE IF NOT EXISTS erp_depreciation(id INTEGER PRIMARY KEY,asset_id INTEGER NOT NULL REFERENCES erp_objects(id),period TEXT NOT NULL,amount INTEGER NOT NULL CHECK(amount>=0),units INTEGER NOT NULL DEFAULT 0,actor INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL,UNIQUE(asset_id,period));
CREATE TABLE IF NOT EXISTS erp_payroll_lines(id INTEGER PRIMARY KEY,run_id INTEGER NOT NULL REFERENCES erp_objects(id),employee_id INTEGER NOT NULL REFERENCES erp_objects(id),gross INTEGER NOT NULL,pension INTEGER NOT NULL,tax INTEGER NOT NULL,other INTEGER NOT NULL,consigned INTEGER NOT NULL,net INTEGER NOT NULL,employer INTEGER NOT NULL,memory TEXT NOT NULL,UNIQUE(run_id,employee_id));
CREATE TABLE IF NOT EXISTS erp_attachments(id INTEGER PRIMARY KEY,object_id INTEGER NOT NULL REFERENCES erp_objects(id),name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT NOT NULL,encrypted BLOB NOT NULL,created_by INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS erp_preferences(user_id INTEGER NOT NULL REFERENCES users(id),key TEXT NOT NULL,value TEXT NOT NULL,PRIMARY KEY(user_id,key));
