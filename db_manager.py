import sqlite3

def init_db():
    conn = sqlite3.connect('payment_system.db')
    cursor = conn.cursor()

    # Drop existing tables in correct order
    cursor.executescript('''
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS bic_codes;
    ''')

    # Create tables with correct schema
    cursor.executescript('''
        CREATE TABLE bic_codes (
            id INTEGER PRIMARY KEY,
            fi_code TEXT UNIQUE,
            bic_code TEXT UNIQUE
        );

        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            fi_code TEXT,
            balance REAL DEFAULT 1000.00,
            FOREIGN KEY (fi_code) REFERENCES bic_codes (fi_code)
        );

        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            receiver_id INTEGER,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        );
    ''')

    # Default BIC codes
    bic_data = [
        ('001', 'BOFCUS3NXXX'),
        ('002', 'CHASUS33XXX'),
        ('003', 'CITIUS33XXX')
    ]

    # Default users (no account column)
    user_data = [
        ('ABC Corporation', '001', 1000.00),
        ('Potato Inc.', '002', 1000.00),
        ('Wallet LLC', '003', 1000.00)
    ]

    cursor.executemany('INSERT INTO bic_codes (fi_code, bic_code) VALUES (?, ?)', bic_data)
    cursor.executemany('INSERT INTO users (name, fi_code, balance) VALUES (?, ?, ?)', user_data)
    
    conn.commit()
    conn.close()

def reset_db():
    """Reset the database to its initial state"""
    try:
        init_db()
        return True, "Database reset successfully"
    except Exception as e:
        return False, f"Error resetting database: {str(e)}"

if __name__ == "__main__":
    init_db()
