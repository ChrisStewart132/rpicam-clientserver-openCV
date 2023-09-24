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
BLUR = False# blurs the image
GRAY = False# converts image to black and white / gray scale
LAPLACIAN_FILTER = False# gray scale -> filter
HOUGH_LINES = False# The Hough Transform is a popular technique to detect any shape,
GRAB_CUT = False# foreground extraction
toggle_keys = {'b':BACKGROUND_SUBTRACTOR, 'c':CORNER_DETECTION, 't':THRESHOLDING, 's':COUNTOURS,
               'g':GRAY, 'h':BLUR, 'l':LAPLACIAN_FILTER, 'j':HOUGH_LINES, 'k':GRAB_CUT}

WINDOW_NAME = "rpicam-clientserver-openCV-CRS"
SCAN_LEN_EST = 1000#(s) guessing len of SOS, if wrong frame broken/merged

def getFrame3(buffer, skip=True):
    '''
    used to scan through buffer to get mjpeg frames
    skips blocks with cmds in headers set
    '''
    if 0:# investigated using buffer.find(signature) to scan from the start of the frame to the end but less performant
        try:
            return 0 + buffer.find(bytearray([0xd9]))
        except ValueError:# eoi not found
            return len(buffer)# frame end not found, read more bytes from socket, re-try
    
    headers = set([0xE0, 0xE1, 0xDB, 0xC0, 0xC4])# xFF xE0/E1... skippable
    non_skippable = set([0x00, 0xd8, 0xda])# xFF x00/xd8/da non skippable
    for i in range(len(buffer)):
        if buffer[i] == 0xFF:# find 0xff then check trailing byte
            if i+1 == len(buffer):
                return i-1# last byte = xFF so point before it for next call
            elif buffer[i+1] in headers:
                temp = buffer[i+2:i+4]
                length = int.from_bytes(temp,'big')
                return i+length# skips a block
            elif buffer[i+1] == 0xD9:
                return i+1# end of frame
            elif buffer[i+1] == 0xda and skip:# start of scan, skip x bytes (risky)
                return i + SCAN_LEN_EST
    return len(buffer)# frame end not found, read more bytes from socket, re-try

# Start a socket listening for connections on 0.0.0.0:PORT_NUMBER (all addrs)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', PORT_NUMBER))
server_socket.settimeout(SOCKET_TIMEOUT)
server_socket.listen(0)


# Accept a single connection and use the created connection socket
print("listening for connection")
connection, addr = server_socket.accept()
print("connection recvd", addr)

cv2.setUseOptimized(True)
#face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades
backSub = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=16, detectShadows=False)
try:
    buffer = bytearray()
    READ_LENGTH = 1024
    COUNTER = 0

    while True:
        frame = bytearray()# holds a mjpeg frame
        while True: # populates 1 frame, and leaves buffer with next frame start in it
            buffer += connection.recv(READ_LENGTH)# FF D8 (start of image).. .. FF D9 (end of image) -- MJPEG FRAME
            eoi = getFrame3(buffer)# find end of image index
            while eoi >= len(buffer):# if skipped ahead read to the skipped index
                buffer += connection.recv(READ_LENGTH)

            frame += buffer[:eoi+1]# add to frame everything up to including last scanned byte
            buffer = buffer[eoi+1:]# remove frame from buffer but keep data that exceeded the frame
            if len(frame) == 0 or frame[-2] == 0xFF and frame[-1] == 0xD9:
                break
        if len(frame) == 0:
            break

        numpy_frame = np.asarray(frame, dtype="uint8")
        image = cv2.imdecode(numpy_frame,cv2.IMREAD_COLOR)  
        gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_scale_blurred = cv2.GaussianBlur(gray_scale, (5, 5), 0)# Gaussian blur to reduce noise
        edges = cv2.Canny(gray_scale_blurred, threshold1=50, threshold2=150, apertureSize = 3)


        if toggle_keys['g']:
            image = gray_scale
            
        if toggle_keys['h']:
            image = gray_scale_blurred if GRAY else cv2.GaussianBlur(image, (5, 5), 0)


        # grab cut foreground extraction
        if toggle_keys['k']:
            '''
            mask - It is a mask image where we specify which areas are background,
            foreground or probable background/foreground etc. It is done by the following flags,
            cv.GC_BGD, cv.GC_FGD, cv.GC_PR_BGD, cv.GC_PR_FGD, or simply pass 0,1,2,3 to image.
            '''
            mask = np.zeros(image.shape[:2], np.uint8)
            #rect: coordinates of a rectangle which includes the foreground object in the format (x,y,w,h)
            height, width = image.shape[:2]
            offset = 100
            rect = (offset,offset,width-offset,height-offset)
            #bdgModel, fgdModel - These are arrays used by the algorithm internally. You just create two np.float64 type zero arrays of size (1,65).
            bgdModel = np.zeros((1,65),np.float64)
            fgdModel = np.zeros((1,65),np.float64)
            #iterCount - Number of iterations the algorithm should run.
            iterCount = 5
            #mode should be cv.GC_INIT_WITH_RECT or cv.GC_INIT_WITH_MASK or combined which decides whether we are drawing rectangle or final touchup strokes.
            cv2.grabCut(image,mask,rect,bgdModel,fgdModel,iterCount,cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask==2)|(mask==0),0,1).astype('uint8')
            image = image*mask2[:,:,np.newaxis]
            cv2.rectangle(image, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 1)

        # laplacian filter
        if toggle_keys['l']:
            laplacian = cv2.Laplacian(gray_scale, cv2.CV_64F)
            laplacian_abs = cv2.convertScaleAbs(laplacian)
            image = laplacian_abs
            


        # hough transform (shape detection)
        if toggle_keys['j']:
            try:
                # probabalistic hough transform
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
                for line in lines:
                    x1,y1,x2,y2 = line[0]
                    cv2.line(image,(x1,y1),(x2,y2),(0,255,0),1)
            except:# lines can possible be None as no lines found
                pass

        # adds circle to the image where corners are detected
        if toggle_keys['c']:
            corners = cv2.goodFeaturesToTrack(gray_scale, maxCorners=256, qualityLevel=0.01, minDistance=10)
            try:
                for i, corner in enumerate(corners):
                    x = int(corner[0][0])
                    y = int(corner[0][1])
                    cv2.circle(image, (x,y), 1, (0,255,0))
            except:
                pass

        
        # thresholding foreground / background focusing 
        if toggle_keys['t']:
            thresh = 66
            max_value = 255
            t = 0#Type: 0: Binary 1: Binary Inverted 2: Truncate 3: To Zero 4: To Zero Inverted
            _, image = cv2.threshold(gray_scale_blurred, thresh, max_value, t)
            
        
        # shape detection 
        if toggle_keys['s']:
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            #drawing = np.zeros_like(image)# alternatively create a blank image and draw the contours on that
            cv2.drawContours(image, contours, -1, (0, 255, 0), 1)
            #image = drawing


        # movement detection
        if toggle_keys['b']:
            image = backSub.apply(image)


        # resize. rotate (camera upside-down irl), add state text, add modified image to window
        #transposed_image = cv2.transpose(image)# Transpose the frame (swap rows and columns)
        #image = cv2.flip(transposed_image, 1)# Flip horizontally to complete the 90-degree counterclockwise rotation
        #image = cv2.warpAffine(image, cv2.getRotationMatrix2D((width / 2, height / 2), 180, 1), (width, height))
        image = cv2.rotate(image, cv2.ROTATE_180)
        image = cv2.resize(image,(1920, 1080))
        cv2.putText(image, f"{COUNTER} {toggle_keys} press \"q\" to exit", (10,20),cv2.FONT_HERSHEY_COMPLEX,0.8,(255,255,255))                 
        cv2.imshow(WINDOW_NAME, image)


        # user key input
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif 96 < key < 0x110000 and chr(key) in toggle_keys:
            toggle_keys[chr(key)] = not(toggle_keys[chr(key)])

        COUNTER += 1
        
finally:
    print("connection closed", addr)
    connection.close()
    server_socket.close()
    cv2.destroyAllWindows()
