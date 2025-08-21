import sqlite3

def initialize_database():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()

        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Create languages table
        c.execute('''
            CREATE TABLE IF NOT EXISTS languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # Summaries Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                summary TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')



        # Insert default languages
        default_languages = [('English',), ('Spanish',), ('Korean',)]
        c.executemany('INSERT OR IGNORE INTO languages (name) VALUES (?)', default_languages)

        conn.commit()

if __name__ == "__main__":
    initialize_database()
