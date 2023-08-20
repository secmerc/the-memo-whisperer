import streamlit
import pathlib
import sys
import logging as log

from memowhisper import TranscriptLedger
from memowhisper import MemoAudio
from memowhisper import AudioTranscript
from memowhisper import get_file_hash
from memowhisper import APPLE_VOICE_MEMO_PATH

log.basicConfig(encoding='utf-8', level=log.INFO)

@streamlit.cache_data
def get_transcription_sources():
    sources = dict()
    sources['iCloud Voice Memo'] = pathlib.Path(str(pathlib.Path.home()) + APPLE_VOICE_MEMO_PATH)

    return(sources)

@streamlit.cache_data
def get_memo_files(source_dir):
    return [file for file in pathlib.Path(source_dir).glob('*') if MemoAudio._is_supported_audio(file)]


if __name__ == "__main__":

    with streamlit.sidebar:
        streamlit.title("The Memo Whisperer")  
        sources = get_transcription_sources()
        selected_source = streamlit.selectbox("Select a memo source", sources)
        
        streamlit.file_uploader("Choose a file", type=['m4a', 'wav'])

    streamlit.header("Memos")

    transcribed_files = [None]
    transcription_contents = ""

    source_dir = sources[selected_source]
    log.info("source dir: {}".format(source_dir))
    #ledger = TranscriptLedger(source_dir)

    files = get_memo_files(source_dir)

        #try:
        #    log.info("Converting to wav: {}".format(file))
        #    audio = MemoAudio(file).get_audio()
        #except FileNotFoundError:
        #    log.info("Skipping non audio file {}".format(file))
        #    continue

        #log.info("Transcribing: {}".format(file))
        #transcript = AudioTranscript(audio).get_transcript()

        #store hashes in ledger only if we succeeded
        #audiohash = get_file_hash(audio)
        #log.info("Adding {} {} to ledger as: {} {}".format(file, audio, hash, audiohash))
        #ledger.append(hash)
        #ledger.append(audiohash)

    selected_file = streamlit.selectbox(
        label="Select a transcription", 
        options=files, 
        index=0,
        label_visibility="collapsed",
        format_func=lambda x: 'Select a memo file...' if x == None else x
    )
    
    if selected_file is not None:
        transcription = pathlib.Path("{}.txt".format(selected_file))
        height = 0
        button = ""
        try:
            with open(transcription, mode='r', encoding='ascii', errors='replace') as f:
                height = 500
                transcription_contents = f.read()
                button = "Delete transcription"
        except FileNotFoundError:
            height = 1
            transcription_contents = ""
            button= "Create transcription"

        streamlit.button(button)
        streamlit.text_area(label="Transcription text", value=transcription_contents, height=height, label_visibility='collapsed')
        
    
    