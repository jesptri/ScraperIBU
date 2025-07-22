import requests
from consts import *

def get_key_from_value(dictionary, target_value):
    return next((key for key, value in dictionary.items() if value == target_value), None)

def get_places(RT, season, level): 
    season_start, season_end = season.split("-")
    season_id = season_start[-2:] + season_end[-2:]

    level_mapping = {
        "WORLD CUP": 1,
        "IBU CUP": 2,
        "JUNIOR": 3
    }
    level_code = level_mapping.get(level)

    url = f"https://biathlonresults.com/modules/sportapi/api/Events?RT={RT}&SeasonId={season_id}&Level={level_code}"
    response = requests.get(url)
    events_data = response.json()

    event_name_to_id = {}
    for event in events_data:
        description = event.get("ShortDescription", "Unavailable Description")
        country = event.get("Nat", "Unavailable Country")
        event_id = event.get("EventId", "Unavailable EventId")
        event_name = f"{description} ({country})"
        event_name_to_id[event_name] = event_id

    return event_name_to_id

def get_races(RT, EventId):
    url = f"https://biathlonresults.com/modules/sportapi/api/Competitions?RT={RT}&EventId={EventId}"
    response = requests.get(url)
    races_data = response.json()

    race_id_to_description = {}
    for race in races_data:
        race_id = race.get("RaceId", "Unavailable RaceId")
        description = race.get("ShortDescription", "Unavailable Description")

        if not any(keyword in description.split() for keyword in ["Relay", "Mass"]):
            race_id_to_description[race_id] = description

    return race_id_to_description

def get_startinfo_pursuit(RT, RaceId):
    url = f"https://biathlonresults.com/modules/sportapi/api/Results?RT={RT}&RaceId={RaceId}"
    response = requests.get(url)
    results_data = response.json().get("Results", [])

    bib_to_start_info = {}
    for athlete in results_data:
        bib = athlete.get("Bib", "Unavailable Bib")
        start_info = athlete.get("StartInfo", "Unavailable StartInfo")
        bib_to_start_info[bib] = start_info

    return bib_to_start_info

def get_bib_name_nat_list(RT, RaceId):
    url = f"https://biathlonresults.com/modules/sportapi/api/Results?RT={RT}&RaceId={RaceId}"
    response = requests.get(url)
    data = response.json()

    competition_data = data.get("Competition", {})
    has_analysis = competition_data.get("HasAnalysis", "Unavailable HasAnalysis")
    has_live_data = competition_data.get("HasLiveData", "Unavailable HasLiveData")
    results_data = data.get("Results", [])

    bib_name_nat_list = []

    for athlete in results_data:
        bib = athlete.get("Bib", "Unavailable Bib")
        family_name = athlete.get("FamilyName", "Unavailable FamilyName")
        given_name = athlete.get("GivenName", "Unavailable GivenName")
        country = athlete.get("Nat", "Unavailable Country")

        # Clean family name by removing spaces
        family_name_clean = "".join(family_name.split())

        # Build initials from given name
        try:
            if " " in given_name or "-" in given_name:
                separators = [" ", "-"]
                for separator in separators:
                    if separator in given_name:
                        parts = given_name.split(separator)
                        initials = "".join([part[0] + "." for part in parts])
                        break
            else:
                initials = given_name[0] + "."
        except:
            initials = "."

        short_name = f"{family_name_clean} {initials}"
        bib_name_nat_list.append([bib, short_name, country])

    return bib_name_nat_list, has_analysis, has_live_data

def convert_chrono_to_seconds(chrono):
    if '+' in chrono:
        chrono = chrono.replace('+', '')
    if ':' in chrono:
        parts = chrono.split(':')
        if len(parts) == 2:
            minutes, secondes_fraction = parts
            minutes = int(minutes) if minutes != '' else 0
        elif len(parts) == 3:
            heures, minutes, secondes_fraction = parts
            heures = int(heures) if heures != '' else 0
            minutes = int(minutes) if minutes != '' else 0
        else:
            raise ValueError("Invalid chrono format")
        
        if '.' in secondes_fraction:
            secondes, fraction = secondes_fraction.split('.')
            secondes = int(secondes) if secondes != '' else 0
            fraction = int(fraction.ljust(2, '0'))  # Ensure fraction is at least two digits
            return (heures * 3600 + minutes * 60 + secondes + fraction / 100) if len(parts) == 3 else (minutes * 60 + secondes + fraction / 100)
        else:
            secondes = int(secondes_fraction) if secondes_fraction != '' else 0
            return (heures * 3600 + minutes * 60 + secondes) if len(parts) == 3 else (minutes * 60 + secondes)
    else:
        return float(chrono) 