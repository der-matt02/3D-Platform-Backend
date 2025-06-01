from enum import Enum


class FilamentType(str, Enum):
    pla = "PLA"
    abs = "ABS"
    petg = "PETG"
    tpu = "TPU"
    nylon = "Nylon"
    hips = "HIPS"
    pc = "PC"
    asa = "ASA"


class FilamentColor(str, Enum):
    black = "Negro"
    white = "Blanco"
    red = "Rojo"
    blue = "Azul"
    green = "Verde"
    yellow = "Amarillo"
    gray = "Gris"
    transparent = "Transparente"
    orange = "Naranja"
    purple = "Púrpura"
    silver = "Plateado"
    gold = "Dorado"


class FilamentDiameter(float, Enum):
    standard_175 = 1.75
    industrial_285 = 2.85
    legacy_300 = 3.0
