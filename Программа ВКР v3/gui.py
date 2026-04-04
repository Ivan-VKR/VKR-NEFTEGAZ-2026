"""Графический интерфейс приложения на Tkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from calculations import InputData, run_calculation
from data_products import get_product, get_product_names
from data_tanks import get_available_volumes, get_tank_template
from recommendations import build_final_package, format_result_text
from reporting import save_txt_report, save_xlsx_report


class TankApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Расчетный модуль резервуарного парка")
        self.geometry("1460x920")
        self.minsize(1300, 820)

        self.current_package: Optional[dict] = None
        self.current_report_text: str = ""

        self._configure_styles()
        self._create_widgets()
        self._set_defaults()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Card.TLabelframe", padding=14)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        style.configure("Primary.TButton", padding=(20, 12))
        style.configure("Action.TButton", padding=(16, 12))

    def _create_widgets(self) -> None:
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        top_frame = ttk.LabelFrame(container, text="Исходные данные", style="Card.TLabelframe")
        top_frame.grid(row=0, column=0, sticky="nsew")

        for col in range(4):
            top_frame.columnconfigure(col, weight=1)

        self.volume_var = tk.StringVar()
        self.product_var = tk.StringVar()
        self.wind_region_var = tk.StringVar()
        self.snow_region_var = tk.StringVar()
        self.terrain_var = tk.StringVar()
        self.ambient_min_var = tk.StringVar()
        self.ambient_max_var = tk.StringVar()
        self.product_temp_var = tk.StringVar()
        self.heating_mode_var = tk.StringVar()
        self.service_life_var = tk.StringVar()
        self.corrosion_var = tk.StringVar()

        fields = [
            ("Номинальный объем резервуара, м³:", "volume"),
            ("Нефтепродукт:", "product"),
            ("Ветровой район:", "wind"),
            ("Снеговой район:", "snow"),
            ("Тип местности:", "terrain"),
            ("Температура продукта, °C:", "product_temp"),
            ("Макс. температура воздуха, °C:", "ambient_max"),
            ("Срок службы, лет:", "service_life"),
            ("Мин. температура воздуха, °C:", "ambient_min"),
            ("Режим подогрева:", "heating_mode"),
            ("Категория коррозионной среды:", "corrosion"),
        ]

        for index, (label_text, field_key) in enumerate(fields):
            row = index // 2
            col_base = (index % 2) * 2
            ttk.Label(top_frame, text=label_text).grid(row=row, column=col_base, sticky="w", padx=10, pady=10)

            if field_key == "volume":
                widget = ttk.Combobox(top_frame, textvariable=self.volume_var, state="readonly", width=36)
                widget["values"] = [str(v) for v in get_available_volumes()]
            elif field_key == "product":
                widget = ttk.Combobox(top_frame, textvariable=self.product_var, state="readonly", width=36)
                widget["values"] = get_product_names()
            elif field_key == "wind":
                widget = ttk.Combobox(top_frame, textvariable=self.wind_region_var, state="readonly", width=36)
                widget["values"] = ["I", "II", "III", "IV", "V", "VI", "VII"]
            elif field_key == "snow":
                widget = ttk.Combobox(top_frame, textvariable=self.snow_region_var, state="readonly", width=36)
                widget["values"] = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
            elif field_key == "terrain":
                widget = ttk.Combobox(top_frame, textvariable=self.terrain_var, state="readonly", width=36)
                widget["values"] = ["A", "B", "C"]
            elif field_key == "ambient_min":
                widget = ttk.Entry(top_frame, textvariable=self.ambient_min_var, width=38)
            elif field_key == "ambient_max":
                widget = ttk.Entry(top_frame, textvariable=self.ambient_max_var, width=38)
            elif field_key == "product_temp":
                widget = ttk.Entry(top_frame, textvariable=self.product_temp_var, width=38)
            elif field_key == "heating_mode":
                widget = ttk.Combobox(top_frame, textvariable=self.heating_mode_var, state="readonly", width=36)
                widget["values"] = ["без подогрева", "периодический подогрев", "постоянный подогрев"]
            elif field_key == "service_life":
                widget = ttk.Entry(top_frame, textvariable=self.service_life_var, width=38)
            else:
                widget = ttk.Combobox(top_frame, textvariable=self.corrosion_var, state="readonly", width=36)
                widget["values"] = ["низкая", "средняя", "высокая"]

            widget.grid(row=row, column=col_base + 1, sticky="ew", padx=10, pady=10)

        button_frame = ttk.Frame(container)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(8, 14))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=1)

        buttons_inner = ttk.Frame(button_frame)
        buttons_inner.grid(row=0, column=1)

        ttk.Button(buttons_inner, text="Выполнить расчет", command=self.calculate, style="Primary.TButton").grid(row=0, column=0, padx=6)
        ttk.Button(buttons_inner, text="Сохранить TXT", command=self.save_txt, style="Action.TButton").grid(row=0, column=1, padx=6)
        ttk.Button(buttons_inner, text="Сохранить XLSX", command=self.save_xlsx, style="Action.TButton").grid(row=0, column=2, padx=6)
        ttk.Button(buttons_inner, text="Очистить", command=self.clear_output, style="Action.TButton").grid(row=0, column=3, padx=6)

        output_frame = ttk.LabelFrame(container, text="Результаты", style="Card.TLabelframe")
        output_frame.grid(row=2, column=0, sticky="nsew")
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(output_frame, wrap="word", font=("Consolas", 11), padx=12, pady=12)
        self.output_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)

    def _set_defaults(self) -> None:
        volumes = [str(v) for v in get_available_volumes()]
        if volumes:
            self.volume_var.set(volumes[0])
        self.product_var.set("Jet A-1")
        self.wind_region_var.set("III")
        self.snow_region_var.set("III")
        self.terrain_var.set("B")
        self.ambient_min_var.set("-25")
        self.ambient_max_var.set("30")
        self.product_temp_var.set("20")
        self.heating_mode_var.set("без подогрева")
        self.service_life_var.set("20")
        self.corrosion_var.set("средняя")

    def _collect_input(self) -> InputData:
        try:
            service_life = int(self.service_life_var.get())
            ambient_min = float(self.ambient_min_var.get().replace(",", "."))
            ambient_max = float(self.ambient_max_var.get().replace(",", "."))
            product_temp = float(self.product_temp_var.get().replace(",", "."))
        except ValueError as exc:
            raise ValueError("Проверьте числовые поля: срок службы и температуры должны быть заполнены корректно.") from exc

        return InputData(
            nominal_volume_m3=int(self.volume_var.get()),
            product_name=self.product_var.get(),
            wind_region=self.wind_region_var.get(),
            snow_region=self.snow_region_var.get(),
            terrain_type=self.terrain_var.get(),
            ambient_temp_min_c=ambient_min,
            ambient_temp_max_c=ambient_max,
            product_temp_c=product_temp,
            heating_mode=self.heating_mode_var.get(),
            service_life_years=service_life,
            corrosion_category=self.corrosion_var.get(),
        )

    def calculate(self) -> None:
        try:
            input_data = self._collect_input()
            template = get_tank_template(input_data.nominal_volume_m3)
            product = get_product(input_data.product_name)
            calculation_result = run_calculation(input_data, template, product)
            package = build_final_package(input_data, template, product, calculation_result)
            report_text = format_result_text(package)

            self.current_package = package
            self.current_report_text = report_text
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, report_text)
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))

    def save_txt(self) -> None:
        if not self.current_report_text:
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
        self.output_text.delete("1.0", tk.END)


if __name__ == "__main__":
    app = TankApp()
    app.mainloop()
