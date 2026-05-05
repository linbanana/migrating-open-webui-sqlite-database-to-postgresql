# Open WebUI Database Migration Tool (SQLite to PostgreSQL)
A robust Python script to migrate your [Open WebUI](https://github.com/open-webui/open-webui) data from the default SQLite database to a production-grade PostgreSQL instance.
## 🚀 Why use this tool?
Open WebUI's official migration can sometimes be tricky due to data type differences between SQLite and PostgreSQL. This script automates the hard parts:
- **Automatic DB Creation**: Creates the target PostgreSQL database if it doesn't exist.
- **Data Type Casting**: Automatically converts SQLite integers (0/1) to PostgreSQL Booleans (True/False).
- **JSON Parsing**: Fixes JSON strings from SQLite to native JSONB format, preventing startup validation errors (Pydantic).
- **Integrity Handling**: Temporarily disables foreign key constraints to safely migrate "orphaned" records.
- **Data Cleaning**: Strips null characters (`\x00`) which are not supported by PostgreSQL.
## 📋 Prerequisites
- **Python 3.11+**
- **uv** (Recommended) or **pip**
- **PostgreSQL 15+** installed and running.
## ⚙️ Configuration
Open `migrate_db.py` and update the following variables:
```python
# Path to your source SQLite file
SQLITE_DB_PATH = 'webui.db' 
# Target PostgreSQL details
PG_USER = 'postgres'
PG_PASSWORD = 'your_password_here'
PG_HOST = 'localhost'
PG_PORT = '5432'
PG_DB_NAME = 'openwebui'
