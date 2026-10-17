@echo off
rem marker Windows-native launcher (llamacpp backend, no docker)
rem Self-naming: this same body is copied as marker.cmd / marker_single.cmd /
rem marker_gui.cmd / marker_server.cmd - each forwards to the matching uv-tool exe.
set "LLAMA_CPP_BINARY=C:\Users\Alex\AppData\Local\llama-cpp\llama-server.exe"
set "SURYA_INFERENCE_BACKEND=llamacpp"
set "PYTHONUTF8=1"
rem 4GB VRAM guard - uncomment if llama-server OOMs during model load / inference:
rem set "SURYA_INFERENCE_PARALLEL=2"
rem set "SURYA_INFERENCE_CTX_SIZE=24576"
"%USERPROFILE%\.local\bin\%~n0.exe" %*
