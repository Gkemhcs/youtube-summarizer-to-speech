from google.cloud import storage
import functions_framework
import uuid ,os
import google.cloud.texttospeech as tts
storage_client = storage.Client()
bucket=storage_client.bucket(os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET_NAME"))
def upload_blob(source_file_name, destination_blob_name):
   
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
def text_to_wav(voice_name: str, text: str,upload_blob):
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )
    uuid_gen=uuid.uuid4()
    filename = f"yt-{uuid_gen}.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Generated speech saved to "{filename}"')
    upload_blob(filename,f"audio/{filename}") 
    return filename   
@functions_framework.http
def convert_to_speech(request):
     print("request received")
     
     text=request.args.get("text")
    
     filename=text_to_wav("en-AU-Neural2-A", text,upload_blob)

     gcs_audio_file_url=f"https://storage.cloud.google.com/{os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET_NAME')}/audio/{filename}"
     return {"audio_url":gcs_audio_file_url}
    
