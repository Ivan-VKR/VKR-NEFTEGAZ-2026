from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ProductData:
    name: str
    density_kg_m3: float
    volatility: str
    vapor_loss_tendency: str
    internal_corrosivity: str
    internal_coating_note: str
    product_group: str
    heating_behavior: str
    note: str


_PRODUCTS: Dict[str, ProductData] = {
    "АИ-92": ProductData(
        name="АИ-92",
        density_kg_m3=750.0,
        volatility="высокая",
        vapor_loss_tendency="высокая",
        internal_corrosivity="средняя",
        internal_coating_note="светлый летучий нефтепродукт; приоритет защиты паровоздушной зоны и зоны переменного смачивания",
        product_group="gasoline",
        heating_behavior="none",
        note="автомобильный бензин регулярного класса",
    ),
    "АИ-95": ProductData(
        name="АИ-95",
        density_kg_m3=745.0,
        volatility="высокая",
        vapor_loss_tendency="высокая",
        internal_corrosivity="средняя",
        internal_coating_note="светлый летучий нефтепродукт; целесообразны химстойкие покрытия и усиленная защита ПВЗ",
        product_group="gasoline",
        heating_behavior="none",
        note="высокооктановый автомобильный бензин",
    ),
    "АИ-98": ProductData(
        name="АИ-98",
        density_kg_m3=740.0,
        volatility="высокая",
        vapor_loss_tendency="высокая",
        internal_corrosivity="средняя",
        internal_coating_note="высоколетучий светлый нефтепродукт; особое внимание паровоздушной зоне",
        product_group="gasoline",
        heating_behavior="none",
        note="высокооктановый автомобильный бензин",
    ),
    "Бензин А-80": ProductData(
        name="Бензин А-80",
        density_kg_m3=755.0,
        volatility="высокая",
        vapor_loss_tendency="высокая",
        internal_corrosivity="средняя",
        internal_coating_note="летучий светлый нефтепродукт; химстойкое покрытие внутренней поверхности",
        product_group="gasoline",
        heating_behavior="none",
        note="бензин пониженного октанового числа",
    ),
    "Jet A-1": ProductData(
        name="Jet A-1",
        density_kg_m3=800.0,
        volatility="средняя",
        vapor_loss_tendency="повышенная",
        internal_corrosivity="средняя",
        internal_coating_note="авиационное топливо керосинового типа; требуется стойкость покрытия к светлым нефтепродуктам",
        product_group="jet_fuel",
        heating_behavior="none",
        note="авиационное топливо международного стандарта",
    ),
    "ТС-1": ProductData(
        name="ТС-1",
        density_kg_m3=800.0,
        volatility="средняя",
        vapor_loss_tendency="повышенная",
        internal_corrosivity="средняя",
        internal_coating_note="авиационный керосин; повышенное внимание паровоздушной зоне и герметичности резервуара",
        product_group="jet_fuel",
        heating_behavior="none",
        note="авиационное топливо для реактивных двигателей",
    ),
    "РТ": ProductData(
        name="РТ",
        density_kg_m3=810.0,
        volatility="средняя",
        vapor_loss_tendency="повышенная",
        internal_corrosivity="средняя",
        internal_coating_note="топливо реактивное; требуется химстойкая система покрытия",
        product_group="jet_fuel",
        heating_behavior="none",
        note="реактивное топливо повышенного качества",
    ),
    "Керосин": ProductData(
        name="Керосин",
        density_kg_m3=810.0,
        volatility="средняя",
        vapor_loss_tendency="средняя",
        internal_corrosivity="средняя",
        internal_coating_note="светлый нефтепродукт; важна стойкость к паровоздушной зоне",
        product_group="kerosene",
        heating_behavior="none",
        note="технический/осветительный керосин",
    ),
    "Дизельное топливо летнее": ProductData(
        name="Дизельное топливо летнее",
        density_kg_m3=840.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="средняя",
        internal_coating_note="дизельное топливо; основное внимание зоне контакта с продуктом и донной части",
        product_group="diesel",
        heating_behavior="diesel_summer",
        note="дизельное топливо летнего сорта",
    ),
    "Дизельное топливо межсезонное": ProductData(
        name="Дизельное топливо межсезонное",
        density_kg_m3=835.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="средняя",
        internal_coating_note="дизельное топливо; предпочтительна защита донной зоны и зоны воды/отстоя",
        product_group="diesel",
        heating_behavior="diesel_mid",
        note="дизельное топливо межсезонного сорта",
    ),
    "Дизельное топливо зимнее": ProductData(
        name="Дизельное топливо зимнее",
        density_kg_m3=830.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="средняя",
        internal_coating_note="зимнее дизельное топливо; внимание к донной зоне и контролю наличия воды",
        product_group="diesel",
        heating_behavior="diesel_winter",
        note="дизельное топливо зимнего сорта",
    ),
    "Дизельное топливо арктическое": ProductData(
        name="Дизельное топливо арктическое",
        density_kg_m3=820.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="средняя",
        internal_coating_note="арктическое дизельное топливо; подогрев обычно не является основным требованием хранения",
        product_group="diesel",
        heating_behavior="diesel_arctic",
        note="дизельное топливо арктического сорта",
    ),
    "Нефть легкая": ProductData(
        name="Нефть легкая",
        density_kg_m3=840.0,
        volatility="средняя",
        vapor_loss_tendency="средняя",
        internal_corrosivity="средняя",
        internal_coating_note="нефть; требуется защита донной части, зоны воды и ПВЗ",
        product_group="crude_light",
        heating_behavior="crude_light",
        note="легкая нефть с умеренной вязкостью",
    ),
    "Нефть средняя": ProductData(
        name="Нефть средняя",
        density_kg_m3=870.0,
        volatility="средняя",
        vapor_loss_tendency="средняя",
        internal_corrosivity="повышенная",
        internal_coating_note="нефть; желательно усиленное покрытие донной части и зоны отстоя воды",
        product_group="crude_medium",
        heating_behavior="crude_medium",
        note="средняя нефть с типовой вязкостью и возможным содержанием воды",
    ),
    "Нефть тяжелая": ProductData(
        name="Нефть тяжелая",
        density_kg_m3=920.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="повышенная",
        internal_coating_note="тяжелая нефть; желательно усиленное покрытие донной части и зоны отстоя воды, контроль при подогреве",
        product_group="crude_heavy",
        heating_behavior="crude_heavy",
        note="тяжелая нефть с повышенной вязкостью",
    ),
    "Мазут М100": ProductData(
        name="Мазут М100",
        density_kg_m3=960.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="повышенная",
        internal_coating_note="тяжелый нефтепродукт; обязательен учет термической стойкости внутреннего покрытия при подогреве",
        product_group="fuel_oil",
        heating_behavior="fuel_oil_constant",
        note="тяжелый вязкий нефтепродукт, как правило требует подогрева",
    ),
    "Мазут Ф5": ProductData(
        name="Мазут Ф5",
        density_kg_m3=930.0,
        volatility="низкая",
        vapor_loss_tendency="низкая",
        internal_corrosivity="повышенная",
        internal_coating_note="флотский мазут; требуется стойкость покрытия к тяжелым нефтепродуктам и температуре",
        product_group="fuel_oil",
        heating_behavior="fuel_oil_periodic",
        note="флотский мазут повышенной вязкости",
    ),
    "Ракетное топливо РГ-1": ProductData(
        name="Ракетное топливо РГ-1",
        density_kg_m3=810.0,
        volatility="средняя",
        vapor_loss_tendency="повышенная",
        internal_corrosivity="средняя",
        internal_coating_note="керосиновое ракетное топливо; требуется химстойкая система покрытия для светлых нефтепродуктов",
        product_group="rocket_fuel",
        heating_behavior="none",
        note="углеводородное ракетное топливо керосинового типа",
    ),
    "Ракетное топливо Т-6": ProductData(
        name="Ракетное топливо Т-6",
        density_kg_m3=840.0,
        volatility="средняя",
        vapor_loss_tendency="средняя",
        internal_corrosivity="средняя",
        internal_coating_note="высокотемпературное углеводородное ракетное топливо; следует учитывать химическую стойкость покрытия",
        product_group="rocket_fuel",
        heating_behavior="none",
        note="термостабильное углеводородное ракетное топливо",
    ),
}


def get_product(name: str) -> ProductData:
    try:
        return _PRODUCTS[name]
    except KeyError as exc:
        raise KeyError(f"Неизвестный нефтепродукт: {name}") from exc



def get_product_names() -> List[str]:
    return list(_PRODUCTS.keys())
