import swisseph as swe
from datetime import datetime, timedelta
import pytz

#####################
# GLOBAL DEFINITIONS
#####################

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def sign_name(sign_number):
    """
    Converts a sign number (1..12) to the corresponding English zodiac name.
    E.g. 1->Aries, 2->Taurus, etc.
    """
    if 1 <= sign_number <= 12:
        return SIGNS[sign_number - 1]
    return "Unknown"

def convert_to_24_hour(time_str):
    """
    Converts '07:30 PM' to '19:30' (24-hour).
    If conversion fails, returns the string as is.
    """
    try:
        return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        return time_str

def get_birth_datetime(date_of_birth, time_of_birth, timezone):
    """
    Returns a localized datetime object for the given birth details.
    """
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Unknown timezone: {timezone}")
    dt_local = tz.localize(datetime.strptime(f"{date_of_birth} {time_of_birth}", "%Y-%m-%d %H:%M"))
    return dt_local

#####################
# TIME & JULIAN DAY
#####################

def calculate_julian_day(date_of_birth, time_of_birth, timezone):
    """
    Combines date/time/timezone => Julian Day for Swiss Ephemeris.
    """
    dt_local = get_birth_datetime(date_of_birth, time_of_birth, timezone)
    dt_utc = dt_local.astimezone(pytz.utc)
    jd = swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    )
    return jd

##############################
# BASIC PLANETS, HOUSES & NAKSHATRA
##############################

def calculate_planetary_positions(jd):
    """
    Sidereal planetary longitudes using Lahiri ayanamsa.
    Ketu = Rahu + 180°.
    Returns a dictionary with planet names as keys and their ecliptic degrees.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS, "Saturn": swe.SATURN,
        "Rahu": swe.TRUE_NODE, "Ketu": None
    }
    pos = {}
    for planet, code in planets.items():
        if planet == "Ketu":
            rahu_pos, _ = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SIDEREAL)
            pos["Ketu"] = (rahu_pos[0] + 180.0) % 360
        else:
            p, _ = swe.calc_ut(jd, code, swe.FLG_SIDEREAL)
            pos[planet] = p[0]
    return pos

def calculate_houses(jd, latitude, longitude):
    """
    Calculates Whole Sign houses in sidereal mode.
    Returns a tuple (houses, ascendant_degs) where houses is a list of 12 cusp values.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    houses, ascmc = swe.houses_ex(jd, latitude, longitude, b"W", swe.FLG_SIDEREAL)
    ascendant = ascmc[0]
    return houses, ascendant

def determine_house_for_planet(ecliptic_degree, houses):
    """
    Determines which house a planet falls in based on its ecliptic degree and the house cusps.
    Assumes Whole Sign houses.
    """
    for i in range(12):
        cusp = houses[i]
        next_cusp = houses[(i + 1) % 12] + (360 if i == 11 else 0)
        adj_deg = ecliptic_degree if ecliptic_degree >= cusp else ecliptic_degree + 360
        if cusp <= adj_deg < next_cusp:
            return i + 1
    return 12

def calculate_nakshatra(jd_birth):
    """
    Determines the Nakshatra (Lunar Mansion) based on the Moon's sidereal position.
    Each nakshatra spans 13°20' (i.e. 13.333...°).
    """
    moon_pos, _ = swe.calc_ut(jd_birth, swe.MOON, swe.FLG_SIDEREAL)
    nakshatra_num = int((moon_pos[0] % 360) / 13.3333333) + 1
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
        "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
        "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]
    return nakshatras[nakshatra_num - 1]

##############################
# VIMSHOTTARI DASHA LOGIC (UPDATED)
##############################

def calculate_vimshottari_dasha(jd_birth):
    """
    Calculates the Vimshottari Dasha periods based on the birth Julian Day.
    Returns a list of dictionaries with 'planet', 'start_date', and 'end_date'.
    """
    # Vimshottari Dasha sequence and their lengths in years
    dasha_sequence = [
        ('Ketu', 7),
        ('Venus', 20),
        ('Sun', 6),
        ('Moon', 10),
        ('Mars', 7),
        ('Rahu', 18),
        ('Jupiter', 16),
        ('Saturn', 19),
        ('Mercury', 17)
    ]

    # Get the Moon's nakshatra at birth
    iflag = swe.FLG_SIDEREAL
    moon_position, ret = swe.calc_ut(jd_birth, swe.MOON, iflag)
    if ret < 0:
        raise Exception(f"Error calculating Moon position: {swe.get_error_message(ret)}")
    moon_lon = moon_position[0]
    nakshatra_number = int((moon_lon % 360) / 13.3333333)  # Each nakshatra is ~13.3333 degrees

    # Determine the starting dasha
    dasha_order = dasha_sequence[nakshatra_number % 9:] + dasha_sequence[:nakshatra_number % 9]

    # Calculate the fraction of the nakshatra completed
    nakshatra_pada = (moon_lon % 13.3333333) / 13.3333333  # Fraction completed
    balance_years = dasha_order[0][1] * (1 - nakshatra_pada)

    # Convert jd_birth to a Python datetime
    year, month, day, hour = swe.revjul(jd_birth, swe.GREG_CAL)
    int_hour = int(hour)
    minute = int((hour - int_hour) * 60)
    second = int((((hour - int_hour) * 60) - minute) * 60)
    current_time = datetime(year, month, day, int_hour, minute, second)

    # Build the dasha periods
    dasha_periods = []

    # First Dasha (remaining fraction of the first planet)
    start_date = current_time
    end_date = start_date + timedelta(days=balance_years * 365.25)
    dasha_periods.append({
        'planet': dasha_order[0][0],
        'start_date': start_date,
        'end_date': end_date
    })
    current_time = end_date

    # Subsequent Dashas (full durations)
    for planet, years in dasha_order[1:]:
        start_date = current_time
        end_date = start_date + timedelta(days=years * 365.25)
        dasha_periods.append({
            'planet': planet,
            'start_date': start_date,
            'end_date': end_date
        })
        current_time = end_date

    return dasha_periods

def get_current_dasha(dasha_periods):
    """
    Finds the current Mahadasha from the list of Dasha periods.
    """
    current_time = datetime.utcnow()
    current_dasha = None
    for dasha in dasha_periods:
        if dasha['start_date'] <= current_time <= dasha['end_date']:
            current_dasha = dasha
            break
    return current_dasha

def calculate_antardasha(current_dasha, dasha_periods):
    """
    Calculates the current Antardasha within the current Mahadasha.
    """
    if not current_dasha:
        return None  # No current Mahadasha found

    # Vimshottari Dasha cycle has a total of 120 years
    # Each Mahadasha is divided into Antardashas based on the same 9-planet sequence
    dasha_sequence = [
        'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
        'Rahu', 'Jupiter', 'Saturn', 'Mercury'
    ]

    mahadasha_planet = current_dasha['planet']
    try:
        start_index = dasha_sequence.index(mahadasha_planet)
    except ValueError:
        raise Exception(f"Mahadasha planet {mahadasha_planet} not found in the sequence.")

    # Define Antardasha sequence starting from Mahadasha planet
    antardasha_sequence = dasha_sequence[start_index:] + dasha_sequence[:start_index]

    # Define the lengths of each Antardasha in years
    antardasha_lengths = {
        'Ketu': 7,
        'Venus': 20,
        'Sun': 6,
        'Moon': 10,
        'Mars': 7,
        'Rahu': 18,
        'Jupiter': 16,
        'Saturn': 19,
        'Mercury': 17
    }

    # Total Mahadasha duration in days
    total_dasha_duration = (current_dasha['end_date'] - current_dasha['start_date']).days

    # Calculate the duration of each Antardasha
    antardasha_periods = []
    cumulative_days = 0
    for planet in antardasha_sequence:
        duration_years = antardasha_lengths[planet]
        duration_days = (duration_years / 120.0) * total_dasha_duration
        start = current_dasha['start_date'] + timedelta(days=cumulative_days)
        end = start + timedelta(days=duration_days)
        antardasha_periods.append({
            'planet': planet,
            'start_date': start,
            'end_date': end
        })
        cumulative_days += duration_days

    # Find current Antardasha
    now = datetime.utcnow()
    current_antardasha = None
    for antardasha in antardasha_periods:
        if antardasha['start_date'] <= now <= antardasha['end_date']:
            current_antardasha = antardasha
            break

    return current_antardasha

##############################
# STANDARD SUB-LOT MAPPING
##############################

def get_sub_lot_index(local_deg, sub_sign_count):
    """
    local_deg in [0, 30)
    Returns the sub-lot index (1 to sub_sign_count) for the given degree within a sign.
    """
    size = 30.0 / sub_sign_count
    idx = int(local_deg // size) + 1
    return min(idx, sub_sign_count)

def compute_divisional_chart(planetary_positions, planetary_signs, sub_sign_count, sign_sequence_func):
    """
    Computes a divisional chart (e.g., D7, D9, etc.) using the provided sign mapping.
    For each planet:
      - Finds the D1 sign.
      - Computes the degree within the sign.
      - Determines the sub-lot index.
      - Uses the sub-lot mapping (via sign_sequence_func) to assign a new sign.
      - Calculates a leftover degree for display.
    Returns a dictionary with each planet's divisional chart data.
    """
    chart_data = {}
    slot_size = 30.0 / sub_sign_count
    for planet, eclip_deg in planetary_positions.items():
        d1_sign = planetary_signs[planet]
        local_deg = eclip_deg % 30.0
        sub_idx = get_sub_lot_index(local_deg, sub_sign_count)
        sub_signs = sign_sequence_func(d1_sign)
        if sub_idx > len(sub_signs):
            sub_idx = len(sub_signs)
        new_sign = sub_signs[sub_idx - 1]
        leftover_deg = (local_deg % slot_size) * sub_sign_count
        chart_data[planet] = {
            "degree": round(leftover_deg, 2),
            "sign": new_sign
        }
    return chart_data

##############################
# DIVISIONAL CHART TABLES (D7, D9, D10, D12, D60)
##############################

def d7_sign_sequence(rashi_name):
    """
    Saptamsa (D7) mapping per classical Parashara.
    """
    D7_TABLE = {
       "Aries":      ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"],
       "Taurus":     ["Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus"],
       "Gemini":     ["Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius"],
       "Cancer":     ["Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio"],
       "Leo":        ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"],
       "Virgo":      ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer"],
       "Libra":      ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries"],
       "Scorpio":    ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn"],
       "Sagittarius":["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"],
       "Capricorn":  ["Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
       "Aquarius":   ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"],
       "Pisces":     ["Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    }
    return D7_TABLE.get(rashi_name, ["Unknown"] * 7)

def d9_sign_sequence(rashi_name):
    """
    Classical Navamsa (D9) mapping per Parashara.
    """
    D9_TABLE = {
        "Aries":      ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
        "Taurus":     ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Gemini":     ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini"],
        "Cancer":     ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
        "Leo":        ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
        "Virgo":      ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Libra":      ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini"],
        "Scorpio":    ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
        "Sagittarius":["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
        "Capricorn":  ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Aquarius":   ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini"],
        "Pisces":     ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    }
    return D9_TABLE.get(rashi_name, ["Unknown"] * 9)

def d10_sign_sequence(rashi_name):
    """
    Dasamsa (D10) mapping.
    """
    D10_TABLE = {
        "Aries":      ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn"],
        "Taurus":     ["Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio"],
        "Gemini":     ["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Cancer":     ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer"],
        "Leo":        ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn"],
        "Virgo":      ["Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio"],
        "Libra":      ["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Scorpio":    ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer"],
        "Sagittarius":["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn"],
        "Capricorn":  ["Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio"],
        "Aquarius":   ["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Pisces":     ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer"]
    }
    return D10_TABLE.get(rashi_name, ["Unknown"] * 10)

def d12_sign_sequence(rashi_name):
    """
    Dvadasamsa (D12) mapping.
    """
    D12_TABLE = {
        "Aries":     ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
        "Taurus":    ["Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries"],
        "Gemini":    ["Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus"],
        "Cancer":    ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini"],
        "Leo":       ["Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer"],
        "Virgo":     ["Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo"],
        "Libra":     ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        "Scorpio":   ["Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"],
        "Sagittarius":["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio"],
        "Capricorn": ["Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
        "Aquarius":  ["Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn"],
        "Pisces":    ["Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius"]
    }
    return D12_TABLE.get(rashi_name, ["Unknown"] * 12)

def d60_sign_sequence(rashi_name):
    """
    Shashtiamsa (D60) simplified cyclical approach:
    Cycles the 12 signs 5 times.
    """
    return SIGNS * 5

###############################
# BUILD REPORT & STRENGTH
###############################

def determine_house_rulers(asc_sign):
    """
    Determines the house ruler for each house based on the Ascendant's sign.
    """
    sign_rulers = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
        "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
        "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
    }
    house_rulers = {}
    for house in range(1, 13):
        # For Whole Sign houses, the house's sign is determined by:
        sign_idx = (asc_sign + house - 2) % 12 + 1
        house_rulers[house] = sign_rulers.get(sign_name(sign_idx), "Unknown")
    return house_rulers

def get_planetary_strength(planet, sign, house):
    """
    Determines the strength of a planet based on its sign, with consideration for
    exaltation, debilitation, ownership, and directional (Dig Bala) strength.
    """
    benefics = ["Sun", "Venus", "Jupiter", "Mercury", "Moon"]
    malefics = ["Mars", "Saturn", "Rahu", "Ketu"]

    exalt = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
             "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"}
    debil = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
             "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"}
    owns = {"Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
            "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
            "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"]}

    if planet in exalt and sign == exalt[planet]:
        strength = "Exalted"
    elif planet in debil and sign == debil[planet]:
        strength = "Debilitated"
    elif planet in owns and sign in owns[planet]:
        strength = "Strong"
    else:
        strength = "Neutral"

    # Check Dig Bala
    dig_bala = {"Sun": 1, "Mars": 10, "Jupiter": 1, "Moon": 4,
                "Venus": 7, "Mercury": 7, "Saturn": 10}
    if planet in dig_bala and house == dig_bala[planet]:
        strength += " + Dig Bala"

    return strength, (planet in benefics)

def make_personalized_report(planet_in_houses, house_rulers,
                             dasha_periods, current_dasha, current_antardasha,
                             planetary_positions, planetary_signs,
                             asc_sign_name, asc_deg, nakshatra):
    """
    Builds a detailed Kundali report.
    """
    report = {}
    for planet, house in planet_in_houses.items():
        sign = planetary_signs[planet]
        strength = get_planetary_strength(planet, sign, house)[0]
        pos_deg = planetary_positions[planet]
        report[planet] = {
            "house": house,
            "house_ruler": house_rulers.get(house, "Unknown"),
            "strength": strength,
            "benefic": (planet in ["Sun", "Venus", "Jupiter", "Mercury", "Moon"]),
            "position": pos_deg,
            "planetary_sign": sign
        }

    report["Mahadasha"] = {}
    if current_dasha:
        report["Mahadasha"] = {
            "planet": current_dasha["planet"],
            "start_date": current_dasha["start_date"].strftime("%Y-%m-%d"),
            "end_date": current_dasha["end_date"].strftime("%Y-%m-%d")
        }
    report["Antardasha"] = {}
    if current_antardasha:
        report["Antardasha"] = {
            "planet": current_antardasha["planet"],
            "start_date": current_antardasha["start_date"].strftime("%Y-%m-%d"),
            "end_date": current_antardasha["end_date"].strftime("%Y-%m-%d")
        }

    summary = prepare_kundali_summary(report, asc_sign_name, asc_deg, nakshatra)
    report["kundali_summary"] = summary

    report["planetary_positions"] = planetary_positions
    report["planet_in_houses"] = planet_in_houses
    report["house_rulers"] = house_rulers
    report["dasha_periods"] = dasha_periods
    report["current_dasha"] = current_dasha
    report["current_antardasha"] = current_antardasha

    return report

def prepare_kundali_summary(report, asc_sign_name, asc_deg, nakshatra):
    """
    Prepares a textual Kundali summary.
    """
    summ = (f"Kundali Report Summary:\n"
            f"Ascendant (Lagna): {asc_sign_name} ({asc_deg:.2f}°)\n"
            f"Nakshatra: {nakshatra}\n\n"
            "Planetary Positions:\n")
    for planet, details in report.items():
        if planet in ["Mahadasha", "Antardasha", "kundali_summary"]:
            continue
        deg = details["position"]
        h = details["house"]
        hr = details["house_ruler"]
        strn = details["strength"]
        ben = details["benefic"]
        sg = details["planetary_sign"]
        summ += (f"{planet}: {deg:.2f}° in {sg}, "
                 f"House {h} ({hr}), "
                 f"Strength: {strn}, "
                 f"Nature: {'Benefic' if ben else 'Malefic'}\n")
    md = report["Mahadasha"]
    if md.get("planet"):
        summ += (f"\nCurrent Mahadasha: {md['planet']} "
                 f"(from {md['start_date']} to {md['end_date']})\n")
    else:
        summ += "\nCurrent Mahadasha: Not Found\n"
    ad = report["Antardasha"]
    if ad.get("planet"):
        summ += (f"Current Antardasha: {ad['planet']} "
                 f"(from {ad['start_date']} to {ad['end_date']})\n")
    else:
        summ += "Current Antardasha: Not Found\n"
    return summ

###############################
# FINAL PUBLIC FUNCTION
###############################

def calculate_kundali(name: str, date_of_birth: str, time_of_birth: str,
                      latitude: float, longitude: float, timezone: str):
    """
    1) Convert time to 24-hour.
    2) Calculate Julian Day and compute sidereal planetary positions and houses.
    3) Compute Vimshottari dasha periods (with updated logic).
    4) Build the main (D1) Kundali report.
    5) Compute additional divisional charts: D7, D9, D10, D12, and D60.
    6) Return the final Kundali report as a dictionary.
    """
    # 1) Convert time
    time_24 = convert_to_24_hour(time_of_birth)

    # 2) Calculate Julian Day and basic positions
    jd_birth = calculate_julian_day(date_of_birth, time_24, timezone)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    planetary_positions = calculate_planetary_positions(jd_birth)
    houses, asc_deg = calculate_houses(jd_birth, latitude, longitude)

    # Determine D1 sign & house for each planet
    planet_in_houses = {}
    planetary_signs = {}
    for planet, deg in planetary_positions.items():
        s_num = int(deg // 30) + 1
        if s_num > 12:
            s_num -= 12
        planetary_signs[planet] = sign_name(s_num)
        planet_in_houses[planet] = determine_house_for_planet(deg, houses)

    # Ascendant sign
    asc_sign_num = int(asc_deg // 30) + 1
    asc_sign_str = sign_name(asc_sign_num)
    house_rulers = determine_house_rulers(asc_sign_num)

    # 3) Compute Vimshottari Dasha and Antardasha (updated logic)
    dasha_periods = calculate_vimshottari_dasha(jd_birth)
    current_dasha = get_current_dasha(dasha_periods)
    current_antardasha = calculate_antardasha(current_dasha, dasha_periods)

    # 4) Calculate Nakshatra
    nakshatra = calculate_nakshatra(jd_birth)

    # 5) Build main D1 report
    base_report = make_personalized_report(
        planet_in_houses, house_rulers,
        dasha_periods, current_dasha, current_antardasha,
        planetary_positions, planetary_signs,
        asc_sign_str, asc_deg, nakshatra
    )

    # 6) Compute additional divisional charts
    base_report["D7"] = compute_divisional_chart(
        planetary_positions,
        planetary_signs,
        sub_sign_count=7,
        sign_sequence_func=d7_sign_sequence
    )
    base_report["D9"] = compute_divisional_chart(
        planetary_positions,
        planetary_signs,
        sub_sign_count=9,
        sign_sequence_func=d9_sign_sequence
    )
    base_report["D10"] = compute_divisional_chart(
        planetary_positions,
        planetary_signs,
        sub_sign_count=10,
        sign_sequence_func=d10_sign_sequence
    )
    base_report["D12"] = compute_divisional_chart(
        planetary_positions,
        planetary_signs,
        sub_sign_count=12,
        sign_sequence_func=d12_sign_sequence
    )
    base_report["D60"] = compute_divisional_chart(
        planetary_positions,
        planetary_signs,
        sub_sign_count=60,
        sign_sequence_func=d60_sign_sequence
    )

    # 7) Add extra details
    base_report["name"] = name
    base_report["date_of_birth"] = date_of_birth
    base_report["time_of_birth_input"] = time_of_birth
    base_report["time_of_birth_24hr"] = time_24
    base_report["latitude"] = latitude
    base_report["longitude"] = longitude
    base_report["timezone"] = timezone

    return base_report
