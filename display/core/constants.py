"""
Konstanten für das Display-System.
"""


# ANSI Farb-Codes
class Colors:
    """ANSI Farbcodes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


# Display Layout
class Layout:
    """Layout-Konstanten"""
    SEPARATOR_WIDTH = 60
    SEPARATOR_CHAR = "="
    SUB_SEPARATOR_CHAR = "-"
    LABEL_WIDTH = 25
    VALUE_WIDTH = 10
    UNIT_WIDTH = 5

    # Tabellen
    TABLE_PADDING = 2
    MIN_COLUMN_WIDTH = 8


# Schwellwerte für Farbcodierung
class Thresholds:
    """Standard-Schwellwerte"""
    # Diese werden normalerweise aus Config überschrieben
    BATTERY_HIGH = 80
    BATTERY_MEDIUM = 30

    AUTARKY_HIGH = 75
    AUTARKY_MEDIUM = 50

    PV_POWER_HIGH = 3000
    PV_POWER_MEDIUM = 1000

    SURPLUS_HIGH = 2000
    SURPLUS_MEDIUM = 500


# Formatierungs-Templates
class Templates:
    """String-Templates"""
    HEADER = "{title:<20} {subtitle}"
    VALUE_LINE = "{label:<{width}} {value:>{vwidth}} {unit}"
    PERCENTAGE = "{value:>5.1f}%"
    POWER = "{value:>6.0f}W"
    ENERGY = "{value:>7.2f} kWh"
    CURRENCY = "{value:>8.2f} {symbol}"