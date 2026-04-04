"""Модуль рекомендаций по конструктивному решению и покрытиям."""

from __future__ import annotations

from typing import Dict, List

from calculations import (
    CalculationResult,
    InputData,
    calculate_temperature_evaporation_score,
    calculate_temperature_span_c,
    classify_condensation_risk,
)
from data_products import ProductData
from data_tanks import TankTemplate


VOLATILITY_SCORE = {"низкая": 0, "средняя": 1, "высокая": 2}
VAPOR_LOSS_SCORE = {"низкая": 0, "средняя": 1, "повышенная": 2, "высокая": 3}


def _build_temperature_note(input_data: InputData) -> str:
    parts: List[str] = []
    temp_span = calculate_temperature_span_c(input_data.ambient_temp_min_c, input_data.ambient_temp_max_c)

    if input_data.product_temp_c >= 35:
        parts.append(f"повышенная температура продукта {input_data.product_temp_c:.0f} °C")
    elif input_data.product_temp_c >= 20:
        parts.append(f"умеренно повышенная температура продукта {input_data.product_temp_c:.0f} °C")

    if input_data.ambient_temp_max_c >= 30:
        parts.append(f"максимальная наружная температура {input_data.ambient_temp_max_c:.0f} °C")

    if temp_span >= 40:
        parts.append(f"большой перепад наружных температур {temp_span:.0f} °C")

    if input_data.heating_mode != "без подогрева":
        parts.append(input_data.heating_mode)

    return ", ".join(parts)


def choose_constructive_solution(
    input_data: InputData,
    template: TankTemplate,
    product: ProductData,
) -> Dict[str, str]:
    volume = template.nominal_volume_m3
    product_score = VOLATILITY_SCORE.get(product.volatility, 0) + VAPOR_LOSS_SCORE.get(product.vapor_loss_tendency, 0)
    temperature_score = calculate_temperature_evaporation_score(input_data)

    if volume >= 20000:
        volume_score = 3
    elif volume >= 10000:
        volume_score = 2
    elif volume >= 3000:
        volume_score = 1
    else:
        volume_score = 0

    total_score = product_score + temperature_score + volume_score
    temp_note = _build_temperature_note(input_data)

    if (
        volume >= 20000
        and product.volatility in {"средняя", "высокая"}
        and VAPOR_LOSS_SCORE.get(product.vapor_loss_tendency, 0) >= 2
        and total_score >= 8
    ):
        justification = (
            "Крупный резервуар, выраженная склонность продукта к испарительным потерям и "
            "повышающий температурный фактор. Плавающая крыша предварительно рассматривается "
            "как наиболее эффективное решение для снижения потерь и уменьшения парового пространства."
        )
        if temp_note:
            justification += f" Дополнительно учитываются: {temp_note}."
        return {
            "solution": "с плавающей крышей",
            "justification": justification,
        }

    if volume >= 3000 and product_score >= 2 and total_score >= 5:
        justification = (
            "Для выбранного объема рационально предварительно рассмотреть внутренний понтон: "
            "он снижает испарительные потери и уменьшает воздействие паровоздушной среды "
            "на внутренние поверхности при меньшей конструктивной сложности по сравнению с плавающей крышей."
        )
        if temp_note:
            justification += f" На решение дополнительно повлияли: {temp_note}."
        return {
            "solution": "с внутренним понтоном",
            "justification": justification,
        }

    return {
        "solution": "без понтона",
        "justification": (
            "Для данного объема и совокупности свойств продукта предварительно допустимо применение "
            "резервуара без понтона и без плавающей крыши. Температурный режим не дает такого роста "
            "испарительных потерь, который делал бы усложнение конструкции обязательным."
        ),
    }


def _external_coating_system(input_data: InputData) -> Dict[str, str]:
    temp_span = calculate_temperature_span_c(input_data.ambient_temp_min_c, input_data.ambient_temp_max_c)

    if input_data.corrosion_category == "высокая":
        if input_data.ambient_temp_min_c <= -40:
            return {
                "system": "цинконаполненный эпоксидный грунт + эпоксидный промежуточный слой + полиуретановый финиш холодостойкого исполнения",
                "thickness": "300-340 мкм",
                "layers": "3 слоя",
                "service_life": "15-20 лет",
            }
        if input_data.ambient_temp_max_c >= 35 or temp_span >= 45:
            return {
                "system": "цинконаполненный эпоксидный грунт + эпоксидный промежуточный слой + полиуретановый финиш с повышенной УФ- и термостойкостью",
                "thickness": "300-340 мкм",
                "layers": "3 слоя",
                "service_life": "15-20 лет",
            }
        return {
            "system": "цинконаполненный эпоксидный грунт + эпоксидный промежуточный слой + полиуретановый финиш",
            "thickness": "280-320 мкм",
            "layers": "3 слоя",
            "service_life": "15-20 лет",
        }

    if input_data.ambient_temp_min_c <= -40:
        return {
            "system": "эпоксидный грунт + атмосферостойкий полиуретановый финиш холодостойкого исполнения",
            "thickness": "240-300 мкм",
            "layers": "3 слоя",
            "service_life": "12-18 лет",
        }

    if input_data.ambient_temp_max_c >= 35 or temp_span >= 45:
        return {
            "system": "эпоксидный грунт + эпоксидный промежуточный слой + полиуретановый финиш с повышенной УФ-стойкостью",
            "thickness": "240-300 мкм",
            "layers": "3 слоя",
            "service_life": "12-16 лет",
        }

    return {
        "system": "эпоксидный грунт + эпоксидный промежуточный слой + полиуретановый финиш",
        "thickness": "220-280 мкм",
        "layers": "3 слоя",
        "service_life": "12-15 лет",
    }


def _internal_coating_system(input_data: InputData, product: ProductData) -> Dict[str, str]:
    if input_data.heating_mode == "постоянный подогрев" or input_data.product_temp_c >= 60:
        return {
            "system": "новолачное эпоксидное покрытие повышенной химической и температурной стойкости",
            "thickness": "450-600 мкм",
            "layers": "3 слоя",
            "service_life": "10-14 лет",
        }

    if input_data.heating_mode == "периодический подогрев" or input_data.product_temp_c >= 40:
        return {
            "system": "химстойкое эпоксидное покрытие повышенной толщины",
            "thickness": "400-550 мкм",
            "layers": "3 слоя",
            "service_life": "10-15 лет",
        }

    if product.name in {"Jet A-1", "ТС-1", "Керосин", "АИ-92", "АИ-95"}:
        return {
            "system": "двухкомпонентное химстойкое эпоксидное или новолачное эпоксидное покрытие",
            "thickness": "350-500 мкм",
            "layers": "2-3 слоя",
            "service_life": "10-15 лет",
        }

    if product.name == "Мазут":
        return {
            "system": "усиленное эпоксидное покрытие для тяжелых нефтепродуктов",
            "thickness": "400-600 мкм",
            "layers": "3 слоя",
            "service_life": "10-14 лет",
        }

    if input_data.corrosion_category == "высокая":
        return {
            "system": "химстойкая эпоксидная система повышенной толщины",
            "thickness": "400-550 мкм",
            "layers": "3 слоя",
            "service_life": "10-15 лет",
        }

    return {
        "system": "эпоксидная система для нефтепродуктов",
        "thickness": "300-400 мкм",
        "layers": "2-3 слоя",
        "service_life": "8-12 лет",
    }


def generate_coating_recommendations(
    input_data: InputData,
    product: ProductData,
    constructive_solution: Dict[str, str],
) -> Dict[str, Dict[str, str]]:
    external = _external_coating_system(input_data)
    internal = _internal_coating_system(input_data, product)
    condensation_risk = classify_condensation_risk(input_data)

    if condensation_risk == "высокий":
        vapor_zone = {
            "zone": "паровоздушная зона",
            "system": "новолачное или химстойкое эпоксидное покрытие повышенной стойкости к конденсату",
            "thickness": "400-500 мкм",
            "layers": "3 слоя",
            "application": "верхняя часть внутренней поверхности и зоны интенсивной конденсации",
            "service_life": "10-14 лет",
        }
    else:
        vapor_zone = {
            "zone": "паровоздушная зона",
            "system": "новолачное или химстойкое эпоксидное покрытие",
            "thickness": "300-450 мкм",
            "layers": "2-3 слоя",
            "application": "верхняя часть внутренней поверхности и зоны возможной конденсации",
            "service_life": "10-15 лет",
        }

    roof_top = {
        "zone": "крыша и верхние наружные участки",
        "system": external["system"],
        "thickness": external["thickness"],
        "layers": external["layers"],
        "application": "наружная поверхность кровли, верх стенки, элементы обвязки",
        "service_life": external["service_life"],
    }

    immersion_note = "нижняя часть стенки, днище, зоны постоянного контакта с продуктом"
    if input_data.heating_mode != "без подогрева" or input_data.product_temp_c >= 40:
        immersion_note += "; рекомендуется усиленный контроль состояния покрытия из-за температурного воздействия"

    immersion_zone = {
        "zone": "зона контакта с нефтепродуктом",
        "system": internal["system"],
        "thickness": internal["thickness"],
        "layers": internal["layers"],
        "application": immersion_note,
        "service_life": internal["service_life"],
    }

    external_zone = {
        "zone": "наружная поверхность",
        "system": external["system"],
        "thickness": external["thickness"],
        "layers": external["layers"],
        "application": "наружная поверхность стенки и навесных элементов",
        "service_life": external["service_life"],
    }

    modernization_note = (
        f"Для варианта '{constructive_solution['solution']}' рекомендуется при модернизации обеспечить "
        "усиленную защиту паровоздушной зоны и зоны переменного смачивания. Температурный режим "
        "должен учитываться при назначении ремонтного цикла, так как он заметно влияет на деградацию покрытия."
    )

    return {
        "внутренняя поверхность": {
            "zone": "внутренняя поверхность",
            "system": internal["system"],
            "thickness": internal["thickness"],
            "layers": internal["layers"],
            "application": "внутренние поверхности резервуара, не относящиеся к наружной атмосфере",
            "service_life": internal["service_life"],
        },
        "наружная поверхность": external_zone,
        "паровоздушная зона": vapor_zone,
        "зона контакта с нефтепродуктом": immersion_zone,
        "крыша и верхние участки": roof_top,
        "краткая рекомендация": {
            "zone": "модернизация",
            "system": modernization_note,
            "thickness": "—",
            "layers": "—",
            "application": product.internal_coating_note,
            "service_life": "по регламенту осмотров и ремонта",
        },
    }


def build_final_package(
    input_data: InputData,
    template: TankTemplate,
    product: ProductData,
    calculation_result: CalculationResult,
) -> Dict[str, object]:
    constructive_solution = choose_constructive_solution(input_data, template, product)
    coatings = generate_coating_recommendations(input_data, product, constructive_solution)

    return {
        "constructive_solution": constructive_solution,
        "coatings": coatings,
        "calculation_result": calculation_result,
    }


def format_result_text(package: Dict[str, object]) -> str:
    calc: CalculationResult = package["calculation_result"]
    constructive_solution = package["constructive_solution"]
    coatings = package["coatings"]

    lines: List[str] = []
    lines.append("РАСЧЕТНО-РЕКОМЕНДАТЕЛЬНЫЙ ОТЧЕТ")
    lines.append("=" * 72)
    lines.append("")
    lines.append("1. Основные данные")
    for key, value in calc.summary.items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("2. Пояса стенки")
    for course in calc.course_results:
        lines.append(
            f"- Пояс {course.course_no}: уровень {course.level_from_bottom_m:.3f} м; "
            f"p={course.pressure_mpa:.5f} МПа; t_тр={course.required_thickness_mm:.2f} мм; "
            f"t_прин={course.adopted_thickness_mm} мм; σ={course.hoop_stress_mpa:.2f} МПа; "
            f"проверка={'OK' if course.strength_ok else 'НЕ OK'}"
        )

    lines.append("")
    lines.append("3. Сочетания нагрузок")
    for item in calc.load_combinations:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("4. Проверки и конструктивные выводы")
    lines.append(f"- Прочность поясов: {'OK' if calc.checks['прочность поясов'] else 'НЕ OK'}")
    lines.append(
        f"- Устойчивость верхней части оболочки: {'OK' if calc.checks['устойчивость верхней части оболочки'] else 'НЕ OK'}"
    )
    upper = calc.checks["верхняя часть оболочки"]
    lines.append(
        f"- Верхняя часть оболочки: σ_ветр={upper['sigma_wind_mpa']} МПа; "
        f"σ_кр={upper['sigma_cr_mpa']} МПа; коэффициент использования={upper['utilization']}"
    )
    roof = calc.checks["кровля"]
    lines.append(
        f"- Кровля: q_сн={roof['snow_load_kpa']} кПа; q_доп={roof['allowable_kpa']} кПа; "
        f"коэффициент использования={roof['utilization']}; проверка={'OK' if roof['ok'] else 'НЕ OK'}"
    )
    wind_ring = calc.checks["ветровое кольцо"]
    lines.append(
        f"- Ветровое кольцо: {'требуется' if wind_ring['need'] else 'не требуется'}; "
        f"ориентировочная площадь сечения={wind_ring['recommended_area_mm2']} мм²; "
        f"расположение={wind_ring['recommended_location']}"
    )
    lines.append(
        f"- Температурный риск испарительных потерь: {calc.checks['температурный риск испарительных потерь']}"
    )
    lines.append(
        f"- Температурный риск конденсации: {calc.checks['температурный риск конденсации']}"
    )

    lines.append("")
    lines.append("5. Рекомендуемое конструктивное решение")
    lines.append(f"- Вариант: {constructive_solution['solution']}")
    lines.append(f"- Обоснование: {constructive_solution['justification']}")

    lines.append("")
    lines.append("6. Рекомендации по защитным покрытиям")
    for zone_name, zone_data in coatings.items():
        lines.append(f"- {zone_name}:")
        lines.append(f"    зона: {zone_data['zone']}")
        lines.append(f"    система: {zone_data['system']}")
        lines.append(f"    толщина: {zone_data['thickness']}")
        lines.append(f"    слои: {zone_data['layers']}")
        lines.append(f"    область применения: {zone_data['application']}")
        lines.append(f"    срок службы: {zone_data['service_life']}")

    lines.append("")
    lines.append("7. Нормативная база")
    for key, value in calc.references.items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("8. Примечание")
    lines.append(
        "- Температурный блок в данной версии используется как инженерно-рекомендательный: "
        "для оценки испарительных потерь, конденсации и выбора покрытий. Для рабочего проекта "
        "необходима детальная проверка по фактическим условиям эксплуатации и данным производителя материалов."
    )
    lines.append(
        "- Результаты предназначены для ВКР как предварительная расчетно-рекомендательная оценка. "
        "Для рабочего проектирования требуется полная нормативная проверка по действующим редакциям документов."
    )

    return "\n".join(lines)
