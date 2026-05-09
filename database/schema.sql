-- 印刷色彩预测与校准智能体 Database Schema
-- Uses SQLite with FTS5 for full-text search

-- ============================================================
-- Table: knowledge_base
-- Stores color management reference articles, terminology, best practices
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    tags        TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ============================================================
-- FTS5 Virtual Table: knowledge_fts
-- Full-text search index for knowledge_base with BM25 ranking
-- ============================================================
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title,
    content,
    tags,
    content='knowledge_base',
    content_rowid='id'
);

-- Triggers to keep FTS index in sync with knowledge_base
CREATE TRIGGER IF NOT EXISTS kb_ai AFTER INSERT ON knowledge_base BEGIN
    INSERT INTO knowledge_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS kb_ad AFTER DELETE ON knowledge_base BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS kb_au AFTER UPDATE ON knowledge_base BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
    INSERT INTO knowledge_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;

-- ============================================================
-- Table: calibration_history
-- Stores calibration events for historical reference queries
-- ============================================================
CREATE TABLE IF NOT EXISTS calibration_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_type      TEXT    NOT NULL,
    target_c        REAL    NOT NULL,
    target_m        REAL    NOT NULL,
    target_y        REAL    NOT NULL,
    target_k        REAL    NOT NULL,
    target_l        REAL,
    target_a        REAL,
    target_b        REAL,
    predicted_l     REAL,
    predicted_a     REAL,
    predicted_b     REAL,
    delta_e         REAL,
    advice_summary  TEXT,
    operator_notes  TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ============================================================
-- Table: paper_types
-- Master table for paper profiles with conversion parameters
-- ============================================================
CREATE TABLE IF NOT EXISTS paper_types (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT    NOT NULL UNIQUE,
    weight_gsm        INTEGER NOT NULL,
    surface           TEXT    NOT NULL,
    dot_gain_pct      REAL    NOT NULL DEFAULT 15.0,
    max_ink_pct       REAL    NOT NULL DEFAULT 340.0,
    white_point_l     REAL    NOT NULL DEFAULT 95.0,
    white_point_a     REAL    NOT NULL DEFAULT 0.0,
    white_point_b     REAL    NOT NULL DEFAULT 0.0,
    description       TEXT,
    conversion_matrix TEXT    NOT NULL
);

-- ============================================================
-- Table: color_conversion_lut
-- Fine-grained lookup table for CMYK-to-Lab conversion per paper
-- ============================================================
CREATE TABLE IF NOT EXISTS color_conversion_lut (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id  INTEGER NOT NULL REFERENCES paper_types(id),
    c         REAL    NOT NULL,
    m         REAL    NOT NULL,
    y         REAL    NOT NULL,
    k         REAL    NOT NULL,
    lab_l     REAL    NOT NULL,
    lab_a     REAL    NOT NULL,
    lab_b     REAL    NOT NULL,
    UNIQUE(paper_id, c, m, y, k)
);
