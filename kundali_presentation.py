# kundali_presentation.py
from datetime import datetime

def display_ascendant_and_planetary_positions(report):
    """
    Retrieves the Ascendant sign and planetary positions from the final Kundali report.

    The new `calculate_kundali` code should set:
      report["asc_sign_name"] = asc_sign_name
      report["ascendant"] = asc_deg
    and each planet key as a dict: { house, house_ruler, strength, benefic, position, planetary_sign }.
    """
    asc_sign = report.get("asc_sign_name", "Unknown")
    ascendant = report.get("ascendant", 0.0)

    # We'll store planet -> { Position, Sign }
    planetary_info = {}
    # These keys are not planet data
    skip_keys = {
        "Mahadasha","Antardasha","kundali_summary","planetary_positions",
        "planet_in_houses","house_rulers","dasha_periods",
        "current_dasha","current_antardasha","asc_sign_name","ascendant",
        "D7","D9","D10","D12","D60",  # Divisional charts
        "name","date_of_birth","time_of_birth_input","time_of_birth_24hr",
        "latitude","longitude","timezone"
    }

    # Identify planet keys in the report
    for key, details in report.items():
        if key in skip_keys or not isinstance(details, dict):
            continue
        # details includes e.g. { house, house_ruler, strength, benefic, position, planetary_sign }
        planetary_info[key] = {
            "Position": f"{details.get('position', 0.0):.2f}°",
            "Sign": details.get('planetary_sign', "Unknown")
        }

    ascendant_info = {
        "Ascendant Sign": f"{asc_sign} ({ascendant:.2f}°)"
    }

    return {
        "ascendant_info": ascendant_info,
        "planetary_info": planetary_info
    }

def display_house_rulers(report):
    """
    Retrieves the ruling planets for each house from the Kundali report.
    """
    house_rulers = report.get("house_rulers", {})
    house_rulers_info = {}
    for house, ruler in house_rulers.items():
        house_rulers_info[f"House {house}"] = ruler
    return house_rulers_info

def display_planets_in_houses(report):
    """
    Shows which planets occupy which houses, plus strength, nature, sign, etc.
    Expects report["planet_in_houses"] and each planet's dict in the main report.
    """
    planet_in_houses = report.get("planet_in_houses", {})
    planets_info = {}

    for planet, house_num in planet_in_houses.items():
        details = report.get(planet, {})
        house_ruler = details.get("house_ruler","Unknown")
        strength = details.get("strength","Unknown")
        benefic_bool = details.get("benefic", False)
        nature = "Benefic" if benefic_bool else "Malefic"
        sign = details.get("planetary_sign","Unknown")
        planets_info[planet] = {
            "House": house_num,
            "House Ruler": house_ruler,
            "Strength": strength,
            "Nature": nature,
            "Sign": sign
        }
    return planets_info

def display_dasha_periods(report):
    """
    Returns a list of all Mahadasha periods from report["dasha_periods"].
    Each period looks like {planet, start_date, end_date} (datetime).
    """
    dasha_periods = report.get("dasha_periods", [])
    result = []
    for d in dasha_periods:
        planet = d.get("planet","Unknown")
        start = d.get("start_date","")
        end = d.get("end_date","")
        if isinstance(start, datetime):
            start = start.strftime("%Y-%m-%d")
        if isinstance(end, datetime):
            end = end.strftime("%Y-%m-%d")
        result.append({
            "Planet": planet,
            "Start Date": start,
            "End Date": end
        })
    return result

def display_current_dasha(report):
    """
    Shows the currently active Mahadasha from report["current_dasha"].
    """
    d = report.get("current_dasha", None)
    if not d:
        return "No current Mahadasha found."
    planet = d.get("planet","Unknown")
    start = d.get("start_date","")
    end = d.get("end_date","")
    if isinstance(start, datetime):
        start = start.strftime("%Y-%m-%d")
    if isinstance(end, datetime):
        end = end.strftime("%Y-%m-%d")
    return {
        "Planet": planet,
        "Start Date": start,
        "End Date": end
    }

def display_current_antardasha(report):
    """
    Shows the currently active Antardasha from report["current_antardasha"].
    """
    ad = report.get("current_antardasha", None)
    if not ad:
        return "No current Antardasha found."
    planet = ad.get("planet","Unknown")
    start = ad.get("start_date","")
    end = ad.get("end_date","")
    if isinstance(start, datetime):
        start = start.strftime("%Y-%m-%d")
    if isinstance(end, datetime):
        end = end.strftime("%Y-%m-%d")
    return {
        "Planet": planet,
        "Start Date": start,
        "End Date": end
    }

def display_overall_summary(report):
    """
    Returns the final textual summary from 'kundali_summary'.
    """
    return report.get("kundali_summary", "No summary available.")

###############################
# OPTIONAL: Display Divisional Charts (D7, D9, D10, D12, D60)
###############################
def display_divisional_charts(report):
    """
    If your final 'report' includes keys like 'D7','D9','D10','D12','D60',
    this function returns them in a user-friendly dictionary.
    """
    charts = {}
    for chart_key in ["D7","D9","D10","D12","D60"]:
        if chart_key in report:
            chart_data = report[chart_key]  # e.g. { 'Sun': { 'degree':..., 'sign':... }, ... }
            chart_dict = {}
            for planet, details in chart_data.items():
                deg = details.get("degree",0.0)
                sign = details.get("sign","Unknown")
                chart_dict[planet] = f"{deg:.2f}° in {sign}"
            charts[chart_key] = chart_dict
    return charts
