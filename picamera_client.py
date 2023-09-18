import socket
import time
import picamera
import sys
if len(sys.argv) < 3:
        print("Usage: python {argv[0]}.py SERVER_ADDR SERVER_PORT")
        sys.exit(1)
SERVER_PORT = int(sys.argv[2])# 8001
SERVER_ADDR = sys.argv[1]# '192.168.1.68'

client_socket = socket.socket()
client_socket.connect((SERVER_ADDR, SERVER_PORT))

# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    camera = picamera.PiCamera()
    quality = ((1920,1080), (1280,720), (640, 480), (480,360))
    camera.resolution = quality[2]
    camera.framerate = 30
    # Start a preview and let the camera warm up for 2 seconds
    #camera.start_preview()
    time.sleep(2)
    # Start recording, sending the output to the connection for 60
    # seconds, then stop
    camera.start_recording(connection, format='mjpeg')#h264, mjpeg, yuv, rgb, rgba, bgr, bgra
    camera.wait_recording(9999)
    #camera.stop_recording()
finally:
    connection.close()
    client_socket.close()