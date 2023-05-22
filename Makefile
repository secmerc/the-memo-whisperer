WHISPERPATH := whisper.cpp
LLAMAPATH := llama.cpp

MODELSIZE := small
LANG := en

WHISPERBIN := $(WHISPERPATH)/main
MODEL := $(WHISPERPATH)/models/ggml-$(MODELSIZE).$(LANG).bin
QUANTIZEDMODEL := $(WHISPERPATH)/models/ggml-$(MODELSIZE).$(LANG)-q5_0.bin
FFMPEG := ffmpeg
VENV := ./venv

transcript: $(WHISPERPATH)/Makefile $(LLAMAPATH)/Makefile $(VENV) $(FFMPEG) $(WHISPERBIN) $(MODEL) $(QUANTIZEDMODEL)

$(VENV):
	python3 -m venv ./venv

$(FFMPEG):
	source ./venv/bin/activate && pip3 install ffmpeg-python
	touch ffmpeg

$(WHISPERPATH)/Makefile $(LLAMAPATH)/Makefile:
	git submodule init
	git submodule update

$(WHISPERBIN):
	@echo "[+] Getting whisper.cpp ready for transcription"
	@echo "[+] Building $(WHISPERBIN)"
	cd $(WHISPERPATH) && make 

$(MODEL):
	@echo "[+] Building $(MODEL)"
	cd $(WHISPERPATH) && bash models/download-ggml-model.sh $(MODELSIZE).en

$(QUANTIZEDMODEL):
	@echo "[+] Building $(QUANTIZEDMODEL)"
	cd $(WHISPERPATH) && make quantize && ./quantize models/ggml-$(MODELSIZE).$(LANG).bin models/ggml-$(MODELSIZE).$(LANG)-q5_0.bin q5_0

clean: clean_python clean_whisper

clean_whisper:
	@echo "[+] Removing $(QUANTIZEDMODEL) $(MODEL)"
	cd $(WHISPERPATH) && make clean
	rm $(QUANTIZEDMODEL) $(MODEL)

clean_python:
	source ./venv/bin/activate && pip3 uninstall ffmpeg-python
	rm -fr $(VENV) $(FFMPEG)
