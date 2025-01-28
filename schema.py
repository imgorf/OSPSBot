import sqlite3

def create_db():
    conn = sqlite3.connect('log.db')
    c = conn.cursor()

    # Create a table to store user data
    c.execute('''
              CREATE TABLE IF NOT EXISTS log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    log_name TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    item_name TEXT,
                    item_price NUMERIC(10, 2)
             );
    ''')

    # Commit and close the connection
    conn.commit()
    conn.close()

# Initialize the database
create_db()