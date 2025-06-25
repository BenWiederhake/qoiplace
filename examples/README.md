# In general

These examples use `telethon` (see requirements.txt), but of course any other user-client library should work.

Note that using a bot to talk with the @QoiPlaceBot cannot work, since Telegram datacenters refuse to transmit messages between bots.

## telethon

First, copy `mysecrets_template.py` to `mysecrets.py` and fill in your API ID and hash.

With telethon, you'll need to "log in", i.e. type in a code on the console that you receive via some other method (usually telegram message from "Telegram", or a SMS code), but only the first time you use it. Afterwards, the authentication is stored in `mybot.session`, which is why you shouldn't share that file with anyone.

Then, have fun. Maybe try out the following examples to see what they're doing.

# `setpixel.py`

Sets the first pixel to red (#FF0000).
