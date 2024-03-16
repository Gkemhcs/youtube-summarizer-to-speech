import functions_framework
from youtube_transcript_api import YouTubeTranscriptApi
from google.cloud import storage
import urllib,json
import urllib.parse
import google.auth.transport.requests
import google.oauth2.id_token
import os,uuid
import requests 
TRANSCRIPT_SUMMARIZER_FUNCTION_URL=os.getenv("TRANSCRIPT_SUMMARIZER_FUNCTION_URL")
storage_client = storage.Client()
bucket=storage_client.bucket(os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET_NAME"))

def upload_blob(source_file_name, destination_blob_name):
   
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def make_authorized_get_request(endpoint, audience, params):
    # Add the parameters to the endpoint URL
    url = endpoint + '?' + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)

    req.add_header("Authorization", f"Bearer {id_token}")
    response = urllib.request.urlopen(req)

    # Parse the JSON response
    data = json.loads(response.read())

    # Extract the 'audio_url' value
    audio_url = data.get('audio_url')

    return audio_url

    
@functions_framework.http
def load_transcript(request):
     video_url=request.args.get("videoUrl")
     video_id = video_url.split('watch?v=')[-1]
     print(video_id)
     print(os.getenv("TRANSCRIPT_SUMMARIZER_FUNCTION_URL"))
     transcript = YouTubeTranscriptApi.get_transcript(video_id)
     text=[]
     
     for entry in transcript:
        text.append(entry['text'])
     uuid_gen=uuid.uuid4()
     filename=f"transcript-{uuid_gen}.txt"
     with open(filename,"w") as f:
        f.write(str(" ".join(text)))
     upload_blob(filename,f'transcripts/{filename}')
     
     audio_url=make_authorized_get_request(TRANSCRIPT_SUMMARIZER_FUNCTION_URL,TRANSCRIPT_SUMMARIZER_FUNCTION_URL,params={"transcript_location":f'transcripts/{filename}'})
     return  {"audio_url":audio_url}
     