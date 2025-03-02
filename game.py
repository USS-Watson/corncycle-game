import pygame
import freenect
import numpy as np
import cv2
import elevenlabs_voice
import random
import threading
import serial

WIDTH, HEIGHT = 800, 600
#QUAD = [(188, 84), (533, 80), (144, 326), (528, 344)]
QUAD = [(143, 29), (493, 12), (115, 272), (496, 273)]
NUM_PLAYERS = 2
screen = None

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
colors = [RED, BLUE, GREEN, YELLOW]

def run():
    global FONT, screen, clock, players, trails

    FONT = pygame.font.Font(None, 36)

    # set fullscreen mode with a fixed resolution of 800x600
    clock = pygame.time.Clock()

    players = []
    trails = {}

    class Player:
        """Player class to represent a player with position, color, and trail."""
        def __init__(self, position, color):
            self.position = position
            self.color = color
            if color == RED:
                self.color_string = "RED"
            elif color == GREEN:
                self.color_string = "GREEN"
            elif color == BLUE:
                self.color_string = "BLUE"
            elif color == YELLOW:
                self.color_string = "YELLOW"
            else:
                self.color_string = "ANONYMOUS"
            self.assigned = False # initially not assigned
            self.trail = [] # list to store previous positions
            self.last_seen = 0 # frames since last detection
            self.alive = True
            self.name = ""

        def update_position(self, new_position):
            """Update the player's position and reset last_seen counter."""
            # if len(self.trail) <= 0 or self.trail[-1] != self.position:
            self.trail.append(self.position)
            trails[self.position] = self
            # if len(self.trail) > 50:
            #    self.trail.pop(0)
            self.position = new_position
            self.last_seen = 0

        def mark_missing(self):
            """Increase the last_seen counter if the player is not detected."""
            self.last_seen += 1
            
        def assign(self):
            """Mark the player as assigned."""
            self.assigned = True
            
        def set_name(self, name):
            """Assign a name to the player."""
            self.name = name


    def get_video():
        array, _ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
        array = cv2.rotate(array, cv2.ROTATE_180)
        
        #remove top of it a little bit because of the sun in the room.
        array = array[65:460, 0:640]    
        return array

    def process_ir_image(frame):
        # normalize, convert to 8-bit for OpenCV processing
        frame = np.clip(frame, 0, 2**10-1)
        frame = (frame / 4).astype(np.uint8)

        # gaussian blur to smooth out noise
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)

        # thresholding to isolate bright IR light sources
        _, thresh = cv2.threshold(frame, 200, 255, cv2.THRESH_BINARY)

        return thresh

    def detect_ir_lights(thresh):
        # find contours (bright spots)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        light_positions = []
        for cnt in contours:
            # get the center of the contour
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                light_positions.append((cx, cy))
        
        mapped_positions = normalize(light_positions)
        print(f'actual positions: {light_positions}, mapped positions: {mapped_positions}')
        return mapped_positions

    def normalize(light_positions):
        dest = [(0, 0), (WIDTH, 0), (0, HEIGHT), (WIDTH, HEIGHT)]
        H = funky_linear_algebra(QUAD, dest)
        result = []
        for position in light_positions:
            cx, cy = position
            point = np.array([cx, cy, 1])
            mapped = H.dot(point)
            mapped /= mapped[2]
            x = int(round(mapped[0]))
            y = int(round(mapped[1]))
            if x >= WIDTH:
                x = WIDTH-1
            if y >= HEIGHT:
                y = HEIGHT-1
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            result.append((x, y))
        return result

    def funky_linear_algebra(src_pts, dst_pts):
        A = []
        for (x, y), (u, v) in zip(src_pts, dst_pts):
            A.append([-x, -y, -1,   0,  0, 0, u*x, u*y, u])
            A.append([ 0,  0,  0, -x, -y,-1, v*x, v*y, v])
        A = np.array(A)
        _, _, V = np.linalg.svd(A)
        H = V[-1].reshape(3, 3)
        return H

    def ask_if_player(position, prompt):
        """Asks user if the detected light is a player and waits for input."""
        waiting = True
        while waiting:
            screen.fill((0, 0, 0))

            text = FONT.render(prompt, True, WHITE)
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
            
            # convert processed IR frame for Pygame
            ir_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
            cv2.imshow("IR", ir_display)

            for position in detected_lights:
                if len(players) >= NUM_PLAYERS:
                    break

                if not check_for_proximity(position): # only proceed if the point is not too close to an assigned player
                    if ask_if_player(position, "Is this a player? (Y/N)"):
                        # assign the color based on the length of the players list
                        player_color = colors[len(players)]
                        # create a new player object with position and color
                        new_player = Player(position, player_color)
                        new_player.assign()  # mark as assigned
                        players.append(new_player)
                        print(f"Player {len(players)} assigned at {position} with color {player_color}")
                        name_player(new_player)

        print("Calibration complete!")

    def kill_player(player):
        player.alive = False    
        pygame.mixer.Sound.play(pygame.mixer.Sound("voice/crash.mp3"))
        
        #serial
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=5)
        
        #color
        color = ""
        if player.color == RED:
            color = "R"
        elif player.color == GREEN:
            color = "G"
        elif player.color == BLUE:
            color = "B"
        
        ser.write(b'G,' + color.encode() + b',DEAD\n')
        ser.close()    
        
        elevenlabs_voice.play_crash(player.name)
        print(f'Player {player.color} died!')

    def end_game():
        # assumes only one player is alive
        player = None
        for p in players:
            if p.alive:
                player = p
                break
        if player == None:
            print('something terrible has happened')
            return
        
        pygame.mixer.music.stop()
        elevenlabs_voice.play_win(player.name)

        font = pygame.font.Font(None, 72)
        text = font.render(f"{player.name.upper()} WINS!", True, player.color)
        text_rect = text.get_rect(center=(400, 200))
        running2 = True
        while running2:
            screen.fill(WHITE)
            screen.blit(text, text_rect)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running2 = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        running2 = False
    
    def nearest_color(color):
        r, g, b = color
        r = r if r > 100 else 0
        g = g if g > 100 else 0
        b = b if b > 100 else 0
        return (r, g, b)

    def name_player(player):
        """Prompts the user to name the player."""
        waiting = True
        text = ""  # Initialize the text variable outside the loop

        while waiting:
            screen.fill((0, 0, 0))

            # Render the text input
            text_surface = FONT.render(text, True, WHITE)
            screen.blit(text_surface, (WIDTH // 4, HEIGHT // 2))

            # Render the prompt
            text_prompt = FONT.render("Enter name:", True, WHITE)
            screen.blit(text_prompt, (WIDTH // 4, HEIGHT // 2 - 50))
            
            #render already assigned players
            for p in players:
                if p.name:
                    text_player = FONT.render(f"{p.color_string}: {p.name}", True, p.color)
                    screen.blit(text_player, (WIDTH // 4, HEIGHT // 2 - 100))
                
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        player.set_name(text)  # Use the set_name method to assign the name
                        print(f'Player {player.color_string} named {player.name}')
                        #save my poor elevenlabs tokens
                        if text == "jose":
                            pygame.mixer.Sound.play(pygame.mixer.Sound("voice/jose.mp3"))
                        elif text == "manuel":
                            pygame.mixer.Sound.play(pygame.mixer.Sound("voice/manuel.mp3"))
                        else:
                             elevenlabs_voice.play_join(player.name)
                        waiting = False
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]  # Remove the last character
                    else:
                        text += event.unicode  # Append the typed character
            

    # === MAIN GAME LOOP ===
    
    calibrate_players()  # wait for player assignment before starting
    screen.fill(WHITE)    

    # wait for space bar to start
    
    start_filenames = elevenlabs_voice.get_start_filenames()
    start_filename = random.choice(start_filenames)
    pygame.mixer.Sound.play(pygame.mixer.Sound(start_filename))
    
    font = pygame.font.Font(None, 72)
    text = font.render("Press SPACE to start", True, BLACK)
    text_rect = text.get_rect(center=(400, 300))
    running2 = True
    while running2:
        screen.fill(WHITE)
        screen.blit(text, text_rect)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running2 = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running2 = False
    
    #3 2 1 go countdown
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        text = FONT.render(str(i), True, BLACK)
        text_rect = text.get_rect(center=(400, 300))
        screen.blit(text, text_rect)
        pygame.display.update()
        #sound 
        count_filename = elevenlabs_voice.get_count_filename(i)
        pygame.mixer.Sound.play(pygame.mixer.Sound(count_filename))
        
        pygame.time.wait(1000)
    
    begin_filename = "voice/begin.mp3"
    pygame.mixer.Sound.play(pygame.mixer.Sound(begin_filename))

    running = True
    pygame.mixer.music.load("voice/music.mp3") #optional music
    pygame.mixer.music.play(-1)
    while running:

    
        frame = get_video()
        thresh = process_ir_image(frame)
        detected_lights = detect_ir_lights(thresh)

        num_alive = 0

        for player in players:
            if not player.alive:
                continue
            num_alive += 1
            if detected_lights:
                closest = min(detected_lights, key=lambda p: np.linalg.norm(np.array(p) - np.array(player.position)), default=None)
                if closest and np.linalg.norm(np.array(closest) - np.array(player.position)) < 50: # allow some tolerance
                    player.update_position(closest)
                    detected_lights.remove(closest) # remove from detection list to avoid duplicate assignment
                    r, g, b, a = None, None, None, None
                    try:
                        r, g, b, a = screen.get_at(player.position)
                    except IndexError:
                        print('skipping')
                        continue
                    position_color = (r, g, b)
                    print(f'loc: {player.position}, player color: {player.color_string}, position color: {position_color}')
                    if position_color != WHITE and position_color != BLACK and nearest_color(position_color) != player.color:
                        kill_player(player)
                    # if player.position[0] <= 5 or player.position[0] >= WIDTH-5 or player.position[1] <= 5 or player.position[1] >= HEIGHT-5:
                    #     kill_player(player)
                    # if player.position in trails and trails[player.position] != player and trails[player.position].alive:
                else:
                    player.mark_missing() # mark as missing if no close match found
            else:
                player.mark_missing() # mark as missing if no detections at all
        
        if num_alive <= 1:
            end_game()
            break

        # convert processed IR frame for Pygame
        ir_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB) # convert grayscale to RGB
        ir_display = np.rot90(ir_display) # rotate if needed
        ir_display = pygame.surfarray.make_surface(ir_display) # convert to Pygame surface

        #screen.fill(WHITE)    
        
        #tron image background
        # tron = pygame.image.load("tron.png")
        # tron = pygame.transform.scale(tron, (WIDTH, HEIGHT))
        # screen.blit(tron, (0, 0))
        screen.fill(WHITE)

        # draw trails for each player
        for player in players:
            if not player.alive:
                continue
            for i in range(len(player.trail) - 10):
                pygame.draw.line(screen, player.color, player.trail[i], player.trail[i + 1], 10)

            x, y = player.position
            # if the player is assigned, draw in the assigned color, else use green
            color = player.color if player.assigned else (0, 255, 0)
            # pygame.draw.circle(screen, color, (x, y), 10)
            # text = FONT.render(f'({x}, {y})', True, color)
            # screen.blit(text, (x, y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.flip()
        clock.tick(30)


if __name__ == '__main__':
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    while True:
        run()
    cv2.destroyAllWindows()
    pygame.quit()