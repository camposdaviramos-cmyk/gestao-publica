CREATE TABLE IF NOT EXISTS inventory_permissions(target_id INTEGER NOT NULL REFERENCES erp_objects(id),user_id INTEGER NOT NULL REFERENCES users(id),allowed INTEGER NOT NULL CHECK(allowed IN(0,1)),actor_id INTEGER NOT NULL REFERENCES users(id),updated_at TEXT NOT NULL,PRIMARY KEY(target_id,user_id));
CREATE TABLE IF NOT EXISTS inventory_fulfillments(id INTEGER PRIMARY KEY,item_id INTEGER NOT NULL REFERENCES erp_objects(id),movement_id INTEGER NOT NULL UNIQUE REFERENCES erp_objects(id),kind TEXT NOT NULL,original_id INTEGER REFERENCES inventory_fulfillments(id),quantity INTEGER NOT NULL CHECK(quantity>0),value INTEGER NOT NULL CHECK(value>=0),date TEXT NOT NULL,actor_id INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS inventory_fulfillment_item ON inventory_fulfillments(item_id,date);
CREATE TABLE IF NOT EXISTS inventory_accounting(stock_ledger_id INTEGER PRIMARY KEY REFERENCES erp_stock_ledger(id),rule_id INTEGER NOT NULL REFERENCES erp_objects(id),debit_entry INTEGER NOT NULL REFERENCES erp_ledger(id),credit_entry INTEGER NOT NULL REFERENCES erp_ledger(id),created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS inventory_invoice_postings(invoice_id INTEGER PRIMARY KEY REFERENCES erp_objects(id),settlement_id INTEGER NOT NULL UNIQUE REFERENCES erp_objects(id),amount INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS inventory_fulfillments_no_update BEFORE UPDATE ON inventory_fulfillments BEGIN SELECT RAISE(ABORT,'Entrega preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_fulfillments_no_delete BEFORE DELETE ON inventory_fulfillments BEGIN SELECT RAISE(ABORT,'Entrega preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_accounting_no_update BEFORE UPDATE ON inventory_accounting BEGIN SELECT RAISE(ABORT,'Contabilização preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_accounting_no_delete BEFORE DELETE ON inventory_accounting BEGIN SELECT RAISE(ABORT,'Contabilização preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_postings_no_update BEFORE UPDATE ON inventory_invoice_postings BEGIN SELECT RAISE(ABORT,'Liquidação preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_postings_no_delete BEFORE DELETE ON inventory_invoice_postings BEGIN SELECT RAISE(ABORT,'Liquidação preservada'); END;

CREATE INDEX IF NOT EXISTS inventory_stock_history ON erp_stock_ledger(warehouse_id,material_id,date);
CREATE TABLE IF NOT EXISTS inventory_classification_imports(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,version TEXT NOT NULL,sha256 TEXT NOT NULL,source TEXT NOT NULL,payload BLOB NOT NULL,imported_at TEXT NOT NULL,actor_id INTEGER NOT NULL REFERENCES users(id));
CREATE TRIGGER IF NOT EXISTS inventory_classification_no_update BEFORE UPDATE ON inventory_classification_imports BEGIN SELECT RAISE(ABORT,'Versão oficial preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_classification_no_delete BEFORE DELETE ON inventory_classification_imports BEGIN SELECT RAISE(ABORT,'Versão oficial preservada'); END;

CREATE TABLE IF NOT EXISTS inventory_movement_postings(movement_id INTEGER PRIMARY KEY REFERENCES erp_objects(id),settlement_id INTEGER NOT NULL UNIQUE REFERENCES erp_objects(id),amount INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS inventory_movement_postings_no_update BEFORE UPDATE ON inventory_movement_postings BEGIN SELECT RAISE(ABORT,'Liquidação preservada'); END;
CREATE TRIGGER IF NOT EXISTS inventory_movement_postings_no_delete BEFORE DELETE ON inventory_movement_postings BEGIN SELECT RAISE(ABORT,'Liquidação preservada'); END;
