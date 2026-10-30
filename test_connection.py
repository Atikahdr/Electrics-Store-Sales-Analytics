from db import test_connection

try:
    result = test_connection()

    print("DATABASE CONNECTION SUCCESSFUL!")
    print("Database:", result[0])
    print("PostgreSQL Version:", result[1])

except Exception as error:
    print("DATABASE CONNECTION FAILED!")
    print(error)