#!/usr/bin/python
import freenect
import numpy as np
import cv2

def get_video():
    array, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
    #rotate it 
    array = cv2.rotate(array, cv2.ROTATE_180)
    return array

def process_ir_image(frame):
    # Normalize and convert to 8-bit for OpenCV processing
    frame = np.clip(frame, 0, 2**10-1)
    frame = (frame / 4).astype(np.uint8)

    # Apply Gaussian blur to smooth out noise
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    # Apply thresholding to isolate bright IR light sources
    _, thresh = cv2.threshold(frame, 200, 255, cv2.THRESH_BINARY)

    return thresh

def detect_ir_lights(thresh):
    # Find contours (bright spots)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    light_positions = []
    for cnt in contours:
        # Get the center of the contour
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            light_positions.append((cx, cy))
    
    return light_positions

if __name__ == "__main__":
    while True:
        frame = get_video()
        thresh = process_ir_image(frame)
        lights = detect_ir_lights(thresh)

        # Display the processed threshold image
        cv2.imshow("Thresholded IR", thresh)

        # Draw detected points
        output = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        for (x, y) in lights:
            cv2.circle(output, (x, y), 5, (0, 0, 255), -1)

        cv2.imshow("IR with Tracked Points", output)

        k = cv2.waitKey(5) & 0xFF
        if k == 27:  # Press 'Esc' to quit
            break

    cv2.destroyAllWindows()
