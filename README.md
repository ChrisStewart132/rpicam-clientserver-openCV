# rpicam-clientserver-openCV

# description
raspberry pi camera python script to send the camera frames to a specified server address
server python script uses openCV library to alter the recieved images and display them
note: MJPEG format is used as openCV2 provides a decoding function, h264 would be more efficient in terms of data rate

client(rpi) script continuously records sending the data to the given addr:port (tcp)
server(probably windows) listens, connects (tcp), displays images as they come, keys: q=quit, b=backsub, c=corner, s=contours, t=thresholding

# how to start
raspberry pi: cntrl+alt+t or ssh pi@192.168.1.66 to open cmd line
	# run cmd in the dir of the script
	python picamera_client.py SERVER_ADDR SERVER_PORT
	python picamera_client.py 192.168.1.68 8002

windows: shift right click in dir-> open windows power shell
	# to send client script to your rpi
	scp picamera_client.py pi@192.168.1.66 #(scp -options source destination)

	# to run the server
	py picamera_server.py SERVER_PORT
	py picamera_server.py 8002

# docs
https://picamera.readthedocs.io/en/release-1.13/api_camera.html
https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
