#!/usr/bin/env python3

import time

from telethon.sync import TelegramClient

from mysecrets import API_ID, API_HASH


QOIPLACE_BOT_NAME = "@QoiPlaceBot"


def run():
    with TelegramClient("mybot", API_ID, API_HASH) as client:
        print("Setting first byte ...")
        # Set the byte at index 0 to 255, i.e. "QOI_OP_RGB"
        client.send_message(QOIPLACE_BOT_NAME, "0 255")
        print("Waiting 60 seconds before setting the next byte, due to ratelimit ...")
        time.sleep(60)

        print("Setting second byte ...")
        # Set the byte at index 1 to 255, i.e. "red = full"
        client.send_message(QOIPLACE_BOT_NAME, "1 255")
        print("Waiting 60 seconds before setting the next byte, due to ratelimit ...")
        time.sleep(60)

        print("Setting third byte ...")
        # Set the byte at index 2 to 0, i.e. "green = off"
        client.send_message(QOIPLACE_BOT_NAME, "2 0")
        print("Waiting 60 seconds before setting the next byte, due to ratelimit ...")
        time.sleep(60)

        print("Setting fourth (last) byte ...")
        # Set the byte at index 3 to 0, i.e. "blue = off"
        client.send_message(QOIPLACE_BOT_NAME, "3 0")
        print("Done!")


if __name__ == "__main__":
    run()
