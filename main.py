import pygame
from engine import StrategyEngine

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Risz Engine - Integrated Prototype")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 16)
large_font = pygame.font.SysFont("Consolas", 20, bold=True)

# 1. Inicjalizacja silnika
engine = StrategyEngine("provinces.json", "events.json")
PLAYER_TAG = "Crown"
player = engine.countries[PLAYER_TAG]
engine.recalculate_incomes()

# 2. Generowanie mapy ID w pamięci (w pełnej wersji: pygame.image.load)
id_map = pygame.Surface((WIDTH, 380))
id_map.fill((15, 15, 20))  # Woda / brak prowincji

# Rysujemy prowincje zgodnie z kolorami z JSON
for prov in engine.provinces.values():
    if prov.id == 1:
        pygame.draw.rect(id_map, prov.color, (50, 40, 200, 280))
    elif prov.id == 2:
        pygame.draw.rect(id_map, prov.color, (280, 40, 220, 280))
    elif prov.id == 3:
        pygame.draw.rect(id_map, prov.color, (530, 40, 220, 280))

selected_province = None

# 3. Zegar symulacji (Tick co 1000 ms)
TICK_EVENT = pygame.USEREVENT + 1
TICK_RATE_MS = 1000
pygame.time.set_timer(TICK_EVENT, TICK_RATE_MS)

paused = False
day_count = 1
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_DOWN:
                player.stability = max(0, player.stability - 15)
            elif event.key == pygame.K_UP:
                player.stability = min(100, player.stability + 15)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Kliknięcie w obrębie samej mapy (y < 380)
            if 0 <= mx < WIDTH and 0 <= my < 380:
                pixel = id_map.get_at((mx, my))
                rgb = (pixel.r, pixel.g, pixel.b)
                selected_province = engine.color_to_province.get(rgb)

        elif event.type == TICK_EVENT and not paused:
            day_count += 1
            engine.tick(PLAYER_TAG)

    # --- RYSOWANIE ---
    screen.fill((25, 25, 30))
    screen.blit(id_map, (0, 0))

    # Panel górny: HUD gracza
    hud_bg = pygame.Rect(0, 0, WIDTH, 35)
    pygame.draw.rect(screen, (10, 10, 12), hud_bg)
    status_txt = "PAUSED (Space)" if paused else "RUNNING (Space)"
    hud_text = f"Day: {day_count} | Status: {status_txt} | Tag: {player.name} | Gold: {player.gold} (+{player.income}/tick) | Stability: {player.stability}%"
    screen.blit(font.render(hud_text, True, (240, 240, 240)), (15, 8))

    # Panel dolny: Szczegóły zaznaczonej prowincji
    panel_y = 380
    pygame.draw.rect(screen, (18, 18, 22), (0, panel_y, WIDTH, HEIGHT - panel_y))
    pygame.draw.line(screen, (60, 60, 70), (0, panel_y), (WIDTH, panel_y), 2)

    if selected_province:
        prov_lines = [
            f"Province: {selected_province.name} (ID: {selected_province.id})",
            f"Owner: {selected_province.owner}",
            f"Tax Yield: {selected_province.tax} gold / tick"
        ]
        screen.blit(large_font.render("PROVINCE DETAILS", True, (200, 180, 100)), (25, panel_y + 15))
        for i, line in enumerate(prov_lines):
            screen.blit(font.render(line, True, (220, 220, 220)), (25, panel_y + 45 + i * 22))
    else:
        screen.blit(font.render("Click any province on the map to inspect details.", True, (140, 140, 140)), (25, panel_y + 45))

    # Informacja o ostatnim evencie
    if engine.last_event_title:
        ev_msg = f"Last Event: {engine.last_event_title}"
        screen.blit(font.render(ev_msg, True, (255, 120, 120)), (480, panel_y + 45))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()