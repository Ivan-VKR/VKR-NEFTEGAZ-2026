"""Модуль рекомендаций по конструктивному решению, покрытиям, оборудованию и логам."""

from __future__ import annotations

from math import pi
from typing import Dict, List

from calculations import (
    CalculationResult,
    InputData,
    calculate_temperature_evaporation_score,
    calculate_temperature_span_c,
    classify_condensation_risk,
    resolve_corrosion_category,
    resolve_heating_mode,
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

    if input_data.heating_mode == "периодический подогрев":
        parts.append("периодический подогрев продукта")
    elif input_data.heating_mode == "постоянный подогрев":
        parts.append("постоянный подогрев продукта")

    return ", ".join(parts)


def choose_constructive_solution(
    input_data: InputData,
    template: TankTemplate,
    product: ProductData,
) -> Dict[str, object]:
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
        solution = "с плавающей крышей"
    elif volume >= 3000 and product_score >= 2 and total_score >= 5:
        justification = (
            "Для выбранного объема рационально предварительно рассмотреть внутренний понтон: "
            "он снижает испарительные потери и уменьшает воздействие паровоздушной среды "
            "на внутренние поверхности при меньшей конструктивной сложности по сравнению с плавающей крышей."
        )
        if temp_note:
            justification += f" На решение дополнительно повлияли: {temp_note}."
        solution = "с внутренним понтоном"
    else:
        solution = "без понтона"
        justification = (
            "Для данного объема и совокупности свойств продукта предварительно допустимо применение "
            "резервуара без понтона и без плавающей крыши. Температурный режим не дает такого роста "
            "испарительных потерь, который делал бы усложнение конструкции обязательным."
        )

    return {
        "solution": solution,
        "justification": justification,
        "product_score": product_score,
        "temperature_score": temperature_score,
        "volume_score": volume_score,
        "total_score": total_score,
        "temperature_note": temp_note,
    }


def _external_coating_system(input_data: InputData) -> Dict[str, str]:
    temp_span = calculate_temperature_span_c(input_data.ambient_temp_min_c, input_data.ambient_temp_max_c)

    if input_data.corrosion_category == "повышенная":
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

    if getattr(product, "product_group", "") in {"jet_fuel", "rocket_fuel", "kerosene", "gasoline"}:
        return {
            "system": "двухкомпонентное химстойкое эпоксидное или новолачное эпоксидное покрытие",
            "thickness": "350-500 мкм",
            "layers": "2-3 слоя",
            "service_life": "10-15 лет",
        }

    if getattr(product, "product_group", "") == "fuel_oil":
        return {
            "system": "усиленное эпоксидное покрытие для тяжелых нефтепродуктов",
            "thickness": "400-600 мкм",
            "layers": "3 слоя",
            "service_life": "10-14 лет",
        }

    if input_data.corrosion_category == "повышенная":
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


def _summary_modernization_values(input_data: InputData, constructive_solution: Dict[str, object]) -> Dict[str, str]:
    if constructive_solution["solution"] == "с плавающей крышей":
        return {
            "thickness": "350-550 мкм",
            "layers": "3 слоя",
        }
    if input_data.heating_mode != "без подогрева" or input_data.product_temp_c >= 40 or input_data.corrosion_category == "повышенная":
        return {
            "thickness": "400-600 мкм",
            "layers": "3 слоя",
        }
    return {
        "thickness": "300-500 мкм",
        "layers": "2-3 слоя",
    }


def generate_coating_recommendations(
    input_data: InputData,
    product: ProductData,
    constructive_solution: Dict[str, object],
) -> Dict[str, Dict[str, str]]:
    external = _external_coating_system(input_data)
    internal = _internal_coating_system(input_data, product)
    condensation_risk = classify_condensation_risk(input_data)
    summary_values = _summary_modernization_values(input_data, constructive_solution)

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
            "thickness": summary_values["thickness"],
            "layers": summary_values["layers"],
            "application": product.internal_coating_note,
            "service_life": "по регламенту осмотров и ремонта",
        },
    }


def _append_equipment(
    items: List[Dict[str, str]],
    name: str,
    qty: str,
    diameter_dn: str,
    purpose: str,
    basis: str,
    group: str = "общее",
) -> None:
    items.append({
        "name": name,
        "qty": qty,
        "diameter_dn": diameter_dn,
        "purpose": purpose,
        "basis": basis,
        "group": group,
    })


def _main_process_dn(volume: int) -> str:
    if volume <= 1000:
        return "DN150"
    if volume <= 5000:
        return "DN200"
    if volume <= 20000:
        return "DN250"
    return "DN300"


def _aux_process_dn(volume: int) -> str:
    if volume <= 1000:
        return "DN80"
    if volume <= 5000:
        return "DN100"
    if volume <= 20000:
        return "DN150"
    return "DN200"


def _breathing_dn(volume: int) -> str:
    if volume <= 1000:
        return "DN100"
    if volume <= 5000:
        return "DN150"
    return "DN200"


def generate_equipment_recommendations(
    input_data: InputData,
    template: TankTemplate,
    product: ProductData,
    constructive_solution: Dict[str, object],
) -> Dict[str, object]:
    """Подбор рекомендуемого состава оборудования резервуара.

    Состав дан в демонстрационно-инженерной форме для ВКР: программа выдает типовой
    рекомендуемый перечень с диаметрами условного прохода, количеством и назначением.
    Конкретная спецификация для рабочего проекта должна уточняться проектировщиком.
    """
    items: List[Dict[str, str]] = []
    volume = template.nominal_volume_m3
    diameter = template.diameter_m
    fixed_roof = constructive_solution["solution"] != "с плавающей крышей"
    volatile = product.volatility in {"средняя", "высокая"} or product.vapor_loss_tendency in {"повышенная", "высокая"}
    heated = input_data.heating_mode != "без подогрева"

    process_dn = _main_process_dn(volume)
    aux_dn = _aux_process_dn(volume)
    breathing_dn = _breathing_dn(volume)
    manholes = "1 шт." if volume <= 1000 else "2 шт."
    light_hatches = "1 шт." if diameter < 12 else "2 шт." if diameter < 30 else "3 шт."
    breathing_valves = "1 шт." if volume <= 1000 else "2 шт."

    _append_equipment(
        items, "Люк-лаз стеновой", manholes, "DN600", 
        "доступ для осмотра, вентиляции и зачистки резервуара",
        "эксплуатационный доступ; врезка в стенку выполняется с усилением по ГОСТ 31385",
        "люки",
    )
    _append_equipment(
        items, "Люк замерный / замерное устройство", "1 шт.", "DN200",
        "ручной замер уровня и контроль продукта",
        "типовой элемент эксплуатационного оснащения резервуара",
        "люки",
    )
    _append_equipment(
        items, "Патрубок приема продукта", "1 шт.", process_dn,
        "подача продукта в резервуар",
        "основной технологический патрубок; конкретный состав оборудования определяет проектировщик",
        "патрубки",
    )
    _append_equipment(
        items, "Патрубок выдачи продукта", "1 шт.", process_dn,
        "отбор продукта из резервуара",
        "основной технологический патрубок резервуара",
        "патрубки",
    )
    _append_equipment(
        items, "Патрубок рециркуляции / перемешивания", "1 шт.", aux_dn,
        "рециркуляция продукта и эксплуатационные операции",
        "целесообразен для резервуаров среднего и большого объема и при наличии подогрева",
        "патрубки",
    )
    _append_equipment(
        items, "Дренажный / зачистной патрубок", "1 шт.", "DN80" if volume <= 5000 else "DN100",
        "слив отстоя, удаление подтоварной воды и зачистка",
        "рекомендуемый базовый эксплуатационный элемент днища",
        "патрубки",
    )
    _append_equipment(
        items, "Патрубок под уровнемер", "1 шт.", "DN100",
        "установка уровнемерного оборудования",
        "типовой патрубок КИПиА для контроля уровня",
        "патрубки",
    )
    _append_equipment(
        items, "Патрубок под сигнализатор уровня", "1 шт.", "DN80",
        "контроль предельных уровней и защита от переполнения",
        "целесообразен для повышения эксплуатационной безопасности",
        "патрубки",
    )
    _append_equipment(
        items, "Патрубок отбора проб", "1 шт.", "DN50",
        "контроль качества продукта",
        "типовое технологическое оснащение для нефтепродуктов и авиатоплива",
        "патрубки",
    )

    if fixed_roof:
        _append_equipment(
            items, "Световой люк", light_hatches, "DN500",
            "осмотр, вентиляция и проведение внутренних работ",
            "рекомендуемый элемент для резервуара со стационарной крышей",
            "люки",
        )
        _append_equipment(
            items, "Дыхательный клапан", breathing_valves, breathing_dn,
            "компенсация избыточного давления и вакуума в газовом пространстве",
            "рекомендуется для резервуаров со стационарной крышей по пожарно-эксплуатационной логике",
            "арматура",
        )
        if volatile:
            _append_equipment(
                items, "Огнепреградитель на дыхательной линии", breathing_valves, breathing_dn,
                "снижение риска распространения пламени через дыхательную арматуру",
                "особенно целесообразен для светлых и летучих нефтепродуктов",
                "арматура",
            )
        if volume >= 5000 or volatile:
            _append_equipment(
                items, "Аварийный клапан", "1-2 шт.", "DN250" if volume <= 20000 else "DN300",
                "аварийный сброс давления при нештатных режимах",
                "назначается при необходимости дополнительной пропускной способности по СП 155",
                "арматура",
            )

    _append_equipment(
        items, "Запорная арматура на приемо-раздаточных линиях", "2 шт.", process_dn,
        "отсечение резервуара от трубопроводной сети",
        "назначается совместно с приемо-раздаточными патрубками",
        "арматура",
    )

    if volume >= 5000:
        _append_equipment(
            items, "Патрубок системы пенного пожаротушения / пенокамера", "1-2 шт.", "DN80" if volume <= 10000 else "DN100",
            "подача пены и пожарная защита резервуара",
            "для резервуаров значительного объема необходима увязка с системой пожарной защиты по СП 155",
            "арматура",
        )

    if heated:
        _append_equipment(
            items, "Патрубок подачи продукта на циркуляционный подогрев", "1 шт.", aux_dn,
            "подключение циркуляционного контура подогрева продукта",
            "назначается для подогреваемых резервуаров",
            "подогрев",
        )
        _append_equipment(
            items, "Патрубок возврата продукта после подогрева", "1 шт.", aux_dn,
            "возврат продукта после циркуляции через подогреватель",
            "назначается для подогреваемых резервуаров",
            "подогрев",
        )
        _append_equipment(
            items, "Патрубок подачи теплоносителя / пара", "1 шт.", "DN80",
            "подача теплоносителя в секционный подогреватель",
            "назначается при наличии системы внутреннего или внешнего подогрева",
            "подогрев",
        )
        _append_equipment(
            items, "Патрубок отвода конденсата / обратного теплоносителя", "1 шт.", "DN50",
            "отвод конденсата или обратного теплоносителя",
            "типовой элемент подогреваемого резервуара",
            "подогрев",
        )
        _append_equipment(
            items, "Патрубок под термопреобразователь / термокарман", "1 шт.", "DN50",
            "контроль температуры продукта",
            "необходим для эксплуатации подогреваемого резервуара",
            "подогрев",
        )
        _append_equipment(
            items, "Секционный подогреватель / циркуляционный узел", "1 компл.", "по проекту",
            "поддержание требуемой температуры продукта",
            "специальное оборудование подогреваемого резервуара",
            "подогрев",
        )

    if constructive_solution["solution"] == "с внутренним понтоном":
        _append_equipment(
            items, "Комплект внутреннего понтона", "1 компл.", "по проекту",
            "снижение испарительных потерь и уменьшение объема паровоздушной зоны",
            "включает направляющую, уплотняющий затвор, опоры и обслуживающие элементы понтона",
            "специальное",
        )
        _append_equipment(
            items, "Направляющая стойка / направляющий патрубок понтона", "1 шт.", "DN200",
            "обеспечение направленного перемещения внутреннего понтона",
            "типовой элемент комплекта понтона",
            "специальное",
        )
        _append_equipment(
            items, "Предохранительное / уравнительное устройство понтона", "1 шт.", "DN150",
            "безопасная работа понтона при изменении режимов",
            "упоминается в логике оборудования понтона по ГОСТ 31385",
            "специальное",
        )

    if constructive_solution["solution"] == "с плавающей крышей":
        _append_equipment(
            items, "Комплект плавающей крыши", "1 компл.", "по проекту",
            "минимизация испарительных потерь при хранении летучих продуктов",
            "включает затвор по периметру, опорные стойки и обслуживающие элементы",
            "специальное",
        )
        _append_equipment(
            items, "Дренажное устройство плавающей крыши", "1 компл.", "DN100",
            "отвод атмосферных осадков с поверхности плавающей крыши",
            "необходимый элемент эксплуатации плавающей крыши",
            "специальное",
        )
        _append_equipment(
            items, "Направляющая стойка плавающей крыши", "1 шт.", "DN200",
            "направление движения крыши и размещение части обслуживающих устройств",
            "типовой элемент конструкции плавающей крыши",
            "специальное",
        )

    normative_notes = [
        "Патрубки и люки в стенке резервуара должны выполняться с усилением листовыми накладками; для отверстий до DN 65 включительно при толщине стенки не менее 6 мм допускается выполнение без усиливающего листа.",
        "Расстояние между смежными врезками в стенку рекомендуется принимать не менее 250 мм; до вертикальных швов стенки — не менее 250 мм; до горизонтальных швов и днища — не менее 100 мм.",
        "Конкретный состав оборудования, количество патрубков и их проходы окончательно назначаются проектом с учетом гидравлики, пожарной защиты и схемы трубопроводной обвязки.",
    ]

    return {"items": items, "normative_notes": normative_notes}

def build_final_package(
    input_data: InputData,
    template: TankTemplate,
    product: ProductData,
    calculation_result: CalculationResult,
) -> Dict[str, object]:
    heating_input = InputData(
        city_name=input_data.city_name,
        nominal_volume_m3=input_data.nominal_volume_m3,
        product_name=input_data.product_name,
        wind_region=input_data.wind_region,
        snow_region=input_data.snow_region,
        terrain_type=input_data.terrain_type,
        ambient_temp_min_c=input_data.ambient_temp_min_c,
        ambient_temp_max_c=input_data.ambient_temp_max_c,
        product_temp_c=input_data.product_temp_c,
        heating_mode=resolve_heating_mode(input_data, product),
        service_life_years=input_data.service_life_years,
        corrosion_category=input_data.corrosion_category,
    )
    effective_input = InputData(
        city_name=heating_input.city_name,
        nominal_volume_m3=heating_input.nominal_volume_m3,
        product_name=heating_input.product_name,
        wind_region=heating_input.wind_region,
        snow_region=heating_input.snow_region,
        terrain_type=heating_input.terrain_type,
        ambient_temp_min_c=heating_input.ambient_temp_min_c,
        ambient_temp_max_c=heating_input.ambient_temp_max_c,
        product_temp_c=heating_input.product_temp_c,
        heating_mode=heating_input.heating_mode,
        service_life_years=heating_input.service_life_years,
        corrosion_category=resolve_corrosion_category(heating_input, product),
    )
    constructive_solution = choose_constructive_solution(effective_input, template, product)
    coatings = generate_coating_recommendations(effective_input, product, constructive_solution)
    equipment = generate_equipment_recommendations(effective_input, template, product, constructive_solution)

    return {
        "input_data": input_data,
        "effective_input": effective_input,
        "template": template,
        "product": product,
        "constructive_solution": constructive_solution,
        "coatings": coatings,
        "equipment": equipment,
        "calculation_result": calculation_result,
    }


def format_result_text(package: Dict[str, object]) -> str:
    calc: CalculationResult = package["calculation_result"]
    constructive_solution = package["constructive_solution"]
    coatings = package["coatings"]
    equipment = package["equipment"]

    lines: List[str] = []
    lines.append("РАСЧЕТНО-РЕКОМЕНДАТЕЛЬНЫЙ ОТЧЕТ")
    lines.append("=" * 72)
    lines.append("")
    lines.append("1. Основные данные")
    for key, value in calc.summary.items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- режим подогрева (принят): {package['effective_input'].heating_mode}")
    lines.append(f"- резервуар подогреваемый: {'да' if package['effective_input'].heating_mode != 'без подогрева' else 'нет'}")

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
    lines.append("5. Подбор листового проката и вариантов стали")
    for idx, variant in enumerate(calc.steel_variants, start=1):
        lines.append(
            f"- Вариант {idx}: {variant.strength_class} ({variant.example_grade}); "
            f"σ_доп={variant.allowable_stress_mpa:.0f} МПа; t стенки={variant.shell_thickness_range_mm} мм; "
            f"лист стенки={variant.shell_sheet_format}; листов на пояс={variant.shell_sheets_per_course}; "
            f"всего листов стенки={variant.shell_total_sheets}; листов днища={variant.bottom_sheet_count}; "
            f"листов крыши={variant.roof_sheet_count}; масса≈{variant.estimated_total_mass_t:.2f} т; "
            f"оценка={variant.suitability}."
        )
        lines.append(f"    примечание: {variant.note}")

    lines.append("")
    lines.append("6. Рекомендуемое конструктивное решение")
    lines.append(f"- Вариант: {constructive_solution['solution']}")
    lines.append(f"- Обоснование: {constructive_solution['justification']}")

    lines.append("")
    lines.append("7. Рекомендации по защитным покрытиям")
    for zone_name, zone_data in coatings.items():
        lines.append(f"- {zone_name}:")
        lines.append(f"    зона: {zone_data['zone']}")
        lines.append(f"    система: {zone_data['system']}")
        lines.append(f"    толщина: {zone_data['thickness']}")
        lines.append(f"    слои: {zone_data['layers']}")
        lines.append(f"    область применения: {zone_data['application']}")
        lines.append(f"    срок службы: {zone_data['service_life']}")

    lines.append("")
    lines.append("8. Рекомендуемый состав дополнительного оборудования")
    for item in equipment["items"]:
        lines.append(f"- {item['name']}: {item['qty']}; проход {item['diameter_dn']}")
        lines.append(f"    назначение: {item['purpose']}")
        lines.append(f"    обоснование: {item['basis']}")
    lines.append("- Нормативные примечания по врезкам и оборудованию:")
    for note in equipment["normative_notes"]:
        lines.append(f"    • {note}")

    lines.append("")
    lines.append("9. Нормативная база")
    for key, value in calc.references.items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append(
        "Примечание: расчет носит предварительный расчетно-рекомендательный характер и предназначен для ВКР."
    )
    lines.append(
        "Для рабочего проектирования требуются детальный прочностной расчет, уточнение свойств продукта,"
    )
    lines.append(
        "спецификация листового проката, подбор полной трубопроводной обвязки и полная нормативная проверка принятого решения."
    )

    return "\n".join(lines)


def format_log_text(package: Dict[str, object]) -> str:
    calc: CalculationResult = package["calculation_result"]
    initial_input: InputData = package["input_data"]
    effective_input: InputData = package["effective_input"]
    template: TankTemplate = package["template"]
    product: ProductData = package["product"]
    constructive_solution = package["constructive_solution"]

    area = float(calc.summary["площадь поперечного сечения, м2"])
    fill_height = float(calc.summary["расчетная высота налива, м"])
    useful_volume = float(calc.summary["ориентировочный полезный объем, м3"])
    product_mass = float(calc.summary["масса нефтепродукта, т"])
    hydro = float(calc.summary["гидростатическое давление у днища, МПа"])
    wind = float(calc.summary["ветровая нагрузка, кПа"])
    snow = float(calc.summary["снеговая нагрузка, кПа"])
    contour = float(calc.summary["нагрузка на опорный контур крыши, кН/м"])

    lines: List[str] = []
    lines.append("ЛОГИ РАСЧЕТА")
    lines.append("=" * 72)
    lines.append("")
    lines.append("Этап 1. Исходные данные")
    lines.append(f"- Vном = {initial_input.nominal_volume_m3} м3")
    lines.append(f"- Продукт = {product.name}")
    lines.append(f"- ρ = {product.density_kg_m3:.1f} кг/м3")
    lines.append(f"- Город = {initial_input.city_name}")
    lines.append(f"- tвозд,min = {effective_input.ambient_temp_min_c:.1f} °C")
    lines.append(f"- tвозд,max = {effective_input.ambient_temp_max_c:.1f} °C")
    lines.append(f"- tпродукта = {effective_input.product_temp_c:.1f} °C")
    lines.append(f"- Подогрев (ввод) = {initial_input.heating_mode}")
    lines.append(f"- Подогрев (принят) = {effective_input.heating_mode}")
    lines.append(f"- Категория коррозионной среды = {effective_input.corrosion_category}")

    lines.append("")
    lines.append("Этап 2. Геометрия")
    lines.append(f"- D = {template.diameter_m:.3f} м")
    lines.append(f"- H = {template.shell_height_m:.3f} м")
    lines.append(f"- nпоясов = {template.shell_courses}")
    lines.append(f"- A = π·D²/4 = π·{template.diameter_m:.3f}²/4 = {area:.3f} м2")
    lines.append(f"- hнал = H·kзап = {template.shell_height_m:.3f}·{template.fill_factor:.2f} = {fill_height:.3f} м")
    lines.append(f"- Vпол = A·hнал = {area:.3f}·{fill_height:.3f} = {useful_volume:.1f} м3")
    lines.append(f"- mпрод = Vпол·ρ/1000 = {useful_volume:.1f}·{product.density_kg_m3:.1f}/1000 = {product_mass:.2f} т")

    lines.append("")
    lines.append("Этап 3. Нагрузки")
    lines.append(f"- pгидр = ρ·g·h / 10^6 = {product.density_kg_m3:.1f}·9.81·{fill_height:.3f}/10^6 = {hydro:.5f} МПа")
    lines.append(f"- qветр = {wind:.3f} кПа")
    lines.append(f"- qсн = {snow:.3f} кПа")
    lines.append(f"- qконтур = {contour:.3f} кН/м")

    lines.append("")
    lines.append("Этап 4. Пояса стенки")
    lines.append("- Формула: tтр ≈ p·D/(2·σдоп) + cкорр")
    for course in calc.course_results:
        lines.append(
            f"  Пояс {course.course_no}: p = {course.pressure_mpa:.5f} МПа; "
            f"tтр = {course.required_thickness_mm:.2f} мм; tприн = {course.adopted_thickness_mm} мм; "
            f"σокр = {course.hoop_stress_mpa:.2f} МПа; {'OK' if course.strength_ok else 'НЕ OK'}"
        )

    lines.append("")
    lines.append("Этап 5. Проверки")
    upper = calc.checks["верхняя часть оболочки"]
    roof = calc.checks["кровля"]
    wind_ring = calc.checks["ветровое кольцо"]
    lines.append(f"- Верхняя часть оболочки: σветр = {upper['sigma_wind_mpa']} МПа; σкр = {upper['sigma_cr_mpa']} МПа; η = {upper['utilization']}")
    lines.append(f"- Кровля: qсн = {roof['snow_load_kpa']} кПа; qдоп = {roof['allowable_kpa']} кПа; η = {roof['utilization']}")
    lines.append(f"- Ветровое кольцо: {'требуется' if wind_ring['need'] else 'не требуется'}; Aрек = {wind_ring['recommended_area_mm2']} мм2")

    lines.append("")
    lines.append("Этап 6. Подбор листового проката")
    for idx, variant in enumerate(calc.steel_variants, start=1):
        lines.append(
            f"- Вариант {idx}: {variant.strength_class}; σдоп = {variant.allowable_stress_mpa:.0f} МПа; "
            f"tстенки = {variant.shell_thickness_range_mm} мм; лист стенки {variant.shell_sheet_format}; "
            f"листов/пояс = {variant.shell_sheets_per_course}; всего листов стенки = {variant.shell_total_sheets}; "
            f"листов днища = {variant.bottom_sheet_count}; листов крыши = {variant.roof_sheet_count}; масса ≈ {variant.estimated_total_mass_t:.2f} т"
        )

    lines.append("")
    lines.append("Этап 7. Выбор конструктивного решения")
    lines.append(
        f"- Баллы: продукт = {constructive_solution['product_score']}; температура = {constructive_solution['temperature_score']}; "
        f"объем = {constructive_solution['volume_score']}; сумма = {constructive_solution['total_score']}"
    )
    lines.append(f"- Итог = {constructive_solution['solution']}")

    lines.append("")
    lines.append("Этап 8. Нормативная база")
    for key, value in calc.references.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)
