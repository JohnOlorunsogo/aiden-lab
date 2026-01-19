"""Database service for storing errors and solutions."""
import aiosqlite
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.config import settings
from app.models.error import DetectedError, Solution, Severity, ErrorWithSolution


class Database:
    """Async SQLite database service."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.get_db_path()
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Initialize database connection and create tables."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._create_tables()
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        await self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                error_line TEXT NOT NULL,
                context TEXT NOT NULL,
                severity TEXT NOT NULL,
                pattern_matched TEXT,
                dismissed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id INTEGER NOT NULL REFERENCES errors(id),
                root_cause TEXT NOT NULL,
                impact TEXT NOT NULL,
                solution TEXT NOT NULL,
                prevention TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_errors_device ON errors(device_id);
            CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors(timestamp);
            CREATE INDEX IF NOT EXISTS idx_solutions_error ON solutions(error_id);
        """)
        # Add dismissed column if it doesn't exist (for existing databases)
        try:
            await self._connection.execute("ALTER TABLE errors ADD COLUMN dismissed INTEGER DEFAULT 0")
            await self._connection.commit()
        except Exception:
            pass  # Column already exists
        await self._connection.commit()
    
    async def insert_error(self, error: DetectedError) -> int:
        """Insert a detected error and return its ID."""
        cursor = await self._connection.execute(
            """
            INSERT INTO errors (device_id, timestamp, error_line, context, severity, pattern_matched)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                error.device_id,
                error.timestamp.isoformat(),
                error.error_line,
                error.context,
                error.severity.value,
                error.pattern_matched
            )
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def insert_solution(self, solution: Solution) -> int:
        """Insert an AI-generated solution and return its ID."""
        cursor = await self._connection.execute(
            """
            INSERT INTO solutions (error_id, root_cause, impact, solution, prevention)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                solution.error_id,
                solution.root_cause,
                solution.impact,
                solution.solution,
                solution.prevention
            )
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def get_errors(
        self, 
        page: int = 1, 
        per_page: int = 20,
        device_id: Optional[str] = None,
        severity: Optional[Severity] = None
    ) -> tuple[List[ErrorWithSolution], int]:
        """Get paginated list of errors with their solutions."""
        # Build query
        where_clauses = []
        params = []
        
        if device_id:
            where_clauses.append("e.device_id = ?")
            params.append(device_id)
        if severity:
            where_clauses.append("e.severity = ?")
            params.append(severity.value)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_cursor = await self._connection.execute(
            f"SELECT COUNT(*) FROM errors e WHERE {where_sql}",
            params
        )
        total = (await count_cursor.fetchone())[0]
        
        # Get paginated results
        offset = (page - 1) * per_page
        cursor = await self._connection.execute(
            f"""
            SELECT e.*, s.id as sol_id, s.root_cause, s.impact, s.solution, s.prevention, s.created_at as sol_created_at
            FROM errors e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE {where_sql}
            ORDER BY e.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        )
        
        rows = await cursor.fetchall()
        results = []
        
        for row in rows:
            error = DetectedError(
                id=row["id"],
                device_id=row["device_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                error_line=row["error_line"],
                context=row["context"],
                severity=Severity(row["severity"]),
                pattern_matched=row["pattern_matched"] or "",
                created_at=datetime.fromisoformat(row["created_at"])
            )
            
            solution = None
            if row["sol_id"]:
                solution = Solution(
                    id=row["sol_id"],
                    error_id=row["id"],
                    root_cause=row["root_cause"],
                    impact=row["impact"],
                    solution=row["solution"],
                    prevention=row["prevention"],
                    created_at=datetime.fromisoformat(row["sol_created_at"])
                )
            
            results.append(ErrorWithSolution(error=error, solution=solution))
        
        return results, total
    
    async def get_error_by_id(self, error_id: int) -> Optional[ErrorWithSolution]:
        """Get a specific error with its solution."""
        cursor = await self._connection.execute(
            """
            SELECT e.*, s.id as sol_id, s.root_cause, s.impact, s.solution, s.prevention, s.created_at as sol_created_at
            FROM errors e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE e.id = ?
            """,
            (error_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        error = DetectedError(
            id=row["id"],
            device_id=row["device_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            error_line=row["error_line"],
            context=row["context"],
            severity=Severity(row["severity"]),
            pattern_matched=row["pattern_matched"] or "",
            created_at=datetime.fromisoformat(row["created_at"])
        )
        
        solution = None
        if row["sol_id"]:
            solution = Solution(
                id=row["sol_id"],
                error_id=row["id"],
                root_cause=row["root_cause"],
                impact=row["impact"],
                solution=row["solution"],
                prevention=row["prevention"],
                created_at=datetime.fromisoformat(row["sol_created_at"])
            )
        
        return ErrorWithSolution(error=error, solution=solution)
    
    async def get_device_stats(self) -> List[dict]:
        """Get error statistics per device."""
        cursor = await self._connection.execute(
            """
            SELECT 
                device_id,
                COUNT(*) as error_count,
                MAX(timestamp) as last_error
            FROM errors
            GROUP BY device_id
            ORDER BY error_count DESC
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_errors_without_solutions(self) -> List[DetectedError]:
        """Get all errors that don't have solutions yet."""
        cursor = await self._connection.execute(
            """
            SELECT e.*
            FROM errors e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE s.id IS NULL
            ORDER BY e.created_at DESC
            """
        )
        rows = await cursor.fetchall()
        
        results = []
        for row in rows:
            error = DetectedError(
                id=row["id"],
                device_id=row["device_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                error_line=row["error_line"],
                context=row["context"],
                severity=Severity(row["severity"]),
                pattern_matched=row["pattern_matched"] or "",
                created_at=datetime.fromisoformat(row["created_at"])
            )
            results.append(error)
        
        return results
    
    async def dismiss_error(self, error_id: int) -> bool:
        """Dismiss a single error from the dashboard."""
        cursor = await self._connection.execute(
            "UPDATE errors SET dismissed = 1 WHERE id = ?",
            (error_id,)
        )
        await self._connection.commit()
        return cursor.rowcount > 0
    
    async def dismiss_all_errors(self) -> int:
        """Dismiss all errors from the dashboard."""
        cursor = await self._connection.execute(
            "UPDATE errors SET dismissed = 1 WHERE dismissed = 0"
        )
        await self._connection.commit()
        return cursor.rowcount
    
    async def get_active_errors(
        self, 
        page: int = 1, 
        per_page: int = 20
    ) -> tuple[List[ErrorWithSolution], int]:
        """Get paginated list of non-dismissed errors for dashboard."""
        # Get total count of non-dismissed errors
        count_cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM errors WHERE dismissed = 0"
        )
        total = (await count_cursor.fetchone())[0]
        
        # Get paginated results
        offset = (page - 1) * per_page
        cursor = await self._connection.execute(
            """
            SELECT e.*, s.id as sol_id, s.root_cause, s.impact, s.solution, s.prevention, s.created_at as sol_created_at
            FROM errors e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE e.dismissed = 0
            ORDER BY e.created_at DESC
            LIMIT ? OFFSET ?
            """,
            [per_page, offset]
        )
        
        rows = await cursor.fetchall()
        results = []
        
        for row in rows:
            error = DetectedError(
                id=row["id"],
                device_id=row["device_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                error_line=row["error_line"],
                context=row["context"],
                severity=Severity(row["severity"]),
                pattern_matched=row["pattern_matched"] or "",
                created_at=datetime.fromisoformat(row["created_at"])
            )
            
            solution = None
            if row["sol_id"]:
                solution = Solution(
                    id=row["sol_id"],
                    error_id=row["id"],
                    root_cause=row["root_cause"],
                    impact=row["impact"],
                    solution=row["solution"],
                    prevention=row["prevention"],
                    created_at=datetime.fromisoformat(row["sol_created_at"])
                )
            
            results.append(ErrorWithSolution(error=error, solution=solution))
        
        return results, total


# Global database instance
db = Database()
