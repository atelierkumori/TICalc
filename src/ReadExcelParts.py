import math
from datetime import datetime, date, time
from Utils import(
    require_float, read_float_or_default, require_non_negative, 
    clamp, safe_log, read_choice, cell, pas, direct_diffuse,
    # ===== Constants =====
    atmP, stefan, elong, elongA, kclo,
    # === Excel row/column definitions ===
    COL_ERROR, COL_OUTPUT_START, N_OUTPUT_COLS, COL_OFFSET, ROW_START,
)


def read_global_params(data):
    """
    data: 2D list loaded (1-based via cell()/read_choice()).
    """
    include_solar = read_choice(data, 2, 1, {"Include", "Exclude"})         # A2
    solar_reflected = read_choice(data, 6, 1, {"Input directly", "Estimate by albedo"})  # A6
    physiol_source = read_choice(data, 3, 12, {"Input directly", "Two-node model"})      # L3

    # default
    lat_deg = 0
    lon_deg = 0
    cc_sky = 0
    albedo = 0

    if include_solar == "Include":
        lat_deg = require_float(cell(data, 3, 1), "Latitude [°]")           # A3
        lat_deg = clamp(lat_deg, 0, 180, "Latitude [°]")

        lon_deg = require_float(cell(data, 4, 1), "Longitude [°]")          # A4
        lon_deg = clamp(lon_deg, 0, 180, "Longitude [°]")

        cc_sky = require_float(cell(data, 2, 7), "Sky factor at pyranometer [-]")  # G2
        cc_sky = clamp(cc_sky, 0, 1, "Sky factor at pyranometer [-]")

        if solar_reflected == "Estimate by albedo":
            albedo = require_float(cell(data, 7, 1), "Albedo [-]")          # A7
            albedo = clamp(albedo, 0, 1, "Albedo [-]")

    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)

    # N or S; E or W
    NorS = read_choice(data, 3, 2, {"N", "S"})                              # B3
    if NorS == "S":
        lat_rad *= -1

    EorW = read_choice(data, 4, 2, {"E", "W"})                              # B4
    if EorW == "W":
        lon_rad *= -1

    # UTC: Coordinated Universal Time
    utc_map = {
        "+14": 14, "+13": 13, "+12:45": 12.75, "+12": 12, "+11:30": 11.5, "+11": 11,
        "+10:30": 10.5, "+10": 10, "+9:30": 9.5, "+9": 9, "+8:45": 8.75, "+8": 8,
        "+7": 7, "+6:30": 6.5, "+6": 6, "+5:45": 5.75, "+5:30": 5.5, "+5": 5,
        "+4:30": 4.5, "+4": 4, "+3:30": 3.5, "+3": 3, "+2": 2, "+1": 1, "0": 0,
        "-1": -1, "-2": -2, "-3": -3, "-3:30": -3.5, "-4": -4, "-4:30": -4.5,
        "-5": -5, "-6": -6, "-7": -7, "-8": -8, "-9": -9, "-9:30": -9.5,
        "-10": -10, "-11": -11, "-12": -12
    }
    UTC = read_choice(data, 5, 1, set(utc_map))                             # A5
    utc_h = utc_map[UTC]

    wind_height_reference = require_float(cell(data, 3, 7), "Reference wind height [m]")   # G3
    wind_height_reference = require_non_negative(wind_height_reference, "Reference wind height [m]")

    wind_height_measured = require_float(cell(data, 4, 7), "Measured wind height [m]")     # G4
    wind_height_measured = require_non_negative(wind_height_measured, "Measured wind height [m]")

    fcd = read_float_or_default(cell(data, 2, 12), "Contact area factor [-]", 0.0)         # L2
    fcd = clamp(fcd, 0, 1, "Contact area factor [-]")

    estimate_hc = read_choice(data, 5, 7, {"Two-node model", "Kuwabara's formula"})        # G5
    humidity_metric = read_choice(data, 6, 7, {"Relative humidity", "Wet-bulb temp", "Humidity ratio", "Vapor pressure"})  # G6
    longwave_rad = read_choice(data, 7, 7, {"Ld and Lu", "Mean radiant temp"})             # G7

    global_params = dict(
        include_solar=include_solar,
        lat_rad=lat_rad, lon_rad=lon_rad,
        NorS=NorS, EorW=EorW,
        utc_h=utc_h,
        solar_reflected=solar_reflected, albedo=albedo,
        cc_sky=cc_sky,
        wind_height_reference=wind_height_reference, wind_height_measured=wind_height_measured,
        estimate_hc=estimate_hc,
        humidity_metric=humidity_metric,
        longwave_rad=longwave_rad,
        fcd=fcd,
        physiol_source=physiol_source,
    )

    return global_params


def read_environment_data(data, global_params, error_rows):
    """
    data       : 2D list (all rows of the sheet, 0-indexed internally)
    global_params: dict from read_global_params
    error_rows : dict {row (1-based): error_message} — filled here, written later
    Returns    : list of record dicts
    """
    env_data = []
    last_row = len(data)

    # Find actual last row with data in column C (col index 2)
    for r in range(last_row - 1, ROW_START - 2, -1):
        if data[r][2] is not None:
            last_row = r + 1  # convert to 1-based
            break
    else:
        last_row = ROW_START - 1

    row = ROW_START
    while row <= last_row:
        env_values = data[row - 1][0:19]  # columns A–S (0-indexed 0..18)

        if all(val is None for val in env_values):
            error_rows[row] = None  # mark as blank → clear outputs
            row += 1
            continue

        record, err = parse_row(data, row, COL_OFFSET, global_params)

        if err:
            error_rows[row] = err
            row += 1
            continue

        env_data.append(record)
        row += 1

    return env_data


def parse_row(data, row, COL_OFFSET, global_params):
    """
    data: 2D list (1-based access via helper)
    row : 1-based Excel row number
    """
    def v(col_1based):
        """Get value at (row, col) — 1-based."""
        return data[row - 1][col_1based - 1]

    include_solar = global_params["include_solar"]
    if include_solar == "Include":

        ymd = v(COL_OFFSET + 1)
        hms = v(COL_OFFSET + 2)

        # ---- ymd ----
        if isinstance(ymd, datetime):
            ymd = ymd.date()
        elif isinstance(ymd, date):
            pass
        elif isinstance(ymd, str):
            try:
                ymd = datetime.fromisoformat(ymd).date()
            except ValueError:
                return None, f"Invalid date: {ymd!r}"
        else:
            return None, f"Invalid date: {ymd!r}"

        # --- hms ---
        if isinstance(hms, datetime):
            hms = hms.time()
        elif isinstance(hms, time):
            pass
        elif isinstance(hms, (float, int)):
            total_seconds = int(round(hms * 24 * 3600))
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            hms = time(h, m, s)
        elif isinstance(hms, str):
            try:
                hms = time.fromisoformat(hms)  # HH:MM[:SS]
            except ValueError:
                return None, f"Invalid time: {hms!r}"
        else:
            return None, f"Invalid time: {hms!r}"

        local_time = datetime.combine(ymd, hms)

        # Calculate solar altitude and azimuth angles
        utc_h = global_params["utc_h"]
        lat_rad = global_params["lat_rad"]
        lon_rad = global_params["lon_rad"]

        yearN = ymd.year
        new_years_day = date(yearN, 1, 1)
        dn = (ymd - new_years_day).days + 1
        new_years_eve = date(yearN, 12, 31)
        dn_new_years_eve = (new_years_eve - new_years_day).days + 1

        Theta = 2 * math.pi * (dn - 1) / dn_new_years_eve

        Declination = (0.006918
                    - 0.399912 * math.cos(Theta)
                    + 0.070257 * math.sin(Theta)
                    - 0.006758 * math.cos(2 * Theta)
                    + 0.000907 * math.sin(2 * Theta)
                    - 0.002697 * math.cos(3 * Theta)
                    + 0.00148 * math.sin(3 * Theta))

        eqTime = (0.000075
                + 0.001868 * math.cos(Theta)
                - 0.032077 * math.sin(Theta)
                - 0.014615 * math.cos(2 * Theta)
                - 0.040849 * math.sin(2 * Theta))

        LST = local_time.hour + local_time.minute / 60.0 + local_time.second / 3600.0 # local Standard time
        hourAngle = math.pi * ((LST - 12) - utc_h) / 12.0 + lon_rad + eqTime

        Sinh = (math.sin(lat_rad) * math.sin(Declination)
                + math.cos(lat_rad) * math.cos(Declination) * math.cos(hourAngle))

        altitude_rad = math.asin(Sinh)

        numerator = math.cos(lat_rad) * math.cos(Declination) * math.sin(hourAngle)
        denominator = math.sin(lat_rad) * Sinh - math.sin(Declination)
        if abs(numerator) < 1e-12 and abs(denominator) < 1e-12:
            azimuth_rad = 0.0
        else:
            azimuth_rad = math.atan2(numerator, denominator)

        solar_reflected = global_params["solar_reflected"]
        cc_sky = global_params["cc_sky"]

        # --- Shortwave radiation ---
        # Adjusted Ikt: assuming that diffuse solar radiation is reduced by the surroundings obscuring the sky when the sky factor is less than 1.

        try:
            Kd = require_float(v(COL_OFFSET + 6), "Kd: Global solar radiation")
            Kd = require_non_negative(Kd, "Kd: Global solar radiation")
        except ValueError as e:
            return None, str(e)

        Ikt = direct_diffuse(Kd)
        Ikt = Ikt / cc_sky if cc_sky > 0 else 0
        Ikt = max(0, min(Kd, Ikt))
        Idh = 0  # default
        Idn = 0  # default

        # Is the place shaded? Remove the direct solar radiation or not
        shade_input = v(COL_OFFSET + 16)
        if shade_input is None:
            is_shaded = False
        elif isinstance(shade_input, str):
            s = shade_input.strip()
            if s == "": # space(s) only
                is_shaded = False
            elif s in ("Y", "y", "YES", "Yes", "yes"):
                is_shaded = True
            elif s in ("N", "n", "NO", "No", "no"):
                is_shaded = False
            else:
                return None, f"Invalid Column P: {s!r}"
        else:
            return None, f"Invalid Column P: {shade_input!r}"

        if not is_shaded and Sinh > 0:
            Idh = Kd - Ikt
            Idn = Idh / Sinh

        # upward component
        if solar_reflected == "Input directly":
            try:
                Ku = require_float(v(COL_OFFSET + 7), "Ku: Reflective solar radiation")
                Ku = require_non_negative(Ku, "Ku: Reflective solar radiation")
            except ValueError as e:
                return None, str(e)

            albedo = 0 if Ku == 0 or Kd == 0 else Ku / Kd
        elif solar_reflected == "Estimate by albedo":
            albedo = global_params["albedo"]
            Ku = albedo * Kd

        if Sinh <= 0: # night time
            Kd = 0.0
            Ku = 0.0
            Idn = 0.0
            Idh = 0.0
            Ikt = 0.0

        if Sinh > 0:
            try:
                nsa_cl = require_float(v(COL_OFFSET + 10), "Net solar absorptance of cloth")
                nsa_cl = clamp(nsa_cl, 0, 1, "Net solar absorptance of cloth")
                # Siegel (1973)
            except ValueError as e:
                return None, str(e)

            try:
                nsa_sk = require_float(v(COL_OFFSET + 11), "Net solar absorptance of skin")
                nsa_sk = clamp(nsa_sk, 0, 1, "Net solar absorptance of skin")
                # Siegel (1973)
            except ValueError as e:
                return None, str(e)

            try:
                c_skyi = require_float(v(COL_OFFSET + 15), "sky factor")
                c_skyi = clamp(c_skyi, 0, 1, "sky factor")
            except ValueError as e:
                return None, str(e)
        else: # Sinh <= 0
            nsa_cl, nsa_sk, c_skyi = 0, 0, 0

        solar_inputs = dict(
            altitude_rad=altitude_rad,
            Kd=Kd, Ikt=Ikt, Idh=Idh, Idn=Idn,
            Ku=Ku, albedo=albedo,
            c_skyi=c_skyi,
            nsa_cl=nsa_cl, nsa_sk=nsa_sk,
        )
    else:  # include_solar == "Exclude"
        solar_inputs = dict(
            altitude_rad=0,
            Kd=0, Ikt=0, Idh=0, Idn=0,
            Ku=0, albedo=0,
            c_skyi=0,
            nsa_cl=0, nsa_sk=0,
        )

    # --- C:ta, D:humidity, E:velocity, H:longwave radiation ---
    try:
        ta = require_float(v(COL_OFFSET + 3), "ta")
        ta = clamp(ta, -50, 50, "ta")
    except ValueError as e:
        return None, str(e)
    try:
        humv = require_float(v(COL_OFFSET + 4), "humidity value")
    except ValueError as e:
        return None, str(e)
    try:
        Vel_raw = require_float(v(COL_OFFSET + 5), "velocity")
        Vel_raw = require_non_negative(Vel_raw, "velocity")
    except ValueError as e:
        return None, str(e)

    longwave_rad = global_params["longwave_rad"]
    if longwave_rad == "Ld and Lu":
        try:
            Ld = require_float(v(COL_OFFSET + 8), "Ld: downward longwave radiation")
        except ValueError as e:
            return None, str(e)
        try:
            Lu = require_float(v(COL_OFFSET + 9), "Lu: upward longwave radiation")
        except ValueError as e:
            return None, str(e)
        tr = ((Ld + Lu) / (2.0 * stefan * elongA)) ** 0.25 - 273.15
    else: # longwave_rad == "Mean radiant temp"
        Ld, Lu = None, None
        try:
            tr = require_float(v(COL_OFFSET + 8), "tr: mean radiant temperature")
        except ValueError as e:
            return None, str(e)

    # --- humidity ---
    humidity_metric = global_params["humidity_metric"]
    if humidity_metric == "Wet-bulb temp":
        try:
            humv = clamp(humv, -50, 50, "Wet-bulb temp")
        except ValueError as e:
            return None, str(e)
        coef = 0.000583 if ta < 0 else 0.000662
        Pa = pas(humv) - coef * atmP * (ta - humv)
        RH = 100.0 * (Pa / pas(ta))
        h_ratio = 622.0 * (Pa / (atmP - Pa))
    elif humidity_metric == "Relative humidity":
        try:
            humv = clamp(humv, 0, 100, "Relative humidity")
        except ValueError as e:
            return None, str(e)
        RH = humv
        Pa = pas(ta) * (RH / 100.0)
        h_ratio = 622.0 * (Pa / (atmP - Pa))
    elif humidity_metric == "Vapor pressure":
        try:
            humv = require_non_negative(humv, "Vapor pressure")
        except ValueError as e:
            return None, str(e)
        Pa = humv / 10.0
        RH = 100.0 * (Pa / pas(ta))
        h_ratio = 622.0 * (Pa / (atmP - Pa))
    elif humidity_metric == "Humidity ratio":
        try:
            humv = require_non_negative(humv, "Humidity ratio")
        except ValueError as e:
            return None, str(e)
        h_ratio = humv
        Pa = atmP * h_ratio / (622.0 + h_ratio)
        RH = 100.0 * (Pa / pas(ta))

    # wind speed height correction (log law)
    # Havenith et al. (2012); Fiala et al. (2012)
    wind_height_reference = global_params["wind_height_reference"]
    wind_height_measured = global_params["wind_height_measured"]

    Vel = Vel_raw * (
        safe_log(max(wind_height_reference, 0.01) / 0.01)
        / safe_log(max(wind_height_measured, 0.01) / 0.01)
    )
    Vel_10 = Vel_raw * (
        safe_log(10 / 0.01)
        / safe_log(max(wind_height_measured, 0.01) / 0.01)
    )

    try:
        Iclo = require_float(v(COL_OFFSET + 12), "clo value")
        Iclo = require_non_negative(Iclo, "clo value")
    except ValueError as e:
        return None, str(e)
    FACL = 1.0 + kclo * Iclo

    try:
        M_met = require_float(v(COL_OFFSET + 13), "metabolic rate")
        M_met = require_non_negative(M_met, "metabolic rate")
    except ValueError as e:
        return None, str(e)
    M_watt = M_met * 58.15
    Ms = M_watt

    try:
        representative_temp = read_float_or_default(
            v(COL_OFFSET + 14),
            "representative temperature (Column N)",
            0.0
            # 24 [°C] gives PMV=0 at the standard environmental parameters of OET, SET*
            # 28.81 [°C] gives PMV=0 at the standard environmental parameters of ETU
        )
    except ValueError as e:
        return None, str(e)

    # --- tsk and wettedness ---
    physiol_source = global_params["physiol_source"]
    if physiol_source == "Input directly":
        try:
            tsk = require_float(v(COL_OFFSET + 17), "tsk") # Q
        except ValueError as e:
            return None, str(e)
        try:
            w = require_float(v(COL_OFFSET + 18), "wettedness")# column R
            w = clamp(w, 0, 1, "wettedness")
        except ValueError as e:
            return None, str(e)
    else:# physiol_source == "Two-node model":
        tsk, w = None, None

    # --- conduct heat ---
    fcd = global_params["fcd"]
    if fcd == 0:
        conduct_heat = 0
    else:
        try:
            conduct_heat = require_float(v(COL_OFFSET + 19), "Heat loss at contact surface") # Heat flux at contact surface: positive for heat loss, negative for heat gain
        except ValueError as e:
            return None, str(e)

    record = dict(
        row=row,
        ta=ta, Vel_raw=Vel_raw, Vel=Vel, Vel_10=Vel_10,
        representative_temp=representative_temp,
        humv=humv, Pa=Pa, RH=RH, h_ratio=h_ratio,
        solar_inputs=solar_inputs,
        Ld=Ld, Lu=Lu, tr=tr,
        Iclo=Iclo, FACL=FACL,
        M_met=M_met, M_watt=M_watt, Ms=Ms,
        tsk=tsk, w=w,
        conduct_heat=conduct_heat,
    )
    return record, None
