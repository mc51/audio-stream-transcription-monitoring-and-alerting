"""Record radio stream data to mp3 files"""
#%%
import logging
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

DAY = datetime.utcnow().date().isoformat()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh = logging.FileHandler(f"./logs/save_stream_{DAY}.log")
fh.setFormatter(fmt)
sh = logging.StreamHandler()
sh.setFormatter(fmt)
log.addHandler(sh)
log.addHandler(fh)

URL = "https://radio.com/stream.mp3"
CHUNK_TIME_SECONDS = 30
DATA_PATH = f"./data/audio/{DAY}"
Path(DATA_PATH).mkdir(exist_ok=True)

# We want to work with this tz, no matter what the local clock is
LOCAL_TZ = ZoneInfo("Europe/Berlin")
# We record only during these times
STREAM_TIME_FROM = time(5, 55, tzinfo=LOCAL_TZ)
STREAM_TIME_TO = time(19, 0, tzinfo=LOCAL_TZ)


def record_stream_to_file(stream: requests.Response):
    """Record stream audio to files as .mp3 in chunks during recording times

    Args:
        stream (requests.Response): Audio stream
    """
    start_utc = datetime.utcnow()
    start_local = datetime.now(tz=LOCAL_TZ)
    current_local_time = start_local.time()
    log.info(
        "Current tz time: %s. Stream from: %s Stream until: %s",
        current_local_time,
        STREAM_TIME_FROM,
        STREAM_TIME_TO,
    )
    if not STREAM_TIME_FROM < current_local_time < STREAM_TIME_TO:
        log.warning("Not during recording time")
        sys.exit(0)
    filename = DATA_PATH + "/stream_" + start_utc.isoformat(timespec="seconds") + ".mp3"
    log.info("Writing stream to: %s", filename)
    with open(filename, "wb") as file:
        try:
            for block in stream.iter_content(1024):
                file.write(block)
                if datetime.utcnow() - start_utc > timedelta(
                    seconds=CHUNK_TIME_SECONDS
                ):
                    file.close()
                    record_stream_to_file(stream)
        except KeyboardInterrupt:
            log.info("Received keyboard interrupt")
            sys.exit(0)


def main():
    """Main"""
    log.info("Started main")
    stream = requests.get(URL, timeout=30, stream=True)
    record_stream_to_file(stream)
    log.info("OK: finished recording")


#%%
if __name__ == "__main__":
    main()
