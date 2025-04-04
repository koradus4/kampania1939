import random
import sys
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageDraw, ImageTk, ImageFont
import json

# Stałe ograniczające zasoby
MAX_ECONOMIC_POINTS = 5000
MAX_SUPPLY_POINTS = 2000

class EconomySystem:
    def __init__(self):
        """Inicjalizuje system ekonomii z domyślnymi wartościami dla każdej nacji."""
        self.nations = {
            "Polska": {
                "economic_points": 1200,
                "supply_points": 800,
                "bases": [
                    {"coords": (5, 5), "supply_limit": 300},
                    {"coords": (10, 10), "supply_limit": 500}
                ],
                "history": ["Rozpoczęcie gry: Polska ma 1200 punktów ekonomicznych i 800 punktów zaopatrzenia."]
            },
            "Niemcy": {
                "economic_points": 2000,
                "supply_points": 1500,
                "bases": [
                    {"coords": (15, 15), "supply_limit": 400},
                    {"coords": (20, 20), "supply_limit": 600}
                ],
                "history": ["Rozpoczęcie gry: Niemcy mają 2000 punktów ekonomicznych i 1500 punktów zaopatrzenia."]
            }
        }

    def get_nation_data(self, nation):
        """Zwraca dane ekonomiczne dla danej nacji."""
        return self.nations.get(nation, {})

    def display_status(self, nation):
        """Zwraca tekstowy status ekonomii dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        return f"Punkty ekonomiczne: {data['economic_points']}, Punkty zaopatrzenia: {data['supply_points']}"

    def modify_economic_points(self, nation, amount):
        """Modyfikuje punkty ekonomiczne o podaną wartość dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['economic_points'] += amount
        if data['economic_points'] < 0:
            data['economic_points'] = 0
        if data['economic_points'] > MAX_ECONOMIC_POINTS:
            data['economic_points'] = MAX_ECONOMIC_POINTS
        return f"Punkty ekonomiczne zmienione o {amount}. Nowa wartość: {data['economic_points']}"

    def modify_supply_points(self, nation, amount):
        """Modyfikuje punkty zaopatrzenia o podaną wartość dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['supply_points'] += amount
        if data['supply_points'] > MAX_SUPPLY_POINTS:
            data['supply_points'] = MAX_SUPPLY_POINTS
        if data['supply_points'] < 0:
            data['supply_points'] = 0
        print(f"Punkty zaopatrzenia zmienione o {amount}. Nowa wartość: {data['supply_points']}")

    def reset_economy(self, nation):
        """Resetuje punkty ekonomiczne i zaopatrzenia do wartości początkowych dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['economic_points'] = 1000
        data['supply_points'] = 500
        print(f"Ekonomia dla {nation} została zresetowana do wartości początkowych.")

    def add_income(self, nation, amount):
        """Dodaje przychód do punktów ekonomicznych dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['economic_points'] += amount
        if data['economic_points'] > MAX_ECONOMIC_POINTS:
            data['economic_points'] = MAX_ECONOMIC_POINTS
        data['history'].append(f"Przychód: {amount}. Nowa wartość punktów ekonomicznych: {data['economic_points']}")
        print(f"Przychód: {amount}. Nowa wartość punktów ekonomicznych: {data['economic_points']}")

    def add_expense(self, nation, amount):
        """Odlicza wydatek od punktów ekonomicznych dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['economic_points'] -= amount
        if data['economic_points'] < 0:
            data['economic_points'] = 0
        data['history'].append(f"Wydatki: {amount}. Nowa wartość punktów ekonomicznych: {data['economic_points']}")
        print(f"Wydatki: {amount}. Nowa wartość punktów ekonomicznych: {data['economic_points']}")

    def produce_supply(self, nation, cost, amount):
        """Konwertuje punkty ekonomiczne na dodatkowe punkty zaopatrzenia dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        if data['economic_points'] >= cost:
            data['economic_points'] -= cost
            data['supply_points'] += amount
            if data['supply_points'] > MAX_SUPPLY_POINTS:
                data['supply_points'] = MAX_SUPPLY_POINTS
            print(f"Wyprodukowano {amount} punktów zaopatrzenia kosztem {cost} punktów ekonomicznych dla {nation}.")
        else:
            print(f"Nie wystarczająca liczba punktów ekonomicznych dla {nation}! Wymagane: {cost}, dostępne: {data['economic_points']}")

    def pay_unit_maintenance(self, nation, cost_per_unit, unit_count):
        """Pobiera punkty zaopatrzenia za utrzymanie określonej liczby jednostek dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        total_cost = cost_per_unit * unit_count
        if data['supply_points'] >= total_cost:
            data['supply_points'] -= total_cost
            data['history'].append(f"Koszt utrzymania {unit_count} jednostek: {total_cost}. Pozostałe punkty zaopatrzenia: {data['supply_points']}")
            print(f"Koszt utrzymania {unit_count} jednostek: {total_cost}. Pozostałe punkty zaopatrzenia: {data['supply_points']}")
        else:
            data['history'].append(f"Nie wystarczająca liczba punktów zaopatrzenia dla {nation}! Wymagane: {total_cost}, dostępne: {data['supply_points']}")
            print(f"Nie wystarczająca liczba punktów zaopatrzenia dla {nation}! Wymagane: {total_cost}, dostępne: {data['supply_points']}")

    def calculate_maintenance(self, nation, units):
        """Symuluje pobór zaopatrzenia przez każdą jednostkę z najbliższej bazy dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        units_with_distance = []
        for unit in units:
            result = self.find_nearest_base(nation, unit['x'], unit['y'])
            if result is not None:
                nearest_base, distance = result
                units_with_distance.append({
                    "unit": unit,
                    "distance": distance,
                    "nearest_base": nearest_base
                })
        units_with_distance.sort(key=lambda u: u["distance"])

        for entry in units_with_distance:
            unit = entry["unit"]
            distance = entry["distance"]
            nearest_base = entry["nearest_base"]
            distance_cost = int(distance) * unit['maintenance_cost']

            if nearest_base["supply_limit"] >= distance_cost:
                nearest_base["supply_limit"] -= distance_cost
                print(f"Jednostka {unit['name']} (nacja: {nation}) pobrała {distance_cost} pkt zaopatrzenia z bazy {nearest_base['coords']} (odległość: {distance:.2f}).")
            else:
                print(f"Baza {nearest_base['coords']} nie ma wystarczającego zaopatrzenia dla jednostki {unit['name']} (nacja: {nation}).")

    def generate_report(self, nation):
        """Generuje raport ekonomiczny dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"

        report = (
            f"=== Raport Ekonomiczny: {nation} ===\n"
            f"Punkty ekonomiczne: {data['economic_points']}\n"
            f"Punkty zaopatrzenia: {data['supply_points']}\n"
            f"\n--- Bazy ---\n"
        )
        for base in data["bases"]:
            report += f"Baza na {base['coords']} z limitem zaopatrzenia {base['supply_limit']}\n"

        return report

    def process_turn(self, nation, income, cost_per_unit, unit_count):
        """Przetwarza turę dla danej nacji."""
        print(f"\n=== Przetwarzanie tury dla {nation} ===")
        self.add_income(nation, income)
        self.pay_unit_maintenance(nation, cost_per_unit, unit_count)
        self.random_event(nation)
        self.generate_report(nation)

    def random_event(self, nation):
        """Losuje wydarzenie ekonomiczne dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        events = [
            ("Kryzys gospodarczy", -500, 0),
            ("Boom gospodarczy", 500, 0),
            ("Niedobór zaopatrzenia", 0, -200),
            ("Dostawa zaopatrzenia", 0, 200),
        ]
        event_name, economic_change, supply_change = random.choice(events)
        data['history'].append(f"Wydarzenie: {event_name}. Zmiana punktów ekonomicznych: {economic_change}, zmiana punktów zaopatrzenia: {supply_change}")
        print(f"\n=== Wydarzenie dla {nation}: {event_name} ===")
        self.modify_economic_points(nation, economic_change)
        self.modify_supply_points(nation, supply_change)

    def show_history(self, nation):
        """Wyświetla historię ekonomicznych zdarzeń dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        print(f"\n=== Historia Ekonomii dla {nation} ===")
        for entry in data['history']:
            print(entry)

    def add_base(self, nation, x, y, supply_limit=100):
        """Dodaje bazę zaopatrzenia dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['bases'].append({"coords": (x, y), "supply_limit": supply_limit})
        if __name__ == "__main__":
            print(f"Dodano bazę dla {nation} na współrzędnych ({x}, {y}) z limitem zaopatrzenia {supply_limit}.")

    def add_key_point(self, nation, x, y, point_type, value):
        """Dodaje kluczowy punkt na mapie dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        data['bases'].append({"coords": (x, y), "type": point_type, "value": value})
        print(f"Dodano kluczowy punkt '{point_type}' dla {nation} na współrzędnych ({x}, {y}) o wartości {value}.")

    def calculate_distance(self, x1, y1, x2, y2):
        """Oblicza odległość euklidesową między dwoma punktami."""
        return ((x2 - x1) ** 2 + (y1 - y2) ** 2) ** 0.5

    def find_nearest_base(self, nation, unit_x, unit_y):
        """Znajduje najbliższą bazę danej nacji względem pozycji jednostki."""
        data = self.get_nation_data(nation)
        if not data or not data['bases']:
            print(f"Brak baz dla nacji {nation}.")
            return None
        nearest_base = min(
            data['bases'],
            key=lambda base: self.calculate_distance(unit_x, unit_y, base["coords"][0], base["coords"][1])
        )
        distance = self.calculate_distance(unit_x, unit_y, nearest_base["coords"][0], nearest_base["coords"][1])
        print(f"Najbliższa baza dla {nation} znajduje się na {nearest_base['coords']} w odległości {distance:.2f}.")
        return nearest_base, distance

    def check_supply(self, unit, nearest_base):
        """Sprawdza, czy najbliższa baza posiada zaopatrzenie dla jednostki."""
        if nearest_base['supply_limit'] < unit['supply_needed']:
            print(f"Baza {nearest_base['coords']} nie ma wystarczającego zaopatrzenia dla jednostki {unit['name']} (nacja: {unit['nation']}).")
            return False
        return True

    def calculate_support_from_allies(self, nation, allies):
        """Oblicza wsparcie od sojuszników dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        total_support = 0
        for ally, max_support in allies.items():
            roll = random.randint(1, 100)
            support = int(max_support * (roll / 100.0))
            total_support += support
            print(f"Sojusznik {ally} przyznał {support} punktów ekonomicznych dla {nation} (rzut: {roll}).")
        self.add_income(nation, total_support)

    def spend_economic_points(self, nation, amount, description=""):
        """Odejmowanie punktów ekonomicznych dla danej nacji."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        if amount > data['economic_points']:
            print(f"Nie można wydać {amount} punktów ekonomicznych dla {nation}. Dostępne: {data['economic_points']}.")
            return
        data['economic_points'] -= amount
        data['history'].append(f"Wydano {amount} punktów ekonomicznych dla {nation}. Opis: {description}. Pozostało: {data['economic_points']}")
        print(f"Wydano {amount} punktów ekonomicznych dla {nation}. Opis: {description}. Pozostało: {data['economic_points']}")

    def load_key_points(self, file_path):
        """Wczytuje kluczowe punkty z pliku JSON."""
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                self.key_points = data.get("key_points", {})
                print(f"Wczytano {len(self.key_points)} kluczowych punktów z pliku {file_path}.")
        except FileNotFoundError:
            print(f"Plik {file_path} nie został znaleziony.")
            self.key_points = {}
        except json.JSONDecodeError:
            print(f"Błąd dekodowania JSON w pliku {file_path}.")
            self.key_points = {}

    def capture_key_point(self, nation, hex_id):
        """Obsługuje zdobycie kluczowego punktu przez daną nację."""
        data = self.get_nation_data(nation)
        if not data:
            return f"Brak danych dla nacji: {nation}"
        if hex_id in self.key_points:
            key_point = self.key_points[hex_id]
            point_value = key_point["value"]
            self.add_income(nation, point_value)
            print(f"Nacja {nation} zdobyła kluczowy punkt '{key_point['type']}' na heksie {hex_id} i otrzymała {point_value} punktów ekonomicznych.")
            del self.key_points[hex_id]
        else:
            print(f"Kluczowy punkt na heksie {hex_id} nie istnieje lub został już zdobyty.")

# Test podstawowych funkcji EconomySystem (do uruchomienia modułu samodzielnie)
if __name__ == "__main__":
    economy = EconomySystem()

    # Test 1: Wczytywanie kluczowych punktów
    economy.load_key_points("c:\\Users\\klif\\kampania_wrzesniowa_1939\\gui\\mapa_cyfrowa\\dane_terenow_hexow_working.json")
    print("=== Test 1: Wczytywanie kluczowych punktów ===")
    print(f"Wczytano kluczowe punkty: {economy.key_points}\n")

    # Test 2: Modyfikacja punktów ekonomicznych
    print("=== Test 2: Modyfikacja punktów ekonomicznych ===")
    print(economy.modify_economic_points("Polska", 500))  # Dodaj 500 punktów
    print(economy.modify_economic_points("Polska", -200))  # Odejmij 200 punktów
    print(economy.display_status("Polska"), "\n")

    # Test 3: Dodawanie przychodu
    print("=== Test 3: Dodawanie przychodu ===")
    economy.add_income("Polska", 300)
    print(economy.display_status("Polska"), "\n")

    # Test 4: Wydatki ekonomiczne
    print("=== Test 4: Wydatki ekonomiczne ===")
    economy.spend_economic_points("Polska", 400, "Zakup zaopatrzenia")
    print(economy.display_status("Polska"), "\n")

    # Test 5: Punkty zaopatrzenia
    print("=== Test 5: Punkty zaopatrzenia ===")
    economy.modify_supply_points("Polska", 200)  # Dodaj 200 punktów zaopatrzenia
    economy.modify_supply_points("Polska", -100)  # Odejmij 100 punktów zaopatrzenia
    print(economy.display_status("Polska"), "\n")

    # Test 6: Produkcja zaopatrzenia
    print("=== Test 6: Produkcja zaopatrzenia ===")
    economy.produce_supply("Polska", 300, 150)  # Koszt 300 punktów ekonomicznych, produkcja 150 punktów zaopatrzenia
    print(economy.display_status("Polska"), "\n")

    # Test 7: Utrzymanie jednostek
    print("=== Test 7: Utrzymanie jednostek ===")
    economy.pay_unit_maintenance("Polska", 50, 5)  # Koszt 50 za jednostkę, 5 jednostek
    print(economy.display_status("Polska"), "\n")

    # Test 8: Kluczowe punkty
    print("=== Test 8: Kluczowe punkty ===")
    economy.capture_key_point("Polska", "4_3")  # Zdobycie kluczowego punktu
    print(economy.display_status("Polska"), "\n")

    # Test 9: Dodawanie bazy zaopatrzenia
    print("=== Test 9: Dodawanie bazy zaopatrzenia ===")
    economy.add_base("Polska", 10, 20, 500)
    print(f"Bazy zaopatrzenia: {economy.get_nation_data('Polska')['bases']}\n")

    # Test 10: Zdarzenia losowe
    print("=== Test 10: Zdarzenia losowe ===")
    economy.random_event("Polska")
    print(economy.display_status("Polska"), "\n")

    # Test 11: Raport ekonomiczny
    print("=== Test 11: Raport ekonomiczny ===")
    print(economy.generate_report("Polska"), "\n")

    # Test 12: Historia ekonomii
    print("=== Test 12: Historia ekonomii ===")
    economy.show_history("Polska")
