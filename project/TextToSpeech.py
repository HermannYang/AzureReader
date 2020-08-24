import os, requests, time

from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from xml.etree import ElementTree

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static") # 挂载静态文件，指定目录
templates = Jinja2Templates(directory="templates") # 模板目录

class Item(BaseModel):
    name: str

@app.get("/")
async def read_data(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/convert')
def calculate(request_data: Item):
    strtext = request_data.name
    Textapp = TextToSpeech('09537ae298bc40e3a354273078a6e95e',strtext)
    Textapp.get_token()
    res = Textapp.save_audio()
    return res


class TextToSpeech(object):
    def __init__(self, subscription_key,strtext):
        self.subscription_key = subscription_key
        self.tts = strtext
        self.timestr = time.strftime("%Y%m%d-%H%M")
        self.access_token = None

    def get_token(self):
        fetch_token_url = "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        response = requests.post(fetch_token_url, headers=headers)
        self.access_token = str(response.text)

    def save_audio(self):
        base_url = 'https://eastus.tts.speech.microsoft.com/'
        path = 'cognitiveservices/v1'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
            'User-Agent': 'SpeechBot'
        }
        xml_body = ElementTree.Element('speak', version='1.0')
        xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'zh-cn')
        voice = ElementTree.SubElement(xml_body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'zh-CN')
        voice.set('name', 'zh-CN-YunyeNeural')
        voice.text = self.tts
        body = ElementTree.tostring(xml_body)

        response = requests.post(constructed_url, headers=headers, data=body)
        #保存文件 save file as audio
        if response.status_code == 200:
            path = os.path.abspath('.');
            filename = './static/' + 'sample-' + self.timestr + '.wav'
            with open(filename, 'wb') as audio:
                audio.write(response.content)
                return {"code": response.status_code,"file" : filename}
        else:
            return {"code": response.status_code,"reason" : str(response.reason) }

    def get_voices_list(self):
        base_url = 'https://eastus.tts.speech.microsoft.com/'
        path = 'cognitiveservices/voices/list'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
        }
        response = requests.get(constructed_url, headers=headers)
        if response.status_code == 200:
            print("\nAvailable voices: \n" + response.text)
        else:
            print("\nStatus code: " + str(response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app,
                host="127.0.0.1",
                port=8080,
                workers=1)