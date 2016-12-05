import sqlite3


class DBUtil:

    def __init__(self, config):
        self.config = config
        # FIXME: May be removed.
        self.connection_to_db = DBUtil._get_connection(config)
        self.cursor = self.connection_to_db.cursor()

    def execute_query(self, query, *args):
        self.cursor.execute(query, args)
        self.connection_to_db.commit()

    def create_tables(self, tables):

        for name in tables:
            print("Creating table {} ".format(name))
            self.execute_query(tables[name])

    def _create_database(self, db_name):
        self.cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))

    @staticmethod
    def _get_connection(config):
        return sqlite3.connect(config['database'])

    def close(self):
        self.cursor.close()
        self.connection_to_db.close()
