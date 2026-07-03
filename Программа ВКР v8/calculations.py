"""Расчетный модуль приложения.

Принцип:
- геометрия берется из встроенного типового каталога;
- ветровые и снеговые районы берутся по упрощенным табличным значениям СП 20.13330.2016;
- температурный блок учитывается через реальные параметры наружного воздуха,
  температуру продукта и режим подогрева;
- температура в данной версии используется прежде всего для оценки испарительных потерь,
  риска конденсации и рекомендаций по покрытиям;
- проверка стенки и кровли выполнена в демонстрационно-инженерной форме,
  пригодной для ВКР как предварительный расчетно-рекомендательный модуль;
- для рабочего проектирования необходима полная нормативная детализация.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, pi
from typing import Dict, List, Tuple

from data_norms import (
    AUTOMATIC_CORROSION_VALUES,
    CORROSION_ALLOWANCE_MM,
    CYLINDER_AERODYNAMIC_COEFFICIENT,
    LOAD_RELIABILITY_FACTOR,
    NORMATIVE_REFERENCES,
    ROOF_ALLOWABLE_SNOW_KPA,
    SHEET_FORMATS,
    SNOW_LOAD_BY_REGION,
    SNOW_SHAPE_COEFFICIENTS,
    STANDARD_PLATE_THICKNESSES_MM,
    STEEL_ALLOWABLE_STRESS_MPA,
    STEEL_DENSITY_KG_M3,
    STEEL_ELASTIC_MODULUS_MPA,
    STEEL_OPTIONS,
    TERRAIN_COEFFICIENTS,
    WIND_PRESSURE_BY_REGION,
    WIND_RING_DIAMETER_TRIGGER_M,
    WIND_RING_WIND_REGION_TRIGGER,
)
from data_products import ProductData
from data_tanks import TankTemplate

G = 9.81
VALID_HEATING_MODES = {
    "автоматически",
    "без подогрева",
    "периодический подогрев",
    "постоянный подогрев",
}


@dataclass
class InputData:
    city_name: str
    nominal_volume_m3: int
    product_name: str
    wind_region: str
    snow_region: str
    terrain_type: str
    ambient_temp_min_c: float
    ambient_temp_max_c: float
    product_temp_c: float
    heating_mode: str
    service_life_years: int
    corrosion_category: str


@dataclass
class CourseResult:
    course_no: int
    level_from_bottom_m: float
    pressure_mpa: float
    required_thickness_mm: float
    adopted_thickness_mm: int
    hoop_stress_mpa: float
    strength_ok: bool


@dataclass
class SteelVariantResult:
    strength_class: str
    example_grade: str
    allowable_stress_mpa: float
    min_design_temp_c: float
    shell_sheet_format: str
    shell_sheets_per_course: int
    shell_total_sheets: int
    shell_thickness_range_mm: str
    bottom_sheet_format: str
    bottom_sheet_count: int
    roof_sheet_format: str
    roof_sheet_count: int
    estimated_total_mass_t: float
    suitability: str
    note: str


@dataclass
class CalculationResult:
    summary: Dict[str, object]
    course_results: List[CourseResult]
    load_combinations: List[str]
    checks: Dict[str, object]
    references: Dict[str, str]
    steel_variants: List[SteelVariantResult]


class CalculationError(Exception):
    pass


def round_up_to_standard_thickness(thickness_mm: float) -> int:
    for value in STANDARD_PLATE_THICKNESSES_MM:
        if value >= thickness_mm:
            return value
    return ceil(thickness_mm / 2.0) * 2


def resolve_heating_mode(input_data: InputData, product: ProductData) -> str:
    """Определяет эффективный режим подогрева.

    Если пользователь выбрал явный режим, он сохраняется.
    Режим "автоматически" оценивается по типу продукта, температуре продукта
    и климату площадки. Логика демонстрационная, но ближе к реальной эксплуатации,
    чем простая ручная отметка.
    """
    if input_data.heating_mode != "автоматически":
        return input_data.heating_mode

    ambient_min = input_data.ambient_temp_min_c
    product_temp = input_data.product_temp_c
    behavior = getattr(product, "heating_behavior", "none")

    if behavior == "fuel_oil_constant":
        if ambient_min <= -10 or product_temp >= 50:
            return "постоянный подогрев"
        return "периодический подогрев"

    if behavior == "fuel_oil_periodic":
        if ambient_min <= -15 or product_temp >= 45:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "crude_heavy":
        if ambient_min <= -20 or product_temp >= 35:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "crude_medium":
        if ambient_min <= -30 and product_temp >= 20:
            return "периодический подогрев"
        if product_temp >= 40:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "crude_light":
        if ambient_min <= -35 and product_temp >= 15:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "diesel_summer":
        if ambient_min <= -20:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "diesel_mid":
        if ambient_min <= -28:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "diesel_winter":
        if ambient_min <= -38:
            return "периодический подогрев"
        return "без подогрева"

    if behavior == "diesel_arctic":
        return "без подогрева"

    return "без подогрева"


def validate_temperature_data(input_data: InputData) -> None:
    if input_data.heating_mode not in VALID_HEATING_MODES:
        raise CalculationError(f"Неизвестный режим подогрева: {input_data.heating_mode}")
    if input_data.corrosion_category not in CORROSION_ALLOWANCE_MM and input_data.corrosion_category not in AUTOMATIC_CORROSION_VALUES:
        raise CalculationError(f"Неизвестная категория коррозионной агрессивности: {input_data.corrosion_category}")
    if input_data.ambient_temp_max_c < input_data.ambient_temp_min_c:
        raise CalculationError("Максимальная температура воздуха не может быть ниже минимальной.")
    if input_data.product_temp_c < -80 or input_data.product_temp_c > 200:
        raise CalculationError("Температура продукта выглядит некорректной для демонстрационного расчета.")
    if input_data.ambient_temp_min_c < -80 or input_data.ambient_temp_max_c > 80:
        raise CalculationError("Температуры наружного воздуха выходят за допустимый диапазон модели.")


def calculate_cross_section_area(diameter_m: float) -> float:
    return pi * diameter_m**2 / 4.0


def calculate_working_fill_height(shell_height_m: float, fill_factor: float) -> float:
    return shell_height_m * fill_factor


def calculate_useful_volume(area_m2: float, fill_height_m: float) -> float:
    return area_m2 * fill_height_m


def calculate_product_mass(useful_volume_m3: float, density_kg_m3: float) -> float:
    return useful_volume_m3 * density_kg_m3 / 1000.0


def calculate_hydrostatic_pressure_mpa(density_kg_m3: float, height_m: float) -> float:
    return density_kg_m3 * G * height_m / 1_000_000.0


def calculate_wind_pressure_kpa(wind_region: str, terrain_type: str, height_m: float) -> float:
    if wind_region not in WIND_PRESSURE_BY_REGION:
        raise CalculationError(f"Неизвестный ветровой район: {wind_region}")
    if terrain_type not in TERRAIN_COEFFICIENTS:
        raise CalculationError(f"Неизвестный тип местности: {terrain_type}")

    w0 = WIND_PRESSURE_BY_REGION[wind_region]
    kz = TERRAIN_COEFFICIENTS[terrain_type]
    height_factor = 0.95 + min(max(height_m, 6.0), 18.0) / 100.0

    return w0 * kz * CYLINDER_AERODYNAMIC_COEFFICIENT * height_factor * LOAD_RELIABILITY_FACTOR


def calculate_snow_load_kpa(snow_region: str, roof_type: str) -> float:
    if snow_region not in SNOW_LOAD_BY_REGION:
        raise CalculationError(f"Неизвестный снеговой район: {snow_region}")

    s0 = SNOW_LOAD_BY_REGION[snow_region]
    mu = SNOW_SHAPE_COEFFICIENTS.get(roof_type, 0.80)

    return s0 * mu * LOAD_RELIABILITY_FACTOR


def calculate_temperature_span_c(ambient_temp_min_c: float, ambient_temp_max_c: float) -> float:
    return ambient_temp_max_c - ambient_temp_min_c


def calculate_temperature_evaporation_score(input_data: InputData) -> int:
    score = 0

    if input_data.product_temp_c >= 25:
        score += 1
    if input_data.product_temp_c >= 35:
        score += 1
    if input_data.product_temp_c >= 50:
        score += 1

    if input_data.ambient_temp_max_c >= 30:
        score += 1
    if input_data.ambient_temp_max_c >= 40:
        score += 1

    if calculate_temperature_span_c(input_data.ambient_temp_min_c, input_data.ambient_temp_max_c) >= 40:
        score += 1

    if input_data.heating_mode == "периодический подогрев":
        score += 1
    elif input_data.heating_mode == "постоянный подогрев":
        score += 2

    return score


def classify_evaporation_risk(input_data: InputData) -> str:
    score = calculate_temperature_evaporation_score(input_data)
    if score >= 6:
        return "очень высокий"
    if score >= 4:
        return "высокий"
    if score >= 2:
        return "средний"
    return "низкий"


def classify_condensation_risk(input_data: InputData) -> str:
    score = 0
    temp_span = calculate_temperature_span_c(input_data.ambient_temp_min_c, input_data.ambient_temp_max_c)

    if temp_span >= 35:
        score += 1
    if temp_span >= 50:
        score += 1
    if input_data.ambient_temp_min_c <= -20:
        score += 1
    if input_data.product_temp_c - input_data.ambient_temp_min_c >= 35:
        score += 1
    if input_data.heating_mode != "без подогрева":
        score += 1

    if score >= 4:
        return "высокий"
    if score >= 2:
        return "средний"
    return "низкий"


def resolve_corrosion_category(input_data: InputData, product: ProductData) -> str:
    if input_data.corrosion_category not in AUTOMATIC_CORROSION_VALUES:
        return input_data.corrosion_category

    score = 0
    internal_score = {"низкая": 0, "средняя": 1, "повышенная": 2}.get(product.internal_corrosivity, 1)
    score += internal_score

    if getattr(product, "product_group", "") in {"crude_light", "crude_medium", "crude_heavy", "fuel_oil"}:
        score += 1
    if input_data.heating_mode == "периодический подогрев":
        score += 1
    elif input_data.heating_mode == "постоянный подогрев":
        score += 2

    if input_data.product_temp_c >= 40:
        score += 1
    if input_data.ambient_temp_min_c <= -25 and input_data.ambient_temp_max_c >= 25:
        score += 1
    if classify_condensation_risk(input_data) == "высокий":
        score += 1

    if score <= 1:
        return "умеренная"
    if score <= 4:
        return "средняя"
    return "повышенная"


def calculate_shell_course_results(
    template: TankTemplate,
    product: ProductData,
    corrosion_category: str,
    allowable_stress_mpa: float = STEEL_ALLOWABLE_STRESS_MPA,
) -> List[CourseResult]:
    course_height = template.shell_height_m / template.shell_courses
    corrosion_allowance_mm = CORROSION_ALLOWANCE_MM[corrosion_category]
    results: List[CourseResult] = []

    for idx in range(template.shell_courses):
        course_no = idx + 1
        level_from_bottom = idx * course_height + course_height / 2.0
        liquid_head = template.shell_height_m * template.fill_factor - idx * course_height
        liquid_head = max(liquid_head, 0.15)

        pressure_mpa = calculate_hydrostatic_pressure_mpa(product.density_kg_m3, liquid_head)

        thickness_m = pressure_mpa * template.diameter_m / (2.0 * allowable_stress_mpa)
        required_thickness_mm = max(4.0, thickness_m * 1000.0 + corrosion_allowance_mm)
        adopted_thickness_mm = round_up_to_standard_thickness(required_thickness_mm)

        hoop_stress_mpa = pressure_mpa * template.diameter_m / (2.0 * (adopted_thickness_mm / 1000.0))
        strength_ok = hoop_stress_mpa <= allowable_stress_mpa

        results.append(
            CourseResult(
                course_no=course_no,
                level_from_bottom_m=round(level_from_bottom, 3),
                pressure_mpa=round(pressure_mpa, 5),
                required_thickness_mm=round(required_thickness_mm, 2),
                adopted_thickness_mm=adopted_thickness_mm,
                hoop_stress_mpa=round(hoop_stress_mpa, 2),
                strength_ok=strength_ok,
            )
        )

    return results


def calculate_shell_weight_tonnes(template: TankTemplate, course_results: List[CourseResult]) -> float:
    course_height = template.shell_height_m / template.shell_courses
    total_mass_kg = 0.0
    circumference = pi * template.diameter_m

    for course in course_results:
        thickness_m = course.adopted_thickness_mm / 1000.0
        volume_m3 = circumference * course_height * thickness_m
        total_mass_kg += volume_m3 * STEEL_DENSITY_KG_M3

    return total_mass_kg / 1000.0


def estimate_bottom_weight_tonnes(template: TankTemplate) -> float:
    bottom_thickness_m = 0.006
    area_m2 = calculate_cross_section_area(template.diameter_m)
    return area_m2 * bottom_thickness_m * STEEL_DENSITY_KG_M3 / 1000.0


def estimate_roof_weight_tonnes(template: TankTemplate) -> float:
    roof_thickness_m = 0.005
    area_m2 = calculate_cross_section_area(template.diameter_m)
    return area_m2 * roof_thickness_m * STEEL_DENSITY_KG_M3 / 1000.0


def estimate_roof_contour_load_kn_m(template: TankTemplate, snow_load_kpa: float) -> float:
    roof_area_m2 = calculate_cross_section_area(template.diameter_m)
    perimeter_m = pi * template.diameter_m
    total_snow_force_kn = snow_load_kpa * roof_area_m2
    return total_snow_force_kn / perimeter_m


def evaluate_wall_stability(
    template: TankTemplate,
    upper_course_thickness_mm: int,
    wind_pressure_kpa: float,
) -> Dict[str, object]:
    t_m = upper_course_thickness_mm / 1000.0
    d_m = template.diameter_m

    sigma_wind_mpa = (wind_pressure_kpa * d_m) / (2.0 * t_m * 1000.0)
    sigma_cr_mpa = 0.60 * STEEL_ELASTIC_MODULUS_MPA * (t_m / d_m)
    utilization = sigma_wind_mpa / sigma_cr_mpa if sigma_cr_mpa > 0 else 999.0

    return {
        "sigma_wind_mpa": round(sigma_wind_mpa, 2),
        "sigma_cr_mpa": round(sigma_cr_mpa, 2),
        "utilization": round(utilization, 3),
        "ok": utilization <= 0.80,
        "method_note": "Упрощенная инженерная оценка устойчивости верхней части оболочки",
    }


def evaluate_roof_check(template: TankTemplate, snow_load_kpa: float) -> Dict[str, object]:
    allowable = ROOF_ALLOWABLE_SNOW_KPA.get(template.roof_type, 2.5)
    utilization = snow_load_kpa / allowable if allowable > 0 else 999.0
    return {
        "snow_load_kpa": round(snow_load_kpa, 3),
        "allowable_kpa": allowable,
        "utilization": round(utilization, 3),
        "ok": utilization <= 1.0,
        "method_note": "Упрощенная предварительная проверка кровли по удельной снеговой нагрузке",
    }


def determine_wind_ring_need(template: TankTemplate, wind_region: str, upper_stability_ok: bool) -> Dict[str, object]:
    need = (
        template.diameter_m >= WIND_RING_DIAMETER_TRIGGER_M
        and wind_region in WIND_RING_WIND_REGION_TRIGGER
    ) or (not upper_stability_ok)

    recommended_area_mm2 = round(1500 + template.diameter_m * 120 + template.shell_height_m * 60)

    return {
        "need": need,
        "recommended_area_mm2": recommended_area_mm2 if need else 0,
        "recommended_location": "по верху оболочки" if need else "не требуется",
        "method_note": "Ориентировочный подбор ветрового кольца для предварительной проработки",
    }


def build_load_combinations(
    product_mass_t: float,
    shell_weight_t: float,
    bottom_weight_t: float,
    roof_weight_t: float,
    wind_pressure_kpa: float,
    snow_load_kpa: float,
) -> List[str]:
    dead_weight_t = shell_weight_t + bottom_weight_t + roof_weight_t
    return [
        f"Постоянная нагрузка: собственный вес ≈ {dead_weight_t:.2f} т.",
        f"Эксплуатационная: собственный вес + продукт ≈ {dead_weight_t + product_mass_t:.2f} т.",
        f"Климатическая (ветер): собственный вес + ветер {wind_pressure_kpa:.3f} кПа.",
        f"Климатическая (снег): собственный вес + снег {snow_load_kpa:.3f} кПа.",
        "Основное сочетание: собственный вес + продукт + ветер.",
        "Основное сочетание для кровли: собственный вес кровли + снег.",
    ]


def _choose_sheet_formats(template: TankTemplate) -> Tuple[object, object, object]:
    if template.diameter_m <= 18:
        shell_format = SHEET_FORMATS[0]
        deck_format = SHEET_FORMATS[0]
    elif template.diameter_m <= 40:
        shell_format = SHEET_FORMATS[1]
        deck_format = SHEET_FORMATS[1]
    else:
        shell_format = SHEET_FORMATS[2]
        deck_format = SHEET_FORMATS[2]
    return shell_format, deck_format, deck_format


def _suitability_label(ambient_min_c: float, min_design_temp_c: float) -> str:
    if ambient_min_c < min_design_temp_c:
        return "условно допустим только после дополнительной проверки хладостойкости"
    if ambient_min_c <= min_design_temp_c + 5:
        return "допустим на границе температурного диапазона"
    return "предварительно подходит"


def select_steel_variants(
    template: TankTemplate,
    product: ProductData,
    effective_input: InputData,
    base_bottom_weight_t: float,
    base_roof_weight_t: float,
) -> List[SteelVariantResult]:
    shell_format, bottom_format, roof_format = _choose_sheet_formats(template)
    circumference = pi * template.diameter_m
    shell_sheets_per_course = ceil(circumference / shell_format.length_m)
    shell_total_sheets = shell_sheets_per_course * template.shell_courses
    bottom_area_m2 = calculate_cross_section_area(template.diameter_m)
    roof_area_m2 = bottom_area_m2
    bottom_sheet_count = ceil(bottom_area_m2 / (bottom_format.width_m * bottom_format.length_m * 0.85))
    roof_sheet_count = ceil(roof_area_m2 / (roof_format.width_m * roof_format.length_m * 0.90))

    variants: List[SteelVariantResult] = []
    for option in STEEL_OPTIONS:
        course_results = calculate_shell_course_results(
            template,
            product,
            effective_input.corrosion_category,
            allowable_stress_mpa=option.allowable_stress_mpa,
        )
        min_t = min(item.adopted_thickness_mm for item in course_results)
        max_t = max(item.adopted_thickness_mm for item in course_results)
        shell_weight_t = calculate_shell_weight_tonnes(template, course_results)
        estimated_total_mass_t = shell_weight_t + base_bottom_weight_t + base_roof_weight_t
        suitability = _suitability_label(effective_input.ambient_temp_min_c, option.min_design_temp_c)
        note = option.note
        if option.strength_class == "С255" and template.nominal_volume_m3 >= 20000:
            note += "; для крупного резервуара возможен рост толщин нижних поясов"
        if effective_input.corrosion_category == "повышенная":
            note += "; при повышенной коррозионной агрессивности требуется особо внимательно назначать припуск и систему защиты"

        variants.append(
            SteelVariantResult(
                strength_class=option.strength_class,
                example_grade=option.example_grade,
                allowable_stress_mpa=option.allowable_stress_mpa,
                min_design_temp_c=option.min_design_temp_c,
                shell_sheet_format=shell_format.name,
                shell_sheets_per_course=shell_sheets_per_course,
                shell_total_sheets=shell_total_sheets,
                shell_thickness_range_mm=f"{min_t}-{max_t}",
                bottom_sheet_format=bottom_format.name,
                bottom_sheet_count=bottom_sheet_count,
                roof_sheet_format=roof_format.name,
                roof_sheet_count=roof_sheet_count,
                estimated_total_mass_t=round(estimated_total_mass_t, 2),
                suitability=suitability,
                note=note,
            )
        )

    def sort_key(item: SteelVariantResult) -> Tuple[int, float, float]:
        order = {
            "предварительно подходит": 0,
            "допустим на границе температурного диапазона": 1,
            "условно допустим только после дополнительной проверки хладостойкости": 2,
        }
        spread = float(item.shell_thickness_range_mm.split("-")[-1])
        return order.get(item.suitability, 9), spread, item.estimated_total_mass_t

    return sorted(variants, key=sort_key)


def run_calculation(input_data: InputData, template: TankTemplate, product: ProductData) -> CalculationResult:
    validate_temperature_data(input_data)
    effective_heating_mode = resolve_heating_mode(input_data, product)
    temp_input = InputData(
        city_name=input_data.city_name,
        nominal_volume_m3=input_data.nominal_volume_m3,
        product_name=input_data.product_name,
        wind_region=input_data.wind_region,
        snow_region=input_data.snow_region,
        terrain_type=input_data.terrain_type,
        ambient_temp_min_c=input_data.ambient_temp_min_c,
        ambient_temp_max_c=input_data.ambient_temp_max_c,
        product_temp_c=input_data.product_temp_c,
        heating_mode=effective_heating_mode,
        service_life_years=input_data.service_life_years,
        corrosion_category=input_data.corrosion_category,
    )
    effective_corrosion = resolve_corrosion_category(temp_input, product)
    effective_input = InputData(
        city_name=temp_input.city_name,
        nominal_volume_m3=temp_input.nominal_volume_m3,
        product_name=temp_input.product_name,
        wind_region=temp_input.wind_region,
        snow_region=temp_input.snow_region,
        terrain_type=temp_input.terrain_type,
        ambient_temp_min_c=temp_input.ambient_temp_min_c,
        ambient_temp_max_c=temp_input.ambient_temp_max_c,
        product_temp_c=temp_input.product_temp_c,
        heating_mode=temp_input.heating_mode,
        service_life_years=temp_input.service_life_years,
        corrosion_category=effective_corrosion,
    )

    area_m2 = calculate_cross_section_area(template.diameter_m)
    fill_height_m = calculate_working_fill_height(template.shell_height_m, template.fill_factor)
    useful_volume_m3 = calculate_useful_volume(area_m2, fill_height_m)
    product_mass_t = calculate_product_mass(useful_volume_m3, product.density_kg_m3)
    hydrostatic_pressure_mpa = calculate_hydrostatic_pressure_mpa(product.density_kg_m3, fill_height_m)

    wind_pressure_kpa = calculate_wind_pressure_kpa(
        effective_input.wind_region, effective_input.terrain_type, template.shell_height_m
    )
    snow_load_kpa = calculate_snow_load_kpa(effective_input.snow_region, template.roof_type)

    course_results = calculate_shell_course_results(template, product, effective_input.corrosion_category)
    shell_weight_t = calculate_shell_weight_tonnes(template, course_results)
    bottom_weight_t = estimate_bottom_weight_tonnes(template)
    roof_weight_t = estimate_roof_weight_tonnes(template)

    upper_course = course_results[-1]
    upper_stability = evaluate_wall_stability(template, upper_course.adopted_thickness_mm, wind_pressure_kpa)
    roof_check = evaluate_roof_check(template, snow_load_kpa)
    wind_ring = determine_wind_ring_need(template, effective_input.wind_region, bool(upper_stability["ok"]))
    contour_load_kn_m = estimate_roof_contour_load_kn_m(template, snow_load_kpa)

    load_combinations = build_load_combinations(
        product_mass_t,
        shell_weight_t,
        bottom_weight_t,
        roof_weight_t,
        wind_pressure_kpa,
        snow_load_kpa,
    )

    temp_span_c = calculate_temperature_span_c(effective_input.ambient_temp_min_c, effective_input.ambient_temp_max_c)
    evaporation_risk = classify_evaporation_risk(effective_input)
    condensation_risk = classify_condensation_risk(effective_input)
    steel_variants = select_steel_variants(template, product, effective_input, bottom_weight_t, roof_weight_t)

    summary = {
        "город": effective_input.city_name,
        "базовый тип": template.tank_type,
        "номинальный объем, м3": template.nominal_volume_m3,
        "нефтепродукт": product.name,
        "диаметр, м": round(template.diameter_m, 3),
        "высота стенки, м": round(template.shell_height_m, 3),
        "тип крыши базового резервуара": template.roof_type,
        "число поясов": template.shell_courses,
        "расчетная высота налива, м": round(fill_height_m, 3),
        "площадь поперечного сечения, м2": round(area_m2, 3),
        "ориентировочный полезный объем, м3": round(useful_volume_m3, 1),
        "масса нефтепродукта, т": round(product_mass_t, 2),
        "гидростатическое давление у днища, МПа": round(hydrostatic_pressure_mpa, 5),
        "ветровая нагрузка, кПа": round(wind_pressure_kpa, 3),
        "снеговая нагрузка, кПа": round(snow_load_kpa, 3),
        "собственный вес стенки, т": round(shell_weight_t, 2),
        "собственный вес днища, т": round(bottom_weight_t, 2),
        "собственный вес кровли, т": round(roof_weight_t, 2),
        "нагрузка на опорный контур крыши, кН/м": round(contour_load_kn_m, 3),
        "мин. температура воздуха, °C": round(effective_input.ambient_temp_min_c, 1),
        "макс. температура воздуха, °C": round(effective_input.ambient_temp_max_c, 1),
        "температура продукта, °C": round(effective_input.product_temp_c, 1),
        "перепад наружных температур, °C": round(temp_span_c, 1),
        "режим подогрева": effective_heating_mode,
        "резервуар подогреваемый": "да" if effective_heating_mode != "без подогрева" else "нет",
        "температурный риск испарительных потерь": evaporation_risk,
        "температурный риск конденсации": condensation_risk,
        "срок службы, лет": effective_input.service_life_years,
        "категория коррозионной среды": effective_input.corrosion_category,
        "рекомендуемый вариант проката": f"{steel_variants[0].strength_class} ({steel_variants[0].example_grade})",
    }
    if input_data.heating_mode == "автоматически":
        summary["режим подогрева (исходный ввод)"] = "автоматически"
        summary["подогрев принят автоматически"] = "да"
    if input_data.corrosion_category in AUTOMATIC_CORROSION_VALUES:
        summary["категория коррозионной среды (исходный ввод)"] = "автоматически"

    checks = {
        "прочность поясов": all(item.strength_ok for item in course_results),
        "верхняя часть оболочки": upper_stability,
        "устойчивость верхней части оболочки": upper_stability["ok"],
        "ветровое кольцо": wind_ring,
        "кровля": roof_check,
        "температурный риск испарительных потерь": evaporation_risk,
        "температурный риск конденсации": condensation_risk,
    }

    return CalculationResult(
        summary=summary,
        course_results=course_results,
        load_combinations=load_combinations,
        checks=checks,
        references=NORMATIVE_REFERENCES,
        steel_variants=steel_variants,
    )
