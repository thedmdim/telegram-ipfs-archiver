#!/bin/sh
ipfs init
key=$(find . -name '*.key' -print -quit)
if [ "$key" ]; then ipfs key import key $key; fi
ipfs daemon & python bot.py
