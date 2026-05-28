import os
import json
import psycopg2
from datetime import datetime

# Database configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "dbname": "hebrew_ai_db"
}

MEMORY_STORE_DIR = "/var/home/sanya/Hebrew-web/memory_store/"

def migrate_memories():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        for root, dirs, files in os.walk(MEMORY_STORE_DIR):
            for file in files:
                if file.endswith(".json") and "memories/" in root:
                    file_path = os.path.join(root, file)
                    print(f"Processing: {file_path}")

                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)

                        # Insert into ai_bridge.memories
                        # Columns: session_id, source_session_id, agent_id, memory_type, content, metadata, importance_score, created_at
                        
                        # Prepare content as JSON
                        content_json = json.dumps({"content": data.get("content", "")})
                        
                        query = """
                            INSERT INTO ai_bridge.memories 
                            (session_id, source_session_id, agent_id, memory_type, content, metadata, importance_score, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        params = (
                            data.get("session_id"),
                            data.get("source_session_id"),
                            data.get("agent_id"),
                            data.get("type"),
                            content_json,
                            "{}",
                            0.5,
                            data.get("created_at")
                        )
                        
                        cur.execute(query, params)
                        print(f"Successfully migrated memory from {file_path}")
                        
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        conn.rollback() # Rollback on error
                        continue
        
        conn.commit()
        print("Migration finished successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_memories()
