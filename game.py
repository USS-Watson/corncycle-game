import pygame
import freenect
import numpy as np
import cv2

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

def get_video():
    array, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
    return array

def process_ir_image(frame):
    #normalize and convert to 8-bit for OpenCV processing
    frame = np.clip(frame, 0, 2**10-1)
    frame = (frame / 4).astype(np.uint8)

    #gaussian blur to smooth out noise
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    #thresholding to isolate bright IR light sources
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

    return thresh

def detect_ir_lights(thresh):
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    light_positions = []
    for cnt in contours:
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            light_positions.append((cx, cy))
    
    return light_positions

running = True
while running:
    frame = get_video()
    thresh = process_ir_image(frame)
    lights = detect_ir_lights(thresh)

    output = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    for (x, y) in lights:
        cv2.circle(output, (x, y), 5, (0, 0, 255), -1)
    cv2.imshow("IR with Tracked Points", output)

    screen.fill((0, 0, 0)) 
    for (x, y) in lights:
        pygame.draw.circle(screen, (0, 255, 0), (x, y), 10) 
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(30)


    #escape key exit
    if cv2.waitKey(5) & 0xFF == 27:
        running = False

cv2.destroyAllWindows()
pygame.quit()