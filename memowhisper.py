import subprocess
import pathlib
import argparse
import logging as log
import ffmpeg
import hashlib
import sys

log.basicConfig(encoding='utf-8', level=log.INFO)

class MemoAudio(object):

    def __init__(self, file: pathlib.Path) -> None:
        if not file.is_file():
            raise FileNotFoundError

        if not self._is_supported_audio(file):
            raise FileNotFoundError("Unsupported file type".format(file))

        self.file = file

    def _is_supported_audio(self, file: pathlib.Path) -> bool:
        try:
            probe = ffmpeg.probe(file)
            audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
            return len(audio_streams) > 0
        except ffmpeg.Error:
            return False        

    def get_audio(self) -> pathlib.Path:
        file = self.file
        audio = str(file) + ".wav"
        try:
            (
                ffmpeg.input(file)
                .output(audio, acodec='pcm_s16le', ar='16000', ac=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return pathlib.Path(audio)
        except ffmpeg.Error as e:
            raise e('An error occurred while converting the file: {}'.format(e.stderr))
             
class AudioTranscript(object):
    
    def __init__(self, file: pathlib.Path, model: pathlib.Path="whisper.cpp/models/ggml-small.en-q5_0.bin") -> None:
        if not file.is_file():
            raise FileNotFoundError

        self.file = file
        self.model = model
        self.whisper = pathlib.Path("whisper.cpp/main") 
 
    def get_transcript(self) -> None:
        transcript = pathlib.Path(str(self.file) + ".txt")
        command = [
            self.whisper,
            "--print-colors",
            "--output-txt",
            "--output-file", str(self.file),
            "-m", self.model,
            "-f", self.file,
        ]
        subprocess.run(command, check=True, capture_output=False)
        return transcript

class TranscriptSummary(object):

    def __init__(self, file: pathlib.Path) -> None:
        # ./llama.cpp/main -t 8 -m ./llama.cpp/models/Wizard-Vicuna-13B-Uncensored.ggml.q5_0.bin --color -c 2048 --temp 0.7 --repeat_penalty 1.1 -n -1 -p "### Instruction: write a story about llamas ### Response:"
        self.llama = pathlib.Path("llama.cpp/main")
        self.model = pathlib.Path("llama.cpp/models/Wizard-Vicuna-13B-Uncensored.ggml.q5_0.bin")
        if pathlib.Path(file).exists():
            self.file = file
        else:
            raise FileExistsError

    def get_summary(self) -> pathlib.Path:
        file = self.file

        with open(file, mode='r', encoding='ascii', errors='replace') as f:
            chunksize = 1024
            first = True
            summary = ""
            total_summary = ""
            
            while True:
                # Avoid truncating words by reading in lines
                chunk = f.readlines(chunksize)
                
                # Flatten into a single string, remove newlines
                chunk = ''.join(chunk).replace('\n', '')

                log.debug("Processing chunk {}".format(chunk))
                if not chunk:
                    break
                                
                if first == True:
                    prompt = """
### Human: Here are my notes: '{}' \n 
### Assistant: Here is a concise summary of your notes as a markdown bulleted list: 
""".format(chunk)
                else:
                    prompt = """
### Human: This is my summary '{}' \n
### Human: Here are additional notes: {} \n
### Assistant: I have updated your original summary with new information from your additional notes, here it is as a concise markdown bulleted list: 
""".format(summary, chunk)
                
                log.debug(prompt)
                command = [
                        self.llama,
                        "-t", "8",
                        "-m", self.model,
                        "--color", 
                        "-c", "2048",
                        "--temp", "0.7",
                        "--repeat_penalty", "1.1",
                        "-n", "-1", 
                        "-p", prompt
                    ]
                val = subprocess.run(command, check=True, capture_output=True, text=False)  
                
                output = val.stdout.decode('ascii', errors='ignore').split("### Assistant")[-1].strip("\n") 
                
                #manual accumulate to debug
                total_summary += output
                
                #llm only accumulate
                summary = output
                first = False

            log.info("Accumulated summary {}".format(total_summary))

            log.info("Summary {}".format(summary))

class TranscriptLedger(object):

    def __init__(self, path: pathlib.Path):
        if path.is_file():
            raise FileExistsError("Source dir was a file instead of a path")

        name = ".transcribed"
        self.storage = path.joinpath(pathlib.Path(name))

        self.ledger = set()

        if pathlib.Path(self.storage).exists():
            with open(self.storage, mode = "r") as f:
                self.ledger = set(f.read().splitlines())
        
        self.ledger.add(name)

    def append(self, entry):
        self.ledger.add(entry)
        with open(self.storage, mode = "a") as f:
            f.write(entry + '\n')
        
    def __contains__(self, entry):
        return (entry in self.ledger)

def get_file_hash(filepath):
    # Initialize the hash object with SHA-256 algorithm
    hasher = hashlib.sha256()

    # Open the file in binary mode
    with open(filepath, 'rb') as file:
        # Read the file in chunks to handle large files efficiently
        chunk_size = 4096
        for chunk in iter(lambda: file.read(chunk_size), b''):
            # Update the hash object with the current chunk
            hasher.update(chunk)

    # Get the final hash value as a hexadecimal string
    hash = hasher.hexdigest()
    return hash

APPLE_VOICE_MEMO_PATH = "/Library/Application Support/com.apple.voicememos/Recordings/"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    prog='memowhisper',
                    description='transcribe and summarize voice memos',
                    epilog='its magic!')

    parser.add_argument("--path", required=False)
    parser.add_argument("--summarize", action='store_true', required=False)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        source_dir = pathlib.Path(str(pathlib.Path.home()) + APPLE_VOICE_MEMO_PATH)
    else:
        source_dir = pathlib.Path(args.path)

    log.info("Target path set to: {}".format(str(source_dir)))

    ledger = TranscriptLedger(source_dir)

    for file in pathlib.Path(source_dir).glob('*'):

        #check if sha is in the ledger, this handles all cases of original audio or processed wav
        ## one edge case can be we have source audio and converted audio, but no txt transcription 
        ## we wont detect that here
        hash = get_file_hash(file)
        log.info("Processing {} {}".format(file, hash))
        if hash in ledger:
            log.info("Skipping previously transcribed file: {}".format(file))
            continue

        try:
            log.info("Converting to wav: {}".format(file))
            audio = MemoAudio(file).get_audio()
        except FileNotFoundError:
            log.info("Skipping non audio file {}".format(file))
            continue

        log.info("Transcribing: {}".format(file))
        transcript = AudioTranscript(audio).get_transcript()

        if args.summarize:
            log.info("Summarizing: {}".format(transcript))
            summary = TranscriptSummary(transcript).get_summary()

        #store hashes in ledger only if we succeeded
        audiohash = get_file_hash(audio)
        log.info("Adding {} {} to ledger as: {} {}".format(file, audio, hash, audiohash))
        ledger.append(hash)
        ledger.append(audiohash)
