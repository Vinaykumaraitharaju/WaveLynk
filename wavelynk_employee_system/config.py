from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "wavelynk.db"

ASSETS_DIR = BASE_DIR / "assets"
EXPORTS_DIR = BASE_DIR / "exports"
EXCEL_EXPORT_DIR = EXPORTS_DIR / "excel"
PDF_EXPORT_DIR = EXPORTS_DIR / "pdf"

SQL_DIR = BASE_DIR / "sql"
SCHEMA_FILE = SQL_DIR / "schema.sql"
SEED_FILE = SQL_DIR / "seed.sql"