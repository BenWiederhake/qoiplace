#!/usr/bin/env python3

import time

from telethon.sync import TelegramClient

from mysecrets import API_ID, API_HASH


QOIPLACE_BOT_NAME = "@QoiPlaceBot"
VERBOSE = True
DEFAULT_COMMANDS = [
    "1034159 108",
    "1034160 228",
    "1034161 223",
    "1034158 254",
]


def run_commands(cmds, ask_user=True):
    print(f"About to execute the following {len(cmds)} commands:")
    for cmd in cmds:
        print(f"  {cmd}")
    if ask_user:
        user_decision = input("Execute? [Y/n] ")
        if user_decision not in ["", "Y", "y", "J", "j"]:
            print("Aborting ...")
            exit(1)
    with TelegramClient("mybot", API_ID, API_HASH) as client:
        for i, cmd in enumerate(cmds):
            print(f'Sending command {i+1}/{len(cmds)}: "{cmd}" ...')
            client.send_message(QOIPLACE_BOT_NAME, cmd)
            print(
                "  Waiting 60 seconds before setting the next byte, due to ratelimit ..."
            )
            time.sleep(60)


if __name__ == "__main__":
    run_commands(DEFAULT_COMMANDS, ask_user=False)
