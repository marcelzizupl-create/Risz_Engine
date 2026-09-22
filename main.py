import pygame
from engine import RuleEngine, CountryState

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Risz Engine - Alpha")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 18)

player_country = CountryState(name="Crown")
engine = RuleEngine("events.json")

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
                player_country.stability = max(0, player_country.stability - 15)

        elif event.type == TICK_EVENT and not paused:
            player_country.gold += player_country.income
            day_count += 1
            engine.evaluate(player_country)

    # Renderowanie
    screen.fill((20, 24, 30))
    status_text = "PAUSE (SPACE)" if paused else "RUNNING (SPACE)"

    ui_lines = [
        f"Day: {day_count} | Status: {status_text}",
        f"Country: {player_country.name}",
        f"Gold: {player_country.gold} (+{player_country.income}/day)",
        f"Stability: {player_country.stability}%",
    ]
    for i, line in enumerate(ui_lines):
        txt_surface = font.render(line, True, (220, 220, 220))
        screen.blit(txt_surface, (20, 25 + i * 28))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()