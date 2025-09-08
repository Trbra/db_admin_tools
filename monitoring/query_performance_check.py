import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path


# === Load credentials ===
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# === Logs directory ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"performance_check_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log")

def log(message):
    """Write to both console and log file."""
    print(message)
    with open(log_file, "a") as f:
        f.write(message + "\n")

def run_query(conn, description, sql):
    """Helper function to run and log query results."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            log(f"\n--- {description} ---")
            for row in rows:
                log(str(row))
    except Exception as e:
        log(f"[ERROR] {description} failed: {e}")

def main():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True;
        log(f"[{datetime.now()}] Connected to {DB_NAME}")

        # === 1. Top 5 slowest queries ===
        run_query(conn, "Top 5 slowest queries",
        """
        SELECT query, calls, ROUND((total_exec_time / calls)::numeric, 2) AS avg_time_ms
        FROM pg_stat_statements
        WHERE calls > 0
        ORDER BY avg_time_ms DESC
        LIMIT 5;
        """)

        # === 2. Largest tables ===
        run_query(conn, "Largest tables (by size)",
        """
        SELECT relname AS table_name,
               pg_size_pretty(pg_total_relation_size(relid)) AS total_size
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC
        LIMIT 5;
        """)

        # === 3. Index usage ===
        run_query(conn, "Index usage efficiency",
        """
        SELECT relname AS table_name,
               idx_scan as index_scans,
               seq_scan as seq_scans,
               (100 * idx_scan / NULLIF(idx_scan + seq_scan, 0))::numeric(5,2) as idx_usage_pct
        FROM pg_stat_user_tables
        ORDER BY idx_usage_pct ASC NULLS LAST
        LIMIT 5;
        """)

        # === 4. Table bloat candidates ===
        run_query(conn, "Potential table bloat",
        """
        SELECT schemaname, relname, n_dead_tup
        FROM pg_stat_all_tables
        WHERE n_dead_tup > 1000
        ORDER BY n_dead_tup DESC
        LIMIT 5;
        """)

        # === 5. Active connections ===
        run_query(conn, "Active connections",
        """
        SELECT count(*) as total_connections,
               state
        FROM pg_stat_activity
        GROUP BY state;
        """)

        # === 6. Deadlocks (if any) ===
        run_query(conn, "Deadlocks detected",
        """
        SELECT datname, deadlocks
        FROM pg_stat_database
        WHERE deadlocks > 0;
        """)

        conn.close()
        log(f"[{datetime.now()}] Performance check completed. Results saved to {log_file}")

    except Exception as e:
        log(f"Error: {e}")

if __name__ == "__main__":
    main()
