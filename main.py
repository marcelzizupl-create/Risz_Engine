import pygame
from engine import StrategyEngine

pygame.init()
WIDTH, HEIGHT = 800, 600
MAP_HEIGHT = 380
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Risz Engine - Armies & Warfare")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 14)
title_font = pygame.font.SysFont("Consolas", 18, bold=True)
button_font = pygame.font.SysFont("Consolas", 13, bold=True)

# 1. Inicjalizacja silnika
engine = StrategyEngine("provinces.json", "events.json", "countries.json")
PLAYER_TAG = "Crown"
player = engine.countries[PLAYER_TAG]
engine.recalculate_incomes()

# 2. Geometria prowincji
PROVINCE_SHAPES = {
    1: [(80, 50), (220, 40), (280, 110), (260, 200), (190, 260), (110, 250), (50, 160)],
    2: [(280, 110), (450, 70), (520, 160), (480, 270), (340, 290), (260, 200)],
    3: [(480, 270), (520, 160), (680, 120), (740, 240), (670, 330), (490, 340), (340, 290)]
}

PROVINCE_CENTERS = {
    1: (160, 160),
    2: (370, 180),
    3: (580, 220)
}

id_map = pygame.Surface((WIDTH, MAP_HEIGHT))
id_map.fill((10, 20, 35))
for prov_id, points in PROVINCE_SHAPES.items():
    prov = engine.provinces[prov_id]
    pygame.draw.polygon(id_map, prov.color, points)

display_map = pygame.Surface((WIDTH, MAP_HEIGHT))
current_mapmode = "POLITICAL"

def render_display_map():
    display_map.fill((15, 25, 40))
    for prov_id, points in PROVINCE_SHAPES.items():
        prov = engine.provinces[prov_id]
        color = engine.get_province_display_color(prov, current_mapmode)
        pygame.draw.polygon(display_map, color, points)
        pygame.draw.polygon(display_map, (30, 35, 45), points, 2)

render_display_map()

selected_province = None
selected_army_id = None

# Przyciski dolne
dev_button_rect = pygame.Rect(470, 440, 150, 36)
recruit_button_rect = pygame.Rect(630, 440, 150, 36)

def get_army_rects():
    """Zwraca słownik {army.id: pygame.Rect} z uwzględnieniem stosu jednostek w prowincji."""
    rects = {}
    province_armies_count = {}
    for army in engine.armies:
        p_id = army.province_id
        if p_id in PROVINCE_CENTERS:
            base_x, base_y = PROVINCE_CENTERS[p_id]
            offset_idx = province_armies_count.get(p_id, 0)
            province_armies_count[p_id] = offset_idx + 1

            # Przesunięcie kafelków armii, gdy jest ich kilka w jednej prowincji
            x = base_x - 30 + (offset_idx * 15)
            y = base_y - 15 + (offset_idx * 15)
            rects[army.id] = pygame.Rect(x, y, 60, 28)
    return rects

# 3. Pętla symulacji
TICK_EVENT = pygame.USEREVENT + 1
TICK_RATE_MS = 1500
pygame.time.set_timer(TICK_EVENT, TICK_RATE_MS)

paused = False
day_count = 1
running = True

POPUP_WIDTH, POPUP_HEIGHT = 500, 260
popup_rect = pygame.Rect((WIDTH - POPUP_WIDTH) // 2, (HEIGHT - POPUP_HEIGHT) // 2, POPUP_WIDTH, POPUP_HEIGHT)

while running:
    mouse_pos = pygame.mouse.get_pos()
    army_rects = get_army_rects()

    event_option_rects = []
    if engine.active_event:
        options = engine.active_event.get("options", [])
        start_y = popup_rect.y + 140
        for i in range(len(options)):
            rect = pygame.Rect(popup_rect.x + 30, start_y + i * 45, POPUP_WIDTH - 60, 35)
            event_option_rects.append(rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not engine.active_event:
                paused = not paused
            elif event.key == pygame.K_1:
                current_mapmode = "POLITICAL"
                render_display_map()
            elif event.key == pygame.K_2:
                current_mapmode = "ECONOMIC"
                render_display_map()

        # LPM - Zaznaczanie i przyciski
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if engine.active_event:
                for idx, opt_rect in enumerate(event_option_rects):
                    if opt_rect.collidepoint(mx, my):
                        engine.resolve_event_choice(PLAYER_TAG, idx)
                        break
            else:
                # 1. Sprawdzamy, czy kliknięto w armię gracza (odwrócona kolejność = od wierzchu)
                clicked_army_id = None
                for army in reversed(engine.armies):
                    if army.owner == PLAYER_TAG and army.id in army_rects:
                        if army_rects[army.id].collidepoint(mx, my):
                            clicked_army_id = army.id
                            break

                if clicked_army_id is not None:
                    selected_army_id = clicked_army_id
                else:
                    # 2. Kliknięcie w przyciski akcji
                    if selected_province and selected_province.owner == PLAYER_TAG:
                        if dev_button_rect.collidepoint(mx, my):
                            if engine.develop_province(selected_province.id, cost=30):
                                render_display_map()
                        elif recruit_button_rect.collidepoint(mx, my):
                            new_army = engine.recruit_army(PLAYER_TAG, selected_province.id, cost=40)
                            if new_army:
                                selected_army_id = new_army.id  # Od razu zaznacz nową armię!

                    # 3. Kliknięcie w mapę prowincji
                    if 0 <= mx < WIDTH and 0 <= my < MAP_HEIGHT:
                        pixel = id_map.get_at((mx, my))
                        rgb = (pixel.r, pixel.g, pixel.b)
                        selected_province = engine.color_to_province.get(rgb)
                        selected_army_id = None  # Odznaczenie armii przy kliknięciu tła

        # PPM - Rozkaz marszu dla zaznaczonej armii
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx, my = event.pos
            if selected_army_id and 0 <= mx < WIDTH and 0 <= my < MAP_HEIGHT:
                pixel = id_map.get_at((mx, my))
                rgb = (pixel.r, pixel.g, pixel.b)
                target_prov = engine.color_to_province.get(rgb)
                if target_prov:
                    success, msg = engine.move_army(selected_army_id, target_prov.id)
                    engine.ai_logs.append(msg)
                    if success:
                        render_display_map()

        elif event.type == TICK_EVENT and not paused and not engine.active_event:
            day_count += 1
            has_new_event, map_changed = engine.tick(PLAYER_TAG)
            if map_changed:
                render_display_map()
            if has_new_event:
                paused = True

    # --- RENDEROWANIE ---
    screen.fill((25, 25, 30))
    screen.blit(display_map, (0, 0))

    if selected_province and selected_province.id in PROVINCE_SHAPES:
        pygame.draw.polygon(screen, (255, 255, 255), PROVINCE_SHAPES[selected_province.id], 3)

    # Rysowanie armii
    for army in engine.armies:
        if army.id in army_rects:
            rect = army_rects[army.id]
            owner_state = engine.countries.get(army.owner)
            base_col = owner_state.color if owner_state else (100, 100, 100)

            is_sel = (army.id == selected_army_id)
            border_col = (255, 255, 255) if is_sel else (20, 20, 20)
            border_w = 3 if is_sel else 1

            pygame.draw.rect(screen, base_col, rect, border_radius=4)
            pygame.draw.rect(screen, border_col, rect, border_w, border_radius=4)

            txt = button_font.render(f"{army.strength}", True, (20, 20, 20) if base_col[0] > 180 else (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))

    # Górny HUD
    pygame.draw.rect(screen, (10, 10, 14), (0, 0, WIDTH, 35))
    status_txt = "EVENT" if engine.active_event else ("PAUSED" if paused else "RUNNING")
    hud_text = f"Day: {day_count} [{status_txt}] | Tag: {player.name} | Gold: {player.gold} (+{player.income}/d) | Stab: {player.stability}%"
    screen.blit(font.render(hud_text, True, (240, 240, 240)), (15, 9))

    # Dolny panel
    panel_y = MAP_HEIGHT
    pygame.draw.rect(screen, (18, 18, 22), (0, panel_y, WIDTH, HEIGHT - panel_y))
    pygame.draw.line(screen, (60, 60, 70), (0, panel_y), (WIDTH, panel_y), 2)

    modes_text = f"Controls: LPM = Select | PPM = Move Army | [1] Political [2] Economic"
    screen.blit(font.render(modes_text, True, (100, 200, 255)), (25, panel_y + 15))

    if selected_province:
        country_obj = engine.countries.get(selected_province.owner)
        owner_name = country_obj.name if country_obj else selected_province.owner

        lines = [
            f"Province: {selected_province.name} (ID: {selected_province.id})",
            f"Owner: {owner_name} [{selected_province.owner}]",
            f"Tax Income: {selected_province.tax} gold / tick"
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, (220, 220, 220)), (25, panel_y + 45 + i * 22))

        if selected_province.owner == PLAYER_TAG:
            can_dev = player.gold >= 30
            d_col = (40, 120, 60) if can_dev else (70, 70, 70)
            pygame.draw.rect(screen, d_col, dev_button_rect, border_radius=4)
            pygame.draw.rect(screen, (180, 180, 180), dev_button_rect, 1, border_radius=4)
            dt = button_font.render("Develop [30g]", True, (255, 255, 255))
            screen.blit(dt, dt.get_rect(center=dev_button_rect.center))

            can_rec = player.gold >= 40
            r_col = (40, 90, 160) if can_rec else (70, 70, 70)
            pygame.draw.rect(screen, r_col, recruit_button_rect, border_radius=4)
            pygame.draw.rect(screen, (180, 180, 180), recruit_button_rect, 1, border_radius=4)
            rt = button_font.render("Recruit (1k) [40g]", True, (255, 255, 255))
            screen.blit(rt, rt.get_rect(center=recruit_button_rect.center))
    else:
        screen.blit(font.render("Click a province or army to interact.", True, (130, 130, 130)), (25, panel_y + 45))

    if engine.ai_logs:
        last_log = f"News: {engine.ai_logs[-1]}"
        screen.blit(font.render(last_log, True, (255, 170, 70)), (25, panel_y + 130))

    # Modal eventu
    if engine.active_event:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (24, 26, 32), popup_rect, border_radius=8)
        pygame.draw.rect(screen, (180, 150, 80), popup_rect, 2, border_radius=8)

        ev_title = engine.active_event.get("title", "Event")
        screen.blit(title_font.render(ev_title, True, (240, 210, 110)), (popup_rect.x + 25, popup_rect.y + 20))
        ev_desc = engine.active_event.get("description", "")
        screen.blit(font.render(ev_desc, True, (220, 220, 220)), (popup_rect.x + 25, popup_rect.y + 60))

        options = engine.active_event.get("options", [])
        for idx, opt_rect in enumerate(event_option_rects):
            is_hover = opt_rect.collidepoint(mouse_pos)
            btn_bg = (55, 60, 75) if is_hover else (38, 42, 54)
            border_c = (200, 180, 100) if is_hover else (100, 110, 130)

            pygame.draw.rect(screen, btn_bg, opt_rect, border_radius=4)
            pygame.draw.rect(screen, border_c, opt_rect, 1, border_radius=4)

            label = options[idx].get("label", "Option")
            opt_text = button_font.render(label, True, (240, 240, 240))
            screen.blit(opt_text, opt_text.get_rect(center=opt_rect.center))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()