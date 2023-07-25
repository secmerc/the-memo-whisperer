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


def get_transcription_sources():

    sources = dict()
    sources['iCloud Voice Memo'] = pathlib.Path(str(pathlib.Path.home()) + APPLE_VOICE_MEMO_PATH)

    return(sources)

if __name__ == "__main__":

    streamlit.title("Memo Whisperer")

    with streamlit.sidebar:  
        streamlit.title("Memos")      
        sources = get_transcription_sources()
        selected_source = streamlit.selectbox("Detected sources", sources)
        
        streamlit.file_uploader("Choose a file", type=['m4a', 'wav'])

    streamlit.header("Transcriptions")

    transcribed_files = []
    transcription_contents = ""

    source_dir = sources[selected_source]
    log.info("source dir: {}".format(source_dir))
    ledger = TranscriptLedger(source_dir)

    for file in pathlib.Path(source_dir).glob('*'):

        #check if sha is in the ledger, this handles all cases of original audio or processed wav
        ## one edge case can be we have source audio and converted audio, but no txt transcription 
        ## we wont detect that here
        hash = get_file_hash(file)
        log.info("Processing {} {}".format(file, hash))
        if hash in ledger:
            transcribed_files.append("{}.wav.txt".format(file))
            log.info("Skipping previously transcribed file: {}".format(file))
            continue

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

    selected_file = streamlit.selectbox("Selected file", transcribed_files)
    
    if selected_file is not None:
        with open(selected_file, mode='r', encoding='ascii', errors='replace') as f:
            transcription_contents = f.read()
    
    streamlit.text_area("Transcription text", transcription_contents)