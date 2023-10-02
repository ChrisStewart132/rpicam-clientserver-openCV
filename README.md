# rpicam-clientserver-openCV
https://github.com/ChrisStewart132/rpicam-clientserver-openCV/assets/30304173/ee3fe275-5224-4503-a1bf-0969055eeeb5


# description
client:	Raspberry Pi python script to send camera MJPEG frames to a specified server address.
server:	python script using openCV to alter recieved images and display them.


# requirements
client:	Python,	Raspberry Pi 3 Model B+ 2017, Raspberry Pi camera Rev 1.3.
server:	Python,	opencv-python.


# how to start
client:

    # to open the cmd line
	cntrl+alt+t or ssh pi@192.168.1.66 
	
	# run cmd in the dir of the script
	python picamera_client.py SERVER_ADDR SERVER_PORT
	python picamera_client.py 192.168.1.68 8002

server:

    # to open windows power shell
	shift right click in directory-> open windows power shell
	
	# to send client script to your rpi. (scp -options source destination)
	scp picamera_client.py pi@192.168.1.66

	# to run the server
	py picamera_server.py SERVER_PORT
	py picamera_server.py 8002

# technical details
	Receiving a networked video data stream, dividing the data stream, and decoding each frame using an openCV function
	MJPEG encodes the video with each frame being compressed as a JPEG image
	In many MJPEG implementations, the header does not explicitly contain the exact length of the frame data. Instead, the length of the frame is determined by the end marker
	
# (M)JPEG/JFIF File Structure / Common Markers

Short name| 	Bytes| 	Payload| 	Name| 	Comments|
--- | --- | --- | --- | --- |
SOI| 	0xFF, 0xD8| 	none| 	Start Of Image| 
SOF0| 	0xFF, 0xC0| 	variable size| 	Start Of Frame (baseline DCT)|
SOF2| 	0xFF, 0xC2| 	variable size| 	Start Of Frame (progressive DCT)| 	Indicates that this is a progressive DCT-based JPEG, and specifies the width, height, number of components, and component subsampling (e.g., 4:2:0).|
DHT| 	0xFF, 0xC4| 	variable size| 	Define Huffman Table(s)| 	Specifies one or more Huffman tables.|
DQT| 	0xFF, 0xDB| 	variable size| 	Define Quantization Table(s)| 	Specifies one or more quantization tables.|
DRI| 	0xFF, 0xDD| 	4 bytes| 	Define Restart Interval| 	Specifies the interval between RSTn markers, in Minimum Coded Units (MCUs). This marker is followed by two bytes indicating the fixed size so it can be treated like any other variable size segment.|
SOS| 	0xFF, 0xDA|	variable size| 	Start Of Scan| 	Begins a top-to-bottom scan of the image. In baseline DCT JPEG images, there is generally a single scan. Progressive DCT JPEG images usually contain multiple scans. This marker specifies which slice of data it will contain, and is immediately followed by entropy-coded data.|
RSTn| 	0xFF, 0xDn (n=0..7)| 	none| 	Restart| 	Inserted every r macroblocks, where r is the restart interval set by a DRI marker. Not used if there was no DRI marker. The low three bits of the marker code cycle in value from 0 to 7.|
APPn| 	0xFF, 0xEn| 	variable size| 	Application-specific| 	For example, an Exif JPEG file uses an APP1 marker to store metadata, laid out in a structure based closely on TIFF.|
COM| 	0xFF, 0xFE| 	variable size| 	Comment| 	Contains a text comment.|
EOI| 	0xFF, 0xD9| 	none| 	End Of Image| 	

	

# docs

https://picamera.readthedocs.io/en/release-1.13/api_camera.html

https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
