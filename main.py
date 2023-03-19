import os
import pvleopard as pvleopard
import pvporcupine
import pyaudio
import struct
import wave
import openai
import pyttsx3
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

openai_key = os.getenv('openai_key')
openai.api_key = openai_key

pvporcupine_key = os.getenv('pvporcupine_key')

porcupine = pvporcupine.create(
    access_key=pvporcupine_key,
    keywords=['jarvis']
)

leopard = pvleopard.create(access_key=pvporcupine_key)

engine = pyttsx3.init()
engine.say("Hello, I'm your personal assistant Jarvis. Say my name and ask me anything:")
engine.runAndWait()

# Initialize PyAudio
audio = pyaudio.PyAudio()
stream = audio.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length * 2,
)

def record_audio(filename, duration):
    frames = []

    for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * duration)):
        audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, audio_data)
        frames.append(audio_data)

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(porcupine.sample_rate)
        wf.writeframes(b''.join(frames))

# Main loop
print("Listening for keywords...")
try:
    while True:
        # Read audio data from the microphone
        audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        audio_frame = struct.unpack_from("h" * porcupine.frame_length, audio_data)

        # Process audio frame with Porcupine
        keyword_index = porcupine.process(audio_frame)

        if keyword_index == 0:
            print("Keyword detected! Recording speech...")

            # Record speech for a fixed duration
            duration_seconds = 5
            audio_file = "recorded_audio.wav"
            record_audio(audio_file, duration_seconds)

            # Transcribe the recorded speech using Leopard
            print("Transcribing speech...")
            transcript, words = leopard.process_file(os.path.abspath(audio_file))
            print("Transcript:", transcript)

            response = openai.ChatCompletion.create(

                model="gpt-3.5-turbo",
                messages=[{"role": "user",
                           "content": ("Formulate a very short reply for the question. Here is the question:"+transcript)}],

                temperature=0.6,
            )

            print(response.choices[0].message.content)

            pyttsx3.speak(response.choices[0].message.content)

            # Remove the audio file if you don't need it
            os.remove(audio_file)

finally:
    # Clean up resources
    stream.stop_stream()
    stream.close()
    audio.terminate()
    porcupine.delete()

