"""Графический интерфейс приложения на Tkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from calculations import InputData, run_calculation
from data_locations import get_city_names, get_city_profile
from data_products import get_product, get_product_names
from data_tanks import get_available_volumes, get_tank_template
from recommendations import build_final_package, format_log_text, format_result_text
from reporting import save_txt_report, save_xlsx_report


SPLASH_TITLE = "Расчетно-рекомендательный модуль резервуарного парка"
SPLASH_AUTHOR = "Автор: Шамаев Иван Никитич"
SPLASH_DETAILS = "Выполнено в рамках ВКР, 2026 год\nДальневосточный федеральный университет (ДВФУ)"


class TankApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Расчетный модуль резервуарного парка")
        self.geometry("1460x920")
        self.minsize(1300, 820)
        self._maximize_window()

        self.current_package: Optional[dict] = None
        self.current_report_text: str = ""
        self.current_log_text: str = ""
        self.city_names = get_city_names()
        self.city_combo: Optional[ttk.Combobox] = None

        self._configure_styles()
        self._create_widgets()
        self._set_defaults()

    def _maximize_window(self) -> None:
        try:
            self.state("zoomed")
        except tk.TclError:
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f"{width}x{height}+0+0")

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Primary.TButton", padding=(20, 12))
        style.configure("Action.TButton", padding=(16, 12))

    def _create_widgets(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        input_title = ttk.Label(container, text="Исходные данные", style="SectionTitle.TLabel")
        input_title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        input_card = tk.Frame(container, bd=1, relief="solid", background="#f5f5f5")
        input_card.grid(row=1, column=0, sticky="nsew")
        for col in range(4):
            input_card.columnconfigure(col, weight=1)

        self.volume_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.city_info_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.product_temp_var = tk.StringVar()
        self.heating_mode_var = tk.StringVar()
        self.service_life_var = tk.StringVar()
        self.corrosion_var = tk.StringVar()

        left_fields = [
            ("Номинальный объем резервуара, м³:", "volume"),
            ("Город:", "city"),
            ("Автоподбор климатических параметров:", "city_info"),
            ("Температура продукта, °C:", "product_temp"),
        ]
        right_fields = [
            ("Нефтепродукт:", "product"),
            ("Режим подогрева:", "heating_mode"),
            ("Срок службы, лет:", "service_life"),
            ("Категория коррозионной среды:", "corrosion"),
        ]

        for row, (label_text, field_key) in enumerate(left_fields):
            self._add_field(input_card, row, 0, label_text, field_key)
        for row, (label_text, field_key) in enumerate(right_fields):
            self._add_field(input_card, row, 2, label_text, field_key)

        button_frame = ttk.Frame(container)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(16, 18))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=1)

        buttons_inner = ttk.Frame(button_frame)
        buttons_inner.grid(row=0, column=1)

        ttk.Button(buttons_inner, text="Выполнить расчет", command=self.calculate, style="Primary.TButton").grid(row=0, column=0, padx=6)
        ttk.Button(buttons_inner, text="Сохранить TXT", command=self.save_txt, style="Action.TButton").grid(row=0, column=1, padx=6)
        ttk.Button(buttons_inner, text="Сохранить XLSX", command=self.save_xlsx, style="Action.TButton").grid(row=0, column=2, padx=6)
        ttk.Button(buttons_inner, text="Логи", command=self.show_logs, style="Action.TButton").grid(row=0, column=3, padx=6)
        ttk.Button(buttons_inner, text="Очистить", command=self.clear_output, style="Action.TButton").grid(row=0, column=4, padx=6)

        output_title = ttk.Label(container, text="Результаты", style="SectionTitle.TLabel")
        output_title.grid(row=3, column=0, sticky="w", pady=(14, 6))

        output_card = tk.Frame(container, bd=1, relief="solid", background="#f5f5f5")
        output_card.grid(row=4, column=0, sticky="nsew")
        output_card.rowconfigure(0, weight=1)
        output_card.columnconfigure(0, weight=1)

        self.output_text = tk.Text(output_card, wrap="word", font=("Consolas", 11), padx=12, pady=12, bd=0)
        self.output_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(output_card, command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)

    def _add_field(self, parent: tk.Frame, row: int, col_base: int, label_text: str, field_key: str) -> None:
        ttk.Label(parent, text=label_text, background="#f5f5f5").grid(row=row, column=col_base, sticky="w", padx=18, pady=12)
        widget = self._make_widget(parent, field_key)
        widget.grid(row=row, column=col_base + 1, sticky="ew", padx=(10, 18), pady=12)

    def _make_widget(self, parent: tk.Frame, field_key: str):
        if field_key == "volume":
            widget = ttk.Combobox(parent, textvariable=self.volume_var, state="readonly", width=38)
            widget["values"] = [str(v) for v in get_available_volumes()]
            return widget
        if field_key == "city":
            widget = ttk.Combobox(parent, textvariable=self.city_var, state="normal", width=38)
            widget["values"] = self.city_names
            widget.bind("<<ComboboxSelected>>", lambda _event: self._update_city_info())
            widget.bind("<KeyRelease>", self._on_city_keyrelease)
            widget.bind("<FocusOut>", lambda _event: self._update_city_info())
            self.city_combo = widget
            return widget
        if field_key == "city_info":
            return ttk.Entry(parent, textvariable=self.city_info_var, width=40, state="readonly")
        if field_key == "product":
            widget = ttk.Combobox(parent, textvariable=self.product_var, state="readonly", width=38)
            widget["values"] = get_product_names()
            return widget
        if field_key == "product_temp":
            return ttk.Entry(parent, textvariable=self.product_temp_var, width=40)
        if field_key == "heating_mode":
            widget = ttk.Combobox(parent, textvariable=self.heating_mode_var, state="readonly", width=38)
            widget["values"] = [
                "автоматически",
                "без подогрева",
                "периодический подогрев",
                "постоянный подогрев",
            ]
            return widget
        if field_key == "service_life":
            return ttk.Entry(parent, textvariable=self.service_life_var, width=40)
        widget = ttk.Combobox(parent, textvariable=self.corrosion_var, state="readonly", width=38)
        widget["values"] = ["автоматически (рекомендуется)", "умеренная", "средняя", "повышенная"]
        return widget

    def _set_defaults(self) -> None:
        self.volume_var.set("")
        self.city_var.set("")
        self.city_info_var.set("")
        self.product_var.set("")
        self.product_temp_var.set("")
        self.heating_mode_var.set("")
        self.service_life_var.set("")
        self.corrosion_var.set("")
        if self.city_combo is not None:
            self.city_combo["values"] = self.city_names

    def _filter_city_names(self, text: str) -> list[str]:
        text = text.strip().lower()
        if not text:
            return self.city_names
        starts = [name for name in self.city_names if name.lower().startswith(text)]
        if starts:
            return starts
        contains = [name for name in self.city_names if text in name.lower()]
        return contains if contains else self.city_names

    def _resolve_city_name(self) -> Optional[str]:
        raw = self.city_var.get().strip()
        if not raw:
            return None
        exact = [name for name in self.city_names if name.lower() == raw.lower()]
        if exact:
            return exact[0]
        prefix = [name for name in self.city_names if name.lower().startswith(raw.lower())]
        if len(prefix) == 1:
            return prefix[0]
        return None

    def _on_city_keyrelease(self, event: tk.Event) -> None:
        if event.keysym in {"Up", "Down", "Left", "Right", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}:
            return
        if self.city_combo is None:
            return
        current_text = self.city_var.get()
        matches = self._filter_city_names(current_text)
        self.city_combo["values"] = matches
        resolved = self._resolve_city_name()
        if resolved:
            profile = get_city_profile(resolved)
            self.city_info_var.set(
                f"ветер {profile.wind_region}; снег {profile.snow_region}; местность {profile.terrain_type}; "
                f"tвозд {profile.ambient_temp_min_c:.0f}…{profile.ambient_temp_max_c:.0f} °C"
            )
        elif current_text.strip():
            self.city_info_var.set(f"Подходящих городов: {len(matches)}")
        else:
            self.city_info_var.set("")

    def _update_city_info(self) -> None:
        resolved = self._resolve_city_name()
        if not resolved:
            if self.city_var.get().strip():
                matches = self._filter_city_names(self.city_var.get())
                self.city_info_var.set(f"Подходящих городов: {len(matches)}")
            else:
                self.city_info_var.set("")
            return
        if self.city_var.get() != resolved:
            self.city_var.set(resolved)
        profile = get_city_profile(resolved)
        self.city_info_var.set(
            f"ветер {profile.wind_region}; снег {profile.snow_region}; местность {profile.terrain_type}; "
            f"tвозд {profile.ambient_temp_min_c:.0f}…{profile.ambient_temp_max_c:.0f} °C"
        )

    def _collect_input(self) -> InputData:
        if not self.volume_var.get().strip():
            raise ValueError("Выберите номинальный объем резервуара.")
        if not self.product_var.get().strip():
            raise ValueError("Выберите нефтепродукт.")
        resolved_city = self._resolve_city_name()
        if not resolved_city:
            raise ValueError("Выберите город из списка или введите его название корректно.")
        try:
            service_life = int(self.service_life_var.get())
            product_temp = float(self.product_temp_var.get().replace(",", "."))
        except ValueError as exc:
            raise ValueError("Проверьте числовые поля: срок службы и температура продукта должны быть заполнены корректно.") from exc

        profile = get_city_profile(resolved_city)
        self.city_var.set(resolved_city)
        self._update_city_info()

        heating_mode = self.heating_mode_var.get().strip() or "автоматически"
        corrosion_category = self.corrosion_var.get().strip() or "автоматически (рекомендуется)"

        return InputData(
            city_name=profile.name,
            nominal_volume_m3=int(self.volume_var.get()),
            product_name=self.product_var.get(),
            wind_region=profile.wind_region,
            snow_region=profile.snow_region,
            terrain_type=profile.terrain_type,
            ambient_temp_min_c=profile.ambient_temp_min_c,
            ambient_temp_max_c=profile.ambient_temp_max_c,
            product_temp_c=product_temp,
            heating_mode=heating_mode,
            service_life_years=service_life,
            corrosion_category=corrosion_category,
        )

    def calculate(self) -> None:
        try:
            input_data = self._collect_input()
            template = get_tank_template(input_data.nominal_volume_m3)
            product = get_product(input_data.product_name)
            calculation_result = run_calculation(input_data, template, product)
            package = build_final_package(input_data, template, product, calculation_result)
            result_text = format_result_text(package)
            log_text = format_log_text(package)
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        self.current_package = package
        self.current_report_text = result_text
        self.current_log_text = log_text
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result_text)

    def show_logs(self) -> None:
        if not self.current_log_text:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет.")
            return
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", self.current_log_text)

    def save_txt(self) -> None:
        if not self.current_package or not self.current_report_text:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Сохранить отчет в TXT",
        )
        if file_path:
            save_txt_report(file_path, self.current_report_text)
            messagebox.showinfo("Готово", "Отчет сохранен в TXT.")

    def save_xlsx(self) -> None:
        if not self.current_package or not self.current_report_text:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Сохранить отчет в XLSX",
        )
        if file_path:
            save_xlsx_report(file_path, self.current_package, self.current_report_text)
            messagebox.showinfo("Готово", "Отчет сохранен в XLSX.")

    def clear_output(self) -> None:
        self.current_package = None
        self.current_report_text = ""
        self.current_log_text = ""
        self.output_text.delete("1.0", tk.END)
        self._set_defaults()


def launch_application() -> None:
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#ffffff")

    width, height = 760, 300
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x_pos = int((screen_w - width) / 2)
    y_pos = int((screen_h - height) / 2)
    splash.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

    card = tk.Frame(splash, bg="#ffffff", bd=1, relief="solid")
    card.pack(fill="both", expand=True, padx=14, pady=14)

    tk.Label(card, text=SPLASH_TITLE, font=("Segoe UI", 16, "bold"), bg="#ffffff").pack(pady=(42, 18))
    tk.Label(card, text=SPLASH_AUTHOR, font=("Segoe UI", 12), bg="#ffffff").pack(pady=(0, 10))
    tk.Label(card, text=SPLASH_DETAILS, font=("Segoe UI", 11), bg="#ffffff", justify="center").pack()

    def start_main() -> None:
        splash.destroy()
        app = TankApp()
        app.mainloop()

    splash.after(2500, start_main)
    splash.mainloop()


if __name__ == "__main__":
    launch_application()
