from pydub import AudioSegment
import assemblyai as aai
import noisereduce as nr
import numpy as np
from scipy.io import wavfile
import os


class AudioProcessor:
    def __init__(self, audio_file, api_key):
        self.audio_file = audio_file
        self.api_key = api_key

        # Get the directory of the input audio file
        self.audio_dir = os.path.dirname(audio_file)

        # Define paths for intermediate and processed files
        self.temp_file = os.path.join(self.audio_dir, "temp.wav")
        self.reduced_file = os.path.join(self.audio_dir, "reduced_noise.wav")
        self.enhanced_file = os.path.join(self.audio_dir, "enhanced_audio.wav")

    def process_audio(self):
        # Convert the input audio file to WAV format
        audio = AudioSegment.from_file(self.audio_file)
        audio.export(self.temp_file, format="wav")

        # Read the WAV file and apply noise reduction
        rate, data = wavfile.read(self.temp_file)
        reduced_noise = nr.reduce_noise(y=data, sr=rate)

        # Save the noise-reduced audio
        wavfile.write(self.reduced_file, rate, reduced_noise)

        # Increase the volume of the noise-reduced audio
        cleaned_audio = AudioSegment.from_file(self.reduced_file)
        louder_audio = cleaned_audio + 30  # Increase volume by 30dB
        louder_audio.export(self.enhanced_file, format="wav")

        print(f"Processed audio saved at: {self.enhanced_file}")

    def transcribe_audio(self):
        # Set AssemblyAI API key
        aai.settings.api_key = self.api_key
        transcriber = aai.Transcriber()

        # Transcribe the enhanced audio
        transcript = transcriber.transcribe(self.enhanced_file)
        return transcript.text


# if __name__ == "__main__":
#     # Input audio file path (can be relative or absolute)
#     input_audio_file = "/home/jzian/ws/RM/test.wav"  # Replace with your audio file path
#     api_key = "aed2e39f5b324388b68db696db3c9ad3"

#     processor = AudioProcessor(audio_file=input_audio_file, api_key=api_key)
#     processor.process_audio()

#     # Transcribe the audio and print the transcript
#     transcript_text = processor.transcribe_audio()
#     print(transcript_text)
