import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageDraw
import math  # Dodaj import, jeśli nie jest jeszcze w kodzie

class HexEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Edytor Heksów")
        self.root.state("zoomed")  # Otwieranie w maksymalnym rozmiarze okna
        self.root.configure(bg="darkolivegreen")

        # Domyślne ustawienia
        self.hex_size = 30
        self.image = None
        self.scaled_image = None
        self.image_tk = None
        self.offset_x = 0
        self.offset_y = 0
        self.rotation = 0

        # Główne ramki
        self.main_frame = tk.Frame(self.root, bg="darkolivegreen")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_frame = tk.Frame(self.main_frame, bg="olivedrab", bd=5, relief=tk.RIDGE)
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.controls_frame = tk.Frame(self.main_frame, bg="darkolivegreen")
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Canvas do podglądu
        self.canvas = tk.Canvas(self.main_frame, bg="black", width=700, height=700)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Podgląd heksa (zmniejszony)
        self.preview_label = tk.Label(self.preview_frame, text="Podgląd Heksa", bg="olivedrab", fg="white", font=("Arial", 14, "bold"))
        self.preview_label.pack(pady=10)

        self.preview_canvas = tk.Canvas(self.preview_frame, bg="white", width=150, height=150)  # Zmniejszono rozmiar
        self.preview_canvas.pack(pady=10)

        # Sekcja wyboru wielkości heksa
        self.size_label = tk.Label(self.preview_frame, text="Wielkość Heksa:", bg="olivedrab", fg="white", font=("Arial", 12))
        self.size_label.pack(pady=5)

        self.size_combobox = ttk.Combobox(self.preview_frame, values=[30], state="readonly")
        self.size_combobox.set(30)
        self.size_combobox.pack(pady=5)

        # Sekcja wyboru układu heksów
        self.layout_label = tk.Label(self.preview_frame, text="Układ Heksów:", bg="olivedrab", fg="white", font=("Arial", 12))
        self.layout_label.pack(pady=5)

        self.layout_combobox = ttk.Combobox(self.preview_frame, values=[
            "1 heks", 
            "2 heksy w pionie", 
            "2 heksy w poziomie", 
            "3 heksy w poziomie"
        ], state="readonly")  # Usunięto "3 heksy w Y" i "7 heksów (1 w środku)"
        self.layout_combobox.set("1 heks")  # Domyślny układ
        self.layout_combobox.pack(pady=5)
        self.layout_combobox.bind("<<ComboboxSelected>>", self.update_canvas)  # Aktualizacja canvasu po zmianie

        # Przyciski do przesuwania i obracania
        self.move_label = tk.Label(self.controls_frame, text="Przesuwanie Tła:", bg="darkolivegreen", fg="white", font=("Arial", 12))
        self.move_label.pack(side=tk.LEFT, padx=10)

        self.move_left_btn = tk.Button(self.controls_frame, text="←", command=lambda: self.move_background(-10, 0))
        self.move_left_btn.pack(side=tk.LEFT, padx=5)

        self.move_right_btn = tk.Button(self.controls_frame, text="→", command=lambda: self.move_background(10, 0))
        self.move_right_btn.pack(side=tk.LEFT, padx=5)

        self.move_up_btn = tk.Button(self.controls_frame, text="↑", command=lambda: self.move_background(0, -10))
        self.move_up_btn.pack(side=tk.LEFT, padx=5)

        self.move_down_btn = tk.Button(self.controls_frame, text="↓", command=lambda: self.move_background(0, 10))
        self.move_down_btn.pack(side=tk.LEFT, padx=5)

        self.rotate_label = tk.Label(self.controls_frame, text="Obracanie Tła:", bg="darkolivegreen", fg="white", font=("Arial", 12))
        self.rotate_label.pack(side=tk.LEFT, padx=10)

        self.rotate_left_btn = tk.Button(self.controls_frame, text="⟲", command=lambda: self.rotate_background(-10))
        self.rotate_left_btn.pack(side=tk.LEFT, padx=5)

        self.rotate_right_btn = tk.Button(self.controls_frame, text="⟳", command=lambda: self.rotate_background(10))
        self.rotate_right_btn.pack(side=tk.LEFT, padx=5)

        # Suwak do zmiany rozdzielczości tła
        self.resolution_label = tk.Label(self.controls_frame, text="Rozdzielczość tła: 100%", bg="darkolivegreen", fg="white", font=("Arial", 12))
        self.resolution_label.pack(side=tk.LEFT, padx=10)

        # Okno wyświetlające aktualną rozdzielczość
        self.resolution_display = tk.Label(self.controls_frame, text="700 x 700 px", bg="white", fg="black", font=("Arial", 12), width=15, relief=tk.SUNKEN, anchor="center")
        self.resolution_display.pack(side=tk.LEFT, padx=5)

        self.resolution_scale = tk.Scale(self.controls_frame, from_=10, to=500, orient=tk.HORIZONTAL, length=300, command=self.update_resolution)
        self.resolution_scale.set(100)  # Domyślna wartość 100%
        self.resolution_scale.pack(side=tk.LEFT, padx=5)

        # Przyciski do wczytania obrazu
        self.load_image_btn = tk.Button(self.controls_frame, text="Wczytaj Obraz", command=self.load_image)
        self.load_image_btn.pack(side=tk.RIGHT, padx=10)

        # Obsługa klawiatury
        self.root.bind("<Left>", lambda event: self.move_background(-10, 0))
        self.root.bind("<Right>", lambda event: self.move_background(10, 0))
        self.root.bind("<Up>", lambda event: self.move_background(0, -10))
        self.root.bind("<Down>", lambda event: self.move_background(0, 10))
        self.root.bind("q", lambda event: self.rotate_background(-10))
        self.root.bind("w", lambda event: self.rotate_background(10))

        # Obsługa przeciągania myszką
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_background)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        # Zmienna do śledzenia przesunięcia
        self.drag_start_x = 0
        self.drag_start_y = 0

    def load_image(self):
        """Wczytuje obraz jako tło."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.image = Image.open(file_path)
            self.scaled_image = self.image.copy()  # Kopia obrazu do skalowania
            self.update_canvas()

    def update_resolution(self, value):
        """Aktualizuje rozdzielczość tła na podstawie wartości suwaka."""
        scale_factor = int(value) / 100  # Przelicznik procentowy
        
        if self.image:
            # Zmiana rozdzielczości obrazu
            new_width = int(self.image.width * scale_factor)
            new_height = int(self.image.height * scale_factor)
            self.scaled_image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Aktualizacja etykiety z rozdzielczością
            self.resolution_label.config(text=f"Rozdzielczość tła: {new_width} x {new_height} px ({int(value)}%)")
            self.resolution_display.config(text=f"{new_width} x {new_height} px")  # Aktualizacja okna z rozdzielczością
            
            # Aktualizacja canvasu
            self.update_canvas()

    def update_canvas(self, event=None):
        """Aktualizuje canvas w zależności od wybranego układu heksów."""
        if self.scaled_image:
            # Użycie przeskalowanego obrazu
            rotated_image = self.scaled_image.rotate(self.rotation, expand=True)
            self.image_tk = ImageTk.PhotoImage(rotated_image)
            self.canvas.create_image(self.offset_x, self.offset_y, image=self.image_tk, anchor=tk.CENTER)

            # Rysowanie układu heksów
            self.canvas.delete("hex_outline")  # Usuń poprzednie heksy
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            center_x = canvas_width // 2
            center_y = canvas_height // 2

            # Pobierz układ heksów z comboboxa
            layout = self.layout_combobox.get()

            # Odległości między heksami
            dx = self.hex_size * 2  # Odległość w poziomie
            dy = int(self.hex_size * math.sqrt(3))  # Odległość w pionie

            # Rysuj odpowiedni układ heksów
            if layout == "1 heks":
                self.draw_hex(center_x, center_y, self.hex_size)
            elif layout == "2 heksy w pionie":
                self.draw_hex(center_x, center_y, self.hex_size)
                self.draw_hex(center_x, center_y + dy, self.hex_size)
            elif layout == "2 heksy w poziomie":
                self.draw_hex(center_x, center_y, self.hex_size)
                self.draw_hex(center_x + dx, center_y, self.hex_size)
            elif layout == "3 heksy w poziomie":
                self.draw_hex(center_x, center_y, self.hex_size)
                self.draw_hex(center_x - dx, center_y, self.hex_size)
                self.draw_hex(center_x + dx, center_y, self.hex_size)

            # Aktualizacja podglądu heksa
            hex_preview = self.generate_hex_preview(rotated_image)
            self.preview_canvas.create_image(75, 75, image=hex_preview, anchor=tk.CENTER)  # Zmniejszono pozycję podglądu

    def generate_hex_preview(self, image):
        """Generuje podgląd heksa na podstawie obrazu."""
        # Przeskalowanie obrazu do 200%
        scaled_image = image.resize((int(image.width * 2), int(image.height * 2)), Image.Resampling.LANCZOS)  # Zmieniono na LANCZOS

        # Tworzenie maski heksa w normalnym rozmiarze
        hex_mask = Image.new("L", (self.hex_size * 2, self.hex_size * 2), 0)
        draw = ImageDraw.Draw(hex_mask)
        draw.polygon(self.get_hex_vertices(self.hex_size, self.hex_size, self.hex_size), fill=255)

        # Przycinanie obrazu do heksa
        hex_image = Image.composite(scaled_image, Image.new("RGBA", scaled_image.size, (255, 255, 255, 0)), hex_mask)
        return ImageTk.PhotoImage(hex_image)

    def get_hex_vertices(self, cx, cy, size):
        """Zwraca wierzchołki heksa."""
        return [
            (cx + size * math.cos(math.radians(60 * i)), cy + size * math.sin(math.radians(60 * i)))
            for i in range(6)
        ]

    def draw_hex(self, cx, cy, size):
        """Rysuje pojedynczy heks na canvasie."""
        hex_vertices = self.get_hex_vertices(cx, cy, size)
        self.canvas.create_polygon(hex_vertices, outline="red", fill="", width=2, tags="hex_outline")

    def move_background(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy
        self.update_canvas()

    def rotate_background(self, angle):
        self.rotation += angle
        self.update_canvas()

    def start_drag(self, event):
        """Rozpoczyna przeciąganie tła."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag_background(self, event):
        """Przesuwa tło podczas przeciągania."""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.offset_x += dx
        self.offset_y += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.update_canvas()

    def end_drag(self, event):
        """Kończy przeciąganie tła."""
        pass  # Możesz dodać dodatkowe akcje, jeśli są potrzebne

if __name__ == "__main__":
    root = tk.Tk()
    app = HexEditor(root)
    root.mainloop()