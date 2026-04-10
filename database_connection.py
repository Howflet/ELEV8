from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool


class DatabaseConnection:
    def __init__(self, host='localhost', user='root', password='12345how', database='elev8', pool_size=5):
        self._pool = MySQLConnectionPool(
            pool_name="elev8_pool",
            pool_size=pool_size,
            host=host,
            user=user,
            password=password,
            database=database,
        )

    def is_healthy(self):
        """Check pool health by borrowing and returning a connection."""
        try:
            conn = self._pool.get_connection()
            conn.close()
            return True
        except Error:
            return False

