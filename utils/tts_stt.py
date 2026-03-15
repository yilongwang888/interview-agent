from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus
import os
import base64
import urllib
import requests
import json
import pyaudio,wave
import numpy as np
import time

#语言录制
class AudioRecord:
    def __init__(self,out_path,stop_time=1.3):
        self.temp = 20
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 2
        self.WAVE_OUTPUT_FILENAME = out_path
        self.mindb = 2000  # 最小声音，大于则开始录音，否则结束
        self.delayTime = stop_time  # 小声1.3秒后自动终止
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)

    def record(self):
        print("开始!计时")

        frames = []
        flag = False  # 开始录音节点
        stat = True  # 判断是否继续录音
        stat2 = False  # 判断声音小了

        tempnum = 0  # tempnum、tempnum2、tempnum3为时间
        tempnum2 = 0

        while stat:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            audio_data = np.frombuffer(data, dtype=np.short)
            temp = np.max(audio_data)
            if temp > self.mindb and flag == False:
                flag = True
                print("开始录音")
                tempnum2 = tempnum

            if flag:

                if (temp < self.mindb and stat2 == False):
                    stat2 = True
                    tempnum2 = tempnum
                    print("声音小，且之前是是大的或刚开始，记录当前点")
                if (temp > self.mindb):
                    stat2 = False
                    tempnum2 = tempnum
                    # 刷新

                if (tempnum > tempnum2 + self.delayTime * 15 and stat2 == True):
                    print("间隔%.2lfs后开始检测是否还是小声" % self.delayTime)
                    if (stat2 and temp < self.mindb):
                        stat = False
                        # 还是小声，则stat=True
                        print("小声！")
                    else:
                        stat2 = False
                        print("大声！")

            print(str(temp) + "      " + str(tempnum))
            tempnum = tempnum + 1
            if tempnum > 150:  # 超时直接退出
                stat = False
        print("录音结束")

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()


#语音转文字
class Text:
    def __init__(self):
        self.API_KEY = '9oghXkpEeYvRkm2Bi3pB0PMY'
        self.SECRET_KEY = 'sjekOtzRMCGTjcaQevbN2cSznw5Hk3xS'
        self.TOKEN_URL = 'http://aip.baidubce.com/oauth/2.0/token'
    
    def fetch_token(self):
        params = {'grant_type': 'client_credentials',
                'client_id': self.API_KEY,
                'client_secret': self.SECRET_KEY}
        post_data = urlencode(params)
        post_data = post_data.encode( 'utf-8')
        req = Request(self.TOKEN_URL, post_data)
        try:
            f = urlopen(req)
            result_str = f.read()
        except URLError as err:
            print('token http response http code : ' + str(err.code))
            result_str = err.read()
        result_str =  result_str.decode()

        result = json.loads(result_str)
        SCOPE=False
        if ('access_token' in result.keys() and 'scope' in result.keys()):
            if SCOPE and (not SCOPE in result['scope'].split(' ')): 
                raise DemoError('scope is not correct')
            return result['access_token']
        else:
            raise DemoError('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')

    def Identify(self):
        AudioRecord("hhh.wav",1).record()
        path="/home/ubuntu22/python_proj/"
        
        timer = time.perf_counter
        AUDIO_FILE = 'hhh.wav' 
        FORMAT = AUDIO_FILE[-3:]  
        CUID = '123456PYTHON'
        RATE = 16000
        DEV_PID = 1537  
        ASR_URL = 'http://vop.baidu.com/server_api'
        SCOPE = 'audio_voice_assistant_get' 

        token = self.fetch_token()

        speech_data = []
        
        with open(path+AUDIO_FILE, 'rb') as speech_file:
            speech_data = speech_file.read()

        length = len(speech_data)
        if length == 0:
            raise DemoError('file %s length read 0 bytes' % AUDIO_FILE)
        speech = base64.b64encode(speech_data)
        speech = str(speech, 'utf-8')
        params = {'dev_pid': DEV_PID,
                'format': FORMAT,
                'rate': RATE,
                'token': token,
                'cuid': CUID,
                'channel': 1,
                'speech': speech,
                'len': length
                }
        post_data = json.dumps(params, sort_keys=False)
        req = Request(ASR_URL, post_data.encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        try:
            begin = timer()
            f = urlopen(req)
            result_str = f.read()
            print ("Request time cost %f" % (timer() - begin))
        except URLError as err:
            print('asr http response http code : ' + str(err.code))
            result_str = err.read()
        try:
            result_str = str(result_str, 'utf-8')
            re=json.loads(result_str)
            text=re['result'][0]
        except:
            text='error!'
        return text







#文字转语音
class Voice:
    def __init__(self):
        self.API_KEY = '9oghXkpEeYvRkm2Bi3pB0PMY'
        self.SECRET_KEY = 'sjekOtzRMCGTjcaQevbN2cSznw5Hk3xS'
        self.TOKEN_URL = 'http://aip.baidubce.com/oauth/2.0/token'
        
    def fetch_token(self):
        params = {'grant_type': 'client_credentials',
                'client_id': self.API_KEY,
                'client_secret': self.SECRET_KEY}
        post_data = urlencode(params)
        post_data = post_data.encode( 'utf-8')
        req = Request(self.TOKEN_URL, post_data)
        try:
            f = urlopen(req)
            result_str = f.read()
        except URLError as err:
            print('token http response http code : ' + str(err.code))
            result_str = err.read()
        result_str =  result_str.decode()

        result = json.loads(result_str)
        SCOPE=False
        if ('access_token' in result.keys() and 'scope' in result.keys()):
            if SCOPE and (not SCOPE in result['scope'].split(' ')): 
                raise DemoError('scope is not correct')
            return result['access_token']
        else:
            raise DemoError('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')

    def Speech(self,text):
        TEXT = text
        PER = 4144
        SPD = 5
        PIT = 5
        VOL = 90
        AUE = 6
        FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
        FORMAT = FORMATS[AUE]
        CUID = "123456PYTHON"
        TTS_URL = 'http://tsn.baidu.com/text2audio'
        SCOPE = 'audio_tts_post' 
        token = self.fetch_token()
        tex = quote_plus(TEXT) 
        params = {'tok': token, 'tex': tex, 'per': PER, 'spd': SPD, 'pit': PIT, 'vol': VOL, 'aue': AUE, 'cuid': CUID,
                'lan': 'zh', 'ctp': 1}  

        data = urlencode(params)
        req = Request(TTS_URL, data.encode('utf-8'))
        has_error = False
        try:
            f = urlopen(req)
            result_str = f.read()
            headers = dict((name.lower(), value) for name, value in f.headers.items())
            has_error = ('content-type' not in headers.keys() or headers['content-type'].find('audio/') < 0)
        except  URLError as err:
            print('asr http response http code : ' + str(err.code))
            result_str = err.read()
            has_error = True
        path="/home/ubuntu22/python_proj/"
        save_file = "error.txt" if has_error else 'result.' + FORMAT
        with open(path+save_file, 'wb') as of:
            of.write(result_str)
        if has_error:
            result_str = str(result_str, 'utf-8')
            print("tts api  error:" + result_str)
        os.system("mplayer"+" "+path+"result.wav")