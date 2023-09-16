import numpy as np
import cv2
import socket
import subprocess
import time


BACKGROUND_SUBTRACTOR = False #white for movement, black for background
CORNER_DETECTION = False #finds corners and draws circles upon them
THRESHOLDING = True #thresholds out dark colours to black, other to white 
COUNTOURS =  False

WINDOW_NAME = "window"
SCAN_LEN_EST = 50000# guessing len of SOS, if wrong frame broken/merged

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

# Start a socket listening for connections on 0.0.0.0:8000 (all addrs)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)


# Accept a single connection and use the created connection socket
print("listening for connection")
connection, addr = server_socket.accept()
print("connection recvd", addr)

#face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades

try:
    buffer = bytearray()
    READ_LENGTH = 4096
    COUNTER = 0
    if BACKGROUND_SUBTRACTOR:
        backSub = cv2.createBackgroundSubtractorMOG2(
            100,16,False
            )

    while True:
        frame = bytearray()       
        while True: #populates 1 frame, and leaves buffer with next frame start in it
            buffer += connection.recv(READ_LENGTH)# FF D8 .. .. FF D9
            i = getFrame3(buffer, COUNTER > 100)#points to last scanned byte in buffer
            while i > len(buffer):#if skipped ahead read to the skipped index
                buffer += connection.recv(READ_LENGTH)

            frame += buffer[:i+1]#add to frame everything up to including last scanned byte
            buffer = buffer[i+1:]
            if len(frame) == 0 or frame[-2] == 0xFF and frame[-1] == 0xD9:
                break
        if len(frame) == 0:
            break
        #print(len(frame))
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
            #lineS,lineE=None,None
            try:
                for i, corner in enumerate(corners):
                    x = int(corner[0][0])
                    y = int(corner[0][1])
                    '''
                    if i == 0:
                        lineS = x,y
                    else:
                        lineE = x,y
                        cv2.line(image, lineS,lineE,(0,255,0))
                        lineS = x,y
                    '''
                    cv2.circle(image, (x,y), 1, (0,255,0))
                    #print(x,y)
            except:
                pass
            
        if BACKGROUND_SUBTRACTOR:
            image = backSub.apply(image)

        if COUNTOURS:
            threshold = 55
            gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            canny_output = cv2.Canny(gray_scale, threshold, threshold * 2)
            contours, _ = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours_poly = [None]*len(contours)
            boundRect = [None]*len(contours)
            centers = [None]*len(contours)
            radius = [None]*len(contours)
            for i, c in enumerate(contours):
                contours_poly[i] = cv2.approxPolyDP(c, 3, True)
                boundRect[i] = cv2.boundingRect(contours_poly[i])
                centers[i], radius[i] = cv2.minEnclosingCircle(contours_poly[i])
            drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
            if True:
                # Draw polygonal contour + bonding rects + circles
                for i in range(len(contours)):
                    color = (0, 255, 0)
                    cv2.drawContours(drawing, contours_poly, i, color)
                    #cv2.rectangle(drawing, (int(boundRect[i][0]), int(boundRect[i][1])), \
                      #(int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3])), color, 2)
                    #cv2.circle(drawing, (int(centers[i][0]), int(centers[i][1])), int(radius[i]), color, 2)
            image = drawing
                
        #image = cv2.resize(image,(1920,1080))
        cv2.putText(image, f"{COUNTER}", (10,20),cv2.FONT_HERSHEY_COMPLEX,0.8,(0,255,0))                 
        cv2.imshow(WINDOW_NAME, image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        COUNTER += 1
finally:
    connection.close()
    server_socket.close()
    cv2.destroyAllWindows()
