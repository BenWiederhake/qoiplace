#!/usr/bin/env python3

from mysecrets import API_ID, API_HASH
from telethon.sync import TelegramClient, events
import time

QOIPLACE_BOT_NAME = "@QoiPlaceBot"


def run():
    with TelegramClient("mybot", API_ID, API_HASH) as client:
        print("Setting first byte ...")
        client.send_message(QOIPLACE_BOT_NAME, "0 255")  # Set the byte at index 0 to 255, i.e. "QOI_OP_RGB"
        print("Waiting 60 seconds before setting the next byte, due to ratelimit ...")
        time.sleep(60)
        print("Setting second byte ...")
        client.send_message(QOIPLACE_BOT_NAME, "1 255")  # Set the byte at index 1 to 255, i.e. "red = full"
        print("Waiting 60 seconds before setting the next byte, due to ratelimit ...")
        time.sleep(60)
        print("Setting third byte ...")
        client.send_message(QOIPLACE_BOT_NAME, "2 0")  # Set the byte at index 2 to 0, i.e. "green = off"
        print("Waiting 60 seconds before setting the next byte, due to ratelimit ...")
        time.sleep(60)
        print("Setting fourth (last) byte ...")
        client.send_message(QOIPLACE_BOT_NAME, "3 0")  # Set the byte at index 3 to 0, i.e. "blue = off"
        print("Done!")


if __name__ == "__main__":
    run()
