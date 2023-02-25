"""Transcribe audio using Whisper Model"""
#%%
import logging
import subprocess
import time
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import whisper
from fuzzysearch import find_near_matches

DAY = datetime.utcnow().date().isoformat()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh = logging.FileHandler(f"./logs/transcribe_{DAY}.log")
fh.setFormatter(fmt)
sh = logging.StreamHandler()
sh.setFormatter(fmt)
log.addHandler(sh)
log.addHandler(fh)

PATH_TO_SIGNAL_SCRIPT = "./msg_group_via_signal.sh"
PATH_AUDIO_FILES = f"./data/audio/{DAY}"
PATH_TEXT_FILES = f"./data/text/{DAY}"

Path(PATH_AUDIO_FILES).mkdir(exist_ok=True)
Path(PATH_TEXT_FILES).mkdir(exist_ok=True)

# Consider file new if created less than this
RECENT_FILES_TIME_MIN = 1

# We want to work with this tz, no matter what the local clock is
LOCAL_TZ = ZoneInfo("Europe/Berlin")
# We record only during these times
STREAM_TIME_FROM = dt_time(5, 55, tzinfo=LOCAL_TZ)
STREAM_TIME_TO = dt_time(19, 15, tzinfo=LOCAL_TZ)

SEARCH_TERMS_LIVE = ["Data Science", "Data Engineering"]
SEARCH_TERMS_DEV = ["Data Analytics"]


def get_recent_files() -> list:
    """Return file paths for recently created files

    Returns:
        list: File paths
    """
    log.info("Listing recent files")
    now = datetime.utcnow()
    audio_files = []
    for file in sorted(Path(PATH_AUDIO_FILES).iterdir()):
        if ".mp3" in file.name:
            file_ts = datetime.fromtimestamp(file.stat().st_ctime)
            if now - file_ts <= timedelta(minutes=RECENT_FILES_TIME_MIN):
                audio_files.append(file)
    log.debug("Recent files: %s", audio_files)
    return audio_files


def send_alarm_to_signal(text: str, live=False):
    """Send alarm via signal bash script

    Args:
        text (str): Text with match
        live (bool, optional): Live or test. Defaults to False.
    """

    message = "This is a test. I've picked up the following: \n"
    if live:
        message = "This is a LIVE. I've picked up the following:\n"
    message = message + text
    subprocess.Popen([PATH_TO_SIGNAL_SCRIPT, message])


def transcribe_file(model, options, file_path: str) -> str:
    """Transcribe the .mp3 file to text

    Args:
        model: Whisper Model
        file_path (str): File path

    Returns:
        str: Transcribed text
    """
    audio = whisper.load_audio(file_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    result = whisper.decode(model, mel, options)
    return result.text  # type: ignore


def search_for_text(text: str):
    """Search for search term in text and send alarm if found"

    Args:
        text (str): Text to search
    """
    log.info("Searching in text")
    text = text.lower()

    for term in SEARCH_TERMS_LIVE:
        results = find_near_matches(term, text, max_l_dist=2)
        if results:
            log.debug("Search results: %s", results)
            log.info("Found live term: %s", term)
            send_alarm_to_signal(text, live=True)

    for term in SEARCH_TERMS_DEV:
        results = find_near_matches(term, text, max_l_dist=1)
        if results:
            log.debug("Search results: %s", results)
            log.info("Found dev term: %s", term)
            send_alarm_to_signal(text, live=False)


def save_text_to_file(text: str):
    """Save transcribed text to file

    Args:
        text (str): Transcribed text
    """
    now = datetime.utcnow().isoformat(timespec="hours")
    path = PATH_TEXT_FILES + "/text_" + now + ".txt"
    with open(path, "a", encoding="utf-8") as file:
        file.write(text + " \n")


def is_transcription_time() -> bool:
    """Check if we are in the time period to transcribe

    Returns:
        bool: is_transcription_time
    """

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
        return False
    return True


def process_audio_files(files: list, model, options):
    """Process audio files

    Args:
        files (list): Input audio files
    """
    log.info("Processing files")
    for file in files:
        now = datetime.utcnow().isoformat(timespec="seconds")
        text = transcribe_file(model, options, file)
        log.debug("File: %s, Time: %s\nText: %s\n", file.name, now, text)
        search_for_text(text)
        save_text_to_file(text)
    log.info("OK: processed all recent files")


def main():
    """Main"""
    log.info("Started")
    model = whisper.load_model("small")
    options = whisper.DecodingOptions(fp16=False)
    while is_transcription_time():
        files = get_recent_files()
        process_audio_files(files, model, options)
        time.sleep(10)
    log.info("OK: finished transcription")


#%%
if __name__ == "__main__":
    main()
