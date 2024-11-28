import sqlite3

# Step 1: Connect to the SQLite database
# Replace 'your_database.db' with the path to your SQLite database file
connection = sqlite3.connect('view_database.db')

# Step 2: Create a cursor object
cursor = connection.cursor()

# Step 3: Execute a SQL query to retrieve data
# Replace 'your_table' with the name of the table you want to view
cursor.execute("SELECT * FROM your_table")

# Step 4: Fetch all results from the executed query
rows = cursor.fetchall()

# Step 5: Display the results
for row in rows:
    print(row)

# Step 6: Close the cursor and connection
cursor.close()
connection.close()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:", tables)