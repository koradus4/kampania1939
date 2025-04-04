"""
Moduł do generowania i zarządzania tokenami dla gry Kampania Wrześniowa 1939.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import json

class TokenGenerator:
    """Klasa zarządzająca generowaniem tokenów zastępczych i różnicowaniem tokenów"""
    
    def __init__(self, tokens_path):
        self.tokens_path = tokens_path
        self.generated_path = os.path.join(tokens_path, "_generowane")
        self.polish_path = os.path.join(self.generated_path, "polskie")
        self.german_path = os.path.join(self.generated_path, "niemieckie")
        
        # Utwórz ścieżki jeśli nie istnieją
        for path in [self.generated_path, self.polish_path, self.german_path]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
    
    def generate_token(self, name, nation, unit_type, token_code, size=200):
        """
        Generuje token na podstawie podanych parametrów.
        
        Args:
            name: Nazwa tokena
            nation: Nacja (polskie/niemieckie)
            unit_type: Typ jednostki (piechota, artyleria, itp.)
            token_code: Kod identyfikacyjny jednostki (np. TŚ, P, itp.)
            size: Rozmiar tokena w pikselach
        
        Returns:
            Ścieżka do wygenerowanego pliku
        """
        try:
            # Wybierz folder docelowy
            if "pol" in nation.lower():
                target_folder = self.polish_path
                border_color = "#ffffff"  # Biały dla Polski
                text_color = "#000000"    # Czarny tekst
            else:
                target_folder = self.german_path
                border_color = "#000000"  # Czarny dla Niemiec
                text_color = "#ffffff"    # Biały tekst
            
            # Przygotuj ścieżkę pliku wyjściowego
            safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
            output_path = os.path.join(target_folder, f"{safe_name}.png")
            
            # Sprawdź czy plik już istnieje
            if os.path.exists(output_path):
                return output_path
            
            # Przygotuj kolory w zależności od typu jednostki
            color_map = {
                "piechota": "#7f9c40",      # Zielony
                "artyleria": "#c83232",      # Czerwony
                "pancerne": "#6b4226",       # Brązowy
                "kawaleria": "#ffcc00",      # Żółty
                "zmotoryzowane": "#666699",  # Niebieski
                "inżynieria": "#993333",     # Ciemny czerwony
                "rozpoznanie": "#99cc99",    # Jasny zielony
                "sztab": "#0066cc",          # Niebieski
                "dowództwo": "#990099",      # Fioletowy
                "ciężki czołg": "#663300",   # Ciemny brąz
                "średni czołg": "#996633",   # Brąz
                "lekki czołg": "#cc9966",    # Jasny brąz
                "przeciwpancerna": "#990000", # Ciemny czerwony
                "ciężka artyleria": "#cc0000", # Czerwony
                "lekka artyleria": "#ff6666", # Jasny czerwony
                "garnizon": "#336699"        # Granatowy
            }
            
            # Domyślny kolor, jeśli nie znaleziono typu
            bg_color = color_map.get(unit_type, "#7f7f7f")  # Szary jako domyślny
            
            # Stwórz obrazek
            img = Image.new('RGB', (size, size), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Dodaj obramowanie
            border_width = 10
            draw.rectangle(
                [(border_width, border_width), (size - border_width, size - border_width)],
                outline=border_color,
                width=border_width
            )
            
            # Spróbuj załadować czcionkę
            font_size = 24
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                try:
                    # Próbuj inne popularne czcionki
                    font_paths = [
                        "C:/Windows/Fonts/arial.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/System/Library/Fonts/Helvetica.ttc"
                    ]
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size)
                            break
                    else:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
            
            # Podziel nazwę tokena na wiersze
            lines = []
            words = name.split()
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) > 15:  # Max 15 znaków w linii
                    lines.append(current_line)
                    current_line = word
                else:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Rysuj tekst
            y_position = size // 2 - (len(lines) * font_size // 2)
            for line in lines:
                # Oblicz szerokość tekstu i centruj
                text_width = draw.textlength(line, font=font)
                x_position = (size - text_width) // 2
                
                draw.text((x_position, y_position), line, fill=text_color, font=font)
                y_position += font_size + 5  # 5 pikseli odstępu
            
            # Dodaj kod jednostki w prawym dolnym rogu
            if token_code:
                code_text = token_code
                code_width = draw.textlength(code_text, font=font)
                draw.text(
                    (size - code_width - 15, size - font_size - 15),
                    code_text,
                    fill=text_color,
                    font=font
                )
            
            # Zapisz obraz i dane tokena
            img.save(output_path)
            
            # Zapisz metadane tokena
            token_data = {
                "name": name,
                "nation": "Polska" if "pol" in nation.lower() else "Niemcy",
                "type": unit_type,
                "code": token_code
            }
            
            metadata_path = os.path.join(os.path.dirname(output_path), "token_data.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=4, ensure_ascii=False)
            
            return output_path
            
        except Exception as e:
            print(f"[BŁĄD] Podczas generowania tokena {name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def apply_token_overlay(self, img, token_code):
        """
        Nakłada kolorowe oznaczenie na obraz tokena na podstawie kodu jednostki.
        
        Args:
            img: Obiekt Image
            token_code: Kod jednostki
            
        Returns:
            Zmodyfikowany obraz z nakładką
        """
        try:
            # Przygotuj kolor na podstawie kodu jednostki
            color_dict = {
                'P': (0, 150, 0, 128),      # Piechota - zielony
                'A': (200, 0, 0, 128),      # Artyleria - czerwony
                'T': (150, 75, 0, 128),     # Pancerne - brązowy
                'K': (255, 204, 0, 128),    # Kawaleria - żółty
                'Z': (100, 100, 150, 128),  # Zmotoryzowane - niebieski
                'I': (150, 50, 50, 128),    # Inżynieria - bordowy
                'R': (150, 200, 150, 128),  # Rozpoznanie - jasny zielony
                'S': (0, 100, 200, 128),    # Sztab - niebieski
                'D': (150, 0, 150, 128),    # Dowództwo - fioletowy
                'G': (50, 100, 150, 128)    # Garnizon - granatowy
            }
            
            # Określ pierwszy znak kodu jako podstawę koloru
            if token_code and len(token_code) > 0:
                first_char = token_code[0]
                color = color_dict.get(first_char, (100, 100, 100, 128))  # Domyślny szary
            else:
                color = (100, 100, 100, 128)  # Szary dla nieznanych
            
            # Konwertuj obraz do trybu RGBA
            img_rgba = img.convert("RGBA")
            width, height = img_rgba.size
            
            # Utwórz nakładkę koloru
            overlay = Image.new("RGBA", (width, height//4), color)
            
            # Nałóż nakładkę na dolną część obrazu
            img_rgba.paste(overlay, (0, height - height//4), overlay)
            
            # Dodaj tekst kodu
            if token_code:
                try:
                    draw = ImageDraw.Draw(img_rgba)
                    try:
                        font = ImageFont.truetype("arial.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    
                    # Dodaj tekst w prawym dolnym rogu
                    draw.text((width - 30, height - 30), token_code, fill=(255, 255, 255, 255), font=font)
                except:
                    pass  # Ignoruj błędy przy dodawaniu tekstu
            
            return img_rgba
            
        except Exception as e:
            print(f"[UWAGA] Błąd podczas nakładania oznaczenia koloru: {e}")
            return img  # Zwróć oryginalny obraz w przypadku błędu
