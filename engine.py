import json
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class Province:
    id: int
    name: str
    color: Tuple[int, int, int]
    owner: str
    tax: int

@dataclass
class Army:
    id: int
    owner: str
    province_id: int
    strength: int = 1000

@dataclass
class CountryState:
    tag: str
    name: str
    color: Tuple[int, int, int]
    gold: int = 100
    stability: int = 50
    income: int = 0

class StrategyEngine:
    def __init__(self, provinces_path: str, events_path: str, countries_path: str):
        self.provinces: Dict[int, Province] = {}
        self.color_to_province: Dict[Tuple[int, int, int], Province] = {}
        self.countries: Dict[str, CountryState] = {}
        self.events: List[dict] = []
        self.fired_events: set[str] = set()
        
        self.active_event: Optional[dict] = None
        self.ai_logs: List[str] = []

        # System armii
        self.armies: List[Army] = []
        self._next_army_id = 1

        # Graf sąsiedztwa prowincji: 1 <-> 2 <-> 3
        self.adjacency: Dict[int, List[int]] = {
            1: [2],
            2: [1, 3],
            3: [2]
        }

        self._load_countries(countries_path)
        self._load_provinces(provinces_path)
        self._load_events(events_path)

        # Na start dajemy po 1 armii każdemu państwu
        self.recruit_army("Crown", 1, free=True)
        self.recruit_army("Rebels", 3, free=True)

    def _load_countries(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                country = CountryState(
                    tag=item["tag"],
                    name=item["name"],
                    color=tuple(item["color"]),
                    gold=item.get("gold", 100),
                    stability=item.get("stability", 50)
                )
                self.countries[country.tag] = country

    def _load_provinces(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                color = tuple(item["color"])
                prov = Province(
                    id=item["id"],
                    name=item["name"],
                    color=color,
                    owner=item["owner"],
                    tax=item["tax"]
                )
                self.provinces[prov.id] = prov
                self.color_to_province[color] = prov

    def _load_events(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.events = json.load(f)

    def recalculate_incomes(self):
        for country in self.countries.values():
            country.income = 0
            
        for prov in self.provinces.values():
            if prov.owner in self.countries:
                self.countries[prov.owner].income += prov.tax

    def recruit_army(self, tag: str, province_id: int, cost: int = 40, free: bool = False) -> Optional[Army]:
        """Rekrutuje armię w danej prowincji i zwraca instancję Army."""
        country = self.countries.get(tag)
        prov = self.provinces.get(province_id)
        if not country or not prov:
            return None
        
        if not free and country.gold < cost:
            return None

        if not free:
            country.gold -= cost

        new_army = Army(
            id=self._next_army_id,
            owner=tag,
            province_id=province_id,
            strength=1000
        )
        self._next_army_id += 1
        self.armies.append(new_army)
        return new_army

    def move_army(self, army_id: int, target_province_id: int) -> Tuple[bool, str]:
        """Przesuwa armię i rozstrzyga walkę lub okupację."""
        army = next((a for a in self.armies if a.id == army_id), None)
        if not army:
            return False, "Army not found."

        if target_province_id not in self.adjacency.get(army.province_id, []):
            return False, "Not an adjacent province!"

        target_prov = self.provinces.get(target_province_id)
        if not target_prov:
            return False, "Invalid destination."

        army.province_id = target_province_id

        # Sprawdzenie wrogich armii w docelowej prowincji
        enemy_armies = [a for a in self.armies if a.province_id == target_province_id and a.owner != army.owner]
        if enemy_armies:
            defender = enemy_armies[0]
            if army.strength >= defender.strength:
                army.strength -= int(defender.strength * 0.6)
                self.armies.remove(defender)
                msg = f"{army.owner} won the battle against {defender.owner}!"
            else:
                defender.strength -= int(army.strength * 0.6)
                self.armies.remove(army)
                msg = f"{defender.owner} defended against {army.owner}!"
            return True, msg

        # Przejęcie wrogiej prowincji pod nieobecność garnizonu
        if target_prov.owner != army.owner:
            target_prov.owner = army.owner
            self.recalculate_incomes()
            return True, f"{army.owner} occupied {target_prov.name}!"

        return True, "Army moved."

    def develop_province(self, prov_id: int, cost: int = 30) -> bool:
        prov = self.provinces.get(prov_id)
        if not prov:
            return False
        owner = self.countries.get(prov.owner)
        if owner and owner.gold >= cost:
            owner.gold -= cost
            prov.tax += 2
            self.recalculate_incomes()
            return True
        return False

    def get_province_display_color(self, prov: Province, mode: str) -> Tuple[int, int, int]:
        if mode == "POLITICAL":
            owner = self.countries.get(prov.owner)
            return owner.color if owner else (80, 80, 80)
        elif mode == "ECONOMIC":
            intensity = min(255, max(40, prov.tax * 16))
            return (30, intensity, 40)
        return prov.color

    def check_conditions(self, state: CountryState, conditions: dict) -> bool:
        if "stability_less_than" in conditions and state.stability >= conditions["stability_less_than"]:
            return False
        if "stability_greater_than" in conditions and state.stability <= conditions["stability_greater_than"]:
            return False
        if "gold_less_than" in conditions and state.gold >= conditions["gold_less_than"]:
            return False
        if "gold_greater_than" in conditions and state.gold <= conditions["gold_greater_than"]:
            return False
        return True

    def apply_effects(self, state: CountryState, effects: dict):
        if "gold_add" in effects:
            state.gold += effects["gold_add"]
        if "stability_add" in effects:
            state.stability = max(0, min(100, state.stability + effects["stability_add"]))

    def evaluate_events(self, state: CountryState) -> bool:
        if self.active_event is not None:
            return False

        for event in self.events:
            event_id = event.get("id")
            if event.get("one_time", False) and event_id in self.fired_events:
                continue

            if self.check_conditions(state, event.get("conditions", {})):
                self.active_event = event
                if event_id:
                    self.fired_events.add(event_id)
                return True
        return False

    def resolve_event_choice(self, player_tag: str, option_index: int):
        if not self.active_event:
            return
        options = self.active_event.get("options", [])
        if 0 <= option_index < len(options):
            choice = options[option_index]
            player = self.countries.get(player_tag)
            if player:
                self.apply_effects(player, choice.get("effects", {}))
        self.active_event = None

    def process_ai(self, player_tag: str) -> bool:
        """AI rekrutuje i rusza swoimi armiami w stronę wroga."""
        map_changed = False
        for tag, country in self.countries.items():
            if tag == player_tag:
                continue

            ai_armies = [a for a in self.armies if a.owner == tag]
            owned_provinces = [p for p in self.provinces.values() if p.owner == tag]

            # Rekrutacja wojska przez AI
            if country.gold >= 40 and owned_provinces and len(ai_armies) < 2:
                spawn = random.choice(owned_provinces)
                if self.recruit_army(tag, spawn.id, cost=40):
                    self.ai_logs.append(f"{country.name} recruited 1000 soldiers in {spawn.name}.")

            # Marsz armii AI
            for army in ai_armies:
                neighbors = self.adjacency.get(army.province_id, [])
                if neighbors:
                    enemy_neighbors = [nid for nid in neighbors if self.provinces[nid].owner != tag]
                    target = random.choice(enemy_neighbors) if enemy_neighbors else random.choice(neighbors)
                    success, msg = self.move_army(army.id, target)
                    if success:
                        self.ai_logs.append(msg)
                        map_changed = True
                        break

        return map_changed

    def tick(self, player_tag: str) -> Tuple[bool, bool]:
        self.recalculate_incomes()
        for country in self.countries.values():
            country.gold += country.income

        map_updated = self.process_ai(player_tag)

        player = self.countries.get(player_tag)
        event_triggered = False
        if player:
            event_triggered = self.evaluate_events(player)

        return event_triggered, map_updated