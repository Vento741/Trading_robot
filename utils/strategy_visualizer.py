import tkinter as tk
from tkinter import ttk
import threading

class StrategyVisualizer:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.window = None
        self.pair_frames = {}
        self.column_frames = []

    def create_window(self):
        self.window = tk.Tk()
        self.window.title(f"Визуализация стратегии: {self.strategy_name}")
        self.window.geometry("1800x800")  # Увеличиваем ширину окна

        # Создаем главный фрейм с прокруткой
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=1)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        main_frame.pack(fill=tk.BOTH, expand=1)
        canvas.pack(side="left", fill=tk.BOTH, expand=1)
        scrollbar.pack(side="right", fill="y")

        # Создаем три колонки
        for _ in range(3):
            column_frame = ttk.Frame(self.scrollable_frame)
            column_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=5)
            self.column_frames.append(column_frame)

    def create_pair_frame(self, symbol):
        # Выбираем колонку с наименьшим количеством пар
        column_frame = min(self.column_frames, key=lambda f: len(f.winfo_children()))
        
        frame = ttk.LabelFrame(column_frame, text=symbol)
        frame.pack(padx=5, pady=5, fill=tk.X)

        conditions_frame = ttk.Frame(frame)
        conditions_frame.pack(side=tk.LEFT, padx=5, pady=5)

        position_frame = ttk.Frame(frame)
        position_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        conditions = ["RSI", "Цена", "Объем", "Тренд", "ATR"]
        labels = {}
        for condition in conditions:
            label = ttk.Label(conditions_frame, text=f"{condition}: ")
            label.pack(anchor="w")
            labels[condition] = label

        position_labels = ["Позиция", "SL", "TP", "Цена входа", "Текущая цена", "Цена добора", "Частичное закрытие"]
        position_info = {}
        for label in position_labels:
            info = ttk.Label(position_frame, text=f"{label}: ")
            info.pack(anchor="w")
            position_info[label] = info

        self.pair_frames[symbol] = {
            "frame": frame,
            "conditions": labels,
            "position": position_info
        }

    def update_data(self, symbol, conditions, position_data):
        if symbol not in self.pair_frames:
            self.create_pair_frame(symbol)

        frame_data = self.pair_frames[symbol]

        for condition, value in conditions.items():
            if condition in frame_data["conditions"]:
                label = frame_data["conditions"][condition]
                if isinstance(value, float):
                    text = f"{condition}: {value:.2f}"
                else:
                    text = f"{condition}: {value}"
                label.config(text=text)
                
                # Устанавливаем цвет в зависимости от условия
                if condition == "RSI":
                    color = "green" if 30 <= value <= 70 else "red"
                elif condition == "Тренд":
                    color = "green" if value > 0 else "red"
                else:
                    color = "black"
                label.config(foreground=color)

        for key, value in position_data.items():
            if key in frame_data["position"]:
                label = frame_data["position"][key]
                if isinstance(value, float):
                    text = f"{key}: {value:.2f}"
                else:
                    text = f"{key}: {value}"
                label.config(text=text)
                
                # Устанавливаем цвет для текущей цены
                if key == "Текущая цена":
                    entry_price = position_data.get("Цена входа", 0)
                    position_type = position_data.get("Позиция", "Нет")
                    if position_type == "LONG":
                        color = "green" if value > entry_price else "red"
                    elif position_type == "SHORT":
                        color = "green" if value < entry_price else "red"
                    else:
                        color = "black"
                    label.config(foreground=color)

    def run(self):
        if self.window is None:
            self.create_window()
        self.window.mainloop()

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

visualizer = None

def initialize_visualizer(strategy_name):
    global visualizer
    visualizer = StrategyVisualizer(strategy_name)
    visualizer.start()

def update_visualizer(symbol, conditions, position_data):
    if visualizer:
        visualizer.window.after(0, visualizer.update_data, symbol, conditions, position_data)