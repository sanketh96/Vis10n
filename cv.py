import cv2

def generate_frames():
    # Create a VideoCapture object
    cap = cv2.VideoCapture(0)

    # Check if camera opened successfully
    if (cap.isOpened() == False):
        print("Unable to read camera feed")

    # Default resolutions of the frame are obtained.The default resolutions are system dependent.
    # We convert the resolutions from float to integer.
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    #out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (frame_width,frame_height))
    frameRate = cap.get(5)


    # Display the resulting frame
    count = 0
    while(1):
        #cap.set(cv2.CAP_PROP_POS_MSEC,count)      # Go to the 1 sec. position
        ret, frame = cap.read()

        cv2.imwrite("frame" + str(count) + ".png", frame)
        #cv2.imshow("frame",frame)
        time.sleep(500/1000.0)

        count += 1

        if(count == 15):
            break
        '''
        # Press Q on keyboard to stop recording
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        '''

    # When everything done, release the video capture and video write objects
    cap.release()
    #out.release()

    # Closes all the frames
    #cv2.destroyAllWindows()
