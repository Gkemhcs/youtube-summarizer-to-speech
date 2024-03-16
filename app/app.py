from flask import Flask,send_file,render_template,request,redirect,url_for
import qrcode,time,os,threading,uuid,json,requests
import urllib,json
import urllib.parse
import google.auth.transport.requests
import google.oauth2.id_token
CONVERTER_FUNCTION_URL=os.getenv("CONVERTER_URL")
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

app=Flask(__name__)
def delete_qrcode(filename):
  
    # Sleep for 2 minutes
    time.sleep(120)

    # Delete the QR code
    if os.path.exists(filename):
        os.remove(filename)
        print("file removed")
@app.route("/")
def home():
       return render_template("home.html")
@app.route("/convert",methods=["POST"])
def convert():
      params={"videoUrl":request.form.get("videoUrl")}
      response=make_authorized_get_request(CONVERTER_FUNCTION_URL,CONVERTER_FUNCTION_URL, params)
      return  redirect(url_for("generate_qrcode",link=response))
       


@app.route("/qrcode")
def generate_qrcode():
      img = qrcode.make(request.args.get("link"))

    # Save the image
      qr_code_uuid = uuid.uuid4()
      filename = f'static/qrcode-{qr_code_uuid}.png'
      img.save(filename)
      threading.Thread(target=delete_qrcode, args=(filename,)).start()
      return render_template('qrcode.html', qr_code_image=filename, audio_url=request.args.get("link"))


if __name__ == '__main__':
    app.run(debug=True)
