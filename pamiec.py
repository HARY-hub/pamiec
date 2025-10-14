import tkinter as tk
from tkinter import messagebox, colorchooser
import os
import sys
import webbrowser
from tkfontchooser import askfont   # pip install tkfontchooser

# baza dla plików (działa i w .py, i w .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notatnik")
        self.root.geometry("400x300")

        self.selection_color = "#4CAF50"
        self.current_font = ("Arial", 10)

        self.data_file = os.path.join(BASE_DIR, "dane.txt")
        self.style_file = os.path.join(BASE_DIR, "style.txt")  # plik przechowujący style linii

        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as file:
                file.write("")

        # główna ramka
        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # pole tekstowe z przewijaniem
        self.text_frame = tk.Frame(self.main_frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.scrollbar = tk.Scrollbar(self.text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(
            self.text_frame,
            height=10,
            width=40,
            font=self.current_font,
            wrap=tk.WORD,
            state=tk.DISABLED,
            selectbackground=self.selection_color,
            inactiveselectbackground=self.selection_color,
            selectforeground="white",
            cursor="arrow",
            yscrollcommand=self.scrollbar.set
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.text_widget.yview)

        # ramka przycisków
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X)

        self.add_button = tk.Button(
            self.button_frame, text="Dopisz", command=self.add_note,
            bg=self.selection_color, fg="white", font=("Arial", 10, "bold"), width=10
        )
        self.add_button.pack(side=tk.LEFT, padx=(0, 5))

        self.edit_button = tk.Button(
            self.button_frame, text="Modyfikuj", command=self.edit_note,
            bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=10
        )
        self.edit_button.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_button = tk.Button(
            self.button_frame, text="Usuń", command=self.delete_note,
            bg="#F44336", fg="white", font=("Arial", 10, "bold"), width=10
        )
        self.delete_button.pack(side=tk.LEFT, padx=(0, 5))

        self.style_button = tk.Button(
            self.button_frame, text="Kolor", command=self.change_line_style,
            bg="#3F51B5", fg="white", font=("Arial", 10, "bold"), width=10
        )
        self.style_button.pack(side=tk.LEFT, padx=(0, 5))

        self.font_button = tk.Button(
            self.button_frame, text="Czcionka", command=self.choose_font,
            bg="#009688", fg="white", font=("Arial", 10, "bold"), width=10
        )
        self.font_button.pack(side=tk.LEFT, padx=(0, 5))

        self.exit_button = tk.Button(
            self.button_frame, text="Zamknij", command=self.on_close,
            bg="#9E9E9E", fg="white", font=("Arial", 10, "bold"), width=10
        )
        self.exit_button.pack(side=tk.LEFT, padx=(0, 5))

        self.instruction_label = tk.Label(
            self.main_frame,
            text="↑/↓ przesuwanie | Dwuklik: otwarcie linku | Kolor: zmiana tła/czcionki",
            font=("Arial", 8),
            fg="gray"
        )
        self.instruction_label.pack(pady=(5, 0))

        # Bindy
        self.text_widget.bind("<Button-1>", self.select_line)
        self.text_widget.bind("<Double-Button-1>", self.handle_double_click)
        self.text_widget.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Up>", self.move_note_up)
        self.root.bind("<Down>", self.move_note_down)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # startowe wczytania
        self.load_data()
        self.restore_font()
        self.restore_geometry(self.root, "MAIN_WINDOW")
        self.load_styles()

    # ---------- CZCIONKA ----------
    def choose_font(self):
        result = askfont(self.root)
        if result:
            family = result["family"]
            size = result["size"]
            self.current_font = (family, size)
            self.text_widget.config(font=self.current_font)
            self.save_font(family, size)

    def save_font(self, family, size):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = [l for l in file.readlines() if not l.startswith("#FONT#")]
        else:
            lines = []
        with open(self.data_file, "w", encoding="utf-8") as file:
            file.writelines(lines)
            file.write(f"#FONT#{family},{size}\n")

    def restore_font(self):
        if not os.path.exists(self.data_file):
            return
        with open(self.data_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
        for line in reversed(lines):
            if line.startswith("#FONT#"):
                try:
                    family, size = line.strip().split("#FONT#")[1].split(",")
                    self.current_font = (family, int(size))
                    self.text_widget.config(font=self.current_font)
                except:
                    pass
                break

    # ---------- STYL LINII ----------
    def change_line_style(self):
        """Wywoływane po kliknięciu 'Kolor' - wybiera kolory i przypisuje tag linii"""
        line_num, _ = self.get_selected_line()
        if not line_num:
            messagebox.showinfo("Informacja", "Najpierw zaznacz linię do zmiany koloru.")
            return
        bg_color = colorchooser.askcolor(title="Wybierz kolor tła")[1]
        fg_color = colorchooser.askcolor(title="Wybierz kolor czcionki")[1]
        if not bg_color or not fg_color:
            return

        tag_name = f"line_{line_num}"
        self.text_widget.tag_config(tag_name, background=bg_color, foreground=fg_color)
        # zakreślamy dokładnie do końca linii (nie dodajemy końcowego \n)
        self.text_widget.tag_add(tag_name, f"{line_num}.0", f"{line_num}.end")
        self.save_style(line_num, bg_color, fg_color)

    def save_style(self, line_num, bg, fg):
        """Zapis pojedynczego stylu do pliku (nadpisuje lub dopisuje)"""
        styles = self.load_style_dict()
        styles[int(line_num)] = (bg, fg)
        with open(self.style_file, "w", encoding="utf-8") as f:
            for ln in sorted(styles.keys()):
                b, fgc = styles[ln]
                f.write(f"{ln}|{b}|{fgc}\n")

    def load_styles(self):
        """Wczytuje style z pliku i aplikuje tagi do widgetu"""
        if not os.path.exists(self.style_file):
            return
        with open(self.style_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    parts = line.strip().split("|")
                    if len(parts) != 3:
                        continue
                    line_num_str, bg, fg = parts
                    line_num = int(line_num_str)
                    tag_name = f"line_{line_num}"
                    self.text_widget.tag_config(tag_name, background=bg, foreground=fg)
                    self.text_widget.tag_add(tag_name, f"{line_num}.0", f"{line_num}.end")
                except Exception:
                    # ignoruj błędy parsowania
                    pass

    def load_style_dict(self):
        """Zwraca dict {line_num: (bg, fg)}"""
        d = {}
        if not os.path.exists(self.style_file):
            return d
        with open(self.style_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ln, bg, fg = line.strip().split("|")
                    d[int(ln)] = (bg, fg)
                except:
                    pass
        return d

    def reconcile_and_save_styles(self, old_lines, new_lines):
        """
        Przy próbie zachowania stylów po zmianie kolejności/edycji:
        - mapuje style z old_lines do new_lines na podstawie pierwszego dopasowania treści.
        - zapisuje wynik do style_file.
        """
        old_styles = self.load_style_dict()  # klucze int -> (bg,fg)
        # mapowanie treści -> lista pozycji w old_lines
        content_positions = {}
        for idx, text in enumerate(old_lines, start=1):
            content_positions.setdefault(text.rstrip("\n"), []).append(idx)

        new_styles = {}
        used_old_positions = set()
        for new_idx, new_text in enumerate(new_lines, start=1):
            candidates = content_positions.get(new_text.rstrip("\n"), [])
            # wybieramy pierwszego nieużytego kandydata
            chosen = None
            for c in candidates:
                if c not in used_old_positions:
                    chosen = c
                    break
            if chosen and chosen in old_styles:
                new_styles[new_idx] = old_styles[chosen]
                used_old_positions.add(chosen)
        # zapis nowych styli
        with open(self.style_file, "w", encoding="utf-8") as f:
            for ln in sorted(new_styles.keys()):
                b, fg = new_styles[ln]
                f.write(f"{ln}|{b}|{fg}\n")

    # ---------- NOTATKI ----------
    def is_link(self, text):
        return text.strip().lower().startswith(('http://', 'https://', 'www.')) if text else False

    def on_mouse_move(self, event):
        try:
            index = self.text_widget.index(f"@{event.x},{event.y}")
            line_num = int(index.split('.')[0])
            line_text = self.text_widget.get(f"{line_num}.0", f"{line_num}.end").strip()
            self.text_widget.config(cursor="hand2" if self.is_link(line_text) else "arrow")
        except Exception:
            pass

    def select_line(self, event):
        try:
            index = self.text_widget.index(f"@{event.x},{event.y}")
            line_num = int(index.split('.')[0])
            self.text_widget.tag_remove("sel", "1.0", tk.END)
            self.text_widget.tag_add("sel", f"{line_num}.0", f"{line_num}.end+1c")
            self.text_widget.see(f"{line_num}.0")
            return "break"
        except Exception:
            return

    def handle_double_click(self, event):
        _, selected_text = self.get_selected_line()
        if selected_text:
            if self.is_link(selected_text):
                self.open_link(selected_text)
            else:
                self.copy_to_clipboard()
            self.root.iconify()
        return "break"

    def open_link(self, link_text):
        try:
            formatted_link = link_text.strip()
            if formatted_link.startswith('www.'):
                formatted_link = 'http://' + formatted_link
            webbrowser.open(formatted_link)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć linku: {str(e)}")

    def copy_to_clipboard(self):
        _, selected_text = self.get_selected_line()
        if selected_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)

    def get_selected_line(self):
        try:
            if self.text_widget.tag_ranges("sel"):
                start_index = self.text_widget.index("sel.first")
                end_index = self.text_widget.index("sel.last")
                line_num = int(start_index.split('.')[0])
                selected_text = self.text_widget.get(start_index, end_index).strip()
                return line_num, selected_text
        except Exception:
            pass
        return None, None

    def move_note_up(self, event):
        line_num, selected_text = self.get_selected_line()
        if selected_text and line_num > 1:
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
            if line_num <= len(lines):
                # swap
                lines[line_num - 1], lines[line_num - 2] = lines[line_num - 2], lines[line_num - 1]
                # zapisz i postaraj się zrekoncilować style
                self._save_with_geometry_and_styles(lines)
                self.load_data()
                # zaznacz nową pozycję
                self.text_widget.tag_remove("sel", "1.0", tk.END)
                self.text_widget.tag_add("sel", f"{line_num-1}.0", f"{line_num-1}.end+1c")
                self.text_widget.see(f"{line_num-1}.0")
        return "break"

    def move_note_down(self, event):
        line_num, selected_text = self.get_selected_line()
        if selected_text:
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
            if line_num < len(lines):
                lines[line_num - 1], lines[line_num] = lines[line_num], lines[line_num - 1]
                self._save_with_geometry_and_styles(lines)
                self.load_data()
                self.text_widget.tag_remove("sel", "1.0", tk.END)
                self.text_widget.tag_add("sel", f"{line_num+1}.0", f"{line_num+1}.end+1c")
                self.text_widget.see(f"{line_num+1}.0")
        return "break"

    def add_note(self):
        self.open_edit_window("Dopisz notatkę", "", is_add=True)

    def edit_note(self):
        line_num, selected_text = self.get_selected_line()
        if selected_text:
            self.open_edit_window("Modyfikuj notatkę", selected_text, line_num, is_add=False)
        else:
            messagebox.showwarning("Ostrzeżenie", "Najpierw zaznacz linię do modyfikacji")

    def delete_note(self):
        line_num, selected_text = self.get_selected_line()
        if selected_text and messagebox.askyesno("Potwierdzenie", f"Czy usunąć notatkę?\n\n{selected_text}"):
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
            if 0 < line_num <= len(lines):
                del lines[line_num - 1]
            self._save_with_geometry_and_styles(lines)
            self.load_data()

    def open_edit_window(self, title, initial_text, line_num=None, is_add=True):
        edit_window = tk.Toplevel(self.root)
        edit_window.title(title)
        edit_window.geometry("400x250")
        edit_window.transient(self.root)
        edit_window.grab_set()
        edit_window.protocol("WM_DELETE_WINDOW", lambda win=edit_window: self.on_close_edit(win))

        edit_frame = tk.Frame(edit_window, padx=10, pady=10)
        edit_frame.pack(fill=tk.BOTH, expand=True)

        text_entry = tk.Text(edit_frame, height=6, width=40, font=self.current_font, wrap=tk.WORD)
        text_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_entry.insert("1.0", initial_text)
        text_entry.focus_set()
        text_entry.tag_add("sel", "1.0", tk.END)

        save_button = tk.Button(
            edit_frame, text="Zapisz",
            command=lambda: self.save_note(text_entry, edit_window, line_num),
            bg=self.selection_color, fg="white", font=("Arial", 10, "bold"), width=10
        )
        save_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = tk.Button(
            edit_frame, text="Anuluj",
            command=lambda win=edit_window: self.on_close_edit(win),
            bg="#9E9E9E", fg="white", font=("Arial", 10, "bold"), width=10
        )
        cancel_button.pack(side=tk.LEFT)

        self.restore_geometry(edit_window, "EDIT_WINDOW")

    def save_note(self, text_entry, edit_window, line_num=None):
        text_content = text_entry.get("1.0", tk.END).strip()
        if not text_content:
            return
        with open(self.data_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
        if line_num is not None and 0 < line_num <= len(lines):
            lines[line_num - 1] = text_content + "\n"
        else:
            lines.append(text_content + "\n")
        self._save_with_geometry_and_styles(lines)
        self.load_data()
        self.on_close_edit(edit_window)

    def load_data(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
            content = "".join([l for l in lines if not l.startswith("#GEOMETRY#") and not l.startswith("#FONT#")])
            self.text_widget.insert("1.0", content)
        self.text_widget.config(state=tk.DISABLED)
        # po wczytaniu danych przywracamy style
        self.load_styles()

    # ---------- GEOMETRIA ----------
    def on_close(self):
        self.save_geometry(self.root, "MAIN_WINDOW")
        self.root.destroy()

    def on_close_edit(self, win):
        self.save_geometry(win, "EDIT_WINDOW")
        win.destroy()

    def save_geometry(self, window, tag):
        geom = window.geometry()
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = [l for l in file.readlines() if not l.startswith(f"#GEOMETRY#{tag}:")]
        else:
            lines = []
        geometry_lines = [l for l in lines if l.startswith("#GEOMETRY#")]
        note_lines = [l for l in lines if not l.startswith("#GEOMETRY#")]
        with open(self.data_file, "w", encoding="utf-8") as file:
            file.writelines(note_lines)
            file.write(f"#GEOMETRY#{tag}:{geom}\n")
            for l in geometry_lines:
                file.write(l)

    def restore_geometry(self, window, tag):
        if not os.path.exists(self.data_file):
            return
        with open(self.data_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
        for line in reversed(lines):
            if line.startswith(f"#GEOMETRY#{tag}:"):
                geom = line.strip().split(":", 1)[1]
                window.geometry(geom)
                break

    # ---------- ZAPIS NOTATEK + ZACHOWANIE STYLI ----------
    def _save_with_geometry_and_styles(self, note_lines):
        """
        Zapisuje note_lines do dane.txt zachowując #GEOMETRY# i #FONT#.
        Dodatkowo rekoncyliuje style (style.txt) względem nowej zawartości.
        """
        # odczytaj stare linie (by dopasować style)
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                old_lines = file.readlines()
        else:
            old_lines = []

        geometry_lines = [l for l in old_lines if l.startswith("#GEOMETRY#")]
        font_lines = [l for l in old_lines if l.startswith("#FONT#")]

        # zapis notatek bez #GEOMETRY#/#FONT#
        with open(self.data_file, "w", encoding="utf-8") as file:
            file.writelines([l for l in note_lines if not l.startswith("#GEOMETRY#") and not l.startswith("#FONT#")])
            for l in font_lines:
                file.write(l)
            for l in geometry_lines:
                file.write(l)

        # rekoncyliujemy style: spróbuj przypisać stare style do nowych pozycji na podstawie treści
        # old_note_lines -> new_note_lines
        old_note_lines = [l for l in old_lines if not l.startswith("#GEOMETRY#") and not l.startswith("#FONT#")]
        new_note_lines = [l for l in note_lines if not l.startswith("#GEOMETRY#") and not l.startswith("#FONT#")]
        self.reconcile_and_save_styles(old_note_lines, new_note_lines)

    # ---------- POMOCNICZE ----------
    def _save_with_geometry(self, note_lines):
        """Zachowany dla kompatybilności — zapis bez rekoncyliacji styli."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as file:
                lines = file.readlines()
        else:
            lines = []
        geometry_lines = [l for l in lines if l.startswith("#GEOMETRY#") or l.startswith("#FONT#")]
        with open(self.data_file, "w", encoding="utf-8") as file:
            file.writelines([l for l in note_lines if not l.startswith("#GEOMETRY#") and not l.startswith("#FONT#")])
            for l in geometry_lines:
                file.write(l)


def main():
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
