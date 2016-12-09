from __future__ import print_function

import socket
from os import listdir
from random import choice
from threading import Thread

from captcha.audio import AudioCaptcha
from captcha.image import ImageCaptcha

import DBController
import TransmissionProtocol
from DBController import *

DEBUG = True
ADD_TEST_ADMIN = False

CAPTCHA_LENGTH = 6
CAPTCHA_ALPHABET = ['z', 'Z', 'y', 'Y', 'x', 'X', 'w', 'W', 'v', 'V',
                    'u', 'U', 't', 'T', 's', 'S', 'r', 'R', 'q', 'Q',
                    'p', 'P', 'o', 'O', 'n', 'N', 'm', 'M', 'l', 'L',
                    'j', 'J', 'i', 'I', 'h', 'H', 'g', 'G', 'f', 'F',
                    'e', 'E', 'd', 'D', 'c', 'C', 'b', 'B', 'a', 'A',
                    '9', '8', '7', '6', '5', '4', '3', '2', '1', '0']

BIND_IP = 'localhost'
BIND_PORT = 9999
BACKLOG = 5

DB_NAME = 'identification.db'
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
        self.db = DBController.DBController(DB_CONFIG)

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

        if DEBUG:
            print('\n\n******************** Server is on air ************************\n\n')

        user_input = input()
        if user_input == 'quit':
            self.close()

    def accept_clients(self):
        try:
            while True:
                client_socket, client_address = self.accept()
                if DEBUG:
                    print('Accept client: {}'.format(client_address))
                self.socket_to_address_dict[client_socket] = client_address
                Thread(target=self.handle_client, args=(client_socket,)).start()
        except OSError:
            pass

        finally:
            self.close()

    def handle_client(self, client: socket.socket):

        if DEBUG:
            print('Start handling {}'.format(client.getsockname()), end='\n\n')

        try:
            def _send_bool(boolean, server_flag):
                MainServer._sendto(client, TransmissionProtocol.to_bytes(boolean, 1), server_flag)

            while True:
                client_input = MainServer._recvfrom(client)
                flag = client_input[0]
                data = client_input[1:]
                if DEBUG:
                    print('Receive from {} data{} with flag {}'
                          .format(self.socket_to_address_dict[client], flag, client_input))

                if flag == TransmissionProtocol.CAPTCHA_REQUEST:
                    captcha_text = MainServer._random_text(CAPTCHA_LENGTH)
                    self.db.execute_query(DBController.SET_CAPTCHA_TEXT, *self.socket_to_address_dict[client],
                                          captcha_text)

                    MainServer._sendto(client,
                                       self.generate_captcha(MainServer._space_text(captcha_text)),
                                       TransmissionProtocol.CAPTCHA_RESPONSE)

                elif flag == TransmissionProtocol.CAPTCHA_TEXT_CHECK_REQUEST:
                    MainServer._sendto(client,
                                       TransmissionProtocol.to_bytes(self.check_user_captcha_guess(
                                           *TransmissionProtocol.parse_str(data, 1)), 1),
                                       TransmissionProtocol.CAPTCHA_TEXT_CHECK_RESPONSE)

                elif flag == TransmissionProtocol.CREDENTIALS_CHECK_REQUEST:
                    MainServer._sendto(client,
                                       TransmissionProtocol.to_bytes(self.validate_password_and_authorizations(
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

                    if self.validate_password_and_authorizations(username, old_password):
                        self.db.execute_query(DBController.SET_PASSWORD_QUERY, new_password, username)
                        _send_bool(True, TransmissionProtocol.CHANGE_PASSWORD_RESPONSE)
                    else:
                        _send_bool(False, TransmissionProtocol.CHANGE_PASSWORD_RESPONSE)

                elif flag == TransmissionProtocol.ADD_IMAGE_REQUEST:
                    username, password, image = TransmissionProtocol.parse_str(data, 2)

                    if self.validate_password_and_authorizations(username, password):
                        self.db.execute_query(DBController.INSERT_IMAGE_QUERY, username, image)
                        _send_bool(True, TransmissionProtocol.ADD_IMAGE_RESPONSE)
                    else:
                        _send_bool(False, TransmissionProtocol.ADD_IMAGE_RESPONSE)

                elif flag == TransmissionProtocol.ADD_NEW_USER_REQUEST:
                    admin_username, admin_password, \
                    first_name, last_name, username, password, num_data = \
                        TransmissionProtocol.parse_str(data, 6)
                    user_id = int.from_bytes(num_data[:4], 'big')
                    permission = num_data[4:]

                    if self.validate_password_and_authorizations(admin_username, admin_username, permission) and \
                                    len(first_name) < TransmissionProtocol.MAX_FIRST_NAME_LENGTH and \
                                    len(last_name) < TransmissionProtocol.MAX_LAST_NAME_LENGTH and \
                                    len(username) < TransmissionProtocol.MAX_USERNAME_LENGTH and \
                                    len(password) < TransmissionProtocol.MAX_PASSWORD_LENGTH and \
                                    permission in PERMISSIONS:

                        self.db.execute_query(DBController.INSERT_NEW_USER, first_name, last_name, username, user_id)
                        self.db.execute_query(DBController.SET_PASSWORD_QUERY, username, password)
                        self.db.execute_query(DBController.SET_PERMISSION_QUERY, username, permission)
                        _send_bool(True, TransmissionProtocol.ADD_NEW_USER_RESPONSE)
                    else:
                        _send_bool(False, TransmissionProtocol.ADD_NEW_USER_RESPONSE)

                else:
                    raise Exception('Not supported flag {}!'.format(flag))

        except ConnectionResetError:
            pass

        finally:
            if DEBUG:
                print("Close {}'s connection".format(client.getsockname()))
            client.close()

    def generate_captcha(self, text):

        return self.captcha_image_generator.generate(text, format='png').read()

    def validate_password_and_authorizations(self, username: str, password: str, permission: int = None) -> bool:
        try:
            encrypted_password_from_db = next(self.db.execute_query(DBController.GET_PASSWORD_QUERY, username))
            permission_from_db = next(self.db.execute_query(DBController.GET_USER_PERMISSION, username))

        except StopIteration:
            return False

        return encrypted_password_from_db == MainServer._encrypt(password) and \
               (True if permission is None else permission_from_db == permission)

    def check_user_captcha_guess(self, client: socket.socket, guess_text: str):
        captcha_text = self.db.execute_query(DBController.GET_CAPTCHA_TEXT, *self.socket_to_address_dict[client])
        return captcha_text == guess_text

    def create_tables(self):

        tables = {
            'users': (
                USERS_TABLE_DDL
            ),
            'login_statistics': (
                LOGIN_STATISTICS_TABLE_DDL
            ),
            'passwords': (
                PASSWORDS_TABLE_DDL
            ),
            'captchas_text': (
                MOST_RECENT_CAPTCHAS_TEXT_DDL
            ),
            'authorizations': (
                USER_AUTHORIZATION_DDL
            )}

        self.db.create_tables(tables)

        if ADD_TEST_ADMIN:
            self.db.execute_query(INSERT_NEW_USER, 'John', 'Doe', 'admin', '0123456789')
            self.db.execute_query(SET_PASSWORD_QUERY, 'admin', 'password')
            self.db.execute_query(SET_PERMISSION_QUERY, 'admin', ADMIN)

    # ************************************** Override methods ***********************************

    def close(self):
        """
        Deallocate the socket and db cached memory.
        """
        for client_socket in self.socket_to_address_dict.keys():
            client_socket.close()
        super(socket.socket, self).close()
        self.db.close()

        if DEBUG:
            print('\n\n******************** Server is down ************************\n\n')

    # ************************************** Static functions ***********************************

    @staticmethod
    def _sendto(client: socket.socket, data: bytes, flag: int):
        """
        This method sends to the client the data Using the protocol defined in file PocketProtocol.
        NOTE: Any data sending to clients should be though this method!

        :param client:  The data's addressee
        :param data:    This data will be send to the client.
        """
        if DEBUG:
            print(
                "Sending packet:\n"
                "   Flag: {}\n"
                "   Data: {}".format(flag, data),
                end='\n\n'
            )

        packet = TransmissionProtocol.wrap_data(data, flag)

        total_sent = 0
        while total_sent < len(packet):
            total_sent += client.send(
                packet[total_sent: min(
                    total_sent + MAX_TRANSFER_AT_ONCE, len(packet))])

    @staticmethod
    def _recvfrom(client: socket.socket) -> bytes:
        """
        This method receives from the client some data and unwrap it using the protocol defined in file PocketProtocol.
        NOTE: Any data receiving from clients should be though this method!

        :param client:  The data's sender.
        """
        data = b''
        size = int.from_bytes(client.recv(
            TransmissionProtocol.NUM_OF_BYTES_IN_DATA_SIZE), 'big') + TransmissionProtocol.NUM_OF_BYTES_IN_MESSAGE_TYPE

        while len(data) < size:
            data += client.recv(
                min(
                    MAX_TRANSFER_AT_ONCE,
                    MainServer._round_to_lower_power_of_2(size - len(data))))
        return data

    @staticmethod
    def _random_text(size: int) -> str:
        """
        :param size: The size of the random str.
        :return:     Random string contain characters from CAPTCHA_CAPTCHA_ALPHABET only.
        """
        return "".join([choice(CAPTCHA_ALPHABET) for _ in range(size)])

    @staticmethod
    def _encrypt(password: str):
        """
        :param password:
        :return:    Hash
        """
        return hash(hash(HASH_PREFIX + password + HASH_SUFFIX))

    @staticmethod
    def _round_to_lower_power_of_2(buffer_size: int):
        """
        :param buffer_size: The suprimum to the power of 2.
        :return:    The biggest power of 2 that is lower then $buffer_size
        """
        return 1 << (buffer_size.bit_length() - 1)

    @staticmethod
    def _space_text(text: str):
        """
        :param text:    The text to be spaced.
        :return:        $text's characters separated with white space.
        """
        return " ".join(text)


if __name__ == '__main__':
    MainServer()
