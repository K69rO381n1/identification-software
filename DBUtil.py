from mysql import connector
from mysql.connector import errorcode


def create_tables(connection_to_db, tables, db_name):
    cursor = connection_to_db.data.cursor()

    try:
        connection_to_db.database = db_name

    except connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            _create_database(cursor, db_name)
            connection_to_db.database = db_name
        else:
            print(err)
            exit(1)

    for name, ddl in tables:

        try:
            print("Creating table {}: ".format(name), end='')
            cursor.execute(ddl)

        except connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

    cursor.close()


def _create_database(cursor, db_name):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except connector.Error as conn_err:
        print("Failed creating database: {}".format(conn_err))
        exit(1)


def get_connection(user, password, host, db_name):
    return connector.connection.MySQLConnection(user=user, password=password,
                                                host=host,
                                                database=db_name)
