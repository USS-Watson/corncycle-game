import pygame

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 400
CELL_SIZE = 10
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
BLACK = (0, 0, 0)

# Directions
DIRECTIONS = {
    "w": (0, -CELL_SIZE), "s": (0, CELL_SIZE), "a": (-CELL_SIZE, 0), "d": (CELL_SIZE, 0),
    "UP": (0, -CELL_SIZE), "DOWN": (0, CELL_SIZE), "LEFT": (-CELL_SIZE, 0), "RIGHT": (CELL_SIZE, 0),
}

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Two-Player Snake")

# Player class
class Player:
    def __init__(self, x, y, color, keys):
        self.body = [(x, y)]
        self.color = color
        self.direction = None  # No movement until a key is pressed
        self.keys = keys
        self.alive = True

    def move(self):
        if not self.alive or self.direction is None:
            return
        
        head_x, head_y = self.body[-1]
        new_x, new_y = head_x + self.direction[0], head_y + self.direction[1]

        # Check for collisions with walls
        if new_x < 0 or new_x >= WIDTH or new_y < 0 or new_y >= HEIGHT:
            self.alive = False
            return

        # Check for self-collision
        if (new_x, new_y) in trails:
            self.alive = False
            return

        self.body.append((new_x, new_y))
        trails.add((new_x, new_y))

    def change_direction(self, key):
        if key in self.keys:
            new_direction = DIRECTIONS[key]
            # Prevent reversing direction
            if self.direction is None or (new_direction[0] != -self.direction[0] or new_direction[1] != -self.direction[1]):
                self.direction = new_direction
                self.move()  # Move immediately when pressing a key

    def draw(self, surface):
        for segment in self.body:
            pygame.draw.rect(surface, self.color, (*segment, CELL_SIZE, CELL_SIZE))

# Initialize players
player1 = Player(WIDTH // 4, HEIGHT // 2, RED, ["w", "a", "s", "d"])
player2 = Player(3 * WIDTH // 4, HEIGHT // 2, BLUE, ["UP", "LEFT", "DOWN", "RIGHT"])
trails = set(player1.body + player2.body)

# Game loop
running = True
while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            player1.change_direction(pygame.key.name(event.key))
            player2.change_direction(pygame.key.name(event.key))

    player1.draw(screen)
    player2.draw(screen)

    # Check if any player has lost
    if not player1.alive or not player2.alive:
        running = False

    pygame.display.flip()

pygame.quit()
