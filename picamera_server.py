import numpy as np
import cv2
import socket
import subprocess
import time
import sys
# Check the number of command-line arguments
if len(sys.argv) < 2:
    print("Usage: py" + argv[0] + ".py PORT_NUMBER")
    sys.exit(1)  # Exit with an error code

PORT_NUMBER = int(sys.argv[1])

SOCKET_TIMEOUT = 1000# how long the socket waits to recieve data before closing

BACKGROUND_SUBTRACTOR = False # detects movement: white for movement, black for background
CORNER_DETECTION = False # draws circles on detected corners
THRESHOLDING = False# shows the foreground and ignores the background, thresholds out dark colours to black, others to white
COUNTOURS =  False# shape analysis and object detection, draws detected shapes on a black background
# toggle keys b,c,t,s

WINDOW_NAME = "rpicam-clientserver-openCV-CRS"
SCAN_LEN_EST = 10000#(s) guessing len of SOS, if wrong frame broken/merged

def getFrame3(buffer, skip=False):
    '''
    used to scan through buffer to get mjpeg frames
    skips blocks with cmds in headers set
    '''  
    headers = set([0xE0, 0xE1, 0xDB, 0xC0, 0xC4])#xFF xE0/E1... skippable
    non_skippable = set([0x00, 0xd8, 0xda])#xFF x00/xd8/da non skippable
    for i in range(0, len(buffer), 1):
        if buffer[i] == 0xFF:
            if i+1 == len(buffer):
                return i-1#last byte = xFF so point before it for next call
            elif buffer[i+1] in headers:
                temp = buffer[i+2:i+4]
                length = int.from_bytes(temp,'big')
                return i+length#skips a block
            elif buffer[i+1] == 0xD9:
                return i+1#this points to xD9 in buffer
            elif buffer[i+1] == 0xda and skip:#start of scan, skip x bytes (risky)
                return i + SCAN_LEN_EST
            elif buffer[i+1] not in non_skippable:
                print("potential header:", hex(buffer[i+1]))
    return len(buffer)

# Start a socket listening for connections on 0.0.0.0:PORT_NUMBER (all addrs)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', PORT_NUMBER))
server_socket.settimeout(SOCKET_TIMEOUT)
server_socket.listen(0)


# Accept a single connection and use the created connection socket
print("listening for connection")
connection, addr = server_socket.accept()
print("connection recvd", addr)

#face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades
backSub = cv2.createBackgroundSubtractorMOG2(100,16,False)
try:
    buffer = bytearray()
    READ_LENGTH = 4096
    COUNTER = 0

    while True:
        frame = bytearray()       
        while True: # populates 1 frame, and leaves buffer with next frame start in it
            buffer += connection.recv(READ_LENGTH)# FF D8 .. .. FF D9 (MPJEG FRAME)
            i = getFrame3(buffer, COUNTER > 10)# points to last scanned byte in buffer
            while i > len(buffer):# if skipped ahead read to the skipped index
                buffer += connection.recv(READ_LENGTH)

            frame += buffer[:i+1]# add to frame everything up to including last scanned byte
            buffer = buffer[i+1:]# remove frame from buffer but keep data that exceeded the frame
            if len(frame) == 0 or frame[-2] == 0xFF and frame[-1] == 0xD9:
                break
        if len(frame) == 0:
            break

        numpy_frame = np.asarray(frame, dtype="uint8")
        image = cv2.imdecode(numpy_frame,cv2.IMREAD_COLOR)        
        
        #gray_scale = cv2.blur(gray_scale, (3,3))
        if THRESHOLDING:
            gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresh = 66
            max_value = 255
            t = 0#Type: 0: Binary 1: Binary Inverted 2: Truncate 3: To Zero 4: To Zero Inverted
            _, image = cv2.threshold(gray_scale, thresh, max_value, t)
        
        if CORNER_DETECTION:
            gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            corners = cv2.goodFeaturesToTrack(gray_scale,64,0.01,10)
            try:
                for i, corner in enumerate(corners):
                    x = int(corner[0][0])
                    y = int(corner[0][1])
                    cv2.circle(image, (x,y), 1, (0,255,0))
            except:
                pass
            
        if BACKGROUND_SUBTRACTOR:
            image = backSub.apply(image)

        if COUNTOURS:
            threshold = 55
            gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_scale = cv2.GaussianBlur(gray_scale, (5, 5), 0)# Gaussian blur to reduce noise
            canny_output = cv2.Canny(gray_scale, threshold, threshold * 2)
            contours, _ = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            #drawing = np.zeros_like(image)# alternatively create a blank image and draw the contours on that
            cv2.drawContours(image, contours, -1, (0, 255, 0), 1)
            #image = drawing
                
        #image = cv2.resize(image,(1920,1080))
        cv2.putText(image, f"{COUNTER} b:{BACKGROUND_SUBTRACTOR} c:{CORNER_DETECTION} t:{THRESHOLDING} s:{COUNTOURS}", (10,20),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,255,0))                 
        cv2.imshow(WINDOW_NAME, image)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('b'):
            BACKGROUND_SUBTRACTOR = not(BACKGROUND_SUBTRACTOR)
        elif key == ord('c'):
            CORNER_DETECTION = not(CORNER_DETECTION)
        elif key == ord('t'):
            THRESHOLDING = not(THRESHOLDING)
        elif key == ord('s'):
            COUNTOURS = not(COUNTOURS)
        COUNTER += 1
        
finally:
    print("connection closed", addr)
    connection.close()
    server_socket.close()
    cv2.destroyAllWindows()
