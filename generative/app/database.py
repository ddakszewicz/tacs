import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MYSQL_HOST=os.getenv('MYSQL_HOST')
MYSQL_ROOT_PASSWORD=os.getenv('MYSQL_ROOT_PASSWORD')
MYSQL_DATABASE=os.getenv('MYSQL_DATABASE')
MYSQL_USER=os.getenv('MYSQL_USER')
MYSQL_PASSWORD=os.getenv('MYSQL_PASSWORD')

def query(query):
    """
    Executes a SQL query against the provided MySQL database and returns the results.

    Parameters:
    query (str): The SQL query to execute.
    host (str): The hostname or IP address of the MySQL server.
    database (str): The name of the database to use.
    user (str): The username to connect to the database.
    password (str): The password for the specified user.

    Returns:
    list: A list of tuples representing the rows returned by the query.
    """
    try:
        # Connect to the MySQL database
        db = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )

        # Execute the query and fetch the results
        cursor = db.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        # Close the database connection
        db.close()

        return results

    except mysql.connector.Error as e:
        print(f"Error connecting to the database: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def healthcheck():
    query("SELECT 1")
    return "FAILED" if query("SELECT 1") is None else "OK";