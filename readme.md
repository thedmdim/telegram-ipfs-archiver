**MOVED TO** https://github.com/thedmdim/telegram-ipfsacer **MOVED TO** https://github.com/thedmdim/telegram-ipfsacer **MOVED TO**

[![Docker Pulls](https://img.shields.io/docker/pulls/thedmdim/telegram-ipfs-archiver)](https://hub.docker.com/r/thedmdim/telegram-ipfs-archiver)
[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/thedmdim/telegram-ipfs-archiver/latest)](https://hub.docker.com/r/thedmdim/telegram-ipfs-archiver)

# Telegram IPFS archivator

![](example.jpg)

## Workflow

1. This bot reads post's last line
3. If it contains youtube link, starts download the video via youtube-dl
4. Adds a folder with videos in ipfs
5. Create IPNS link (for link to be static, use your own key)

## Examlpe channel
https://t.me/mov3371

## Docker run example
```bash
docker run -t \
  -e API_TOKEN=your_telegram_api_token \
  -e CHANNEL_ID=your_channel_id \
  -e MAX_RETRIES=50 \
  -v ~/your/video/dir/:/root/storage \
  -v ~/your/ipfs/key.key:/root/key.key \
  -p 4001:4001 \
  -p 4001:4001/udp \
  thedmdim/telegram-ipfs-archiver
```

## Optional parameters
`MAX_RETRIES` - max quantity youtube-dl will try to download the video, if not set default 50

`-v ~/your/ipfs/key.key:/root/key.key` - if not set, will use your default IPNS id
