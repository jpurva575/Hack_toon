import os
import time
import datetime
import pandas as pd
from pathlib import Path
from src.config import LOCATIONS, LIVE_LOG_PATH
from src.live import get_live_data_and_level


def log_all_locations():
    """
    Polls live traffic and weather across all configured locations and appends to data/live_log.csv.
    """
    records = []
    timestamp = datetime.datetime.now().isoformat()
    
    print(f"[{timestamp}] Polling live data for configured locations...")
    for loc_name in LOCATIONS.keys():
        try:
            res = get_live_data_and_level(loc_name)
            record = {
                "timestamp": timestamp,
                "location": loc_name,
                "lat": res["lat"],
                "lon": res["lon"],
                "current_speed": res["current_speed"],
                "free_flow_speed": res["free_flow_speed"],
                "speed_ratio": res["speed_ratio"],
                "live_level": res["live_level"],
                "live_index": res["live_index"],
                "traffic_is_live": res["traffic_is_live"],
                "temp_c": res["weather"].get("temperature_2m", None),
                "rain_mm": res["weather"].get("precipitation", None),
                "cloud_cover": res["weather"].get("cloud_cover", None)
            }
            records.append(record)
            print(f"  -> {loc_name}: Level={res['live_level']}, SpeedRatio={res['speed_ratio']:.2f}")
        except Exception as e:
            print(f"  Error polling {loc_name}: {e}")
            
    if records:
        df_new = pd.DataFrame(records)
        if LIVE_LOG_PATH.exists():
            df_new.to_csv(LIVE_LOG_PATH, mode="a", header=False, index=False)
        else:
            LIVE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            df_new.to_csv(LIVE_LOG_PATH, mode="w", header=True, index=False)
        print(f"Successfully logged {len(records)} records to {LIVE_LOG_PATH}")


if __name__ == "__main__":
    log_all_locations()
