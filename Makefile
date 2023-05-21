WHISPERBIN = whisper.cpp/main
SMALLQUANTIZEDMODEL = whisper.cpp/models/ggml-small.en.bin whisper.cpp/models/ggml-small.en-q5_0


transcription: $(WHISPERBIN) $(SMALLQUANTIZEDMODEL) 
	cd whisper.cpp && bash models/download-ggml-model.sh small.en
	cd whisper.cpp && make quantize && quantize models/ggml-small.en.bin models/ggml-small.en-q5_0.bin q5_0
	cd whisper.cpp && make 

clean:
	cd whisper.cpp && make clean
	rm $(SMALLQUANTIZEDMODEL)
