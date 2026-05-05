"""
Open WebUI Migration Tool (SQLite to PostgreSQL)
This tool handles:
1. Automatic creation of the target PostgreSQL database
2. Fixing boolean mismatches between SQLite (0/1) and PostgreSQL (True/False)
3. Fixing JSON field formats to satisfy Pydantic validation
4. Temporary disabling of foreign key constraints to handle orphaned records
5. Cleaning of null characters (\x00) not supported by PostgreSQL
"""

import os
import json
from sqlalchemy import create_engine, MetaData, Table, insert, text

# --- CONFIGURATION AREA ---
# Path to your source SQLite database file. 
# Common default paths on Windows:
# 1. %USERPROFILE%/.open_webui/webui.db
# 2. %APPDATA%/../Local/Programs/Python/Python31x/Lib/site-packages/open_webui/data/webui.db
SQLITE_DB_PATH = 'webui.db'
SQLITE_DB_PATH = 'webui.db'

# PostgreSQL Connection Details
PG_USER = 'postgres'
PG_PASSWORD = 'your_password_here'
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB_NAME = 'openwebui'
# --------------------------

def ensure_database_exists():
    """Connects to system database and ensures the target database exists"""
    sys_url = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres'
    engine = create_engine(sys_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{PG_DB_NAME}'")).fetchone()
        if not exists:
            print(f"Creating database: {PG_DB_NAME}...")
            conn.execute(text(f"CREATE DATABASE {PG_DB_NAME}"))
        else:
            print(f"Database '{PG_DB_NAME}' already exists.")

def migrate():
    ensure_database_exists()
    
    postgres_url = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}'
    sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
    pg_engine = create_engine(postgres_url)
    
    # Reflect schema from PostgreSQL to ensure accurate types
    metadata = MetaData()
    metadata.reflect(bind=pg_engine)
    
    print("\n🚀 Starting migration (Advanced Compatibility Mode)...")
    
    with sqlite_engine.connect() as sqlite_conn:
        with pg_engine.begin() as pg_conn:
            # Disable foreign key checks for migration
            pg_conn.execute(text("SET session_replication_role = 'replica';"))
            
            for table in metadata.sorted_tables:
                table_name = table.name
                
                # Check if table exists in source SQLite
                table_exists = sqlite_conn.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                ).fetchone()
                
                if not table_exists:
                    continue
                
                print(f"Migrating table: {table_name}...")
                pg_conn.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
                
                # Read data from SQLite
                result = sqlite_conn.execute(text(f'SELECT * FROM "{table_name}"'))
                data = result.fetchall()
                
                if data:
                    rows = []
                    for row in data:
                        row_dict = dict(row._mapping)
                        for col_name, value in row_dict.items():
                            if col_name in table.c:
                                col_type = str(table.c[col_name].type).lower()
                                
                                # 1. Remove null characters (\x00) not supported by PostgreSQL
                                if isinstance(value, str):
                                    value = value.replace('\x00', '')
                                    row_dict[col_name] = value

                                # 2. Handle Boolean compatibility
                                if 'boolean' in col_type:
                                    if value is not None:
                                        row_dict[col_name] = bool(value)
                                
                                # 3. Handle JSON field parsing
                                elif 'json' in col_type:
                                    if isinstance(value, str):
                                        try:
                                            row_dict[col_name] = json.loads(value)
                                        except:
                                            if value.lower() == 'null':
                                                row_dict[col_name] = None
                        rows.append(row_dict)
                    
                    pg_conn.execute(table.insert(), rows)
                    print(f"  ✅ Successfully migrated {len(rows)} rows.")
            
            # Re-enable foreign key checks
            pg_conn.execute(text("SET session_replication_role = 'origin';"))
    
    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    migrate()
