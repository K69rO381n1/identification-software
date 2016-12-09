import sqlite3

OP_DEBUG = True
QUERY_DEBUG = False

PASSWORDS_TABLE_DDL = \
    "CREATE TABLE IF NOT EXISTS passwords" \
    "(" \
    "    username VARCHAR(20) PRIMARY KEY NOT NULL," \
    "    password BIGINT(20)              NOT NULL," \
    "    CONSTRAINT passwords FOREIGN KEY (username) REFERENCES users (username) " \
    "    ON DELETE CASCADE ON UPDATE CASCADE" \
    ");"

LOGIN_STATISTICS_TABLE_DDL = \
    "CREATE TABLE IF NOT EXISTS login_statistics" \
    "(" \
    "    stage               TINYINT(4)  NOT NULL," \
    "    username            VARCHAR(30) NOT NULL," \
    "    number_of_failures  INT(11)     NOT NULL," \
    "    date                DATE        NOT NULL," \
    "    CONSTRAINT `PRIMARY` PRIMARY KEY (username, stage)," \
    "    CONSTRAINT login_statistics FOREIGN KEY (username) REFERENCES users (username)" \
    "    ON DELETE CASCADE ON UPDATE CASCADE" \
    ");"

USERS_TABLE_DDL = \
    "CREATE TABLE IF NOT EXISTS users" \
    "(" \
    "    first_name VARCHAR(20)             NOT NULL," \
    "    last_name  VARCHAR(20)             NOT NULL," \
    "    username   VARCHAR(30)             NOT NULL UNIQUE ," \
    "    id         BIGINT(20)  PRIMARY KEY NOT NULL" \
    ");"

USERS_IMAGES_DDL = \
    "CREATE TABLE IF NOT EXISTS images" \
    "(" \
    "    username  VARCHAR(30) NOT NULL," \
    "    image     LONGBLOB    NOT NULL," \
    "    CONSTRAINT image FOREIGN KEY (username) REFERENCES users (username)" \
    "    ON DELETE CASCADE ON UPDATE CASCADE" \
    ");"

MOST_RECENT_CAPTCHAS_TEXT_DDL = \
    "CREATE TEMPORARY TABLE captchas_text" \
    "(" \
    "    ip           VARCHAR(128) NOT NULL," \
    "    port         INT          NOT NULL," \
    "    captcha_text VARCHAR(10)  NOT NULL," \
    "    CONSTRAINT client_address PRIMARY KEY (ip, port)" \
    ")"

USER_AUTHORIZATION_DDL = \
    "CREATE TABLE authorizations" \
    "(" \
    "    username TEXT NOT NULL," \
    "    permission INTEGER NOT NULL," \
    "    FOREIGN KEY (username) REFERENCES users (username) DEFERRABLE INITIALLY DEFERRED" \
    ");"

SET_CAPTCHA_TEXT = \
    "INSERT INTO captchas_text VALUES (@ip, @port, @captcha_text)"

SET_PASSWORD_QUERY = \
    "INSERT INTO passwords VALUES (@username, @password)"

SET_PERMISSION_QUERY = \
    "INSERT INTO authorizations VALUES (@username, @permission)"

GET_ALL_IMAGES_QUERY = \
    "SELECT image FROM images WHERE username=@username"

GET_CAPTCHA_TEXT = \
    "SELECT captcha_text FROM captchas_text WHERE ip=@ip AND port=@port"

GET_PASSWORD_QUERY = \
    "SELECT password FROM passwords WHERE username = ?"

GET_ALL_STATISTICS_DATA_QUERY = \
    "SELECT * FROM login_statistics"

GET_USER_PERMISSION = \
    "SELECT permission FROM authorizations WHERE username = ?"

INSERT_NEW_USER = \
    "INSERT INTO users VALUES (?, ?, ?, ?)"

INSERT_IMAGE_QUERY = \
    "INSERT INTO images VALUES (?, ?)"

INSERT_FAILURE_INCIDENT_DETAILS = \
    "INSERT INTO login_statistics VALUES (?, ?, ?, ?)"

ADMIN = 0
USER = 1

PERMISSIONS = [ADMIN, USER]


class DBController:
    def __init__(self, config):
        self.config = config
        self.connection_to_db = DBController._get_connection(config)
        self.cursor = self.connection_to_db.cursor()

    def execute_query(self, query: str, *args):
        if QUERY_DEBUG:
            print('Executing {}\nwith args {}'.format(query, args), end='\n\n')
        return self.cursor.execute(query, args)

    def create_tables(self, tables):
        for name in tables:
            prompt = 'Creating table {}: '.format(name)
            try:
                self.execute_query(tables[name])
                prompt += 'New'
            except sqlite3.OperationalError:
                prompt += 'Already exists'

            if OP_DEBUG:
                print(prompt)

    def _create_database(self, db_name):
        self.cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))

    @staticmethod
    def _get_connection(config):
        return sqlite3.connect(config['database'], check_same_thread=False)

    def close(self):
        if OP_DEBUG:
            print('Closing connection with DB...')
        self.connection_to_db.commit()
        self.cursor.close()
        self.connection_to_db.close()
