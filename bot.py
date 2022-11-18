import logging, re, subprocess, os
import time
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError

STORAGE = Path("storage")
API_TOKEN = os.environ.get("API_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

K51_KEY = None

# Configuration
mrvar = os.environ.get("MAX_RETRIES")
MAX_RETRIES = int(mrvar) if mrvar else 50

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('archiver')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Initialize youtube-dl
ydl_opts = {
    'outtmpl': f"{STORAGE}/%(title)s-%(id)s.%(ext)s",
    'logger': logger,
    'restrictfilenames': True
}
ydl = YoutubeDL(ydl_opts)

async def startup(dispatcher):
    STORAGE.mkdir(exist_ok=True)
    while True:
        ipfs_keys = subprocess.run(["ipfs", "key", "list"], capture_output=True)
        if ipfs_keys.returncode:
            ipfs_keys_stderr = ipfs_keys.stderr.decode("utf-8")
            if "lock" in ipfs_keys_stderr:
                logger.warning(ipfs_keys_stderr)
                time.sleep(1)
                continue
            else:
                logger.info(ipfs_keys_stderr)
                return
        break

    keys = ipfs_keys.stdout.decode("utf-8").rstrip().split("\n")
    if len(keys) > 1:
        try:
            global K51_KEY
            K51_KEY = keys[keys.index("key")]
            logger.info("found a key")
        except ValueError:
            logger.info("no keys found, using default")

    if os.listdir(STORAGE):
        add_and_publish()


def download_video(link: str, retries: int):
    for i in range(retries):
        try:
            logger.info("Start downloading video")
            info = ydl.extract_info(link, download=False)
            title = Path(ydl.prepare_filename(info)).stem
            ydl.download([link])
            return title
        except DownloadError:
            logger.warning(f"DownloadError, try {i}/{retries}")
            time.sleep(2)
            continue
    logger.error(f"Couldn't download video in {retries} tries")

def add_and_publish():
    ipfs_add = subprocess.run(["ipfs", "add", "--nocopy", "-r", f"{STORAGE}"], capture_output=True)

    if ipfs_add.returncode:
        logger.error(ipfs_add.stderr.decode("utf-8"))
        return

    logger.info("Folder updated")

    ipfs_stdout = ipfs_add.stdout.decode("utf-8").rstrip().replace("added ", "")
    files = [file.split(" ", 1) for file in ipfs_stdout.split("\n")]
    files = [{"hash": i[0], "filename": i[1]} for i in files]

    [dir_hash] = [i["hash"] for i in files if Path(i["filename"]) == STORAGE]

    command = ["ipfs", "name", "publish", "--quieter", f"{dir_hash}"]
    if K51_KEY:
        command.append(f"--key={K51_KEY}")

    ipfs_publish = subprocess.run(command, capture_output=True)

    if ipfs_publish.returncode:
        logger.error(ipfs_publish.stderr.decode("utf-8"))
        return

    logger.info(f"IPNS published: {ipfs_publish.stdout.decode('utf-8').rstrip()}")

    return files


@dp.channel_post_handler()
async def post(message: types.Message):
    youtube_pattern = r"(?i)\b((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

    message_lines = message.html_text.split("\n")
    last_line = message_lines.pop().replace("\\","")

    match = re.search(youtube_pattern, last_line)

    if match and message.from_id == CHANNEL_ID:

        logger.info(f"got a youtube link: {match.group(0)}")

        # download the video
        title = download_video(match.group(0), MAX_RETRIES)
        if not title:
            return

        files = add_and_publish()

        [last_added] = [i["hash"] for i in files if title in i["filename"]]

        replacer = f'<a href="{last_line}">youtube</a> | <a href="https://ipfs.io/ipfs/{last_added}">ipfs</a>'
        message_lines.append(re.sub(youtube_pattern, replacer, last_line, count=1))
        await message.edit_text("\n".join(message_lines), parse_mode="HTML")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=startup)
