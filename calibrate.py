import pygame

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

#open window
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    #put dot in top left, bottom left, top right, bottom right
    

    screen.fill((0, 0, 255))
    
    pygame.display.flip()
    clock.tick(60)