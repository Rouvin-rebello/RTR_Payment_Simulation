import sqlite3

# Connect to the database
conn = sqlite3.connect('payment_system.db')
cursor = conn.cursor()


# Query to retrieve all BICs
cursor.execute("SELECT * FROM bic_codes")
bic = cursor.fetchall()

# Print out the users
for code in bic:
    print(code)


# Query to retrieve all users
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

# Print out the users
for user in users:
    print(user)




# Close the connection
conn.close()
