from __future__ import unicode_literals
import logging, re, os, subprocess
import time

from aiogram import Bot, Dispatcher, executor, types
from youtube_dl import YoutubeDL

STORAGE_DIR = 'storage'
API_TOKEN = os.environ.get("API_TOKEN")
STORAGE = os.path.abspath(STORAGE_DIR)
K51_KEY = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('archiver')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Initialize youtube-dl
ydl_opts = {
    'logger': logger,
}
ydl = YoutubeDL(ydl_opts)

async def startup(dispatcher):
    if not os.path.exists(STORAGE):
        logger.info("No storage folder found")
        os.makedirs(STORAGE)
        logger.info("Storage folder created")


    while ipfs_keys := subprocess.run(["ipfs", "key", "list"], capture_output=True).returncode:
        ipfs_keys_msg = ipfs_keys.stderr.decode("utf-8")
        if "lock" in ipfs_keys_msg:
            time.sleep(1)
            logger.warning(ipfs_keys_msg)
            continue
        else:
            return


    keys = ipfs_keys.stdout.decode("utf-8").rstrip().split("\n")
    if len(keys) > 1:
        try:
            global K51_KEY
            K51_KEY = keys[keys.index("key")]
            logger.info("found a key")
        except ValueError:
            logger.info("no keys found, using default")


@dp.channel_post_handler()
async def post(message: types.Message):
    youtube_pattern = r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
    if match := re.search(youtube_pattern, message.text):
        link = match.group(0)
        logger.info(f"got youtube link: {link}")

        # download the video
        title = ydl.extract_info(link, download=False).get("title")
        ydl.download([link])


        ipfs_add = subprocess.run(["ipfs", "add", "--nocopy", "-r", f"{STORAGE}"], capture_output=True)

        if ipfs_add.returncode:
            logger.error(ipfs_add.stderr.decode("utf-8"))
            return
        logger.info("the video added to ipfs")

        ipfs_stdout = ipfs_add.stdout.decode("utf-8").rstrip().replace("added ", "")
        files = [file.split(" ", 1) for file in ipfs_stdout.split("\n")]
        files = [{"hash":i[0], "filename":i[1]} for i in files]

        [dir_hash] = [i["hash"] for i in files if i["filename"] == STORAGE_DIR]
        [last_added] = [i["hash"] for i in files if title in i["filename"]]

        await message.edit_text(message.md_text + f"\n\n[[ipfs]](https://ipfs.io/ipfs/{last_added})", parse_mode="MarkdownV2")

        command = ["ipfs", "name", "publish", "--quieter", f"{dir_hash}"]

        if K51_KEY:
            logger.info(f"k51 key {K51_KEY}")
            command.append(f"--key={K51_KEY}")

        ipfs_publish = subprocess.run(command, capture_output=True)

        if ipfs_publish.returncode:
            logger.error(ipfs_publish.stderr.decode("utf-8"))
            return

        logger.info(f"ipns updated {ipfs_publish.stdout.decode('utf-8').rstrip()}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=startup)
