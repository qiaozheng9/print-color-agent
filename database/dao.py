"""Data Access Objects for parameterized database queries."""

from __future__ import annotations

from database.db_manager import get_connection


class KnowledgeDAO:
    """DAO for knowledge_base table with FTS5 search."""

    @staticmethod
    def search(query: str, limit: int = 5) -> list[dict]:
        """Run FTS5 MATCH query, return ranked results with BM25 relevance score."""
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT kb.id, kb.title, kb.category, kb.content, kb.tags,
                       bm25(knowledge_fts) AS rank
                FROM knowledge_fts
                JOIN knowledge_base kb ON knowledge_fts.rowid = kb.id
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(article_id: int) -> dict | None:
        """Retrieve a single knowledge article by ID."""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM knowledge_base WHERE id = ?",
                (article_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def insert(title: str, category: str, content: str, tags: str = "") -> int:
        """Insert a new knowledge article, return its ID."""
        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO knowledge_base (title, category, content, tags) VALUES (?, ?, ?, ?)",
                (title, category, content, tags),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_all(limit: int = 100) -> list[dict]:
        """Return all knowledge articles up to limit."""
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, title, category, tags, created_at FROM knowledge_base ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


class CalibrationDAO:
    """DAO for calibration_history table."""

    @staticmethod
    def insert(
        paper_type: str,
        target_c: float,
        target_m: float,
        target_y: float,
        target_k: float,
        target_lab: tuple[float, float, float] | None = None,
        predicted_lab: tuple[float, float, float] | None = None,
        delta_e: float | None = None,
        advice_summary: str = "",
        operator_notes: str = "",
    ) -> int:
        """Insert a calibration record, return its ID."""
        conn = get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO calibration_history
                    (paper_type, target_c, target_m, target_y, target_k,
                     target_l, target_a, target_b,
                     predicted_l, predicted_a, predicted_b,
                     delta_e, advice_summary, operator_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper_type,
                    target_c, target_m, target_y, target_k,
                    target_lab[0] if target_lab else None,
                    target_lab[1] if target_lab else None,
                    target_lab[2] if target_lab else None,
                    predicted_lab[0] if predicted_lab else None,
                    predicted_lab[1] if predicted_lab else None,
                    predicted_lab[2] if predicted_lab else None,
                    delta_e,
                    advice_summary,
                    operator_notes,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def search(
        paper_type: str | None = None,
        max_delta_e: float | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search calibration history with optional filters."""
        conditions = []
        params: list = []
        if paper_type:
            conditions.append("paper_type = ?")
            params.append(paper_type)
        if max_delta_e is not None:
            conditions.append("delta_e <= ?")
            params.append(max_delta_e)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        conn = get_connection()
        try:
            rows = conn.execute(
                f"""
                SELECT * FROM calibration_history
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(record_id: int) -> dict | None:
        """Retrieve a single calibration record by ID."""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM calibration_history WHERE id = ?",
                (record_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


class PaperTypeDAO:
    """DAO for paper_types table."""

    @staticmethod
    def get_all() -> list[dict]:
        """Return all paper types."""
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, name, weight_gsm, surface, dot_gain_pct, max_ink_pct, "
                "white_point_l, white_point_a, white_point_b, description, conversion_matrix "
                "FROM paper_types ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_name(name: str) -> dict | None:
        """Retrieve a paper type by name."""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM paper_types WHERE name = ?",
                (name,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


class LUTDAO:
    """DAO for color_conversion_lut table."""

    @staticmethod
    def get_nearest(paper_id: int, c: float, m: float, y: float, k: float) -> list[dict]:
        """Retrieve the nearest LUT grid points for interpolation.

        Returns up to 8 nearest points (corners of the enclosing hypercube)
        ordered by Euclidean distance in CMYK space.
        """
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT c, m, y, k, lab_l, lab_a, lab_b,
                       ((c - ?) * (c - ?) + (m - ?) * (m - ?) +
                        (y - ?) * (y - ?) + (k - ?) * (k - ?)) AS dist_sq
                FROM color_conversion_lut
                WHERE paper_id = ?
                ORDER BY dist_sq
                LIMIT 8
                """,
                (c, c, m, m, y, y, k, k, paper_id),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
