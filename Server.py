from __future__ import print_function

from threading import Thread
import socket
from DBUtil import DBUtil

from PIL import Image
from captcha.image import ImageCaptcha
from captcha.audio import AudioCaptcha
from random import choice

import PocketProtocol

from os import listdir

NUM_OF_CHARS_IN_CAPTCHA = 6
CAPTCHA_ALPHABET = ['z', 'Z', 'y', 'Y', 'x', 'X', 'w', 'W', 'v', 'V',
                    'u', 'U', 't', 'T', 's', 'S', 'r', 'R', 'q', 'Q',
                    'p', 'P', 'o', 'O', 'n', 'N', 'm', 'M', 'l', 'L',
                    'j', 'J', 'i', 'I', 'h', 'H', 'g', 'G', 'f', 'F',
                    'e', 'E', 'd', 'D', 'c', 'C', 'b', 'B', 'a', 'A',
                    '9', '8', '7', '6', '5', '4', '3', '2', '1', '0']

PASSWORDS_TABLE_DDL = "CREATE TABLE IF NOT EXISTS passwords" \
                      "(" \
                      "    username VARCHAR(20) PRIMARY KEY NOT NULL," \
                      "    password BIGINT(20) NOT NULL," \
                      "    CONSTRAINT passwords FOREIGN KEY (username) REFERENCES users (username) " \
                      "    ON DELETE CASCADE ON UPDATE CASCADE" \
                      ");"

LOGIN_STATISTICS_TABLE_DDL = "CREATE TABLE IF NOT EXISTS login_statistics" \
                             "(" \
                             "    stage TINYINT(4) NOT NULL," \
                             "    username VARCHAR(30) NOT NULL," \
                             "    number_of_failures INT(11) NOT NULL," \
                             "    date DATE NOT NULL," \
                             "    CONSTRAINT `PRIMARY` PRIMARY KEY (username, stage)," \
                             "    CONSTRAINT login_statistics FOREIGN KEY (username) REFERENCES users (username)" \
                             "    ON DELETE CASCADE ON UPDATE CASCADE" \
                             ");"

USERS_TABLE_DDL = "CREATE TABLE IF NOT EXISTS users" \
                  "(" \
                  "    first_name VARCHAR(20) NOT NULL," \
                  "    last_name VARCHAR(20) NOT NULL," \
                  "    username VARCHAR(30) NOT NULL," \
                  "    id BIGINT(20) PRIMARY KEY NOT NULL," \
                  "    CONSTRAINT UNIQUE INDEX (username)" \
                  ");"

USERS_IMAGES_DDL = "CREATE TABLE IF NOT EXISTS images" \
                   "(" \
                   "    username VARCHAR(30) NOT NULL," \
                   "    images LONGBLOB NOT NULL," \
                   "    CONSTRAINT images FOREIGN KEY (username) REFERENCES users (username)" \
                   "    ON DELETE CASCADE ON UPDATE CASCADE" \
                   ");"

GET_PASSWORD_QUERY = "SELECT password FROM passwords WHERE username = @0"

BIND_IP = "0.0.0.0"
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
FONTS = [FONTS_DIR+font for font in listdir(FONTS_DIR)]


class MainServer(socket.socket):
    def __init__(self):
        super().__init__()

        # Getting a connection to the DB.
        self.db = DBUtil(DB_CONFIG)

        # Creating the necessary tables. for more information see the DDLs above...
        self.create_tables()

        # Creating a list of all clients.
        self.clients_socket_and_address = []

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
            while not self.s.close():
                client_socket, client_address = self.accept()
                self.clients_socket_and_address.append((client_socket, client_address))
        except OSError:
            pass

    def handle_client(self, client: socket.socket):

        try:
            while True:
                client_input = MainServer._recvfrom(client)
                if client_input[0] == b'1':
                    pass
                    # TODO: Complete...
        finally:
            client.close()

    def send_captcha(self, client: socket):

        bytes_io = self.captcha_image_generator.generate('', format='png')

        captcha2send = b''

        read = bytes_io.read()
        while read != -1:
            captcha2send += read
            read = bytes_io.read()

        MainServer._sendto(client, captcha2send, 1)

    def validate_password(self, username, password):
        pass
    def check_user_captcha_guess(self, client, guess_text):
        return self.last_captcha_text.get(client).get_text() == guess_text

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
        self.db.create_tables(TABLES, DB_NAME)

    # ************************************** Override methods ***********************************

    def close(self):
        super(socket.socket, self).close()
        self.connection_to_db.close()

    # ************************************** Static functions ***********************************

    @staticmethod
    def _sendto(client: socket.socket, data, flag):
        """
        This method sends to the client the data Using the protocol defined in file PocketProtocol.
        NOTE: Any data sending to clients should be though this method!

        :param client:  The data's addressee
        :param data:    This data will be send to the client.
        """

        total_sent = 0
        packet = PocketProtocol.wrap_data(data, flag)

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
        size = client.recvfrom(PocketProtocol.NUM_OF_DIGITS_IN_DATA_SIZE) + PocketProtocol.NUM_OF_DIGITS_IN_MESSAGE_TYPE

        while len(data) < size:
            data += client.recv(
                min(
                    MAX_TRANSFER_AT_ONCE,
                    MainServer._round_to_lower_power_of_2(size - len(data))))
        return data

    @staticmethod
    def random_text(size):
        return "".join([choice(CAPTCHA_ALPHABET) for _ in range(size)])

    @staticmethod
    def bytes2images(image_as_bytes):
        height = image_as_bytes[0]
        width = image_as_bytes[1]
        image = Image.new(IMAGE_MODE, (height, width), IMAGE_COLORS)

        for i in range(height):
            for j in range(width):
                image.putpixel((i, j), image_as_bytes[i * width + j + 2])

        return image

    @staticmethod
    def encrypt(password):
        return hash(hash(HASH_PREFIX + password + HASH_SUFFIX))

    @staticmethod
    def _round_to_lower_power_of_2(buffer_size):
        return 1 << (buffer_size.bit_length() - 1)
