import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="vignesh",
    database="exam_management"
)

cursor = db.cursor()

cursor.execute("SHOW TABLES")

tables = cursor.fetchall()

print("\n✅ Tables in exam_management database:\n")
for table in tables:
    print(table[0])

cursor.close()
db.close()
