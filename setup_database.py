import sqlite3

# Connect to the SQLite database (this will create the database file if it doesn't exist)
conn = sqlite3.connect('payment_system.db')
cursor = conn.cursor()

# Drop the tables if they exist
def drop_tables():
    cursor.execute("DROP TABLE IF EXISTS payments;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute("DROP TABLE IF EXISTS bic_codes;")

# Create the tables (Users, BIC Codes, Payments)
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bic_codes (
        fi_code TEXT PRIMARY KEY,
        bic_code TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        fi_code TEXT NOT NULL,
        account TEXT NOT NULL,
        balance REAL DEFAULT 1000.00,
        FOREIGN KEY (fi_code) REFERENCES bic_codes (fi_code)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (recipient_id) REFERENCES users (id)
    );
    """)

# Insert sample data into the bic_codes and users tables
def insert_sample_data():
    # Insert BIC codes
    cursor.execute("INSERT OR REPLACE INTO bic_codes (fi_code, bic_code) VALUES ('001', 'RBIACATTXXX')")
    cursor.execute("INSERT OR REPLACE INTO bic_codes (fi_code, bic_code) VALUES ('002', 'NPCUCATTXXX')")
    cursor.execute("INSERT OR REPLACE INTO bic_codes (fi_code, bic_code) VALUES ('003', 'MPLLCATTXXX')")
    cursor.execute("INSERT OR REPLACE INTO bic_codes (fi_code, bic_code) VALUES ('004', 'NTBKCATTXXX')")

    # Insert users with initial balances
    cursor.execute("INSERT INTO users (name, fi_code, account, balance) VALUES ('Alice Robertson', '001', '100123456789', 5000.00)")
    cursor.execute("INSERT INTO users (name, fi_code, account, balance) VALUES ('Michael Chen', '002', '200987654321', 7500.00)")
    cursor.execute("INSERT INTO users (name, fi_code, account, balance) VALUES ('Sophia Khan', '003', '300555777111', 3000.00)")
    cursor.execute("INSERT INTO users (name, fi_code, account, balance) VALUES ('Ethan McLeod', '004', '400333999888', 10000.00)")

# Create the tables and insert sample data
drop_tables()
create_tables()
insert_sample_data()

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully, and sample data inserted.")


# Checking the database connection and table creation

# Connect to the database
conn = sqlite3.connect('payment_system.db')
cursor = conn.cursor()

# Query to retrieve all users
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

# Print out the users
for user in users:
    print(user)

# Close the connection
conn.close()
