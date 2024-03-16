import os,requests,vertexai,functions_framework
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models
from google.cloud import storage
import urllib,json
import urllib.parse
import google.auth.transport.requests
import google.oauth2.id_token

TEXT_TO_SPEECH_CONVERTER_FUNCTION_URL=os.getenv("TEXT_TO_SPEECH_CONVERTER_FUNCTION_URL")
client = storage.Client()
bucket = client.get_bucket(os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET_NAME"))

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

  

    return data


def read_file_from_gcs(blob_name):
    # Create a client
   

    # Get the blob
    blob = bucket.blob(blob_name)

    # Download the blob to a string
    data = blob.download_as_text()

    return data


def summarize_data(data):
  vertexai.init(location=os.getenv("VERTEX_AI_LOCATION"))
  model = GenerativeModel("gemini-1.0-pro-001")
  responses = model.generate_content(
    f"""\"Given a transcript of a YouTube video, generate a concise summary that captures the main points and essential details. If the transcript is short, condense it to a few key sentences. If the transcript is long, reduce it to a few paragraphs, ensuring that the summary does not lose significant information or meaning from the original content.\"
  remove any stars in output
  input:
  {data}
  summarize:
""",
    generation_config={
        "max_output_tokens": 2048,
        "temperature": 0.9,
        "top_p": 1
    },
    safety_settings={
          generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
          generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
          generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
          generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    stream=True,
  )
  summarized_text=[]
  for response in responses:
    summarized_text.append(response.text)
  return " ".join(summarized_text)

@functions_framework.http
def summarize_transcript(request):
        transcript_location=request.args.get("transcript_location")
        transcript_data=read_file_from_gcs(transcript_location)
        print("transcript",transcript_data)
        text=summarize_data(transcript_data)
        print("summarised",text)
        response=make_authorized_get_request(TEXT_TO_SPEECH_CONVERTER_FUNCTION_URL,TEXT_TO_SPEECH_CONVERTER_FUNCTION_URL,params={"text":text})
        return response
    