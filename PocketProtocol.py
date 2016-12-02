"""
Send / Receive protocol:
    Every data will be transferred in its *full form,
    wrapped with header that contains 10 digits for that data length and 4 digits for the msg purpose.
    [ length (10 dig) : Flag (4 dig) : data ]

    Length: integer from b'0000000000' to b'999999999' (almost 1 GB, more then enough...)
    Flag: One of the following values,

        From client:

            b'0':   Request for captcha image.
                    Data expected: None

            b'1':   Request for credentials check
                    Data expected: [username length (2 dig) : username... : password length (2 dig) : password....]

            b'2':   Request for facial image check
                    Data expected: Full png Image file (As-Is, including any header / footer)

            b'3':   Request for statistics data.
                    Data expected: None

            b'4':   Request for change password.
                    Data expected:  [username length (2 dig) : username... :
                                    old password length (2 dig) : old password.... :
                                    new password length (2 dig) : new password...]

            b'5'    Request for adding new facial image.
                    Data expected: [username length (2 dig) : username... :
                                    old password length (2 dig) : old password.... :
                                    Full png Image file (As-Is, including any header / footer)]

        From server:

            b'0':   Captcha response from server.
                    Data expected: Full png Image file (As-Is, including any header / footer)

            b'1':   Credentials validation response.
                    Data expected: Boolean value (1 byte: 0 for FALSE or something else for TRUE)

            b'2':   Facial recognition validation response.
                    Data expected: Boolean value (1 byte: 0 for FALSE or something else for TRUE)

            b'3':   Return of the statistic data.
                    Data Expected: See static data package description.

            b'4':   Password change success response.
                    Data expected: Boolean value (1 byte:
                                    0 if the old username & password didn't match,
                                    something else if the old username & password were
                                    correct and the password updated.

            b'5':   Facial image addition success response.
                    Data expected: Boolean value (1 byte:
                                    0 if the old username & password didn't match,
                                    something else if the old username & password were
                                    correct and the image added.

"""

NUM_OF_DIGITS_IN_DATA_SIZE = 10
NUM_OF_DIGITS_IN_MESSAGE_TYPE = 4
NUM_OF_DIGITS_IN_USERNAME_LENGTH = 2
NUM_OF_DIGITS_IN_PASSWORD_LENGTH = 2


def wrap_data(data: bytes, flag: int) -> bytes:
    return _zeros_padding(len(data), NUM_OF_DIGITS_IN_DATA_SIZE) + \
           _zeros_padding(flag, NUM_OF_DIGITS_IN_MESSAGE_TYPE) + \
           data


def _zeros_padding(value: int, padding_size: int) -> bytes:
    return bytes('{0:0' + str(padding_size) + 'd}'.format(value))
