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
            b'1':


        From server:

            b'0' Captcha response from server

    * For example, Image or Text files will keep their completeness (including any header / footer) and send As-Is.
"""

NUM_OF_DIGITS_IN_DATA_SIZE = 10
NUM_OF_DIGITS_IN_MESSAGE_TYPE = 4


def wrap_data(data: bytes, flag: int) -> bytes:
    return _zeros_padding(len(data), NUM_OF_DIGITS_IN_DATA_SIZE) + \
           _zeros_padding(flag, NUM_OF_DIGITS_IN_MESSAGE_TYPE) + \
           data


def _zeros_padding(value: int, padding_size: int) -> bytes:
    return bytes('{0:0' + str(padding_size) + 'd}'.format(value))
