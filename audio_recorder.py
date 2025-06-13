import wave
import os

class AudioRecorder:
    def __init__(self, output_path="session_audio.wav"):
        self.output_path = output_path
        self.wav_file = None

    def start(self):
        self.wav_file = wave.open(self.output_path, 'wb')
        self.wav_file.setnchannels(1)
        self.wav_file.setsampwidth(2)  # 16-bit
        self.wav_file.setframerate(48000)

    def write(self, pcm_data):
        if self.wav_file:
            self.wav_file.writeframes(pcm_data)

    def stop(self):
        if self.wav_file:
            self.wav_file.close()