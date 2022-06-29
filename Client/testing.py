import subprocess

'''
stream_address="rtmp://192.168.100.21:1935/show/u2"
cmd = f"ffplay -fflags nobuffer {stream_address}"

proc =subprocess.Popen(f"{cmd}", shell=True, stdout=subprocess.PIPE)

proc.wait()
'''
import platform
print(platform.system())


'''

ffmpeg -f dshow -i video="OBS Virtual Camera":audio="Microphone (Realtek High Definition Audio)" -profile:v high -pix_fmt yuvj420p -level:v 4.1 -preset ultrafast -tune zerolatency -vcodec libx264 -r 10 -b:v 512k -s 640x360 -acodec aac -ac 2 -ab 32k -ar 44100 -f flv rtmp://192.168.100.21:1935/show/u1


ffmpeg -f v4l2 -i /dev/video0 -f alsa -i hw:0 -vcodec libx264 -b:v 300k -threads 2 -tune zerolatency -fflags low_delay -fflags nobuffer -g 8 -f flv
ffmpeg -f dshow -i video="OBS Virtual Camera":audio="Microphone (Realtek High Definition Audio)" -profile:v high -level:v 4.1 -preset ultrafast -tune zerolatency -fflags nobuffer -threads 2 -vcodec libx264 -r 10 -b:v 512k -s 1920x1080 -acodec aac -ac 2 -ab 32k -ar 44100 -f flv rtmp://192.168.100.21:1935/show/u1
ffmpeg -f dshow -i video="OBS Virtual Camera":audio="Microphone (Realtek High Definition Audio)" -vcodec libx264 -r 10 -b:v 512k -rtbufsize 15M -s 1280x1024 -threads 2 -preset ultrafast -crf 22 -tune zerolatency -fflags nobuffer -acodec aac -ac 2 -ab 32k -ar 44100 -f flv rtmp://192.168.100.21:1935/show/u1
'''