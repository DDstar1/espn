from datetime import datetime
from utils import extract_espnfitt, my_print


def get_details_and_commentary_of_game(espn_game_id, data_dic):
    """
    Extract game details and commentary from ESPN data dictionary.

    Args:
        espn_game_id: The ESPN game identifier
        data_dic: Dictionary containing game data

    Returns:
        Dictionary containing game details and commentary
    """

    my_print(f"\n{'='*60}")
    my_print(f"Processing game ID: {espn_game_id}")
    my_print(f"{'='*60}\n")

    gm_info = data_dic.get("gmInfo", {})
    my_print("✓ Retrieved game info")

    # -----------------------
    # Extract commentary & timeline events
    # -----------------------
    match_commentary = (
        data_dic
        .get("mtchCmmntry", {})
        .get("allCommentary", [])
    )

    key_events = (
        data_dic
        .get("tmlne", {})
        .get("keyEvents", [])
    )

    league_info = (data_dic.get("stndngs") or [{}])[0]
    league_name = league_info.get("dspNm")
    league_id = league_info.get("lgUid")

    my_print(f"✓ Commentary entries: {len(match_commentary)}")
    my_print(f"✓ Key events entries: {len(key_events)}")

    # -----------------------
    # Base details structure
    # -----------------------
    details = {
        "espn_id": espn_game_id,
        "date": None,
        "referee": None,
        "attendance": None,
        "place": None,
        "state": None,
        "country": None,
        "commentary": {
            "match_commentary": match_commentary,
            "key_events": key_events
        },
        "league_name":league_name,
        "league_id":league_id
    }

    # -----------------------
    # Date / Time
    # -----------------------
    raw_dt = gm_info.get("dtTm")
    if raw_dt:
        try:
            details["date"] = datetime.fromisoformat(
                raw_dt.replace("Z", "+00:00")
            ).isoformat()
            my_print(f"✓ Date parsed: {details['date']}")
        except Exception as e:
            my_print(f"✗ Error parsing date: {e}")

    # -----------------------
    # Attendance
    # -----------------------
    details["attendance"] = gm_info.get("attnd")
    if details["attendance"]:
        my_print(f"✓ Attendance: {details['attendance']:,}")

    # -----------------------
    # Stadium / Location
    # -----------------------
    details["place"] = gm_info.get("loc")
    if details["place"]:
        my_print(f"✓ Stadium: {details['place']}")

    loc_addr = gm_info.get("locAddr", {})
    details["state"] = loc_addr.get("city")
    details["country"] = loc_addr.get("country")

    if details["state"] or details["country"]:
        location = (
            f"{details['state']}, {details['country']}"
            if details["state"] and details["country"]
            else details["state"] or details["country"]
        )
        my_print(f"✓ Location: {location}")

    # -----------------------
    # Referee
    # -----------------------
    refs = gm_info.get("refs", [])
    if refs:
        details["referee"] = refs[0].get("dspNm")
        my_print(f"✓ Referee: {details['referee']}")

    my_print(f"\n{'='*60}")
    my_print("Processing complete!")
    my_print(f"{'='*60}\n")


    return details
