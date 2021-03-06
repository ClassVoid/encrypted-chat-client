import requests as requests
from PyQt5.QtCore import QObject, pyqtSignal
import subprocess
import threading
import platform

from client_utils import *


class LoginWorker(QObject):
    finished = pyqtSignal(requests.Response, str)

    def __init__(self, username: str, password: str):
        super(QObject, self).__init__()
        self.username=username
        self.password=password

    def run(self):
        res = requests.Response()
        try:
            res:requests.Response = getUserData(self.username)
        except requests.exceptions.ConnectionError:
            res.status_code = 503
        finally:
            self.finished.emit(res, self.password)


class SignUpWorker(QObject):
    finished = pyqtSignal(requests.Response)

    def __init__(self, username: str, password: str):
        super(QObject, self).__init__()
        self.username=username
        self.password=password

    def run(self):
        res = requests.Response()
        try :
            res = createAccount(self.username, self.password)
        except requests.exceptions.ConnectionError:
            res.status_code=503
        finally:
            self.finished.emit(res)


class NewChatWorker(QObject):
    finished = pyqtSignal(requests.Response, str)

    def __init__(self, credentials: Dict[str, str], chat_name: str):
        super(QObject, self).__init__()
        self.credentials=credentials
        self.chat_name=chat_name

    def run(self):
        res = createChat(self.credentials, self.chat_name)
        self.finished.emit(res, self.chat_name)


class MessagesWorker(QObject):
    finished = pyqtSignal(requests.Response)

    def __init__(self, chat_name:str, date_time: str):
        super(QObject, self).__init__()
        self.chat_name=chat_name
        self.date_time=date_time

    def run(self):
        res = getMessages(self.chat_name, self.date_time)
        self.finished.emit(res)


class StreamSenderWorker(QObject):
    finished = pyqtSignal()
    error_signal=pyqtSignal(str)

    def __init__(self, stream_address):
        super(QObject, self).__init__()
        self.stream_address=stream_address

    def run(self):
        #stream_address = "rtmp://localhost:1935/show/test"
        '''
        ffmpeg -f v4l2 -i /dev/video0 -f alsa -i hw:0 -vcodec libx264 -b:v 300k -threads 2 -tune zerolatency -fflags low_delay -fflags nobuffer -g 8 -f flv rtmp://127.0.0.1:1935/show/test
        '''
        windows_stream_cmd=f"ffmpeg -f dshow -i video='Integrated Webcam':audio='Microphone (Realtek Audio)' -profile:v high -pix_fmt yuvj420p -level:v 4.1 -preset ultrafast -tune zerolatency -vcodec libx264 -r 10 -b:v 512k -s 640x360 -acodec aac -ac 2 -ab 32k -ar 44100 -f flv {self.stream_address}"

        stream_cmd=f"ffmpeg -f v4l2 -i /dev/video0 -f alsa -i hw:0 -vcodec libx264 -b:v 300k -threads 2 -tune zerolatency -fflags low_delay -fflags nobuffer -g 8 -f flv {self.stream_address}"
        # view_camera_cmd = "ffplay -i /dev/video0 -fflags nobuffer".rstrip().lstrip().split()

        self.proc = subprocess.Popen(f"exec {stream_cmd}", shell=True, stdout=subprocess.PIPE)
        self.proc.wait()
        if self.proc.returncode==1:
            self.error_signal.emit("Server connection refused")

    def stop(self):
        self.proc.terminate()
        self.finished.emit()


class StreamConsumerWorker(QObject):
    finished= pyqtSignal()

    def __init__(self, stream_address):
        super(QObject, self).__init__()
        self.stream_address=stream_address

    def run(self):
        #stream_address = "rtmp://127.0.0.1/show/test"
        cmd = f"ffplay -fflags nobuffer {self.stream_address}"#.rstrip().lstrip().split()

        if platform.system()=="Windows":
            self.proc=subprocess.Popen(f"{cmd}", shell=True, stdout=subprocess.PIPE)
        else:
            self.proc=subprocess.Popen(f"exec {cmd}", shell=True, stdout=subprocess.PIPE)


        self.proc.wait()
        self.finished.emit()


    def stop(self):
        if platform.system()!="Windows":
            self.proc.terminate()
        else:
            subprocess.Popen(f"taskkill /F /T /PID {self.proc.pid}")
