import math

# ===== Constants =====
I0 = 1.37 * 1000.0      # Solar constant [W/m2]
atmP = 101.325          # [kPa]
stefan = 5.6697e-8      # Stefan-Boltzmann constant
elong = 0.98            # emissivity of clothed body
elongA = 0.95           # emissivity of surroundings
Ar_ratio = 0.72         # projected area factor [-]
kclo = 0.25             # clothing area factor [-]Gagge et al.(1986)
w_max = 0.85            # maximum skin wettedness [-]
icl = 0.45              # intrinsic permeation efficiency ratio [-]Gagge et al.(1986)
Work = 0.0              # external work [W/m2]
# average sized man # Gagge et al (1986)
Weight = 70             # [kg] 
Area = 1.8              # [m2]

# === Excel row/column definitions ===
COL_ERROR = 23          # W
COL_OUTPUT_START = 24   # X
N_OUTPUT_COLS = 20
COL_OFFSET = 0
ROW_START = 10

def require_float(x, name, row=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        loc = f" at row {row}" if row is not None else ""
        raise ValueError(f"Invalid {name}{loc} (not a number: {x!r})")

def read_float_or_default(x, name, default, row=None):
    if x is None:
        return default
    try:
        return float(x)
    except (TypeError, ValueError):
        loc = f" at row {row}" if row is not None else ""
        raise ValueError(f"Invalid {name}{loc} (not a number: {x!r})")

def require_non_negative(x, name="value", row=None):
    if x < 0:
        loc = f" at row {row}" if row is not None else ""
        raise ValueError(f"Invalid {name}{loc} (expected >= 0, got {x!r})")
    return x
    
def clamp(x, lo, hi, name="value", row=None):
    if not (lo <= x <= hi):
        loc = f" at row {row}" if row is not None else ""
        raise ValueError(
            f"Invalid {name}{loc} (expected {lo}-{hi}, got {x!r})"
        )
    return x

def read_str(data, row, col):
    """Read a string value from the 2D array (1-based row/col)."""
    v = data[row - 1][col - 1]
    if not isinstance(v, str):
        raise ValueError(f"Invalid cell ({row},{col}) (not a string: {v!r})")
    return v.strip()

def read_choice(data, row, col, choices):
    """Read a choice value from the 2D array (1-based row/col)."""
    v = read_str(data, row, col)
    if v not in choices:
        raise ValueError(f"Invalid cell ({row},{col}) (expected one of {choices}, got {v!r})")
    return v

def cell(data, row, col):
    """Read a cell value from the 2D array (1-based row/col)."""
    return data[row - 1][col - 1]

def safe_log(x):
    return math.log(max(x, 1e-9))

# ===== Saturation vapour pressure [kPa] =====
# Antoine's formula
def pas(t_c: float) -> float:
    return math.exp(16.6536 - 4030.183 / (t_c + 235))

# ===== Direct-diffuse separation =====
# Reindl et al. (1990)
def direct_diffuse(Kd: float) -> float:
    ClearIndex = Kd / I0
    if ClearIndex > 1:
        print("Warning: ClearIndex > 1. Forced to 1.")
        ClearIndex = 1.0
    if ClearIndex <= 0.3:
        Ikt = Kd * (1.02 - 0.248 * ClearIndex)
        Ikt = min(Ikt, Kd)
    elif ClearIndex <= 0.78:
        Ikt = Kd * (1.45 - 1.67 * ClearIndex)
    else:  # 0.78 < ClearIndex <= 1
        Ikt = Kd * 0.147
    return Ikt

# ===== Projected area factor =====
# Underwood and Ward (1966)
def f_projected(altitude_rad: float, Area: float) -> float:
    # Calculate the projected area by changing the azimuth angle from 0 to 90 degrees in 15-degree intervals, and then calculate the projected area factor from the mean value.
    azimuths = [math.pi / 12 * i for i in range(7)]  # [rad]
    underwood_values = [
        0.043 * math.sin(altitude_rad) + 
        2.997 * math.cos(altitude_rad) * 
        (0.02133 * math.cos(az) ** 2 + 0.0091 * math.sin(az) ** 2) ** 0.5  # [m2]
        for az in azimuths
    ]
    underwood_sum = sum(underwood_values)
    return underwood_sum / 7 / Area
