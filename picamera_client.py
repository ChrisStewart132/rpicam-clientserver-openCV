import socket
import time
import picamera

SERVER_PORT = 8000
SERVER_ADDR = '192.168.1.68'

client_socket = socket.socket()
client_socket.connect((SERVER_ADDR, SERVER_PORT))

# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
try:
    camera = picamera.PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 1
    # Start a preview and let the camera warm up for 2 seconds
    camera.start_preview()
    time.sleep(2)
    # Start recording, sending the output to the connection for 60
    # seconds, then stop
    camera.start_recording(connection, format='rgb')
'''	
    'h264' - Write an H.264 video stream
    'mjpeg' - Write an M-JPEG video stream
    'yuv' - Write the raw video data to a file in YUV420 format
    'rgb' - Write the raw video data to a file in 24-bit RGB format
    'rgba' - Write the raw video data to a file in 32-bit RGBA format
    'bgr' - Write the raw video data to a file in 24-bit BGR format
    'bgra' - Write the raw video data to a file in 32-bit BGRA format
'''
    camera.wait_recording(60)
    camera.stop_recording()
finally:
    connection.close()
    client_socket.close()
