PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, permissions TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
 group_id INTEGER NOT NULL REFERENCES groups(id), department TEXT NOT NULL DEFAULT '',
 active INTEGER NOT NULL DEFAULT 1, force_password INTEGER NOT NULL DEFAULT 0,
 failures INTEGER NOT NULL DEFAULT 0, locked_until TEXT, schedule TEXT NOT NULL DEFAULT '{}',
 permissions TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, user_id INTEGER, actor TEXT NOT NULL, action TEXT NOT NULL, module TEXT NOT NULL, target TEXT, detail TEXT NOT NULL, ip TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'Auditoria imutável'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'Auditoria imutável'); END;
CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, module TEXT NOT NULL, title TEXT NOT NULL, department TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, amount INTEGER NOT NULL DEFAULT 0, data TEXT NOT NULL, created_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS records_module_created ON records(module,created_at);
CREATE INDEX IF NOT EXISTS records_updated ON records(updated_at DESC,id DESC);
CREATE INDEX IF NOT EXISTS records_module_status ON records(module,status,updated_at);
CREATE TABLE IF NOT EXISTS approvals (id INTEGER PRIMARY KEY, module TEXT NOT NULL, operation TEXT NOT NULL, record_id INTEGER, payload TEXT NOT NULL, requester INTEGER NOT NULL REFERENCES users(id), reviewer INTEGER REFERENCES users(id), status TEXT NOT NULL DEFAULT 'Pendente', reason TEXT, created_at TEXT NOT NULL, decided_at TEXT);
CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, body TEXT NOT NULL, read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS shortcuts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, url TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS training_progress (user_id INTEGER REFERENCES users(id), lesson TEXT, completed_at TEXT, PRIMARY KEY(user_id,lesson));
CREATE TABLE IF NOT EXISTS ticket_comments (id INTEGER PRIMARY KEY, record_id INTEGER NOT NULL REFERENCES records(id), user_id INTEGER NOT NULL REFERENCES users(id), body TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY, name TEXT NOT NULL, encrypted_script TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS audit_created ON audit(created_at);
CREATE INDEX IF NOT EXISTS notifications_user ON notifications(user_id,read);
