import oracledb

try:
    connection = oracledb.connect(
        user="system",
        password="123456",
        dsn="localhost:1521/ORCL"
    )
    print("✅ Oracle connection successful!")
    
    # Test query
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM v$version")
    result = cursor.fetchone()
    print("Oracle Version:", result[0])
    
    connection.close()
except Exception as e:
    print("❌ Error:", e)