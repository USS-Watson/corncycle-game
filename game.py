import pygame
import freenect
import numpy as np
import cv2

pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

NUM_PLAYERS = 2
players = []
colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0)]  #rgby

class Player:
    """Player class to represent a player with position, color, and trail."""
    def __init__(self, position, color):
        self.position = position
        self.color = color
        self.assigned = False #initially not assigned
        self.trail = []  #previous positions

    def update_position(self, new_position):
        """Update the player's position and store the old position for trail."""
        self.trail.append(self.position) #old position
        if len(self.trail) > 10:  # Limit trail length to 10 points
            self.trail.pop(0)  # Remove the oldest point in the trail
        self.position = new_position

    def assign(self):
        """Mark the player as assigned."""
        self.assigned = True

def get_video():
    array, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
    return array

def process_ir_image(frame):
    """Convert frame to 8-bit, blur, and threshold to detect IR points."""
    frame = np.clip(frame, 0, 2**10-1)  #clip values
    frame = (frame / 4).astype(np.uint8)  #convert to 8-bit

    # Apply Gaussian blur to remove noise
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

    return thresh

def detect_ir_lights(thresh):
    """Find bright IR points in the thresholded image."""
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    light_positions = []

    for cnt in contours:
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            light_positions.append((cx, cy))

    return light_positions

def ask_if_player(position):
    """Asks user if the detected light is a player and waits for input."""
    waiting = True
    while waiting:
        screen.fill((0, 0, 0))

        text = font.render(f"Is this a player? (Y/N)", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 4, HEIGHT - 50))

        pygame.draw.circle(screen, (0, 255, 0), position, 10)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True
                elif event.key == pygame.K_n:
                    return False

def check_for_proximity(new_position):
    """Check if the new position is too close to an already assigned player."""
    for player in players:
        dist = np.linalg.norm(np.array(new_position) - np.array(player.position))
        if dist < 50: 
            return True
    return False

def calibrate_players():
    """Detects and confirms players before the game starts."""
    global players

    print("Waiting for players to appear...")

    while len(players) < NUM_PLAYERS:
        frame = get_video()    
        thresh = process_ir_image(frame)
        detected_lights = detect_ir_lights(thresh)
        
        #convert processed IR frame for Pygame
        ir_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)  #convert grayscale to RGB
        cv2.imshow("IR", ir_display)

        for position in detected_lights:
            if len(players) >= NUM_PLAYERS:
                break  #stop asking if we have enough players

            if not check_for_proximity(position):  #only proceed if the point is not too close to an assigned player
                if ask_if_player(position):
                    #assign the color based on the length of the players list
                    player_color = colors[len(players)]
                    #create a new player object with position and color
                    new_player = Player(position, player_color)
                    players.append(new_player)
                    print(f"Player {len(players)} assigned at {position} with color {player_color}")

    print("Calibration complete!")


calibrate_players() #wait for player assignment before starting

running = True
while running:
    frame = get_video()
    thresh = process_ir_image(frame)
    detected_lights = detect_ir_lights(thresh)

    #update player positions if a detected light matches a stored player
    for player in players:
        closest = min(detected_lights, key=lambda p: np.linalg.norm(np.array(p) - np.array(player.position)), default=None)
        if closest:
            player.update_position(closest)
            player.assign()  #mark the player as assigned

    #convert processed IR frame for Pygame
    ir_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)  #convert grayscale to RGB
    ir_display = np.rot90(ir_display)
    ir_display = pygame.surfarray.make_surface(ir_display)
    
    #display Pygame window with IR feed
    screen.blit(ir_display, (0, 0))

    #draw trails (lines connecting previous positions) for each player
    for player in players:
        for i in range(len(player.trail) - 1):
            pygame.draw.line(screen, player.color, player.trail[i], player.trail[i + 1], 2)

        x, y = player.position
        color = player.color if player.assigned else (0, 255, 0)
        pygame.draw.circle(screen, color, (x, y), 10)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(30)

cv2.destroyAllWindows()
pygame.quit()
