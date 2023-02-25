## What?

Transcribe an audio-stream in almost real time using [OpenAI-Whisper](https://github.com/openai/whisper). Monitor it for specific terms in the transcribed text using fuzzy-matching. Trigger an alarm via Signal messenger when your terms are mentioned.

## How?

Run `pip install -r requirements.txt` to resolve dependencies.

Consists of three parts:
1. `save_stream.py` saves .mp3 files in chunks of 30sec from an audio stream
2. `transcribe.py` transcribes each incoming audio chunk using [OpenAI-Whisper](https://github.com/openai/whisper). Then, it uses fuzzy matching to monitor the spoken word for specific terms. On match, it calls `msg_group_via_signal.sh`
3. `msg_group_via_signal.sh` relays the alarm message to the [signal-cli](https://github.com/AsamK/signal-cli) tool which messages a group on the Signal messenger

Take a look at the files to configure them. For example, you can set durations during which the stream is monitored.
Per default the `small` OpenAI-Whisper model is used. Thus, the transcription quality is decent but not perfect. Hence, we use fuzzy-matching to monitor for our terms, so that we reduce false-negatives (but increase false-positive) alarms. The benefit of the `small` model being that it works in almost real-time even on a CPU-only machine with mediocre specs (on AWS a `c5a.large` EC2 instance is sufficient). There will be some delay because of the 30sec chunks and because inference takes some time, but it's fast enough to process all audio without falling behind. With better specs / GPU you can increase model size for better quality transcriptions or reduce latency.

## Why?

My very specific use case:
My sports team participated in a contest hosted by a local radio station that went on for a couple of weeks. If the name of our team was mentioned on-air, we had a couple of minutes to call the radio station in order to win a prize.
This was my alternative to listening to shitty music.
