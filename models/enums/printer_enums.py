from enum import Enum

class PrinterType(str, Enum):
    fdm = "FDM"
    sla = "SLA"
    sls = "SLS"
    dlp = "DLP"
    msla = "MSLA"

class NozzleSize(str, Enum):  # usamos str para documentar bien
    point2 = "0.2"
    point4 = "0.4"
    point6 = "0.6"
    point8 = "0.8"
    one = "1.0"

class SupportType(str, Enum):
    tree = "Árbol"
    linear = "Lineal"
