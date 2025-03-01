import pygame
import freenect
import numpy as np
import cv2

pygame.init()

WIDTH, HEIGHT = 640, 480

# Set fullscreen mode with a fixed resolution of 640x480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

NUM_PLAYERS = 2
players = []
colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0)]  # Red, Blue, Green, Yellow

class Player:
    """Player class to represent a player with position, color, and trail."""
    def __init__(self, position, color):
        self.position = position
        self.color = color
        self.assigned = False  # Initially not assigned
        self.trail = []  # List to store previous positions
        self.last_seen = 0  # Frames since last detection

    def update_position(self, new_position):
        """Update the player's position and reset last_seen counter."""
        self.trail.append(self.position)  # Store the old position
        #if len(self.trail) > 10:  # Limit trail length to 10 points
        #    self.trail.pop(0)  # Remove the oldest point in the trail
        self.position = new_position
        self.last_seen = 0  # Reset the missing frame counter

    def mark_missing(self):
        """Increase the last_seen counter if the player is not detected."""
        self.last_seen += 1
        
    def assign(self):
        """Mark the player as assigned."""
        self.assigned = True


def get_video():
    array, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
    array = cv2.rotate(array, cv2.ROTATE_180)  # Rotate if needed
    
    #remove top of it a little bit because of the sun in the room.
    array = array[20:460, 0:640]    
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
                    return True  # User confirmed
                elif event.key == pygame.K_n:
                    return False  # User rejected

def check_for_proximity(new_position):
    """Check if the new position is too close to an already assigned player."""
    for player in players:
        dist = np.linalg.norm(np.array(new_position) - np.array(player.position))
        if dist < 50:  # You can adjust this threshold as needed
            return True  # Too close to an already assigned player
    return False

def calibrate_players():
    """Detects and confirms players before the game starts."""
    global players

    print("Waiting for players to appear...")

    while len(players) < NUM_PLAYERS:
        frame = get_video()    
        thresh = process_ir_image(frame)
        detected_lights = detect_ir_lights(thresh)
        
        # Convert processed IR frame for Pygame
        ir_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)  # Convert grayscale to RGB
        cv2.imshow("IR", ir_display)

        for position in detected_lights:
            if len(players) >= NUM_PLAYERS:
                break  # Stop asking if we have enough players

            if not check_for_proximity(position):  # Only proceed if the point is not too close to an assigned player
                if ask_if_player(position):
                    # Assign the color based on the length of the players list
                    player_color = colors[len(players)]
                    # Create a new player object with position and color
                    new_player = Player(position, player_color)
                    new_player.assign()  # Mark as assigned
                    players.append(new_player)
                    print(f"Player {len(players)} assigned at {position} with color {player_color}")

    print("Calibration complete!")


# === MAIN GAME LOOP ===
calibrate_players()  # Wait for player assignment before starting

running = True
while running:
    frame = get_video()
    thresh = process_ir_image(frame)
    detected_lights = detect_ir_lights(thresh)

    # Update player positions if a detected light matches a stored player
    for player in players:
        if detected_lights:
            closest = min(detected_lights, key=lambda p: np.linalg.norm(np.array(p) - np.array(player.position)), default=None)
            if closest and np.linalg.norm(np.array(closest) - np.array(player.position)) < 50:  # Allow some tolerance
                player.update_position(closest)
                detected_lights.remove(closest)  # Remove from detection list to avoid duplicate assignment
            else:
                player.mark_missing()  # Mark as missing if no close match found
        else:
            player.mark_missing()  # Mark as missing if no detections at all

    # Convert processed IR frame for Pygame
    ir_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)  # Convert grayscale to RGB
    ir_display = np.rot90(ir_display)  # Rotate if needed
    ir_display = pygame.surfarray.make_surface(ir_display)  # Convert to Pygame surface

    #display a yellow background in pygame
    screen.fill((255, 255, 0))    

    # Draw trails (lines connecting previous positions) for each player
    for player in players:
        # Draw the player's trail
        for i in range(len(player.trail) - 1):
            pygame.draw.line(screen, player.color, player.trail[i], player.trail[i + 1], 2)  # Small trail lines

        x, y = player.position
        # If the player is assigned, draw in the assigned color, else use green
        color = player.color if player.assigned else (0, 255, 0)  # Use green if not assigned
        pygame.draw.circle(screen, color, (x, y), 10)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(30)

cv2.destroyAllWindows()
pygame.quit()
