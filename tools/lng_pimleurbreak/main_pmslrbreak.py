"""
prompt chatGPT
-------------------------------------------------
... programma in modo che riconosca sia l'Inglese sia il Tedesco, 
e salvi ogni frase completa in un file. 
Il nome file deve terminare con il numero della frase

answer:
-------------------------------------------------

"""

import os
import wave
import json
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
from tqdm import tqdm




def extract_and_save_phrases(model_native, model_foreign, 
                             input_mp3_path, output_dir):

    # Convert mp3 to wav
    audio = AudioSegment.from_mp3(input_mp3_path)
    wav_path = "./delete.wav"
    
    audio.export(wav_path, format="wav")
    print("esportato in .wav")

    # Open the wav file
    nr_canali = 1
    with wave.open(wav_path, "rb") as wf:
        nr_canali = wf.getnchannels()
    if nr_canali > 1:        
        print(f"ha più di un canale, ne ha: {nr_canali}")
        audio = audio.set_channels(1)
        print("esporto di nuovo dopo aver selezionato il canale 1")
        audio.export(wav_path, format="wav")

    rec_native = KaldiRecognizer(model_native,  wf.getframerate())
    rec_foreign = KaldiRecognizer(model_foreign, wf.getframerate())
    rec_native.SetWords(True)
    rec_foreign.SetWords(True)

    total_frames = wf.getnframes()
    chunk_size = 4000*5

    phrase_counter = 0

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    lingua_non_riconosciuta = 0
    iterazioni = 0
    lng_suffix = "undef"
    with wave.open(wav_path, "rb") as wf:
        # Initialize tqdm progress bar
        with tqdm(total=total_frames, unit='frames', desc='Processing Audio') as pbar:
            while True:
                iterazioni += 1
                data = wf.readframes(chunk_size)
                if len(data) == 0:
                    break
                
                # Try recognizing with the English model
                if rec_native.AcceptWaveform(data):
                    result = json.loads(rec_native.Result())
                    lng_suffix = "native"
                # If English model doesn't recognize, try the German model
                elif rec_foreign.AcceptWaveform(data):
                    result = json.loads(rec_foreign.Result())
                    lng_suffix = "foreign"
                else:
                    # If neither model recognizes, continue
                    lingua_non_riconosciuta += 1
                    continue

                if 'result' in result:
                    phrase_counter += 1
                    phrase_start = int(result['result'][0]['start'] * 1000)  # in milliseconds
                    phrase_end = int(result['result'][-1]['end'] * 1000)  # in milliseconds
                    phrase_audio = audio[phrase_start:phrase_end]

                    # Save each phrase to a separate file
                    phrase_output_path = os.path.join(output_dir, f"phrase_{phrase_counter}_{lng_suffix}.mp3")
                    phrase_audio.export(phrase_output_path, format="mp3")

                # Update progress bar
                pbar.update(chunk_size)

    # Clean up temporary files
    os.remove(wav_path)
    print(f"non riconosciute {lingua_non_riconosciuta/iterazioni*100}%")


input_mp3 = "D:\\large\\lng-video\\\out-audio\\pmslr-de-006.mp3"
output_mp3_extract_voice = "./extract_voice.mp3"
output_mp3_lower_non_voice = "./lower_non_voice.mp3"

model_path_en = "D:\\data_ENRICO\\08_dev\\08-dev-pers\\vosk_models\\vosk-model-en-us-0.22"
model_path_de = "D:\\data_ENRICO\\08_dev\\08-dev-pers\\vosk_models\\vosk-model-de-0.21"

wav_path = "d:\\large\\lng-video\\out-audio\\Bleach-001720pDualAnime_Gallery.wav"


if __name__ == "__main__":

    # Load the Vosk models
    model_en = Model(model_path_en)
    model_de = Model(model_path_de)

    extract_and_save_phrases(model_native = model_en, model_foreign = model_de, 
                             input_mp3_path = input_mp3, output_dir = "D:\\large\\lng-video\\\out-audio")


