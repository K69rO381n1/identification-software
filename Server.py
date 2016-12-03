from __future__ import print_function

import socket
from os import listdir
from random import choice
from threading import Thread

from captcha.audio import AudioCaptcha
from captcha.image import ImageCaptcha

import TransmissionProtocol
from DBUtil import DBUtil

CAPTCHA_LENGTH = 6
CAPTCHA_ALPHABET = ['z', 'Z', 'y', 'Y', 'x', 'X', 'w', 'W', 'v', 'V',
                    'u', 'U', 't', 'T', 's', 'S', 'r', 'R', 'q', 'Q',
                    'p', 'P', 'o', 'O', 'n', 'N', 'm', 'M', 'l', 'L',
                    'j', 'J', 'i', 'I', 'h', 'H', 'g', 'G', 'f', 'F',
                    'e', 'E', 'd', 'D', 'c', 'C', 'b', 'B', 'a', 'A',
                    '9', '8', '7', '6', '5', '4', '3', '2', '1', '0']

PASSWORDS_TABLE_DDL = \
    "CREATE TABLE IF NOT EXISTS passwords" \
    "(" \
    "    username VARCHAR(20) PRIMARY KEY NOT NULL," \
    "    password BIGINT(20) NOT NULL," \
    "    CONSTRAINT passwords FOREIGN KEY (username) REFERENCES users (username) " \
    "    ON DELETE CASCADE ON UPDATE CASCADE" \
    ");"

LOGIN_STATISTICS_TABLE_DDL = \
    "CREATE TABLE IF NOT EXISTS login_statistics" \
    "(" \
    "    stage TINYINT(4) NOT NULL," \
    "    username VARCHAR(30) NOT NULL," \
    "    number_of_failures INT(11) NOT NULL," \
    "    date DATE NOT NULL," \
    "    CONSTRAINT `PRIMARY` PRIMARY KEY (username, stage)," \
    "    CONSTRAINT login_statistics FOREIGN KEY (username) REFERENCES users (username)" \
    "    ON DELETE CASCADE ON UPDATE CASCADE" \
    ");"

USERS_TABLE_DDL = \
    "CREATE TABLE IF NOT EXISTS users" \
    "(" \
    "    first_name VARCHAR(20) NOT NULL," \
    "    last_name VARCHAR(20) NOT NULL," \
    "    username VARCHAR(30) NOT NULL," \
    "    id BIGINT(20) PRIMARY KEY NOT NULL," \
    "    CONSTRAINT UNIQUE INDEX (username)" \
    ");"

USERS_IMAGES_DDL = \
    "CREATE TABLE IF NOT EXISTS images" \
    "(" \
    "    username VARCHAR(30) NOT NULL," \
    "    image LONGBLOB NOT NULL," \
    "    CONSTRAINT image FOREIGN KEY (username) REFERENCES users (username)" \
    "    ON DELETE CASCADE ON UPDATE CASCADE" \
    ");"

MOST_RECENT_CAPTCHAS_TEXT_DDL = \
    "CREATE TEMPORARY TABLE identificationdb.captchas_text" \
    "(" \
    "    ip VARCHAR(128) NOT NULL," \
    "    port INT NOT NULL," \
    "    captcha_text VARCHAR(10) NOT NULL," \
    "    CONSTRAINT client_address PRIMARY KEY (ip, port)" \
    ")"

GET_CAPTCHA_TEXT = \
    "SELECT captcha_text FROM captchas_text WHERE ip=@0 AND port=@1"

GET_PASSWORD_QUERY = \
    "SELECT password FROM passwords WHERE username = @0"

UPDATE_PASSWORD_QUERY = \
    "UPDATE passwords SET password=@0 WHERE username=@1"

GET_ALL_IMAGES_QUERY = \
    "SELECT image FROM images WHERE username=@0"

GET_ALL_STATISTICS_DATA_QUERY = \
    "SELECT * FROM login_statistics"

BIND_IP = 'localhost'
BIND_PORT = 9999
BACKLOG = 5

DB_NAME = 'identificationdb'
DB_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': DB_NAME,
}

HASH_PREFIX = "16d5f1gs48tg1"
HASH_SUFFIX = "134gs2d4gsa"

IMAGE_MODE = "L"
IMAGE_COLORS = "RGBA"

MAX_TRANSFER_AT_ONCE = 2048

FONTS_DIR = "data/font/"
VOICES_DIR = "data/voice/"
FONTS = [FONTS_DIR + font for font in listdir(FONTS_DIR)]


class MainServer(socket.socket):
    def __init__(self):
        super(MainServer, self).__init__(socket.AF_INET, socket.SOCK_STREAM)

        # Getting a connection to the DB.
        self.db = DBUtil(DB_CONFIG)

        # Creating the necessary tables. for more information see the DDLs above...
        self.create_tables()

        self.socket_to_address_dict = {}

        self.socket_to_username_dict = {}

        # Creating dictionary that maps from client to the latest captcha that has been send to him.
        self.last_captcha_text = {}

        self.captcha_image_generator = ImageCaptcha(fonts=FONTS)

        self.captcha_audio_generator = AudioCaptcha(voicedir=VOICES_DIR)

        # Listening to the required IP and PORT.
        self.bind((BIND_IP, BIND_PORT))

        # Limiting the number of clients to BACKLOG.
        self.listen(BACKLOG)

        # starting a new thread that accepts new clients
        Thread(target=self.accept_clients).start()

    def accept_clients(self):
        try:
            while not self._closed:
                client_socket, client_address = self.accept()
                self.socket_to_address_dict[client_socket] = client_address
        except OSError:
            pass

    def handle_client(self, client: socket.socket):

        try:
            while True:
                client_input = MainServer._recvfrom(client)
                flag = client_input[0]
                data = client_input[1:]
                if flag == TransmissionProtocol.CAPTCHA_REQUEST:
                    MainServer._sendto(client,
                                       self.generate_captcha(),
                                       TransmissionProtocol.CAPTCHA_RESPONSE)

                elif flag == TransmissionProtocol.CAPTCHA_TEXT_CHECK_REQUEST:
                    MainServer._sendto(client,
                                       TransmissionProtocol.to_bytes(self.check_user_captcha_guess(
                                           *TransmissionProtocol.parse_str(data, 1)), 1),
                                       TransmissionProtocol.CAPTCHA_TEXT_CHECK_RESPONSE)

                elif flag == TransmissionProtocol.CREDENTIALS_CHECK_REQUEST:
                    MainServer._sendto(client,
                                       TransmissionProtocol.to_bytes(self.validate_password(
                                           *TransmissionProtocol.parse_str(data, 2)), 1),
                                       TransmissionProtocol.CREDENTIALS_CHECK_RESPONSE)

                elif flag == TransmissionProtocol.FACE_IMAGE_CHECK_REQUEST:
                    # TODO: Complete...
                    pass

                elif flag == TransmissionProtocol.STATISTICS_DATA_REQUEST:
                    # TODO: Complete...
                    pass

                elif flag == TransmissionProtocol.CHANGE_PASSWORD_REQUEST:
                    username, old_password, new_password = TransmissionProtocol.parse_str(data, 3)
                    if self.validate_password(username, old_password):
                        self.db.execute_query(UPDATE_PASSWORD_QUERY, new_password, username)
                        MainServer._sendto(client, TransmissionProtocol.to_bytes(True, 1),
                                           TransmissionProtocol.CHANGE_PASSWORD_RESPONSE)
                    else:
                        MainServer._sendto(client, TransmissionProtocol.to_bytes(False, 1),
                                           TransmissionProtocol.CHANGE_PASSWORD_RESPONSE)

        finally:
            client.close()

    def generate_captcha(self):

        return self.captcha_image_generator.generate(
            MainServer._space_text(MainServer._random_text(CAPTCHA_LENGTH)),
            format='png').read()

    def validate_password(self, username: str, password: str) -> bool:
        password_from_db = next(self.db.execute_query(GET_PASSWORD_QUERY, username))
        return password_from_db == password

    def check_user_captcha_guess(self, client: socket.socket, guess_text: str):
        captcha_text = self.db.execute_query(GET_CAPTCHA_TEXT, *self.socket_to_address_dict[client])
        return captcha_text == guess_text

    def create_tables(self):

        TABLES = {}

        TABLES['users'] = (
            USERS_TABLE_DDL
        )

        TABLES['login_statistics'] = (
            LOGIN_STATISTICS_TABLE_DDL
        )

        TABLES['passwords'] = (
            PASSWORDS_TABLE_DDL
        )

        TABLES['captchas_text'] = (
            MOST_RECENT_CAPTCHAS_TEXT_DDL
        )

        self.db.create_tables(TABLES, DB_NAME)

    # ************************************** Override methods ***********************************

    def close(self):
        super(socket.socket, self).close()
        self.db.close()

    # ************************************** Static functions ***********************************

    @staticmethod
    def _sendto(client: socket.socket, data: bytes, flag: int):
        """
        This method sends to the client the data Using the protocol defined in file PocketProtocol.
        NOTE: Any data sending to clients should be though this method!

        :param client:  The data's addressee
        :param data:    This data will be send to the client.
        """

        total_sent = 0
        packet = TransmissionProtocol.wrap_data(data, flag)

        while total_sent < len(packet):
            total_sent += client.send(
                packet[total_sent: min(
                    total_sent + MAX_TRANSFER_AT_ONCE,
                    MainServer._round_to_lower_power_of_2(len(packet)))])

    @staticmethod
    def _recvfrom(client: socket.socket) -> bytes:
        """
        This method receives from the client data and unwrap it using the protocol defined in file PocketProtocol.
        NOTE: Any data receiving from clients should be though this method!

        :param client:  The data's sender.
        """

        data = b''
        size = client.recvfrom(
            TransmissionProtocol.NUM_OF_BYTES_IN_DATA_SIZE) + TransmissionProtocol.NUM_OF_BYTES_IN_MESSAGE_TYPE

        while len(data) < size:
            data += client.recv(
                min(
                    MAX_TRANSFER_AT_ONCE,
                    MainServer._round_to_lower_power_of_2(size - len(data))))
        return data

    @staticmethod
    def _random_text(size: int) -> str:
        return "".join([choice(CAPTCHA_ALPHABET) for _ in range(size)])

    @staticmethod
    def encrypt(password: str):
        return hash(hash(HASH_PREFIX + password + HASH_SUFFIX))

    @staticmethod
    def _round_to_lower_power_of_2(buffer_size: int):
        return 1 << (buffer_size.bit_length() - 1)

    @staticmethod
    def _space_text(text: str):
        return " ".join(text)


if __name__ == '__main__':
    a = MainServer()
