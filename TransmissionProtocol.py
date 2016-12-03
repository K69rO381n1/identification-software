"""
Send / Receive protocol:
    Every data will be transferred in its *full form,
    wrapped with header that contains 3 bytes for that data length and 1 byte for the msg purpose.
    [length (3 bytes) : Flag (1 byte) : data]

    Length: integer from 0 to 256^3 (more that 16 MB...)
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

            b'5'    Request for adding new facial image.
                    Data expected: [username length (1 byte) : username... :
                                    old password length (1 byte) : old password.... :
                                    Full png Image file (As-Is, including any header / footer)]

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
"""

NUM_OF_BYTES_IN_DATA_SIZE = 3
NUM_OF_BYTES_IN_MESSAGE_TYPE = 1

BYTE_ORDER = 'big'

CAPTCHA_RESPONSE            = CAPTCHA_REQUEST               = b'0'
CAPTCHA_TEXT_CHECK_RESPONSE = CAPTCHA_TEXT_CHECK_REQUEST    = b'1'
CREDENTIALS_CHECK_RESPONSE  = CREDENTIALS_CHECK_REQUEST     = b'2'
FACE_IMAGE_CHECK_RESPONSE   = FACE_IMAGE_CHECK_REQUEST      = b'3'
STATISTICS_DATA_RESPONSE    = STATISTICS_DATA_REQUEST       = b'4'
CHANGE_PASSWORD_RESPONSE    = CHANGE_PASSWORD_REQUEST       = b'5'
ADD_IMAGE_RESPONSE          = ADD_IMAGE_REQUEST             = b'6'


def wrap_data(data: bytes, flag: int) -> bytes:

    return \
        to_bytes(len(data), NUM_OF_BYTES_IN_DATA_SIZE) + \
        to_bytes(flag, NUM_OF_BYTES_IN_MESSAGE_TYPE) + \
        data


def to_bytes(value, length) -> bytes:
    return value.to_bytes(length, BYTE_ORDER)


def parse_str(data: bytes, num_of_argument_expected: int) -> tuple:
    i = 0
    strings = []
    while i < len(data):
        str_len = int.from_bytes(data[i], 'big')
        strings.append(
            _bytes_to_str(data[i+1: i+1+str_len]))
        i += 1+str_len

    assert len(strings) == num_of_argument_expected, \
        Exception('The data does not match to the number of arguments expected!')

    return tuple(strings)


def _bytes_to_str(bytes_value: bytes) -> str:
    return str(bytes_value)[2:-1]
