import subprocess

'''
stream_address="rtmp://192.168.100.21:1935/show/u2"
cmd = f"ffplay -fflags nobuffer {stream_address}"

proc =subprocess.Popen(f"{cmd}", shell=True, stdout=subprocess.PIPE)

proc.wait()
'''
import platform
print(platform.system())