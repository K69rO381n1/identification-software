"""
Send / Receive protocol:
    Every data will be transferred in its *full form,
    wrapped with header that contains 4 bytes for that data length and 1 byte for the msg purpose.
    [length (4 bytes) : Flag (1 byte) : data]

    Length: integer from 0 to 256^3 (more that 16 Gb...)
    Flag: One of the following values,

        From client:

            b'0':   Request for captcha image.
                    Data expected: None

            b'1':   Request for captcha-text guess check
                    Data expected: [guess length (1 byte) : users's guess...]

            b'2':   Request for credentials check
                    Data expected: [username length (1 byte) : username... : password length (1 byte) : password....]

            b'3':   Request for facial image check
                    Data expected: Full png Image file (As-Is, including any header / footer)

            b'4':   Request for statistics data.
                    Data expected: None

            b'5':   Request for change password.
                    Data expected:  [username length (1 byte) : username... :
                                    old password length (1 byte) : old password.... :
                                    new password length (1 byte) : new password...]

            b'6'    Request for adding new facial image.
                    Data expected: [username length (1 byte) : username... :
                                    old password length (1 byte) : old password.... :
                                    Full png Image file (As-Is, including any header / footer)]

            b'7'    Request for adding new user. This request must made by an admin or it will fail.
                    Data expected: [
                                    admin username length   (1 byte)  : admin username...   :
                                    admin password length   (1 byte)  : admin password...   :
                                    first name length (1 byte)  : first name... :
                                    last name length  (1 byte)  : last name...  :
                                    username length   (1 byte)  : username...   :
                                    password length   (1 byte)  : password...   :
                                    id (4 byte) : permission (1 byte)]

        From server:

            b'0':   Captcha response from server.
                    Data expected: Full png Image file (As-Is, including any header / footer)

            b'1':   Captcha-text guess validation response.
                    Data expected: Boolean value (1 byte: b'\x00' for FALSE and b'\x01' for TRUE)

            b'2':   Credentials validation response.
                    Data expected: Boolean value (1 byte: b'\x00' for FALSE and b'\x01' for TRUE)

            b'3':   Facial recognition validation response.
                    Data expected: Boolean value (1 byte: b'\x00' for FALSE and b'\x01' for TRUE)

            b'4':   Return of the statistic data.
                    Data Expected: See static data package description.

            b'5':   Password change success response.
                    Data expected: Boolean value (1 byte:
                                    b'\x00' if the old username & password didn't match
                                    b'\x01' if the old username & password were correct and the password updated.

            b'6':   Facial image addition success response.
                    Data expected: Boolean value (1 byte:
                                    b'\x00' if the old username & password didn't match,
                                    b'\x01' if the old username & password were correct and the image added.

            b'7'    Adding new user success response.
                    Data expected: Boolean value (1 byte:
                                    b'\x00' if the admin username & password weren't correct,
                                    b'\x01' if the admin username & password weren't correct and the user has added.
"""

NUM_OF_BYTES_IN_DATA_SIZE = 4
NUM_OF_BYTES_IN_MESSAGE_TYPE = 1

BYTE_ORDER = 'big'

CAPTCHA_RESPONSE = CAPTCHA_REQUEST = 0
CAPTCHA_TEXT_CHECK_RESPONSE = CAPTCHA_TEXT_CHECK_REQUEST = 1
CREDENTIALS_CHECK_RESPONSE = CREDENTIALS_CHECK_REQUEST = 2
FACE_IMAGE_CHECK_RESPONSE = FACE_IMAGE_CHECK_REQUEST = 3
STATISTICS_DATA_RESPONSE = STATISTICS_DATA_REQUEST = 4
CHANGE_PASSWORD_RESPONSE = CHANGE_PASSWORD_REQUEST = 5
ADD_IMAGE_RESPONSE = ADD_IMAGE_REQUEST = 6
ADD_NEW_USER_RESPONSE = ADD_NEW_USER_REQUEST = 7

MAX_USERNAME_LENGTH = MAX_PASSWORD_LENGTH = 30
MAX_FIRST_NAME_LENGTH = MAX_LAST_NAME_LENGTH = 20


def wrap_data(data: bytes, flag: int) -> bytes:

    return \
        to_bytes(len(data) + NUM_OF_BYTES_IN_MESSAGE_TYPE, NUM_OF_BYTES_IN_DATA_SIZE) + \
        to_bytes(flag, NUM_OF_BYTES_IN_MESSAGE_TYPE) + \
        data


def to_bytes(value, length) -> bytes:
    return value.to_bytes(length, BYTE_ORDER)


def parse_str(data: bytes, num_of_argument_expected: int) -> tuple:
    i = 0
    strings = []
    while i < len(data) and len(strings) < num_of_argument_expected:
        str_len = int.from_bytes(data[i:i + 1], 'big')
        strings.append(
            _bytes_to_str(data[i+1: i+1+str_len]))
        i += 1+str_len

    # If there is eny excess data we append it too (as bytes!)
    if i < len(data):
        strings.append(data[i:])

    return tuple(strings)


def _bytes_to_str(bytes_value: bytes) -> str:
    return str(bytes_value)[2:-1]
