-- works_schema.sql: Tabelas auxiliares e complementares do módulo de Obras Públicas
CREATE TABLE IF NOT EXISTS works_diary_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diary_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    caption TEXT DEFAULT '',
    approved INTEGER DEFAULT 0,
    approved_by INTEGER REFERENCES users(id),
    approved_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS works_spreadsheet_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    active INTEGER DEFAULT 1,
    justification TEXT NOT NULL,
    bdi_linear REAL DEFAULT 0,
    discount_linear REAL DEFAULT 0,
    total_amount INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS works_engineer_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES erp_objects(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'Fiscal',
    allowed INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_works_photos_diary ON works_diary_photos(diary_id);
CREATE INDEX IF NOT EXISTS idx_works_photos_project ON works_diary_photos(project_id);
CREATE INDEX IF NOT EXISTS idx_works_versions_project ON works_spreadsheet_versions(project_id);
CREATE INDEX IF NOT EXISTS idx_works_assignments_user ON works_engineer_assignments(user_id);
