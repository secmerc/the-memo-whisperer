import subprocess
import pathlib
import argparse
import logging as log
import ffmpeg
import hashlib


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
            raise e(f'An error occurred while converting the file: {e.stderr}')
        
        
class AudioTranscript(object):
    
    def __init__(self, file: pathlib.Path, model: pathlib.Path="whisper.cpp/models/ggml-small.en.bin") -> None:
        if not file.is_file():
            raise FileNotFoundError

        self.file = file
        self.model = model
        self.whisper = pathlib.Path("./whisper.cpp/main") 
 
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
        self.llama = pathlib.Path("./llama.cpp/main")
        self.model = pathlib.Path("./llama.cpp/models/Wizard-Vicuna-13B-Uncensored.ggml.q5_0.bin")
        if pathlib.Path(file).exists():
            self.file = file
        else:
            raise FileExistsError

    def get_summary(self) -> pathlib.Path:
        file = self.file
        
        with open(file, mode = "r") as f:
            chunksize = 2048
            first = True
            summary = ""
            
            while True:
                chunk = f.read(chunksize).strip("\n")
                log.info("Processing chunk {}".format(chunk))

                if not chunk:
                    break
                
                # break into peices
                # ask for summary
                # if >1 piece, feed first summary back in + next chunk, ask to update summary with any new info
                
                if first == True:
                    log.info("First prompt")
                    prompt = "### Instruction: Concisely summarize the single quoted text '{}' ### Response: ".format(chunk)
                else:
                    log.info("Second prompt")
                    prompt = "### Instruction: Update this single quoted summary '{}' with any new information from single quoted text '{}'".format(summary, chunk)
                
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
                print(val.stdout)
                summary += val.stdout.decode('ascii', errors='ignore').split("### Response")[-1].strip("\n")
                first = False

class TranscriptLedger(object):

    def __init__(self, path: pathlib.Path):
        if path.is_file():
            raise FileExistsError("Source dir was a file instead of a path")

        name = ".transcribed"
        self.storage = path.joinpath(pathlib.Path(name))
        #self.storage = path.cwd().joinpath(name)

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


APPLE_VOICE_MEMO_PATH = "~/Library/Application Support/com.apple.voicememos/Recordings/"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')

    parser.add_argument('filename')
    args = parser.parse_args()

    if not args.filename:
        source_dir = pathlib.Path(APPLE_VOICE_MEMO_PATH)
    else:
        source_dir = pathlib.Path(args.filename)

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


        # TODO: finish implementing summarization
        """
        transcript = file
        log.info("Summarizing: {}".format(transcript))
        summary = TranscriptSummary(transcript).get_summary()
        """

        #store hashes in ledger only if we succeeded
        audiohash = get_file_hash(audio)
        log.info("Adding {} {} to ledger as: {} {}".format(file, audio, hash, audiohash))
        ledger.append(hash)
        ledger.append(audiohash)
        