# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
import base64


# CRC Stuff


async def crc_that(string: str) -> int:
    """
    the PHP's hash(crc32) in Python :P

    implem in python:
       https://chezsoi.org/shaarli/shaare/U7admg
       https://stackoverflow.com/a/50843127/636849
    """
    a = bytearray(string, "utf-8")
    crc = 0xffffffff
    for x in a:
        crc ^= x << 24
        for k in range(8):
            crc = (crc << 1) ^ 0x04c11db7 if crc & 0x80000000 else crc << 1
    crc = ~crc
    crc &= 0xffffffff
    return int.from_bytes(crc.to_bytes(4, 'big'), 'little')


async def small_hash(text: str) -> str:
    """
    Returns the small hash of a string, using RFC 4648 base64url format
    eg. smallHash('20111006_131924') --> yZH23w
    Small hashes:
     - are unique (well, as unique as crc32, at last)
     - are always 6 characters long.
     - only use the following characters: a-z A-Z 0-9 - _ @
     - are NOT cryptographically secure (they CAN be forged)
    In Shaarli, they are used as a tinyurl-like link to individual entries.
    """
    number = await crc_that(text)

    number_bytes = number.to_bytes((number.bit_length() + 7) // 8, byteorder='big')

    encoded = base64.b64encode(number_bytes)
    final_value = encoded.decode().rstrip('=').replace('+', '-').replace('/', '_')
    return final_value
