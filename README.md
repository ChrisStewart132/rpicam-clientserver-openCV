# rpicam-clientserver-openCV
simple raspberry pi camera python script to send the camera frames to a specified server address

server python script uses openCV library to alter the recieved images and display them

note: the current implementation recieves frames in the form of mjpeg frames and should be optimised (better understood)


workflow:
	ssh pi@192.168.1.66
	from windows powershell (shift right click in file exporer dir -> powershell here)
		scp picamera_client.py pi@192.168.1.66 #(scp -options source destination)

	in the ssh of pi run
		python3 picamera_client.py