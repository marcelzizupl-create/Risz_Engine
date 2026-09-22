import pygame
import json

pygame.init()
WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Color-Coded Province Map")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 16)

# --- 1. Simulation JSON file ---
provinces_data = [
    {"id": 1, "name": "Pomorze", "color": (255, 0, 0), "owner": "Polska", "tax": 8},
    {"id": 2, "name": "Mazowsze", "color": (0, 255, 0), "owner": "Polska", "tax": 12},
    {"id": 3, "name": "Małopolska", "color": (0, 0, 255), "owner": "Polska", "tax": 10},
]
# Quick lookup map: RGB tuple -> province data dictionary
PROVINCE_BY_COLOR = {tuple(p['color']): p for p in provinces_data}

# --- 2. MAP SURFACES ---
id_map = pygame.Surface((WIDTH, HEIGHT))
id_map.fill((0, 0, 0)) # Default background (black = woda/brak prowincji)
pygame.draw.rect(id_map, (255, 0, 0), (50, 50, 200, 150))   # Pomorze
pygame.draw.rect(id_map, (0, 255, 0), (300, 50, 200, 150))  # Mazowsze
pygame.draw.rect(id_map, (0, 0, 255), (550, 50, 200, 150))  # Małopolska

selected_province = None

# --- 3. MAIN LOOP ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if 0 <= mx < WIDTH and 0 <= my < HEIGHT:
                pixel_color = id_map.get_at((mx, my))
                rgb = (pixel_color.r, pixel_color.g, pixel_color.b)
                
                selected_province = PROVINCE_BY_COLOR.get(rgb, None)

    # DRAWING
    screen.fill((30, 30, 35))

    screen.blit(id_map, (0, 0))

    panel_y = 380
    pygame.draw.rect(screen, (20, 20, 20), (0, panel_y, WIDTH, HEIGHT - panel_y))
    pygame.draw.line(screen, (70, 70, 70), (0, panel_y), (WIDTH, panel_y), 2)

    if selected_province:
        info_lines = [
            f"Selected province: {selected_province['name']} (ID: {selected_province['id']})",
            f"Owner: {selected_province['owner']}",
            f"Base tax: {selected_province['tax']} gold / month"
        ]
    else:
        info_lines = ["Click on a province to view details (black background = water/none)."]

    for i, line in enumerate(info_lines):
        txt = font.render(line, True, (220, 220, 220))
        screen.blit(txt, (20, panel_y + 15 + i * 25))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()