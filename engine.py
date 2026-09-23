import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class Province:
    id: int
    name: str
    color: Tuple[int, int, int]
    owner: str
    tax: int

@dataclass
class CountryState:
    name: str
    gold: int = 100
    stability: int = 50
    income: int = 0

class StrategyEngine:
    def __init__(self, provinces_path: str, events_path: str):
        self.provinces: Dict[int, Province] = {}
        self.color_to_province: Dict[Tuple[int, int, int], Province] = {}
        self.countries: Dict[str, CountryState] = {}
        self.events: List[dict] = []
        self.fired_events: set[str] = set()
        self.last_event_title: Optional[str] = None

        self._load_provinces(provinces_path)
        self._load_events(events_path)

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

                # Inicjalizacja państw wykrytych w prowincjach
                if prov.owner not in self.countries:
                    self.countries[prov.owner] = CountryState(name=prov.owner)

    def _load_events(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.events = json.load(f)

    def recalculate_incomes(self):
        """Przelicza dochód państwa jako sumę podatków z kontrolowanych prowincji."""
        for country in self.countries.values():
            country.income = 0
            
        for prov in self.provinces.values():
            if prov.owner in self.countries:
                self.countries[prov.owner].income += prov.tax

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

    def evaluate_events(self, state: CountryState):
        for event in self.events:
            event_id = event.get("id")
            if event.get("one_time", False) and event_id in self.fired_events:
                continue

            if self.check_conditions(state, event.get("conditions", {})):
                self.last_event_title = event.get("title", event_id)
                self.apply_effects(state, event.get("effects", {}))
                if event_id:
                    self.fired_events.add(event_id)

    def tick(self, player_tag: str):
        """Pojedynczy krok symulacji (np. 1 dzień)."""
        self.recalculate_incomes()
        for country in self.countries.values():
            country.gold += country.income

        player = self.countries.get(player_tag)
        if player:
            self.evaluate_events(player)