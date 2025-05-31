"""
Create the pedigree_db database if it doesn't exist
"""
import pymysql
import sys

def create_database():
    print("Attempting to connect to MySQL server...")
    print("Host: localhost")
    print("User: root")
    print("Password: ***")
    
    try:
        # Connect to MySQL server (not to a specific database)
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            charset='utf8mb4'
        )
        
        print("✅ Successfully connected to MySQL server!")
        
        with connection.cursor() as cursor:
            # Check if database exists
            cursor.execute("SHOW DATABASES LIKE 'pedigree_db'")
            result = cursor.fetchone()
            
            if result:
                print("✅ Database 'pedigree_db' already exists!")
            else:
                # Create the database
                cursor.execute("CREATE DATABASE pedigree_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print("✅ Database 'pedigree_db' created successfully!")
            
            # Show all databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("\nAvailable databases:")
            for db in databases:
                print(f"  - {db[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible issues:")
        print("1. MySQL/MariaDB server is not running")
        print("2. Wrong username or password")
        print("3. Connection refused - check if MySQL service is started")
        return False

if __name__ == "__main__":
    print("Creating pedigree_db database...")
    if create_database():
        print("\n✅ Database setup completed! You can now run the application.")
    else:
        print("\n❌ Database setup failed. Please check your MySQL installation.")
