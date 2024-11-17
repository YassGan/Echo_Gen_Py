import tkinter as tk
import pyaudio
import wave
import threading
import speech_recognition as sr
import google.generativeai as genai
import os

# Parameters for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILENAME = "output.wav"

# Initialize variables for recording
audio = pyaudio.PyAudio()
stream = None
frames = []
recording = False



from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Get the API key from the .env file
Gemini_flash_api_key = os.getenv("GEMINI_FLASH_API_KEY")

# Check if the API key is loaded correctly
if not Gemini_flash_api_key:
    raise ValueError("API key not found. Please set GEMINI_FLASH_API_KEY in the .env file.")

# Configure the Gemini API
genai.configure(api_key=Gemini_flash_api_key)
client_responses_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Start recording function
def start_recording():
    global stream, frames, recording
    if not recording:
        recording = True
        frames = []
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        record_button.config(state=tk.DISABLED, bg="#cccccc")
        threading.Thread(target=record_audio).start()

# Stop recording function
def stop_recording():
    global stream, recording
    if recording:
        recording = False
        stream.stop_stream()
        stream.close()
        save_audio()
        record_button.config(state=tk.NORMAL, bg="green")

# Record audio in a separate thread
def record_audio():
    global recording, frames
    while recording:
        data = stream.read(CHUNK)
        frames.append(data)

# Save the recorded audio to a file
def save_audio():
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    print(f"Audio file saved as {OUTPUT_FILENAME}")
    transcribe_and_generate_response()

# Transcribe audio to text and generate AI response
def transcribe_and_generate_response():
    # Create the loading window
    loading_window = tk.Toplevel(root)
    loading_window.title("Processing...")
    loading_window.geometry("300x100")
    loading_label = tk.Label(loading_window, text="Processing your request...\nPlease wait.", font=("Arial", 14))
    loading_label.pack(expand=True)

    # Disable the main window until the process is done
    root.attributes('-disabled', True)
    
    # Run transcription and AI response generation in a separate thread
    threading.Thread(target=process_audio, args=(loading_window,)).start()

def process_audio(loading_window):
    audio_file = OUTPUT_FILENAME
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_file) as source:
            print("Listening...")
            audio_data = recognizer.record(source)

            print("Recognizing...")
            text = recognizer.recognize_google(audio_data)
            transcription_text.delete(1.0, tk.END)
            transcription_text.insert(tk.END, text)

            print("Generating AI response...")
            response_from_gemini = client_responses_model.generate_content(text)
            ai_response = response_from_gemini.text
            ai_response_text.delete(1.0, tk.END)
            ai_response_text.insert(tk.END, ai_response)

    except sr.UnknownValueError:
        transcription_text.delete(1.0, tk.END)
        transcription_text.insert(tk.END, "Could not understand the audio.")
    except sr.RequestError as e:
        transcription_text.delete(1.0, tk.END)
        transcription_text.insert(tk.END, "Request error. Please try again later.")
    finally:
        # Close the loading window and re-enable the main window
        loading_window.destroy()
        root.attributes('-disabled', False)

# Create GUI
root = tk.Tk()
root.title("Audio Recorder and AI Response")

window_width, window_height = 500, 650
screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
x_coordinate = (screen_width // 2) - (window_width // 2)
y_coordinate = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

# Frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

record_button = tk.Button(button_frame, text="Record", font=("Arial", 16), bg="green", fg="white", command=start_recording, width=15)
record_button.pack(side=tk.LEFT, padx=10)

stop_button = tk.Button(button_frame, text="Stop", font=("Arial", 16), bg="red", fg="white", command=stop_recording, width=15)
stop_button.pack(side=tk.LEFT, padx=10)

# Transcription display
transcription_label = tk.Label(root, text="Transcription:", font=("Arial", 14))
transcription_label.pack(pady=5)

transcription_text = tk.Text(root, height=4, width=50, font=("Arial", 12), wrap=tk.WORD, bg="#f0f0f0")
transcription_text.pack(pady=10)

# AI Response display
ai_response_label = tk.Label(root, text="AI Response:", font=("Arial", 14))
ai_response_label.pack(pady=5)

ai_response_text = tk.Text(root, height=4, width=50, font=("Arial", 12), wrap=tk.WORD, bg="#f0f0f0")
ai_response_text.pack(pady=10)

root.mainloop()
audio.terminate()
