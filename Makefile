WHISPERPATH := whisper.cpp

WHISPERBIN := $(WHISPERPATH)/main
SMALLMODEL := $(WHISPERPATH)/models/ggml-small.en.bin
SMALLQUANTIZEDMODEL := $(WHISPERPATH)/models/ggml-small.en-q5_0.bin

transcript: $(WHISPERBIN) $(SMALLMODEL) $(SMALLQUANTIZEDMODEL) 

$(WHISPERBIN):
	cd $(WHISPERPATH) && make 

$(SMALLMODEL):
	cd $(WHISPERPATH) && bash models/download-ggml-model.sh small.en

$(SMALLQUANTIZEDMODEL):
	cd $(WHISPERPATH) && make quantize && ./quantize models/ggml-small.en.bin models/ggml-small.en-q5_0.bin q5_0

clean:
	cd $(WHISPERPATH) && make clean
	rm $(SMALLQUANTIZEDMODEL) $(SMALLMODEL)
