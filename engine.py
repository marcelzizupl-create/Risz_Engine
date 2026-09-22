import json
from dataclasses import dataclass

@dataclass
class CountryState:
    name: str
    gold: int = 100
    stability: int = 50
    income: int = 5

class RuleEngine:
    def __init__(self, rules_path: str):
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def check_conditions(self, state: CountryState, conditions: dict) -> bool:
        if "stability_less_than" in conditions and state.stability >= conditions["stability_less_than"]:
            return False
        if "stability_greater_than" in conditions and state.stability <= conditions["stability_greater_than"]:
            return False
        if "gold_less_than" in conditions and state.gold >= conditions["gold_less_than"]:
            return False
        if "income_greater_than" in conditions and state.income <= conditions["income_greater_than"]:
            return False
        return True

    def apply_effects(self, state: CountryState, effects: dict):
        if "gold_add" in effects:
            state.gold += effects["gold_add"]
        if "stability_add" in effects:
            state.stability = max(0, min(100, state.stability + effects["stability_add"]))

    def evaluate(self, state: CountryState):
        for rule in self.rules:
            if self.check_conditions(state, rule["conditions"]):
                print(f"Event triggered: {rule['title']}")
                self.apply_effects(state, rule["effects"])
        