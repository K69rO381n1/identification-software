from mysql import connector
from mysql.connector import errorcode


class DBUtil:

    def __init__(self, config):
        self.config = config
        # FIXME: May be removed.
        self.connection_to_db = DBUtil._get_connection(**config)
        self.cursor = self.connection_to_db.cursor()

    def execute_query(self, query, *args):
        self.cursor.execute(query, args)

    def create_tables(self, tables, db_name):

        try:
            self.connection_to_db.database = db_name

        except connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                self._create_database(db_name)
                self.connection_to_db.database = db_name
            else:
                print(err)
                exit(1)

        for name in tables:
            try:
                print("Creating table {}: ".format(name), end='')
                self.execute_query(tables[name])

            except connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")

        self.cursor.close()

    def _create_database(self, db_name):
        try:
            self.cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        except connector.Error as conn_err:
            print("Failed creating database: {}".format(conn_err))

    @staticmethod
    def _get_connection(config):
        return connector.connect(**config)

    def close(self):
        self.cursor.close()
        self.connection_to_db.close()
