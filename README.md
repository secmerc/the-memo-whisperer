```
                    Wizardsh.it presents: The Memo Whisperer
                              '             .           .
                           o       '   o  .     '   . O
                        '   .   ' .   _____  '    .      .
                         .     .   .mMMMMMMMm.  '  o  '   .
                       '   .     .MMXXXXXXXXXMM.    .   ' 
                      .       . /XX77:::::::77XX\ .   .   .
                         o  .  ;X7:::''''''':::7X;   .  '
                        '    . |::'.:'        '::| .   .  .
                           .   ;:.:.            :;. o   .
                        '     . \'.:            /.    '   .
                           .     `.':.        .'.  '    .
                         '   . '  .`-._____.-'   .  . '  .
                          ' o   '  .   O   .   '  o    '
                           . ' .  ' . '  ' O   . '  '   '
                            . .   '    '  .  '   . '  '
                             . .'..' . ' ' . . '.  . '
                              `.':.'        ':'.'.'
                                `\\_  |     _//'
                                  \(  |\    )/
                                  //\ |_\  /\\
                                 (/ /\(" )/\ \)
                                  \/\ (  ) /\/
                                     |(  )|
                                     | \( \
                                     |  )  \
                                     |      \
                                     |       \
                                     |        `.__,
                                     \_________.-' its magic
```

# This is a pre-alpha work. Don't trip.

# Problem 
Voice memos trap your information in difficult to search audio files that often contain a lot of filler, and a few important gems. Another problem is that they may contain sensitive information you dont want to share with third parties.

# Goals
* private
* searchable
* summarized

# Design & Implementation
m1 macbook + python + ffmpeg + whisper.cpp + llama.cpp

1. Scan the target path for audio files `__main__`
1. Convert to pcm 16bit wav with ffmpeg and write it to target path `class MemoAudio(object)` `get_audio(file)`
1. Transcribe the wav file with whisper.cpp and write it to target path `class AudioTranscript(object)` `get_transcript(audio)`
1. **Optionally** Summarize the transcription with llama.cpp `class TranscriptSummary(object)` `get_summary(transcript)`
1. Write hashes of transcribed audio to a ledger stored in the target path `class TranscriptLedger(object):` `append(file)` `append(audio)`

Easily searchable text files with full transcriptions & summaries, all while retaining original audio!

# Installation
Install python dependencies in venv, build whisper.cpp, download and quantize small model. Everything you need to get started running on MacOS CPU.

`git clone --recurse-submodule https://github.com/secmerc/the-memo-whisperer.git && cd the-memo-whisperer && make`

# Usage
```
python3 memowhisper.py [--path] [--summarize]

#transcribe a path
python3 memowhisper.py --path /path/to/memos 

#transcribe apple voice memos
python3 memowhisper.py 

#transcribe and summarize apple voice memos
python3 memowhisper.py --summarize

#transcribe and summarize a path
python3 memowhisper.py --path /path/to/memos --summarize
```

The transcription ledger is kept in the target path

There is only one argument, the path to the files to be transcribed. If you omit the path, it will use default to apple voice memo path for the current user: `~/Library/Application Support/com.apple.voicememos/Recordings/`

Run it with no arguments, or plug your voice recorder in via USB and run the tool on the volume!