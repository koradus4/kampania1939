import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json
import math
import shutil
import glob
import time
from gui.map_editor import MapEditor
from gui.token_editor import TokenEditor
from engine.economy import EconomySystem

# Ścieżki do zasobów
MAP_PATH = os.path.join("gui", "mapa_cyfrowa", "mapa_hex.jpg")
MAP_DATA_PATH = os.path.join("gui", "mapa_cyfrowa", "mapa_dane.json")
TOKENS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokeny")

# Klasa reprezentująca panel z żetonami - można go przeciągać
class TokenPanel(ttk.Frame):
    def __init__(self, parent, title, nation, initial_x=0, initial_y=0):
        super().__init__(parent)
        
        self.parent = parent
        self.nation = nation
        self.title = title
        self.minimized = False
        self.tokens = []  # Lista żetonów w panelu
        self.tokens_locked = False  # Flag indicating if tokens are locked (confirmed)
        
        # Ustawienie początkowej pozycji
        self.x = initial_x
        self.y = initial_y
        
        # Główna ramka panelu
        self.frame = ttk.Frame(parent, borderwidth=2, relief="raised")
        self.frame.place(x=self.x, y=self.y)
        
        # Nagłówek panelu (można za niego przeciągać)
        self.header = ttk.Frame(self.frame)
        self.header.pack(side="top", fill="x")
        self.header.configure(style='Header.TFrame')
        
        # Tło nagłówka - zmiana koloru na bardziej militarny
        self.header_bg = tk.Frame(self.header, bg="#5D7B4C", height=30)  # Ciemniejsza zieleń militarna
        self.header_bg.pack(fill="x", expand=True)
        self.header_bg.place(x=0, y=0, relwidth=1, height=30)
        
        # Tytuł panelu
        self.title_label = ttk.Label(self.header, text=title, font=("Arial", 10, "bold"), 
                                    background="#5D7B4C", foreground="white")
        self.title_label.pack(side="left", padx=5, pady=3)
        self.title_label.lift()  # Upewnienie się, że jest na wierzchu
        
        # Przyciski w nagłówku
        self.min_button_text = tk.StringVar(value="Nie pokazuj dost. żetonów")
        self.min_button = ttk.Button(self.header, textvariable=self.min_button_text,
                                    command=self.toggle_minimize, width=20, style="Military.TButton")
        self.min_button.pack(side="right", padx=5, pady=3)
        
        # Kontener o stałej wysokości i szerokości
        self.container = ttk.Frame(self.frame, height=200, width=200, style="Panel.TFrame")
        self.container.pack(fill="both", expand=True)
        self.container.pack_propagate(False)  # Wymuszenie stałych wymiarów
        
        # Canvas z paskiem przewijania dla zawartości - poprawiony kontrast tła
        self.canvas = tk.Canvas(self.container, background="#E1DBC5")  # Lekko beżowe tło
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Wewnętrzna ramka dla zawartości przewijalnego obszaru - poprawione tło
        self.content_frame = ttk.Frame(self.canvas, style="Content.TFrame")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Przycisk zatwierdzania pozycji żetonów - poprawiony kontrast
        self.accept_button = ttk.Button(self.content_frame, text="Zatw. poz. żetonów",
                                       command=self.confirm_token_positions, width=20, style="Military.TButton")
        self.accept_button.pack(pady=5)
        
        # Dodanie przykładowej etykiety z informacją - poprawiona widoczność
        self.info_label = ttk.Label(self.content_frame, text=f"Żetony {self.nation} (0)", 
                                   wraplength=180, background="#E1DBC5", foreground="#333333")
        self.info_label.pack(pady=5)
        
        # Konfiguracja zdarzeń
        self.header.bind("<ButtonPress-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<ButtonRelease-1>", self.stop_drag)
        
        self.title_label.bind("<ButtonPress-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.on_drag)
        self.title_label.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Dodanie bindingów do tła nagłówka
        self.header_bg.bind("<ButtonPress-1>", self.start_drag)
        self.header_bg.bind("<B1-Motion>", self.on_drag)
        self.header_bg.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Obsługa przewijania myszką
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.content_frame.bind("<Configure>", self.on_frame_configure)
        
        # Zmiana rozmiaru żetonów do dostosowania do heksów
        self.token_size = 60  # Dostosowany rozmiar żetonów
        self.token_images = []  # Lista do przechowywania referencji do obrazków
        
        # Dodajemy flagę do wykrywania, czy panel może przyjmować żetony
        self.can_receive_tokens = True
        
        # Dodajemy binding, aby wykryć upuszczenie żetonu na panel
        self.frame.bind("<ButtonRelease-1>", self.on_token_drop)
        self.content_frame.bind("<ButtonRelease-1>", self.on_token_drop)
        self.canvas.bind("<ButtonRelease-1>", self.on_token_drop)
    
    def on_canvas_configure(self, event):
        """Dostosowuje szerokość okna przewijania do szerokości canvasa"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def on_frame_configure(self, event):
        """Aktualizuje region przewijania na podstawie rozmiaru zawartości"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_mousewheel(self, event):
        """Obsługuje przewijanie myszką"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def start_drag(self, event):
        """Rozpoczyna przeciąganie panelu"""
        # Zapisz aktualną pozycję kursora względem ekranu
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        
        # Zapisz aktualną pozycję panelu
        self.drag_panel_start_x = self.frame.winfo_x()
        self.drag_panel_start_y = self.frame.winfo_y()
        
        print(f"Rozpoczęto przeciąganie panelu {self.title} z pozycji ({self.drag_panel_start_x}, {self.drag_panel_start_y})")
        return "break"  # Zatrzymaj propagację zdarzenia
    
    def on_drag(self, event):
        """Obsługuje przeciąganie panelu"""
        # Oblicz przesunięcie względem początkowej pozycji kursora
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        # Oblicz nową pozycję panelu
        new_x = self.drag_panel_start_x + dx
        new_y = self.drag_panel_start_y + dy
        
        # Ograniczenia, aby panel nie wyszedł poza okno
        if new_x < 0: new_x = 0
        if new_y < 0: new_y = 0
        if new_x > self.parent.winfo_width() - 100: new_x = self.parent.winfo_width() - 100
        if new_y > self.parent.winfo_height() - 50: new_y = self.parent.winfo_height() - 50
            
        # Zapis nowej pozycji i przemieszczenie ramki
        self.x, self.y = new_x, new_y
        self.frame.place(x=new_x, y=new_y)
        
        return "break"  # Zatrzymaj propagację zdarzenia
    
    def stop_drag(self, event):
        """Kończy przeciąganie panelu"""
        print(f"Zakończono przeciąganie panelu {self.title}. Nowa pozycja: ({self.x}, {self.y})")
        return "break"  # Zatrzymaj propagację zdarzenia
    
    def toggle_minimize(self):
        """Przełącza stan minimalizacji panelu"""
        self.minimized = not self.minimized
        
        if self.minimized:
            self.container.pack_forget()
            self.min_button_text.set("Pokaż dostępne żetony")
        else:
            self.container.pack(fill="both", expand=True)
            self.min_button_text.set("Nie pokazuj dost. żetonów")
    
    def confirm_token_positions(self):
        """Obsługuje zatwierdzenie pozycji żetonów z podwójnym potwierdzeniem"""
        # Jeśli żetony są już zablokowane, nie rób nic
        if self.tokens_locked:
            messagebox.showinfo("Informacja", f"Pozycje żetonów {self.nation} zostały już zatwierdzone.")
            return
            
        response = messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz zatwierdzić pozycje żetonów {self.nation}?",
            icon='question'
        )
        if response:
            response2 = messagebox.askyesno(
                "Potwierdzenie",
                "Ta operacja jest nieodwracalna!\nCzy na pewno chcesz kontynuować?",
                icon='warning'
            )
            if response2:
                # Zablokuj możliwość operowania żetonami
                self.tokens_locked = True
                # Zmień wygląd przycisku na nieaktywny
                self.accept_button.config(state="disabled")
                
                # Powiadom interfejs gry o zablokowaniu żetonów
                if hasattr(self.parent, 'lock_nation_tokens') and callable(getattr(self.parent, 'lock_nation_tokens')):
                    self.parent.lock_nation_tokens(self.nation)
                    
                messagebox.showinfo("Sukces", 
                    f"Zatwierdzono pozycje żetonów {self.nation}.\n"
                    "Żetony zostały zablokowane do startu gry.")
    
    def add_token(self, token_data):
        """Dodaje żeton do panelu"""
        # Sprawdź czy żeton o tej samej nazwie już istnieje
        for token in self.tokens:
            if token["name"] == token_data["name"]:
                # Token już istnieje, nie dodawaj ponownie
                print(f"Żeton {token_data['name']} już istnieje w panelu {self.title}, nie dodawany ponownie")
                return
        
        # Dodaj żeton tylko jeśli nie istnieje
        self.tokens.append(token_data)
        self.update_tokens_display()
    
    def token_exists(self, token_name):
        """Sprawdza czy żeton o podanej nazwie istnieje w panelu"""
        for token in self.tokens:
            if token["name"] == token_name:
                return True
        return False
    
    def update_tokens_display(self):
        """Aktualizuje wyświetlanie żetonów w panelu"""
        # Uaktualnij liczbę żetonów w etykiecie
        self.info_label.config(text=f"Żetony {self.nation} ({len(self.tokens)})")
        
        # Wyczyść obecne żetony z kontenera
        for widget in self.content_frame.winfo_children():
            if widget != self.accept_button and widget != self.info_label:
                widget.destroy()
        
        # Wyczyść referencje do obrazków
        self.token_images = []
        
        # Dodaj żetony jako obrazki z etykietami
        for token in self.tokens:
            try:
                # Sprawdź czy jest dostępny obraz
                if "path" in token and os.path.exists(token["path"]):
                    # Sprawdź czy istnieje token_data.json w podfolderze tokena
                    token_dir = os.path.dirname(token["path"])
                    token_name = os.path.basename(token_dir)
                    
                    # Stwórz ramkę dla tokena - poprawione tło
                    token_frame = ttk.Frame(self.content_frame, style="TokenItem.TFrame")
                    token_frame.pack(fill="x", padx=5, pady=5)
                    
                    # Wczytaj i przeskaluj obraz
                    img = Image.open(token["path"])
                    img = img.resize((self.token_size, self.token_size), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.token_images.append(photo)  # Zapobiegaj garbage collection
                    
                    # Dodaj obraz z etykietą
                    lbl = ttk.Label(token_frame, image=photo)
                    lbl.image = photo  # Trzymaj referencję
                    lbl.pack(side="left")
                    
                    # Dodaj etykietę z nazwą tokena - poprawiona widoczność
                    name_lbl = ttk.Label(token_frame, text=token_name, wraplength=120,
                                        background="#E1DBC5", foreground="#333333")
                    name_lbl.pack(side="left", padx=5)
                    
                    # Dodaj obsługę przeciągania na mapę
                    lbl.bind("<ButtonPress-1>", lambda e, t=token: self.start_token_drag(e, t))
                    lbl.bind("<B1-Motion>", self.drag_token)
                    lbl.bind("<ButtonRelease-1>", self.drop_token)
                    
            except Exception as e:
                print(f"Błąd podczas wyświetlania tokena {token['name']} jeśli 'name' in token else 'nieznany'}}: {e}")
        
        # Aktualizuj obszar przewijania
        self.content_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def start_token_drag(self, event, token):
        """Rozpoczyna przeciąganie tokena"""
        # Sprawdź czy żetony są zablokowane
        if self.tokens_locked:
            return "break"  # Zatrzymaj propagację zdarzenia
            
        self._drag_data = {"x": event.x, "y": event.y, "token": token}
        
        # Sprawdź czy istnieje metoda place_token w rodzicu
        if hasattr(self.parent, 'start_place_token') and callable(getattr(self.parent, 'start_place_token')):
            self.parent.start_place_token(token)
    
    def drag_token(self, event):
        """Obsługuje przeciąganie tokena"""
        if hasattr(self.parent, 'drag_place_token') and callable(getattr(self.parent, 'drag_place_token')):
            self.parent.drag_place_token(event)
    
    def drop_token(self, event):
        """Upuszcza token na mapie"""
        if hasattr(self.parent, 'place_token_on_hex') and callable(getattr(self.parent, 'place_token_on_hex')):
            self.parent.place_token_on_hex(event)
        self._drag_data = None
    
    def on_token_drop(self, event):
        """Obsługuje upuszczenie żetonu na panel"""
        # Sprawdź czy żetony są zablokowane
        if self.tokens_locked:
            return "break"  # Zatrzymaj propagację zdarzenia
            
        # Sprawdź, czy panel może przyjmować żetony i czy coś jest przeciągane
        if self.can_receive_tokens and hasattr(self.parent, 'current_dragging_map_token') and self.parent.current_dragging_map_token:
            token_data = self.parent.current_dragging_map_token
            
            # Sprawdź, czy token jest z tej samej nacji co panel
            if token_data["nation"] == self.nation:
                # Sprawdź, czy tura jest aktywna dla tej nacji
                if not self.parent.is_turn_active(self.nation):
                    messagebox.showerror(
                        "Błąd",
                        "Nie możesz umieszczać żetonów tej nacji w tej turze."
                    )
                    return "break"

                # Usuń token z mapy i dodaj go z powrotem do panelu
                self.parent.remove_token_from_map(token_data["hex_id"])
                print(f"Zwrócono żeton {token_data['name']} do panelu {self.title}")
            
            # Wyczyść informacje o przeciąganym żetonie
            self.parent.current_dragging_map_token = None
            
            # Dla stabilności, zaktualizuj widok
            self.update()
            return "break"  # Zatrzymaj propagację zdarzenia
        
        return None  # Propaguj zdarzenie dalej
    
    def remove_token_by_name(self, token_name):
        """Usuwa żeton z panelu na podstawie jego nazwy i aktualizuje wyświetlanie"""
        for i, token in enumerate(self.tokens):
            if token["name"] == token_name:
                del self.tokens[i]
                self.update_tokens_display()
                print(f"Usunięto żeton {token_name} z panelu {self.title}")
                return True
        return False

    def lock_tokens(self):
        """Blokuje możliwość operowania żetonami w tym panelu"""
        self.tokens_locked = True
        self.accept_button.config(state="disabled")
        print(f"Panel {self.title}: żetony zablokowane")
    
    def unlock_tokens(self):
        """Odblokowuje możliwość operowania żetonami w tym panelu"""
        self.tokens_locked = False
        self.accept_button.config(state="normal")
        print(f"Panel {self.title}: żetony odblokowane")

class GameInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.economy_system = EconomySystem()  # Inicjalizacja systemu ekonomicznego
        self.current_turn_nation = "Polska"   # Domyślnie zaczyna Polska
        self.title("Wrzesień 1939 – Prototyp")
        self.geometry("1280x800")
        self.resizable(True, True)
        
        # Maksymalizuj okno na starcie
        self.state('zoomed')
        
        # Ustaw kolorystykę
        self.configure(bg="darkolivegreen")
        
        # Wywołanie panelu startowego
        self.init_start_panel()
        self.current_turn = "Gracz 1"  # Domyślnie zaczyna Gracz 1

    def init_start_panel(self):
        """Tworzy panel startowy z opcjami wyboru nacji i przyciskiem Start"""
        self.start_panel = ttk.Frame(self, style="Panel.TFrame")
        self.start_panel.pack(fill="both", expand=True)

        # Tytuł gry
        title_label = ttk.Label(
            self.start_panel, 
            text="Wrzesień 1939 – Wybór nacji", 
            font=("Arial", 20, "bold"), 
            style="TLabel"
        )
        title_label.pack(pady=20)

        # Opcje wyboru nacji dla gracza 1
        player1_label = ttk.Label(self.start_panel, text="Gracz 1:", font=("Arial", 12))
        player1_label.pack(pady=5)
        self.player1_nation = tk.StringVar(value="Polska")
        player1_dropdown = ttk.Combobox(
            self.start_panel, 
            textvariable=self.player1_nation, 
            values=["Polska", "Niemcy"], 
            state="readonly"
        )
        player1_dropdown.pack()

        # Opcje wyboru nacji dla gracza 2
        player2_label = ttk.Label(self.start_panel, text="Gracz 2:", font=("Arial", 12))
        player2_label.pack(pady=5)
        self.player2_nation = tk.StringVar(value="Niemcy")
        player2_dropdown = ttk.Combobox(
            self.start_panel, 
            textvariable=self.player2_nation, 
            values=["Polska", "Niemcy"], 
            state="readonly"
        )
        player2_dropdown.pack()

        # Opcja wyboru sterowania AI dla gracza 2
        self.player2_ai = tk.BooleanVar(value=False)
        player2_ai_checkbox = ttk.Checkbutton(
            self.start_panel, 
            text="Gracz 2 sterowany przez AI", 
            variable=self.player2_ai
        )
        player2_ai_checkbox.pack(pady=5)

        # Przycisk Start
        start_button = ttk.Button(
            self.start_panel, 
            text="Start", 
            command=self.start_game, 
            style="Military.TButton"
        )
        start_button.pack(pady=20)

    def start_game(self):
        """Przechodzi do głównego panelu gry"""
        # Sprawdź, czy wybrano różne nacje
        if self.player1_nation.get() == self.player2_nation.get():
            messagebox.showerror(
                "Błąd wyboru nacji",
                "Obaj gracze nie mogą wybrać tej samej nacji. Wybierz różne nacje."
            )
            return

        # Zapisanie wyboru nacji graczy
        self.player1_choice = self.player1_nation.get()
        self.player2_choice = self.player2_nation.get()

        # Wyświetlenie wyborów w konsoli
        print(f"Gracz 1 wybrał: {self.player1_choice}")
        print(f"Gracz 2 wybrał: {self.player2_choice}")

        # Usunięcie panelu startowego
        self.start_panel.destroy()

        # Inicjalizacja głównego panelu gry
        self.define_styles()

        # Dane heksów (przykładowe na wypadek braku pliku danych)
        self.hex_data = {
            # Dodajemy przykładowe dane dla testów
            "5_5": {"nazwa": "Las", "teren": "Leśny", "obiekty": "Bunkier", "jednostki": "2 Pułk Piechoty"},
            "6_5": {"nazwa": "Wzgórze 123", "teren": "Wzgórze", "obiekty": "Okopy", "jednostki": "Brak"},
            "7_7": {"nazwa": "Dolina", "teren": "Równina", "obiekty": "Most", "jednostki": "1 Dywizja Pancerna"},
            "10_10": {"nazwa": "Warszawa", "teren": "Miasto", "obiekty": "Brama miejska", "jednostki": "Garnizon"},
            # Dodaj więcej danych testowych dla różnych heksów
            "12_8": {"nazwa": "Rzeka Wisła", "teren": "Woda", "obiekty": "Brak", "jednostki": "Brak"},
            "15_5": {"nazwa": "Linia kolejowa", "teren": "Infrastruktura", "obiekty": "Tory", "jednostki": "Transport wojskowy"},
        }

        # Wczytaj dane mapy z pliku JSON jeśli istnieje
        self.hex_centers = {}
        self.map_data = None  # Przechowujemy całe dane mapy
        self.terrain_types = {}  # Typy terenu
        self.debug_mode = True  # Tryb debugowania - pokaż więcej informacji

        # Parametry heksów (będą nadpisane danymi z JSON jeśli dostępne)
        self.hex_width = 60
        self.hex_height = 52
        self.hex_horiz_offset = 45
        self.hex_vert_offset = 39
        self.hex_size = 30  # Podstawowy rozmiar heksu

        # Ładowanie mapy
        try:
            self.map_image = Image.open(MAP_PATH)
            print(f"Mapa wczytana: {MAP_PATH}, rozmiar: {self.map_image.size}")
        except FileNotFoundError:
            print("[BŁD] Nie znaleziono pliku mapy:", MAP_PATH)
            messagebox.showerror("Błąd", f"Nie znaleziono pliku mapy: {MAP_PATH}")
            self.quit()
            return

        self.map_scale = 2
        self.map_zoomed = self.map_image.resize(
            (self.map_image.width * self.map_scale, self.map_image.height * self.map_scale),
            Image.Resampling.LANCZOS
        )
        self.tk_map = ImageTk.PhotoImage(self.map_zoomed)
        print(f"Mapa przeskalowana: {self.map_zoomed.size}")

        # Wczytaj dane mapy - po załadowaniu obrazu, przed utworzeniem interfejsu
        self.wczytaj_dane_mapy()

        self.selected_hex = None
        self.selected_hex_highlight = None

        # UI: górny pasek (tura, przyciski)
        self.top_frame = ttk.Frame(self, height=50, style="Panel.TFrame")
        self.top_frame.pack(side="top", fill="x")
        self.init_top_panel()

        # UI: prawy panel
        self.right_frame = ttk.Frame(self, width=200, style="Panel.TFrame")
        self.right_frame.pack(side="right", fill="y")

        # UI: prawy panel na informacje o heksie
        self.hex_info_frame = ttk.LabelFrame(self.right_frame, text="Informacje o heksie", style="MilitaryLabel.TLabelframe")
        self.hex_info_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Kontener o stałej wysokości 200 pikseli
        self.hex_info_container = ttk.Frame(self.hex_info_frame, height=200, style="Panel.TFrame")
        self.hex_info_container.pack(fill="x", expand=True)
        self.hex_info_container.pack_propagate(False)  # Wymuszenie stałej wysokości

        # Panel z przewijaniem dla zawartości
        self.hex_info_text = tk.Text(self.hex_info_container, wrap="word", state="disabled",
                                    bg="#E1DBC5", fg="#333333")  # Beżowe tło, ciemny tekst
        self.hex_info_scrollbar = ttk.Scrollbar(self.hex_info_container, orient="vertical", command=self.hex_info_text.yview)
        self.hex_info_text.configure(yscrollcommand=self.hex_info_scrollbar.set)

        self.hex_info_scrollbar.pack(side="right", fill="y")
        self.hex_info_text.pack(side="left", fill="both", expand=True)

        # Domyślna informacja w panelu
        self.update_hex_info(None)

        # Nowa sekcja: Informacje ekonomiczne
        self.economic_info_frame = ttk.LabelFrame(self.right_frame, text="Informacje ekonomiczne", style="MilitaryLabel.TLabelframe")
        self.economic_info_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Kontener o stałej wysokości
        self.economic_info_container = ttk.Frame(self.economic_info_frame, height=200, style="Panel.TFrame")
        self.economic_info_container.pack(fill="x", expand=True)
        self.economic_info_container.pack_propagate(False)

        # Panel z przewijaniem dla zawartości ekonomicznej
        self.economic_info_text = tk.Text(self.economic_info_container, wrap="word", state="disabled",
                                          bg="#E1DBC5", fg="#333333")
        self.economic_info_scrollbar = ttk.Scrollbar(self.economic_info_container, orient="vertical", command=self.economic_info_text.yview)
        self.economic_info_text.configure(yscrollcommand=self.economic_info_scrollbar.set)

        self.economic_info_scrollbar.pack(side="right", fill="y")
        self.economic_info_text.pack(side="left", fill="both", expand=True)

        # Wyświetlenie domyślnego raportu ekonomicznego
        self.update_economic_info()

        # UI: środek – mapa na canvasie (rozszerzona na całą szerokość)
        self.center_frame = ttk.Frame(self, style="Panel.TFrame")
        self.center_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.center_frame, bg="black",
            scrollregion=(0, 0, self.tk_map.width(), self.tk_map.height())
        )
        self.hbar = tk.Scrollbar(self.center_frame, orient="horizontal", command=self.canvas.xview)
        self.vbar = tk.Scrollbar(self.center_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.hbar.pack(side="bottom", fill="x")
        self.vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.map_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_map)

        # Dodanie paneli dla żetonów
        self.polish_panel = TokenPanel(self, "Żetony Polskie", "polskie", 10, 500)
        self.german_panel = TokenPanel(self, "Żetony Niemieckie", "niemieckie", 1070, 500)
        
        # Ustaw początkowy stan blokady żetonów odpowiednio do pierwszej tury
        if self.current_turn_nation == "Polska":
            self.polish_tokens_locked = False
            self.german_tokens_locked = True
            self.polish_panel.unlock_tokens()
            self.german_panel.lock_tokens()
        else:
            self.polish_tokens_locked = True
            self.german_tokens_locked = False
            self.polish_panel.lock_tokens()
            self.german_panel.unlock_tokens()

        try:
            # Wczytaj żetony z folderu - dodajemy obsługę błędów
            self.load_tokens_from_folder()
        except Exception as e:
            print(f"[BŁĄD] Podczas wczytywania żetonów: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showwarning(
                "Problem z wczytaniem żetonów",
                "Wystąpił problem podczas wczytywania żetonów. Niektóre obrazki mogą nie być dostępne.\n\nRozpocnij grę od nowa lub sprawdź logi."
            )

        # Rysuj heksy na podstawie danych z JSON
        if self.hex_centers:
            self.draw_hex_grid()
        # Dodanie nowego atrybutu do śledzenia aktualnie przeciąganego tokena
        self.current_dragging_token = None
        self.current_dragging_map_token = None
        self.token_preview = None
        self.drag_threshold = 5  # Próg ruchu myszy, aby uznać za przeciąganie
        self.placed_token_images = {}  # Słownik przechowujący umieszczone tokeny

        # Dodanie zdarzeń myszy do obsługi mapy
        self.canvas.bind("<ButtonPress-1>", self.on_hex_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_hex_click)

    def define_styles(self):
        """Definicja stylów dla elementów interfejsu"""
        style = ttk.Style()
        
        # Definicja stylu dla nagłówka panelu
        style.configure('Header.TFrame', background='#5D7B4C')  # Ciemniejsza zieleń militarna
        
        # Podstawowe ramki i panele
        style.configure("Panel.TFrame", background="darkolivegreen")
        
        # Dodanie stylu dla ramek zawartości żetonów
        style.configure("Content.TFrame", background="#E1DBC5")
        style.configure("TokenItem.TFrame", background="#E1DBC5")
        
        # Etykiety - poprawa widoczności
        style.configure("TLabel", background="darkolivegreen", foreground="white")
        
        # Specjalne etykiety dla żetonów
        style.configure("Token.TLabel", background="#E1DBC5", foreground="#333333")
        
        # Ramki z etykietami
        style.configure("MilitaryLabel.TLabelframe", background="darkolivegreen")
        style.configure("MilitaryLabel.TLabelframe.Label", background="darkolivegreen", 
                       foreground="white", font=("Arial", 10, "bold"))
        
        # Przyciski - poprawa widoczności tekstu
        style.configure("Military.TButton", background="saddlebrown", foreground="black")
        style.map("Military.TButton",
                 background=[('active', '#8B6534'), ('pressed', '#654321')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # Styl dla zwykłych przycisków - poprawa kontrastu
        style.configure("TButton", background="saddlebrown", foreground="black")
        style.map("TButton",
                 background=[('active', '#8B6534'), ('pressed', '#654321')],
                 foreground=[('active', 'white'), ('pressed', 'white')])

    def init_top_panel(self):
        """Inicjalizuje panel górny z przyciskami i informacją o turze"""
        # Rozszerzenie etykiety z turą na całą szerokość
        self.turn_label = ttk.Label(
            self.top_frame, 
            text=f"Tura: {self.get_current_turn_nation()}",
            font=("Arial", 14, "bold"), 
            anchor="center"  # Wyśrodkowanie tekstu
        )
        self.turn_label.pack(fill="x", padx=10, pady=5)  # Wypełnienie całej szerokości
        
        # Przyciski z poprawionym kontrastem tekstu
        end_turn_button = ttk.Button(self.top_frame, text="Zakończ turę", command=self.end_turn, style="Military.TButton")
        end_turn_button.pack(side="left", padx=5)
        
        save_btn = ttk.Button(self.top_frame, text="Zapisz grę", command=self.save_game, style="Military.TButton")
        save_btn.pack(side="left", padx=5)
        
        load_btn = ttk.Button(self.top_frame, text="Wczytaj grę", command=self.load_game, style="Military.TButton")
        load_btn.pack(side="left", padx=5)
        
        btn3 = ttk.Button(self.top_frame, text="Wyjście", command=self.quit, style="Military.TButton")
        btn3.pack(side="right", padx=10)

    def get_current_turn_nation(self):
        """Zwraca nazwę nacji na podstawie aktualnej tury."""
        if self.current_turn == "Gracz 1":
            return self.player1_choice
        elif self.current_turn == "Gracz 2":
            return self.player2_choice
        return "Nieznana nacja"

    def end_turn(self):
        """Zakończenie tury i przełączenie na kolejną nację."""
        # Przetwarzanie ekonomii
        self.economy_system.process_turn(
            nation=self.current_turn_nation,
            income=100,  # Przykładowy dochód, dostosuj do logiki gry
            cost_per_unit=10,  # Przykładowy koszt na jednostkę
            unit_count=len(self.placed_token_images)  # Liczba jednostek na mapie
        )
        
        # Określ obecną i następną nację
        previous_nation = self.current_turn_nation
        
        # Zmiana tury
        if self.current_turn_nation == "Polska":
            self.current_turn_nation = "Niemcy"
            self.current_turn = "Gracz 2"
            # Odblokuj żetony niemieckie i zablokuj polskie
            self.polish_tokens_locked = True
            self.german_tokens_locked = False
            # Synchronizuj stan z panelami żetonów
            self.polish_panel.lock_tokens()
            self.german_panel.unlock_tokens()
            print("Zablokowano żetony polskie, odblokowano żetony niemieckie")
        else:
            self.current_turn_nation = "Polska"
            self.current_turn = "Gracz 1"
            # Odblokuj żetony polskie i zablokuj niemieckie
            self.polish_tokens_locked = False
            self.german_tokens_locked = True
            # Synchronizuj stan z panelami żetonów
            self.polish_panel.unlock_tokens()
            self.german_panel.lock_tokens()
            print("Zablokowano żetony niemieckie, odblokowano żetony polskie")
        
        # Aktualizacja informacji ekonomicznych dla nowej nacji
        self.update_economic_info()
        
        # Aktualizacja innych elementów interfejsu (np. tury)
        self.turn_label.config(text=f"Tura: {self.current_turn_nation}")

    def on_hex_press(self, event):
        """Zapamiętuje początkową pozycję kliknięcia na heksie"""
        self.click_start = (event.x, event.y)

    def on_hex_click(self, event):
        """Obsługa kliknięcia na heks"""
        # Sprawdzenie czy kliknięcie było w tym samym miejscu (z małym marginesem błędu)
        if hasattr(self, 'click_start'):
            dx = event.x - self.click_start[0]
            dy = event.y - self.click_start[1]
            if abs(dx) > self.drag_threshold or abs(dy) > self.drag_threshold:
                # Jeśli było zbyt duże przesunięcie, ignorujemy kliknięcie
                return
        
        # Oblicz współrzędne względem canvasa (uwzględniając scrollowanie)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        print(f"Kliknięcie na pozycji: ({canvas_x}, {canvas_y})")
        
        # Znajdź najbliższy heks jeśli mamy dane z pliku JSON
        clicked_hex = None
        if self.hex_centers:
            # Znajdź najbliższy heks na podstawie odległości od środka
            min_distance = float('inf')
            for hex_id, (center_x, center_y) in self.hex_centers.items():
                # Skaluj pozycje zgodnie z map_scale
                scaled_x = center_x * self.map_scale
                scaled_y = center_y * self.map_scale
                
                # Oblicz odległość od kliknięcia do środka heksu
                distance = ((scaled_x - canvas_x) ** 2 + (scaled_y - canvas_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    clicked_hex = hex_id
            
            # Wypisz informacje o znalezionym heksie
            if clicked_hex:
                center_x, center_y = self.hex_centers[clicked_hex]
                scaled_x = center_x * self.map_scale
                scaled_y = center_y * self.map_scale
                print(f"Najbliższy heks: {clicked_hex} w odległości {min_distance:.2f}px")
                print(f"Środek heksu: ({center_x}, {center_y}) -> skalowany: ({scaled_x}, {scaled_y})")
            
            # Użyj heksu tylko jeśli kliknięcie jest wystarczająco blisko środka
            max_valid_distance = self.hex_size * self.map_scale  # Maksymalna akceptowalna odległość
            if min_distance > max_valid_distance:
                print(f"Kliknięcie zbyt daleko od środka heksu ({min_distance:.2f} > {max_valid_distance:.2f})")
                clicked_hex = None
        else:
            print("Brak danych o pozycjach heksów, używanie starej metody...")
            # Jeśli nie mamy danych z JSON, użyj starej metody
            col = int(canvas_x / self.hex_horiz_offset)
            row = int(canvas_y / self.hex_vert_offset)
            # Korekta dla parzystych wierszy (przesunięcie o pół heksa)
            if row % 2 == 1:
                col = int((canvas_x - self.hex_horiz_offset/2) / self.hex_horiz_offset)
            clicked_hex = f"{col}_{row}"
            print(f"Wyliczony heks metodą matematyczną: {clicked_hex}")
        
        # Jeśli znaleziono heks
        if clicked_hex:
            self.selected_hex = clicked_hex
            
            # Pobierz dane heksu lub użyj domyślnych wartości
            hex_data = self.hex_data.get(clicked_hex, self.hex_defaults)
            
            # Wyświetl dane heksu w prawym panelu
            self.update_hex_info(hex_data)
            print(f"Dane dla heksu {clicked_hex}: {hex_data}")
            
            # Podświetl heks
            if clicked_hex in self.hex_centers:
                # Jeśli są wczytane dane o pozycjach
                center_x, center_y = self.hex_centers[clicked_hex]
                scaled_x = center_x * self.map_scale
                scaled_y = center_y * self.map_scale
                self.highlight_hex_at_position(scaled_x, scaled_y)
            else:
                # Stara metoda obliczania pozycji
                col, row = map(int, clicked_hex.split('_'))
                self.highlight_hex(col, row)

    def update_hex_info(self, hex_info):
        """Aktualizuje panel informacji o heksie z uwzględnieniem wszystkich dostępnych danych."""
        self.hex_info_text.config(state="normal")
        self.hex_info_text.delete(1.0, tk.END)
        
        if not hex_info or self.selected_hex is None:
            self.hex_info_text.insert(tk.END, "Wybierz heks aby zobaczyć informacje")
            self.hex_info_text.config(state="disabled")
            return
        
        # 1. Identyfikator i pozycja heksu
        self.hex_info_text.insert(tk.END, f"Heks: {self.selected_hex}\n", "header")
        
        # Dodaj informacje o pozycji heksu, jeśli dostępne
        if self.selected_hex in self.hex_centers:
            x, y = self.hex_centers[self.selected_hex]
            self.hex_info_text.insert(tk.END, f"Pozycja: X={x:.1f}, Y={y:.1f}\n", "position")
        
        # 2. Dane terenu i modyfikatory
        self.hex_info_text.insert(tk.END, "\nTeren:\n", "section")
        
        # Sprawdź czy heks ma specjalne modyfikatory terenu
        if "move_mod" in hex_info or "defense_mod" in hex_info:
            move_mod = hex_info.get("move_mod", self.hex_defaults.get("move_mod", 0))
            defense_mod = hex_info.get("defense_mod", self.hex_defaults.get("defense_mod", 0))
            self.hex_info_text.insert(tk.END, f"Modyfikator ruchu: {move_mod}\n")
            self.hex_info_text.insert(tk.END, f"Modyfikator obrony: {defense_mod}\n")
        
        # 3. Dodatkowe dane terenu
        for key, value in hex_info.items():
            if key not in ["move_mod", "defense_mod", "jednostki"]:
                self.hex_info_text.insert(tk.END, f"{key}: {value}\n")
        
        # 4. Dane żetonu/jednostki na heksie (jeśli istnieją)
        if "jednostki" in hex_info and hex_info["jednostki"] != "Brak":
            self.hex_info_text.insert(tk.END, "\nJednostka:\n", "section")
            self.hex_info_text.insert(tk.END, f"{hex_info['jednostki']}\n")
            
            # Pobierz dodatkowe dane jednostki
            unit_data = self.get_token_data_for_hex(self.selected_hex)
            if unit_data:
                for key, value in unit_data.items():
                    self.hex_info_text.insert(tk.END, f"{key}: {value}\n")
        
        # Formatowanie tekstu - poprawione kolory dla lepszej czytelności
        self.hex_info_text.tag_configure("header", font=("Arial", 10, "bold"), foreground="#004d00")  # Ciemniejsza zieleń
        self.hex_info_text.tag_configure("section", font=("Arial", 9, "bold"), foreground="#663300")  # Ciemniejszy brąz
        self.hex_info_text.tag_configure("position", foreground="#003366")  # Ciemniejszy niebieski
        self.hex_info_text.config(state="disabled")

    def get_token_data_for_hex(self, hex_id):
        """Pobiera dane żetonu znajdującego się na wskazanym heksie.
        Zwraca None jeśli na heksie nie ma żetonu.
        """
        # Sprawdzamy, czy na heksie znajduje się żeton
        if hex_id in self.placed_token_images:
            token_info = self.placed_token_images[hex_id]
            token_data = token_info["token_data"]
            
            # Jeśli token ma dodatkowe dane, zwracamy je
            if "data" in token_data:
                return token_data["data"]
            
            # Jeśli nie ma dodatkowych danych, tworzymy podstawowe informacje
            basic_info = {
                "typ": "Jednostka",
                "nazwa": token_data["name"]
            }
            
            # Dodać dodatkowe informacje na podstawie nazwy jednostki
            nazwa = token_data["name"].lower()
            if "pułk" in nazwa or "pulk" in nazwa:
                basic_info["typ"] = "Piechota"
                basic_info["siła"] = "4"
                basic_info["morale"] = "Standardowe"
            elif "dywizj" in nazwa:
                basic_info["typ"] = "Dywizja"
                basic_info["siła"] = "8"
                basic_info["morale"] = "Wysokie"
            elif "panc" in nazwa:
                basic_info["typ"] = "Pancerna"
                basic_info["siła"] = "8"
                basic_info["paliwo"] = "100%"
            elif "artyle" in nazwa:
                basic_info["typ"] = "Artyleria"
                basic_info["siła"] = "3"
                basic_info["zasięg"] = "2 heksy"
            return basic_info
        
        # Brak żetonu na heksie
        return None

    def highlight_hex(self, col, row):
        """Podświetla heks na mapie na podstawie kolumny i wiersza"""
        # Usuń poprzednie podświetlenie
        self.clear_highlight()
        
        # Oblicz pozycję środka heksu
        x = col * self.hex_horiz_offset
        y = row * self.hex_vert_offset
        
        if row % 2 == 1:
            x += self.hex_horiz_offset/2
        
        # Utwórz prostokąt wokół heksu (można zastąpić bardziej skomplikowanym kształtem)
        rect_size = min(self.hex_width, self.hex_height) / 2
        self.selected_hex_highlight = self.canvas.create_rectangle(
            x - rect_size, y - rect_size, 
            x + rect_size, y + rect_size,
            outline="yellow", width=2, tags="highlight"
        )

    def highlight_hex_at_position(self, x, y):
        """Podświetla heks na mapie na podstawie współrzędnych x i y"""
        # Usuń poprzednie podświetlenie
        self.clear_highlight()
        
        # Utwórz prostokąt wokół heksu
        rect_size = min(self.hex_width, self.hex_height) / 2
        self.selected_hex_highlight = self.canvas.create_rectangle(
            x - rect_size, y - rect_size, 
            x + rect_size, y + rect_size,
            outline="yellow", width=2, tags="highlight"
        )

    def clear_highlight(self):
        """Usuwa podświetlenie heksu"""
        if self.selected_hex_highlight:
            self.canvas.delete(self.selected_hex_highlight)
            self.selected_hex_highlight = None

    def save_game(self):
        """Zapisuje stan gry do pliku save_game.json wraz z kopiami obrazów żetonów"""
        print("[INFO] Zapisywanie gry...")
        save_folder = os.path.join(os.getcwd(), "saves")
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            print(f"Utworzono folder zapisu: {save_folder}")
        
        # Utwórz folder dla obrazów żetonów
        images_folder = os.path.join(save_folder, "images")
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)
            print(f"[INFO] Utworzono folder dla obrazów żetonów: {images_folder}")
        
        # Utwórz kopię zapasową istniejącego pliku zapisu
        save_file = os.path.join(save_folder, "save_game.json")
        if os.path.exists(save_file):
            backup_file = os.path.join(save_folder, "save_game_backup.json")
            try:
                shutil.copy2(save_file, backup_file)
                print(f"[INFO] Utworzono kopię zapasową poprzedniego pliku zapisu: {backup_file}")
            except Exception as e:
                print(f"[UWAGA] Nie udało się utworzyć kopii zapasowej: {e}")
        
        # Zapisz tokeny z kopiami obrazów
        placed_tokens = {}
        for hex_id, token_info in self.placed_token_images.items():
            token_data = token_info["token_data"]
            original_path = token_data["path"]
            token_name = token_data["name"]
            token_nation = token_data["nation"]
            
            # Utwórz unikalną nazwę dla kopii obrazu
            image_filename = f"{token_nation}_{token_name}_{hex_id}.png".replace(" ", "_")
            image_save_path = os.path.join(images_folder, image_filename)
            
            # Skopiuj obraz do folderu zapisu
            try:
                if os.path.exists(original_path):
                    shutil.copy2(original_path, image_save_path)
                    print(f"[INFO] Utworzono kopię obrazu dla tokena {token_name}: {image_save_path}")
                else:
                    print(f"[UWAGA] Nie znaleziono oryginału obrazu dla tokena {token_name}: {original_path}")
            except Exception as e:
                print(f"[BŁĄD] Podczas kopiowania obrazu tokena {token_name}: {e}")
                image_save_path = original_path  # W przypadku błędu, użyj oryginalnej ścieżki
            
            # Zapisz dane tokena z nową ścieżką względną
            rel_image_path = os.path.relpath(image_save_path, os.getcwd())
            placed_tokens[hex_id] = {
                "name": token_name,
                "nation": token_nation,
                "path": rel_image_path,
                "original_path": os.path.relpath(original_path, os.getcwd()) if os.path.exists(original_path) else ""
            }
        
        game_state = {
            "current_turn": self.current_turn,
            "placed_tokens": placed_tokens,
            "hex_data": self.hex_data
        }
        
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(game_state, f, indent=4, ensure_ascii=False)
        
        print(f"[INFO] Gra zapisana w pliku: {save_file}")
        messagebox.showinfo("Zapisywanie zakończone", f"Gra została zapisana w pliku: {save_file}")

    def load_game(self):
        """Wczytuje stan gry z pliku save_game.json"""
        print("[INFO] Wczytywanie gry...")
        save_folder = os.path.join(os.getcwd(), "saves")
        save_file = os.path.join(save_folder, "save_game.json")
        
        if not os.path.exists(save_file):
            messagebox.showerror(
                "Błąd wczytywania",
                f"Nie znaleziono pliku zapisu gry: {save_file}"
            )
            return
        
        try:
            # Wczytaj dane z pliku
            with open(save_file, "r", encoding="utf-8") as f:
                game_state = json.load(f)
            
            # Wyczyść istniejące dane i żetony z mapy
            self.clear_map()
            
            # Przywróć turę
            self.current_turn = game_state.get("current_turn", "Gracz 1")
            self.current_turn_nation = self.get_current_turn_nation()
            
            # Aktualizuj etykietę tury
            self.turn_label.config(text=f"Tura: {self.current_turn_nation}")
            
            # Przywróć dane heksów
            self.hex_data = game_state.get("hex_data", {})
            
            # Przywróć żetony na mapę
            placed_tokens = game_state.get("placed_tokens", {})
            tokens_placed = 0
            tokens_failed = 0
            error_list = []
            
            # Przechowuj listę nazw żetonów do usunięcia z paneli
            polish_tokens_to_remove = []
            german_tokens_to_remove = []
            
            # Umieść żetony na mapie
            for hex_id, token_data in placed_tokens.items():
                success = self.place_token_on_hex_from_load(hex_id, token_data)
                if success:
                    tokens_placed += 1
                    # Dodaj żeton do odpowiedniej listy do usunięcia
                    if token_data["nation"] == "polskie":
                        polish_tokens_to_remove.append(token_data["name"])
                    elif token_data["nation"] == "niemieckie":
                        german_tokens_to_remove.append(token_data["name"])
                else:
                    tokens_failed += 1
                    error_list.append(f"Heks {hex_id}: {token_data['name']} ({token_data['path']})")
            
            # Usuń żetony z paneli bocznych
            print("[INFO] Usuwanie żetonów z paneli bocznych, które są już na mapie...")
            for token_name in polish_tokens_to_remove:
                self.polish_panel.remove_token_by_name(token_name)
                print(f"[INFO] Usunięto żeton {token_name} z polskiego panelu")
                
            for token_name in german_tokens_to_remove:
                self.german_panel.remove_token_by_name(token_name)
                print(f"[INFO] Usunięto żeton {token_name} z niemieckiego panelu")
            
            # Ustaw blokady żetonów zgodnie z aktualną turą
            self.update_token_locks()
            
            # Aktualizuj informacje ekonomiczne
            self.update_economic_info()
            
            # Pokaż szczegółową informację o wyniku wczytywania
            message = f"Przywrócono grę z zapisu.\nPomyślnie wczytano {tokens_placed} żetonów."
            if tokens_failed > 0:
                message += f"\nNie udało się wczytać {tokens_failed} żetonów."
                message += "\n\nSzczegóły błędów można znaleźć w konsoli."
            
            message += f"\n\nAktualna tura: {self.current_turn_nation}"
            messagebox.showinfo("Wczytywanie zakończone", message)
            
            print(f"[INFO] Wczytano grę z pliku: {save_file}")
            print(f"[INFO] Wczytano {tokens_placed} żetonów, nie udało się wczytać {tokens_failed} żetonów")
            print(f"[INFO] Usunięto {len(polish_tokens_to_remove)} polskich i {len(german_tokens_to_remove)} niemieckich żetonów z paneli")
            
            if tokens_failed > 0 and tokens_placed > 0:
                response = messagebox.askyesno(
                    "Naprawić zapisy żetonów?",
                    f"Nie udało się wczytać {tokens_failed} żetonów. Czy chcesz zaktualizować plik zapisu z poprawionymi ścieżkami wczytanych tokenów?\n"
                    "UWAGA: Aktualny stan gry zostanie zapisany ponownie, nadpisując istniejący plik zapisu."
                )
                if response:
                    self.save_game()
                    messagebox.showinfo(
                        "Plik zapisu zaktualizowany",
                        "Plik zapisu został zaktualizowany z bieżącymi (poprawnymi) ścieżkami plików."
                    )
        
        except Exception as e:
            messagebox.showerror(
                "Błąd wczytywania",
                f"Wystąpił błąd podczas wczytywania gry:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def place_token_on_hex_from_load(self, hex_id, token_data):
        """
        Umieszcza token na heksie podczas wczytywania gry.
        Zmodyfikowana wersja która najpierw szuka kopii obrazu z zapisu.
        """
        try:
            # Sprawdź czy heks istnieje w danych mapy
            if hex_id not in self.hex_centers:
                print(f"[BŁĄD] Nie znaleziono heksu {hex_id} podczas wczytywania")
                return False
                    
            # Pobierz pozycję heksu
            center_x, center_y = self.hex_centers[hex_id]
            scaled_x = center_x * self.map_scale
            scaled_y = center_y * self.map_scale
            
            # Spróbuj znaleźć plik obrazu tokena
            image_path = token_data["path"]
            found_image = False
            
            # 1. Najpierw spróbuj użyć kopii zapisanej w folderze zapisu
            save_images_folder = os.path.join(os.getcwd(), "saves", "images")
            image_basename = os.path.basename(image_path)
            saved_image_path = os.path.join(save_images_folder, image_basename)
            
            if os.path.exists(saved_image_path):
                image_path = saved_image_path
                found_image = True
                print(f"[INFO] Znaleziono kopię obrazu tokena w folderze zapisu: {image_path}")
            
            # 2. Jeśli nie znaleziono kopii, spróbuj użyć bezpośrednio podanej ścieżki
            elif os.path.exists(image_path):
                found_image = True
                print(f"[INFO] Znaleziono token bezpośrednio: {image_path}")
            else:
                # 3. Jeśli nie istnieje, spróbuj zinterpretować ścieżkę jako względną od katalogu gry
                rel_path = os.path.join(os.getcwd(), image_path)
                if os.path.exists(rel_path):
                    image_path = rel_path
                    found_image = True
                    print(f"[INFO] Znaleziono token jako ścieżkę względną: {image_path}")
            
            # 4. Jeśli nadal nie znaleziono, spróbuj użyć oryginalnej ścieżki jeśli była zapisana
            if not found_image and "original_path" in token_data and token_data["original_path"]:
                original_path = os.path.join(os.getcwd(), token_data["original_path"])
                if os.path.exists(original_path):
                    image_path = original_path
                    found_image = True
                    print(f"[INFO] Znaleziono oryginalny obraz tokena: {image_path}")
            
            # 5. Jeśli nadal nie znaleziono, szukaj tokena po nazwie i nacji
            if not found_image:
                found_path = self.find_token_by_name(token_data["name"], token_data["nation"])
                if found_path:
                    image_path = found_path
                    found_image = True
                    print(f"[INFO] Znaleziono alternatywną ścieżkę do tokena: {image_path}")
            
            # Jeśli nie znaleziono obrazu tokena, zwróć błąd
            if not found_image:
                print(f"[BŁĄD] Nie znaleziono obrazu tokena: {token_data['path']}")
                return False
                    
            # Wczytaj i przeskaluj obraz
            img = Image.open(image_path)
            token_size = self.hex_size * self.map_scale * 1.5
            img = img.resize((int(token_size), int(token_size)), Image.LANCZOS)
            token_img = ImageTk.PhotoImage(img)
            
            # Umieść token na mapie
            token_id = self.canvas.create_image(scaled_x, scaled_y, image=token_img, tags=f"token_{hex_id}")
            
            # Utwórz obiekt danych tokena z zaktualizowaną ścieżką
            token_obj = {
                "name": token_data["name"],
                "path": image_path,  # Zaktualizuj ścieżkę do faktycznie używanego pliku
                "nation": token_data["nation"],
                "original_path": token_data.get("original_path", "")
            }
            
            # Zapisz referencję tokena
            self.placed_token_images[hex_id] = {
                "image": token_img,
                "image_id": token_id,
                "token_data": token_obj,
                "hex_id": hex_id
            }
            
            # Dodaj obsługę zdarzeń do tokena
            self.canvas.tag_bind(token_id, "<ButtonPress-1>", 
                               lambda e, hid=hex_id: self.start_drag_token_from_map(e, hid))
            
            # Aktualizuj dane heksu
            if hex_id not in self.hex_data:
                self.hex_data[hex_id] = {}
            self.hex_data[hex_id]["jednostki"] = token_data["name"]
            
            print(f"[INFO] Umieszczono token {token_data['name']} na heksie {hex_id} z zapisu")
            return True
        
        except Exception as e:
            print(f"[BŁĄD] Podczas umieszczania tokena na heksie {hex_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_place_token(self, token):
        """Rozpoczyna proces umieszczania tokena na mapie."""
        # Sprawdź, czy żetony tej nacji są zablokowane
        if self.is_nation_locked(token["nation"]):
            messagebox.showerror(
                "Blokada żetonów",
                f"Żetony {token['nation']} są zablokowane, nie można ich przesuwać w tej turze."
            )
            return
        
        # Sprawdź, czy token pochodzi z panelu zgodnego z aktualną turą
        if not self.is_turn_active(token["nation"]):
            messagebox.showerror(
                "Niewłaściwa tura",
                f"Nie możesz umieszczać żetonów {token['nation']} w turze {self.current_turn_nation}."
            )
            return

        self.current_dragging_token = token
        print(f"Rozpoczęto umieszczanie tokena: {token['name']}")

    def drag_place_token(self, event):
        """Obsługuje przeciąganie tokena po mapie"""
        if not self.current_dragging_token:
            return
        
        # Pobierz współrzędne myszy względem canvasa
        x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        
        # Usuń poprzedni podgląd
        if self.token_preview:
            self.canvas.delete(self.token_preview)
        
        # Stwórz nowy podgląd tokena na mapie
        if hasattr(self, 'token_preview_img'):
            self.token_preview = self.canvas.create_image(x, y, image=self.token_preview_img, tags="token_preview")

    def show_hex_occupied_message(self, hex_id):
        """Wyświetla migający czerwony komunikat nad zajętym heksem"""
        if hex_id in self.hex_centers:
            center_x, center_y = self.hex_centers[hex_id]
            scaled_x = center_x * self.map_scale
            scaled_y = center_y * self.map_scale
            
            # Stwórz komunikat nad żetonem
            message_id = self.canvas.create_text(
                scaled_x, scaled_y - 30,  # Pozycja nad żetonem
                text="Żeton wraca do kontenera",
                fill="red",
                font=("Arial", 12, "bold"),
                tags="warning_message"
            )
            
            # Funkcja do migania (zmiany widoczności)
            def flash_message(count=0):
                if count >= 6:  # 3 mignięcia (widoczny, niewidoczny) * 2
                    self.canvas.delete(message_id)
                    return
                
                # Zmień stan widoczności
                visibility = "hidden" if count % 2 else "normal"
                self.canvas.itemconfig(message_id, state=visibility)
                
                # Zaplanuj kolejną zmianę
                self.after(500, lambda c=count+1: flash_message(c))
            
            # Rozpocznij miganie
            flash_message()

    def place_token_on_hex(self, event):
        """Umieszcza token na heksie po zakończeniu przeciągania"""
        if not self.current_dragging_token:
            return
        
        # Usuń podgląd
        if self.token_preview:
            self.canvas.delete(self.token_preview)
            self.token_preview = None
        
        # Pobierz współrzędne myszy
        x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        
        # Konwertuj do współrzędnych canvasa
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        # Znajdź heks pod kursorem
        clicked_hex = None
        if self.hex_centers:
            min_distance = float('inf')
            for hex_id, (center_x, center_y) in self.hex_centers.items():
                # Skaluj pozycje zgodnie z map_scale
                scaled_x = center_x * self.map_scale
                scaled_y = center_y * self.map_scale
                
                # Oblicz odległość od kliknięcia do środka heksu
                distance = ((scaled_x - canvas_x) ** 2 + (scaled_y - canvas_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    clicked_hex = hex_id
            
            # Sprawdź czy kliknięcie jest wystarczająco blisko środka heksu
            max_valid_distance = self.hex_size * self.map_scale * 1.5
            if min_distance > max_valid_distance:
                clicked_hex = None
        
        # Jeśli znaleziono heks, umieść token
        if clicked_hex:
            # Sprawdź czy na heksie już jest token
            if clicked_hex in self.placed_token_images:
                # Heks zajęty, pokaż komunikat i zwróć token do kontenera
                self.show_hex_occupied_message(clicked_hex)
                
                # Zwróć token do odpowiedniego kontenera
                token_nation = self.current_dragging_token["nation"]
                token_obj = {
                    "name": self.current_dragging_token["name"],
                    "path": self.current_dragging_token["path"],
                    "nation": token_nation,
                    "data": self.current_dragging_token.get("data", {})
                }
                
                if token_nation == "polskie":
                    self.polish_panel.add_token(token_obj)
                elif token_nation == "niemieckie":
                    self.german_panel.add_token(token_obj)
                
                # Koniec przetwarzania
                self.current_dragging_token = None
                return
            
            # Pobierz pozycję heksu
            center_x, center_y = self.hex_centers[clicked_hex]
            scaled_x = center_x * self.map_scale
            scaled_y = center_y * self.map_scale
            
            # Dodaj token na stałe do mapy
            try:
                img = Image.open(self.current_dragging_token["path"])
                token_size = self.hex_size * self.map_scale * 1.5
                img = img.resize((int(token_size), int(token_size)), Image.LANCZOS)
                token_img = ImageTk.PhotoImage(img)
                        
                # Zachowaj referencję do obrazka, aby uniknąć garbage collection
                if not hasattr(self, 'placed_token_images'):
                    self.placed_token_images = {}
                
                # Najpierw usuń istniejący token na tym heksie, jeśli istnieje
                if clicked_hex in self.placed_token_images:
                    self.canvas.delete(self.placed_token_images[clicked_hex]["image_id"])
                
                # Umieść token na mapie
                token_id = self.canvas.create_image(scaled_x, scaled_y, image=token_img, tags=f"token_{clicked_hex}")
                self.placed_token_images[clicked_hex] = {
                    "image": token_img,
                    "image_id": token_id,
                    "token_data": self.current_dragging_token,
                    "hex_id": clicked_hex  # Dodaj odnośnik do ID heksu
                }
                
                # Dodaj obsługę zdarzeń, aby można było podnosić token z mapy
                self.canvas.tag_bind(token_id, "<ButtonPress-1>", 
                                    lambda e, hid=clicked_hex: self.start_drag_token_from_map(e, hid))
                
                # Aktualizuj dane heksu
                if clicked_hex not in self.hex_data:
                    self.hex_data[clicked_hex] = {}
                self.hex_data[clicked_hex]["jednostki"] = self.current_dragging_token["name"]
                
                print(f"Umieszczono token {self.current_dragging_token['name']} na heksie {clicked_hex}")
                
                # Jeśli heks jest aktualnie wybrany, zaktualizuj informacje
                if self.selected_hex == clicked_hex:
                    self.update_hex_info(self.hex_data[clicked_hex])
                
                # Usuń żeton z odpowiedniego panelu
                token_nation = self.current_dragging_token["nation"]
                token_name = self.current_dragging_token["name"]
                if token_nation == "polskie":
                    self.polish_panel.remove_token_by_name(token_name)
                elif token_nation == "niemieckie":
                    self.german_panel.remove_token_by_name(token_name)
                
            except Exception as e:
                print(f"Błąd podczas umieszczania tokena na heksie: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Nie znaleziono heksu pod kursorem.")
            self.update_hex_info(self.hex_data[clicked_hex])
        
        # Zakończ proces przeciągania
        self.current_dragging_token = None
        
        # Dla stabilności, odśwież canvas
        self.canvas.update_idletasks()

    def start_drag_token_from_map(self, event, hex_id):
        """Rozpoczyna przeciąganie żetonu z mapy"""
        if hex_id in self.placed_token_images:
            token_info = self.placed_token_images[hex_id]
            
            # Sprawdź czy żetony tej nacji są zablokowane
            nation = token_info["token_data"]["nation"]
            if self.is_nation_locked(nation):
                print(f"Żetony {nation} są zablokowane, nie można ich przesuwać")
                
                # Ręcznie zaktualizuj informacje o heksie - to umożliwi przeglądanie
                # danych heksów nawet gdy żetony są zablokowane
                self.selected_hex = hex_id
                hex_data = self.hex_data.get(hex_id, self.hex_defaults)
                self.update_hex_info(hex_data)
                
                # Podświetl heks
                if hex_id in self.hex_centers:
                    center_x, center_y = self.hex_centers[hex_id]
                    scaled_x = center_x * self.map_scale
                    scaled_y = center_y * self.map_scale
                    self.highlight_hex_at_position(scaled_x, scaled_y)
                
                return "break"  # Zatrzymaj propagację zdarzenia
            
            # Utwórz tymczasowy obiekt z informacjami o tokenie
            self.current_dragging_map_token = {
                "name": token_info["token_data"]["name"],
                "path": token_info["token_data"]["path"],
                "nation": token_info["token_data"]["nation"],
                "hex_id": hex_id,
                "data": token_info["token_data"].get("data", {})
            }
            print(f"Podniesiono token {self.current_dragging_map_token['name']} z heksu {hex_id}")
            
            # Utwórz podgląd tokenu podczas przeciągania
            try:
                img = Image.open(token_info["token_data"]["path"])
                token_size = self.hex_size * self.map_scale * 1.5
                img = img.resize((int(token_size), int(token_size)), Image.LANCZOS)
                self.token_preview_img = ImageTk.PhotoImage(img)
                
                # Dodaj binding do przeciągania
                self.canvas.bind("<B1-Motion>", self.drag_map_token)
                self.canvas.bind("<ButtonRelease-1>", self.drop_map_token)
                
                # Zacznij od razu pokazywać podgląd
                x, y = event.x, event.y
                if self.token_preview:
                    self.canvas.delete(self.token_preview)
                self.token_preview = self.canvas.create_image(x, y, image=self.token_preview_img, tags="token_preview")
                
                return "break"  # Zatrzymaj propagację zdarzenia
            except Exception as e:
                print(f"Błąd podczas tworzenia podglądu tokena z mapy: {e}")
                self.current_dragging_map_token = None
        
        return None

    def drag_map_token(self, event):
        """Obsługuje przeciąganie tokena z mapy"""
        if self.current_dragging_map_token:
            # Aktualizuj pozycję podglądu
            x, y = event.x, event.y
            if self.token_preview:
                self.canvas.delete(self.token_preview)
            self.token_preview = self.canvas.create_image(x, y, image=self.token_preview_img, tags="token_preview")

    def drop_map_token(self, event):
        """Obsługuje upuszczenie tokena z mapy"""
        if not self.current_dragging_map_token:
            return
        
        # Usuń podgląd
        if self.token_preview:
            self.canvas.delete(self.token_preview)
            self.token_preview = None
        
        # Sprawdź, czy token został upuszczony nad którymkolwiek z kontenerów żetonów
        token_nation = self.current_dragging_map_token["nation"]
        token_name = self.current_dragging_map_token["name"]
        
        # Sprawdź czy żetony tej nacji są zablokowane
        if self.is_nation_locked(token_nation):
            print(f"Żetony {token_nation} są zablokowane, nie można ich przesuwać")
            
            # Anuluj operację i pozostaw żeton na swoim miejscu
            self.current_dragging_token = None
            self.current_dragging_map_token = None    
            return
        
        # Konwertuj współrzędne zdarzenia na współrzędne względem głównego okna
        root_x = self.winfo_pointerx() - self.winfo_rootx()
        root_y = self.winfo_pointery() - self.winfo_rooty()
        
        # Sprawdź czy kursor jest nad panelem polskim
        if token_nation == "polskie" and self.is_over_panel(self.polish_panel, root_x, root_y):
            # Sprawdź czy token już istnieje w panelu
            if not self.polish_panel.token_exists(token_name):
                # Utwórz kopię danych tokena przed usunięciem z mapy
                token_obj = {
                    "name": token_name,
                    "path": self.current_dragging_map_token["path"],
                    "nation": "polskie",
                    "data": self.current_dragging_map_token.get("data", {})
                }
                
                # Dodaj token z powrotem do panelu tylko jeśli nie istnieje
                self.polish_panel.add_token(token_obj)
                print(f"Zwrócono żeton {token_obj['name']} do panelu polskiego")
            else:
                print(f"Żeton {token_name} już istnieje w panelu polskim, nie dodawany ponownie")
            
            # Usuń token z mapy
            hex_id = self.current_dragging_map_token["hex_id"]
            self.remove_token_from_map(hex_id)
            
            self.current_dragging_map_token = None
            return
        
        # Sprawdź czy kursor jest nad panelem niemieckim
        elif token_nation == "niemieckie" and self.is_over_panel(self.german_panel, root_x, root_y):
            # Sprawdź czy token już istnieje w panelu
            if not self.german_panel.token_exists(token_name):
                # Utwórz kopię danych tokena przed usunięciem z mapy
                token_obj = {
                    "name": token_name,
                    "path": self.current_dragging_map_token["path"],
                    "nation": "niemieckie",
                    "data": self.current_dragging_map_token.get("data", {})
                }
                
                # Dodaj token z powrotem do panelu tylko jeśli nie istnieje
                self.german_panel.add_token(token_obj)
                print(f"Zwrócono żeton {token_obj['name']} do panelu niemieckiego")
            else:
                print(f"Żeton {token_name} już istnieje w panelu niemieckim, nie dodawany ponownie")
            
            # Usuń token z mapy
            hex_id = self.current_dragging_map_token["hex_id"]
            self.remove_token_from_map(hex_id)
            
            self.current_dragging_map_token = None
            return
        
        # Tutaj sprawdzamy, czy token został upuszczony gdzie indziej na mapie (przesunięcie na inny hex)
        # Pobierz współrzędne myszy
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Znajdź heks pod kursorem
        clicked_hex = None
        if self.hex_centers:
            min_distance = float('inf')
            for hex_id, (center_x, center_y) in self.hex_centers.items():
                scaled_x = center_x * self.map_scale
                scaled_y = center_y * self.map_scale
                
                # Oblicz odległość od kliknięcia do środka heksu
                distance = ((scaled_x - canvas_x) ** 2 + (scaled_y - canvas_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    clicked_hex = hex_id
            
            # Sprawdź czy kliknięcie jest wystarczająco blisko środka heksu
            max_valid_distance = self.hex_size * self.map_scale * 1.5
            if min_distance <= max_valid_distance:
                # Jeśli to nowy hex, przesuń token (usuń ze starego, umieść na nowym)
                old_hex_id = self.current_dragging_map_token["hex_id"]
                if clicked_hex != old_hex_id:
                    # Sprawdź czy nowy heks jest już zajęty
                    if clicked_hex in self.placed_token_images:
                        # Heks zajęty, pokaż komunikat
                        self.show_hex_occupied_message(clicked_hex)
                        
                        # Zwracamy token do panelu, z którego pochodzi
                        token_obj = {
                            "name": self.current_dragging_map_token["name"],
                            "path": self.current_dragging_map_token["path"],
                            "nation": self.current_dragging_map_token["nation"],
                            "data": self.current_dragging_map_token.get("data", {})
                        }
                        
                        # Usuń token ze starego heksu
                        self.remove_token_from_map(old_hex_id)
                        
                        # Dodaj token z powrotem do panelu
                        if token_obj["nation"] == "polskie":
                            self.polish_panel.add_token(token_obj)
                        elif token_obj["nation"] == "niemieckie":
                            self.german_panel.add_token(token_obj)
                        
                        # Koniec przetwarzania
                        self.current_dragging_token = None
                        self.current_dragging_map_token = None
                        return
                    
                    # Usuń token ze starego heksu
                    self.remove_token_from_map(old_hex_id)
                    
                    # Umieść token na nowym heksie (używamy tokena jako current_dragging_token)
                    self.current_dragging_token = {
                        "name": self.current_dragging_map_token["name"],
                        "path": self.current_dragging_map_token["path"],
                        "nation": self.current_dragging_map_token["nation"],
                        "data": self.current_dragging_map_token["data"]
                    }
                    
                    # Pobierz pozycję nowego heksu
                    center_x, center_y = self.hex_centers[clicked_hex]
                    scaled_x = center_x * self.map_scale
                    scaled_y = center_y * self.map_scale
                    
                    # Stwórz token na nowym heksie
                    img = Image.open(self.current_dragging_token["path"])
                    token_size = self.hex_size * self.map_scale * 1.5
                    img = img.resize((int(token_size), int(token_size)), Image.LANCZOS)
                    token_img = ImageTk.PhotoImage(img)
                    
                    # Umieść token na mapie
                    token_id = self.canvas.create_image(scaled_x, scaled_y, image=token_img, tags=f"token_{clicked_hex}")
                    self.placed_token_images[clicked_hex] = {
                        "image": token_img,
                        "image_id": token_id,
                        "token_data": self.current_dragging_token,
                        "hex_id": clicked_hex
                    }
                    
                    # Dodaj obsługę zdarzeń, aby można było podnosić token z mapy
                    self.canvas.tag_bind(token_id, "<ButtonPress-1>", 
                                      lambda e, hid=clicked_hex: self.start_drag_token_from_map(e, hid))
                    
                    # Aktualizuj dane heksu
                    if clicked_hex not in self.hex_data:
                        self.hex_data[clicked_hex] = {}
                    self.hex_data[clicked_hex]["jednostki"] = self.current_dragging_token["name"]
                    print(f"Przeniesiono token {self.current_dragging_token['name']} na heks {clicked_hex}")
                    
                    # Jeśli heks jest aktualnie wybrany, zaktualizuj informacje
                    if self.selected_hex == clicked_hex:
                        self.update_hex_info(self.hex_data[clicked_hex])
        
        # Usuń podgląd
        if self.token_preview:
            self.canvas.delete(self.token_preview)
            self.token_preview = None
        
        # Wyczyść zmienne
        self.current_dragging_token = None
        self.current_dragging_map_token = None

    def remove_token_from_map(self, hex_id):
        """Usuwa token z mapy i z danych heksu"""
        if hex_id in self.placed_token_images:
            # Usuń obiekt z canvasa
            self.canvas.delete(self.placed_token_images[hex_id]["image_id"])
            
            # Usuń informację o jednostkach z danych heksu
            if hex_id in self.hex_data and "jednostki" in self.hex_data[hex_id]:
                del self.hex_data[hex_id]["jednostki"]
                if not self.hex_data[hex_id]:
                    del self.hex_data[hex_id]
            
            # Usuń token z listy umieszczonych
            del self.placed_token_images[hex_id]
            
            # Jeśli heks jest aktualnie wybrany, zaktualizuj informacje
            if self.selected_hex == hex_id:
                hex_data = self.hex_data.get(hex_id, self.hex_defaults)
                self.update_hex_info(hex_data)
            
            print(f"Usunięto token z heksu {hex_id}")
            return True
        return False

    def is_over_panel(self, panel, x, y):
        """Sprawdza czy dane współrzędne są nad panelem żetonów"""
        panel_frame = panel.frame
        panel_x = panel_frame.winfo_x()
        panel_y = panel_frame.winfo_y()
        panel_width = panel_frame.winfo_width()
        panel_height = panel_frame.winfo_height()
        
        # Sprawdź czy punkt (x, y) jest wewnątrz prostokąta panelu
        return (panel_x <= x <= panel_x + panel_width and 
                panel_y <= y <= panel_y + panel_height)

    def quit(self):
        """Zamyka aplikację z podwójnym potwierdzeniem"""
        response = messagebox.askyesno(
            "Potwierdzenie",
            "Czy na pewno chcesz wyjść z gry?\nNiezapisane zmiany zostaną utracone.",
            icon='question'
        )
        if response:
            super().quit()

    def lock_nation_tokens(self, nation):
        """
        Blokuje możliwość operowania żetonami danej nacji.
        Zmodyfikowana wersja, która nie usuwa folderów z obrazami żetonów.
        """
        if nation == "polskie":
            self.polish_tokens_locked = True
            print("Zablokowano żetony polskie")
        elif nation == "niemieckie":
            self.german_tokens_locked = True
            print("Zablokowano żetony niemieckie")
        
        # Zamiast usuwać oryginalne foldery, najpierw zrobimy kopie obrazów do folderu zapisu
        save_images_folder = os.path.join(os.getcwd(), "saves", "images")
        if not os.path.exists(save_images_folder):
            os.makedirs(save_images_folder, exist_ok=True)
        
        # Znajdź wszystkie tokeny danej nacji, które zostały umieszczone na mapie
        for hex_id, token_info in self.placed_token_images.items():
            token_data = token_info["token_data"]
            if token_data["nation"] == nation:
                # Zamiast usuwać, zrób kopię obrazu
                token_path = token_data["path"]
                token_name = token_data["name"]
                if os.path.exists(token_path):
                    try:
                        # Utwórz unikalną nazwę dla kopii obrazu
                        image_filename = f"{nation}_{token_name}_{hex_id}.png".replace(" ", "_")
                        image_save_path = os.path.join(save_images_folder, image_filename)
                        
                        # Skopiuj obraz do folderu zapisu
                        shutil.copy2(token_path, image_save_path)
                        print(f"[INFO] Utworzono kopię obrazu dla tokena {token_name}: {image_save_path}")
                        
                        # Zaktualizuj ścieżkę tokena do nowej kopii
                        token_data["original_path"] = token_path
                        token_data["path"] = image_save_path
                    except Exception as e:
                        print(f"[UWAGA] Nie udało się utworzyć kopii obrazu dla tokena {token_name}: {e}")

    def unlock_nation_tokens(self, nation):
        """Odblokowuje możliwość operowania żetonami danej nacji."""
        nation_lower = nation.lower()
        
        # Bardziej elastyczne sprawdzanie na podstawie części nazwy
        if "pol" in nation_lower:
            self.polish_tokens_locked = False
            print("Odblokowano żetony polskie")
        elif "niem" in nation_lower or "germ" in nation_lower:
            self.german_tokens_locked = False
            print("Odblokowano żetony niemieckie")
        else:
            print(f"Nieznana nacja: {nation}")

    def is_nation_locked(self, nation):
        """Sprawdza czy żetony danej nacji są zablokowane."""
        nation_lower = nation.lower()
        
        if "pol" in nation_lower:
            return self.polish_tokens_locked
        elif "niem" in nation_lower or "germ" in nation_lower:
            return self.german_tokens_locked
        
        # Jeśli nie rozpoznano nacji, domyślnie zwracamy False
        print(f"Nieznana nacja w sprawdzeniu blokady: {nation}")
        return False

    def is_turn_active(self, nation):
        """Sprawdza, czy obecny gracz ma aktywną turę."""
        nation_lower = nation.lower()
        current_nation_lower = self.current_turn_nation.lower()
        
        # Porównanie na podstawie części nazwy
        if (("pol" in nation_lower and "pol" in current_nation_lower) or
            (("niem" in nation_lower or "germ" in nation_lower) and 
             ("niem" in current_nation_lower or "germ" in current_nation_lower))):
            return True
        return False

    def update_economic_info(self):
        """Aktualizuje panel informacji ekonomicznych na podstawie aktualnej nacji."""
        self.economic_info_text.config(state="normal")
        self.economic_info_text.delete(1.0, tk.END)
        
        # Pobranie raportu ekonomicznego dla aktualnej nacji
        report = self.economy_system.generate_report(self.current_turn_nation)
        
        # Wyświetlenie raportu w sekcji
        self.economic_info_text.insert(tk.END, report)
        self.economic_info_text.config(state="disabled")

    def wczytaj_dane_mapy(self):
        """Wczytuje dane mapy z pliku JSON."""
        try:
            if not os.path.exists(MAP_DATA_PATH):
                print(f"[UWAGA] Nie znaleziono pliku danych mapy: {MAP_DATA_PATH}")
                return
            
            with open(MAP_DATA_PATH, 'r', encoding='utf-8') as f:
                self.map_data = json.load(f)
                
                # Wczytaj domyślne wartości dla heksów jeśli istnieją
                self.hex_defaults = {"defense_mod": 0, "move_mod": 0}
                if "defaults" in self.map_data and "hex" in self.map_data["defaults"]:
                    self.hex_defaults = self.map_data["defaults"]["hex"]
                    print(f"Wczytano domyślne wartości dla heksów: {self.hex_defaults}")
                
                # Wczytaj dane heksów jeśli istnieją
                if "hex_data" in self.map_data:
                    self.hex_data = self.map_data["hex_data"]
                    print(f"Wczytano dane dla {len(self.hex_data)} niestandardowych heksów")
                
                # Wczytaj typy terenu
                if "terrain_types" in self.map_data:
                    self.terrain_types = self.map_data["terrain_types"]
                    print(f"Wczytano {len(self.terrain_types)} typów terenu")
                
                # Wczytaj pozycje środków heksów
                if "hex_centers" in self.map_data:
                    self.hex_centers = {}
                    for hex_id, coords in self.map_data["hex_centers"].items():
                        if isinstance(coords, list) and len(coords) == 2:
                            self.hex_centers[hex_id] = tuple(coords)
                        elif isinstance(coords, list) and len(coords) == 1:
                            print(f"[UWAGA] Nieprawidłowy format pozycji dla heksu {hex_id}")
                    print(f"Wczytano pozycje dla {len(self.hex_centers)} heksów")
                
                if not self.hex_centers:
                    print("[UWAGA] Brak informacji o pozycjach heksów w pliku danych. Generowanie pozycji...")
                    self.generate_hex_positions()
                
                # Wczytaj konfigurację jeśli istnieje
                if "config" in self.map_data:
                    config = self.map_data["config"]
                    print("Wczytano konfigurację mapy")
                    
                    if "hex_size" in config:
                        self.hex_size = config["hex_size"]
                        self.hex_width = 2 * self.hex_size
                        self.hex_height = math.sqrt(3) * self.hex_size
                        self.hex_horiz_offset = 1.5 * self.hex_size
                        self.hex_vert_offset = self.hex_height
                        print(f"Ustawiono parametry heksów: size={self.hex_size}, width={self.hex_width}, height={self.hex_height}")
        except Exception as e:
            print(f"[BŁD] Problem podczas wczytywania danych mapy: {e}")
            import traceback
            traceback.print_exc()

    def generate_hex_positions(self):
        """Generuje pozycje heksów na podstawie konfiguracji mapy."""
        self.hex_centers.clear()
        
        if self.map_data and "config" in self.map_data:
            config = self.map_data["config"]
            s = config.get("hex_size", 30)
            grid_cols = config.get("grid_cols", 56)
            grid_rows = config.get("grid_rows", 40)
        else:
            s = 30
            grid_cols = 56
            grid_rows = 40
        
        self.hex_size = s
        hex_height = math.sqrt(3) * s
        horizontal_spacing = 1.5 * s
        
        for col in range(grid_cols):
            center_x = s + col * horizontal_spacing
            for row in range(grid_rows):
                center_y = (s * math.sqrt(3) / 2) + row * hex_height
                if col % 2 == 1:
                    center_y += hex_height / 2
                hex_id = f"{col}_{row}"
                self.hex_centers[hex_id] = (center_x, center_y)
        print(f"Wygenerowano pozycje dla {len(self.hex_centers)} heksów")

    def draw_hex_grid(self):
        """Rysuje siatkę heksów na mapie na podstawie danych JSON."""
        print("Rysowanie siatki heksów z danych JSON...")
        
        for hex_id, (center_x, center_y) in self.hex_centers.items():
            x = center_x * self.map_scale
            y = center_y * self.map_scale
            
            vertices = self.get_hex_vertices(x, y, self.hex_size * self.map_scale)
            self.canvas.create_polygon(vertices, outline="red", fill="", width=2, tags=f"hex_{hex_id}")
            
            if self.debug_mode:
                self.canvas.create_text(x, y, text=hex_id, fill="blue", font=("Arial", 8), tags=f"text_{hex_id}")
            
            if hex_id in self.hex_data:
                terrain = self.hex_data[hex_id]
                if "move_mod" in terrain and "defense_mod" in terrain:
                    tekst = f"M:{terrain['move_mod']} D:{terrain['defense_mod']}"
                    self.canvas.create_text(x, y + 15, text=tekst, fill="green", font=("Arial", 8), tags=f"info_{hex_id}")
        print(f"Narysowano {len(self.hex_centers)} heksów")

    def get_hex_vertices(self, center_x, center_y, size):
        """Zwraca współrzędne wierzchołków heksagonu (flat-topped)."""
        return [
            (center_x - size, center_y),
            (center_x - size/2, center_y - (math.sqrt(3)/2)*size),
            (center_x + size/2, center_y - (math.sqrt(3)/2)*size),
            (center_x + size, center_y),
            (center_x + size/2, center_y + (math.sqrt(3)/2)*size),
            (center_x - size/2, center_y + (math.sqrt(3)/2)*size),
        ]

    def clear_map(self):
        """Usuwa wszystkie tokeny z mapy i przygotowuje ją na wczytanie nowego stanu gry"""
        print("[INFO] Czyszczenie mapy...")
        
        if hasattr(self, 'placed_token_images'):
            for hex_id, token_info in list(self.placed_token_images.items()):
                try:
                    if "image_id" in token_info:
                        self.canvas.delete(token_info["image_id"])
                except Exception as e:
                    print(f"[UWAGA] Błąd podczas usuwania tokena z heksu {hex_id}: {e}")
            
            self.placed_token_images.clear()
        
        self.clear_highlight()
        self.selected_hex = None
        
        self.update_hex_info(None)
        
        if hasattr(self, 'current_dragging_token'):
            self.current_dragging_token = None
        
        if hasattr(self, 'current_dragging_map_token'):
            self.current_dragging_map_token = None
        
        if hasattr(self, 'token_preview') and self.token_preview:
            self.canvas.delete(self.token_preview)
            self.token_preview = None
        self.clear_highlight()
        print("[INFO] Mapa została wyczyszczona")

    def update_token_locks(self):
        """Aktualizuje stan blokady żetonów na podstawie aktualnej tury"""
        print(f"[INFO] Aktualizacja blokad żetonów dla tury: {self.current_turn_nation}")
        if self.current_turn_nation == "Polska":
            self.polish_tokens_locked = False
            self.german_tokens_locked = True
            self.polish_panel.unlock_tokens()
            self.german_panel.lock_tokens()
            print("[INFO] Żetony polskie odblokowane, żetony niemieckie zablokowane")
        else:
            self.polish_tokens_locked = True
            self.german_tokens_locked = False
            self.polish_panel.lock_tokens()
            self.german_panel.unlock_tokens()
            print("[INFO] Żetony polskie zablokowane, żetony niemieckie odblokowane")

    def load_tokens_from_folder(self):
        """Wczytuje żetony z folderu tokeny i jego podfolderów"""
        try:
            print(f"[INFO] Rozpoczynam wczytywanie żetonów z folderu: {TOKENS_PATH}")
            
            if not os.path.exists(TOKENS_PATH):
                print(f"[UWAGA] Folder z żetonami nie istnieje: {TOKENS_PATH}")
                os.makedirs(TOKENS_PATH, exist_ok=True)
                print(f"[INFO] Utworzono folder dla żetonów: {TOKENS_PATH}")
                
                messagebox.showinfo(
                    "Brak żetonów",
                    f"Nie znaleziono żetonów w folderze {TOKENS_PATH}.\nUtworzono pusty folder, możesz dodać tam żetony."
                )
                return
            
            polish_folder = os.path.join(TOKENS_PATH, "polskie")
            german_folder = os.path.join(TOKENS_PATH, "niemieckie")
            
            if not os.path.exists(polish_folder):
                os.makedirs(polish_folder, exist_ok=True)
                print(f"[INFO] Utworzono folder dla żetonów polskich: {polish_folder}")
            if not os.path.exists(german_folder):
                os.makedirs(german_folder, exist_ok=True)
                print(f"[INFO] Utworzono folder dla żetonów niemieckich: {german_folder}")
            
            polish_tokens = []
            german_tokens = []
            
            print(f"[DEBUG] Skanowanie folderów żetonów, katalog główny: {TOKENS_PATH}")
            for dirpath, dirnames, filenames in os.walk(TOKENS_PATH):
                if dirpath == TOKENS_PATH:
                    print(f"[DEBUG] Pomijam główny katalog: {dirpath}")
                    continue
                
                png_files = [f for f in filenames if f.lower().endswith('.png')]
                if not png_files:
                    print(f"[DEBUG] Brak plików PNG w katalogu: {dirpath}")
                    continue
                
                token_name = os.path.basename(dirpath)
                token_path = os.path.join(dirpath, png_files[0])
                print(f"[DEBUG] Znaleziono token: {token_name}, ścieżka: {token_path}")
                
                token_data_path = os.path.join(dirpath, "token_data.json")
                token_data = {}
                if os.path.exists(token_data_path):
                    try:
                        with open(token_data_path, 'r', encoding='utf-8') as f:
                            token_data = json.load(f)
                            print(f"[DEBUG] Wczytano dane tokena z: {token_data_path}")
                    except Exception as e:
                        print(f"[BŁĄD] Podczas wczytywania danych tokena {token_name}: {e}")
                
                nation = token_data.get("nation", "")
                
                token_obj = {
                    "name": token_name,
                    "path": token_path,
                    "data": token_data
                }
                
                if "Polska" in token_name or "polska" in token_name or nation == "Polska":
                    token_obj["nation"] = "polskie"
                    polish_tokens.append(token_obj)
                    print(f"[INFO] Token {token_name} dodany jako polski")
                elif "Niemcy" in token_name or "niemieck" in token_name or nation == "Niemcy":
                    token_obj["nation"] = "niemieckie"
                    german_tokens.append(token_obj)
                    print(f"[INFO] Token {token_name} dodany jako niemiecki")
                else:
                    if "polskie" in dirpath.lower():
                        token_obj["nation"] = "polskie"
                        polish_tokens.append(token_obj)
                        print(f"[INFO] Token {token_name} dodany jako polski (na podstawie ścieżki)")
                    elif "niemieckie" in dirpath.lower() or "niemcy" in dirpath.lower():
                        token_obj["nation"] = "niemieckie"
                        german_tokens.append(token_obj)
                        print(f"[INFO] Token {token_name} dodany jako niemiecki (na podstawie ścieżki)")
                    else:
                        print(f"[UWAGA] Nie można ustalić nacji dla tokena {token_name}, token pominięty")
            
            if not polish_tokens and not german_tokens:
                print("[UWAGA] Nie znaleziono żadnych żetonów!")
                messagebox.showwarning(
                    "Brak żetonów",
                    "Nie znaleziono żadnych żetonów do wczytania.\n"
                    f"Sprawdź zawartość katalogów:\n"
                    f"- {polish_folder}\n"
                    f"- {german_folder}"
                )
                return
                
            for token in polish_tokens:
                self.polish_panel.add_token(token)
            
            for token in german_tokens:
                self.german_panel.add_token(token)
            
            print(f"[INFO] Wczytano {len(polish_tokens)} polskich żetonów i {len(german_tokens)} niemieckich żetonów")
            
        except Exception as e:
            print(f"[BŁĄD] Wystąpił błąd podczas wczytywania żetonów: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    app = GameInterface()
    app.mainloop()