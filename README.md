# QOI place

Like a crossover of pixelflut and place, but with the QOI format.

This is the "server" and some (intentionally-limited) clients for a little ad-hoc game, to be played via Telegram (for now).

In particular:
- Like pixelflut: Everyone (including you!) is allowed and meant to manipulate a common resource (e.g. the shared QOI file).
- Like r/place: There's a cooldown timer of 60 seconds between each modification. (The exact number is subject to change.)
- With the QOI format: Instead of writing RGB values, you write raw bytes of a file. This file is then interpreted as a QOI file.
- Every minute or so, the newest image will be posted to the "QOI place" channel, if anything changed.

## Table of Contents

- [Quickstart](#quickstart): How to draw your very first pixels
- [Install](#install): How to set up your own "server"
- [Usage](#usage): How to interact, how to use the examples
- [TODOs](#todos): What's left to be done
- [NOTDOs](#notdos): What is definitely out of scope
- [Contribute](#contribute): Contribute!

## Quickstart

Go to [@QoiPlaceBot](https://t.me/QoiPlaceBot), send him something like "12 34" (i.e. set the byte with index 12 to value 34), and see the result a bit later in [QoiPlace](https://t.me/qoiplace)! Technically, that's already everything.

Computing these indices and byte values by hand might be quite cumbersome, so you might enjoy some kind of automation as seen in the [examples](https://github.com/BenWiederhake/qoiplace/tree/master/examples#telethon) folder. Try running `setpixel.py`, and watch the first pixel turning red!

## Install

```console
$ # Install Python3 somehow
$ python3 -m venv .venv  # Prepare a virtual environment
$ source .venv/bin/activate  # or whichever script is appropriate for your shell
$ pip3 install -r requirements.txt
```

Copy `mysecrets_template.py` to `mysecrets.py`, and fill in your details. You need to [create a bot](https://github.com/BenWiederhake/der-wopper-bot?tab=readme-ov-file#usage) if you don't already have one.

Then, just run it with the virtual environment enabled. I like to run it as `./bot.py 2>&1 | tee bot_$(date +%s).log` because that works inside screen and I still have arbitrary scrollback.

## Usage

As the saying goes, we live in a society, so please be excellent. In particular:
- Have fun, and let other people also have fun (in particular, no hate speech or illegal imagery)
- Live and let live (in particular, don't behave in any way that might seem like attacking the people, bot, infrastructure, or anyone else)
- If you have any ideas how to make this project even more awesome, feel free to post them here! I'd love to hear your suggestions :D
- Also, feel free to leave feedback on this repo

If you're fine with this, you're welcome to join the fun!
- https://t.me/qoiplace : This is where the bot regularly posts the newest QOI files and PNG renders
- There's also a discussion group (linked from the qoiplace channel)
- https://t.me/QoiPlaceBot : This is the bot itself. Talk to it, in order to "write" to the QOI file!

The bot has an internal buffer of 1,048,576 bytes, that's the maximum file size of a 512×512 pixel QOI image.
You can read up on the QOI format here: https://qoiformat.org/qoi-specification.pdf
Send the bot messages like "456789 123" to set the 456789th byte to 123.

You'll have to wait 59 seconds between any such message. Note that this is a retaliatory rate limit: If you try to cheat and send a message before the time is up, then the timer resets to (at least) 59 seconds. So you might want to wait 60 seconds instead, or something like that.

There are some examples in the `examples/` subfolder.

## TODOs

- Examples
- Censor-command for admin
- Web interface with some kind of telegram-based authentication maybe?
- Maybe some more efficient way to deal with the state?

## NOTDOs

Here are some things this project will definitely (probably) not support:
* Huge canvases
* Anything AI
* Any form of monetization

## Contribute

Feel free to dive in! [Open an issue](https://github.com/BenWiederhake/qoiplace/issues/new) or submit PRs.
