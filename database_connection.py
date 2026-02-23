import mysql.connector
from mysql.connector import Error


class DatabaseConnection:
    def __init__(self, host='localhost', user='root', password='12345how', database='elev8'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                return True
        except Error as e:
            print(f"Database connection error: {e}")
            self.connection = None
            return False

    def disconnect(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=None):
        """Execute a SELECT query and return the results."""
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return None

            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Query execution error: {e}")
            return None

    def get_user_by_campus_id(self, campus_id):
        """Look up a user by their campus_id. Returns the user row or None."""
        query = "SELECT campus_id, password, access_level FROM users WHERE campus_id = %s"
        results = self.execute_query(query, (campus_id,))
        if results and len(results) > 0:
            return results[0]
        return None