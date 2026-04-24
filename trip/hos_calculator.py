def plan_trip(current_location, pickup_location, dropoff_location, current_cycle_hours, distance_to_pickup, distance_to_dropoff):

    # =============================
    # CONSTANTS
    # =============================
    MAX_DRIVING_PER_DAY = 11
    MAX_WINDOW_PER_DAY = 14
    REQUIRED_REST = 10
    BREAK_AFTER = 8
    BREAK_DURATION = 0.5
    FUEL_EVERY_MILES = 1000
    PICKUP_DROPOFF_TIME = 1
    SPEED = 55

    # =============================
    # STATE
    # =============================
    events = []
    log_days = []

    miles_driven = 0
    day = 1
    clock = 0

    # =============================
    # HELPERS
    # =============================
    def add_event(event_type, duration, location="En route"):
        nonlocal clock, day

        remaining_duration = duration
        while clock + remaining_duration > 24:
            chunk = 24 - clock
            if chunk > 0:
                events.append({
                    "type": event_type,
                    "location": location,
                    "duration_hours": round(chunk, 4),
                    "day": day
                })
            remaining_duration -= chunk
            clock = 0
            day += 1

        if remaining_duration > 0:
            events.append({
                "type": event_type,
                "location": location,
                "duration_hours": round(remaining_duration, 4),
                "day": day
            })
            clock += remaining_duration

    # =============================
    # MAIN LOOP (SAFE + LINEAR)
    # =============================
    remaining_drive_to_pickup = distance_to_pickup / SPEED
    remaining_drive_to_dropoff = distance_to_dropoff / SPEED
    
    pickup_done = False
    dropoff_done = False

    cycle_hours_used = current_cycle_hours

    while remaining_drive_to_pickup > 0 or not pickup_done or remaining_drive_to_dropoff > 0 or not dropoff_done:

        driving_today = 0
        hours_since_break = 0
        shift_window = 0

        # Daily shift loop
        while driving_today < MAX_DRIVING_PER_DAY and shift_window < MAX_WINDOW_PER_DAY and (remaining_drive_to_pickup > 0 or not pickup_done or remaining_drive_to_dropoff > 0 or not dropoff_done):

            # 1. Enforce 70-hour cycle restart
            if cycle_hours_used >= 70:
                add_event("off_duty", 34)  # 34-hour restart counts as Off Duty
                cycle_hours_used = 0
                driving_today = 0
                hours_since_break = 0
                shift_window = 0
                continue

            # enforce break before exceeding 8h of continuous driving
            if hours_since_break >= BREAK_AFTER:
                if 70 - cycle_hours_used < BREAK_DURATION:
                    cycle_hours_used = 70
                    continue
                if MAX_WINDOW_PER_DAY - shift_window < BREAK_DURATION:
                    shift_window = MAX_WINDOW_PER_DAY
                    continue
                add_event("break", BREAK_DURATION)
                cycle_hours_used += BREAK_DURATION
                shift_window += BREAK_DURATION
                hours_since_break = 0
                continue

            if remaining_drive_to_pickup > 0:
                chunk = min(2, MAX_DRIVING_PER_DAY - driving_today, MAX_WINDOW_PER_DAY - shift_window, remaining_drive_to_pickup, BREAK_AFTER - hours_since_break, 70 - cycle_hours_used)
                if chunk <= 0:
                    cycle_hours_used = 70
                    continue

                add_event("driving", chunk)
                driving_today += chunk
                hours_since_break += chunk
                shift_window += chunk
                remaining_drive_to_pickup -= chunk
                cycle_hours_used += chunk

                miles_chunk = chunk * SPEED
                prev_miles = miles_driven
                miles_driven += miles_chunk

                if int(prev_miles // FUEL_EVERY_MILES) < int(miles_driven // FUEL_EVERY_MILES):
                    add_event("fuel", 0.5)
                    cycle_hours_used += 0.5
                    shift_window += 0.5
                    hours_since_break = 0

            elif not pickup_done:
                if 70 - cycle_hours_used < PICKUP_DROPOFF_TIME:
                    cycle_hours_used = 70
                    continue
                if MAX_WINDOW_PER_DAY - shift_window < PICKUP_DROPOFF_TIME:
                    shift_window = MAX_WINDOW_PER_DAY
                    continue
                add_event("pickup", PICKUP_DROPOFF_TIME, location=pickup_location)
                cycle_hours_used += PICKUP_DROPOFF_TIME
                shift_window += PICKUP_DROPOFF_TIME
                pickup_done = True
                hours_since_break = 0 

            elif remaining_drive_to_dropoff > 0:
                chunk = min(2, MAX_DRIVING_PER_DAY - driving_today, MAX_WINDOW_PER_DAY - shift_window, remaining_drive_to_dropoff, BREAK_AFTER - hours_since_break, 70 - cycle_hours_used)
                if chunk <= 0:
                    cycle_hours_used = 70
                    continue

                add_event("driving", chunk)
                driving_today += chunk
                hours_since_break += chunk
                shift_window += chunk
                remaining_drive_to_dropoff -= chunk
                cycle_hours_used += chunk

                miles_chunk = chunk * SPEED
                prev_miles = miles_driven
                miles_driven += miles_chunk

                if int(prev_miles // FUEL_EVERY_MILES) < int(miles_driven // FUEL_EVERY_MILES):
                    add_event("fuel", 0.5)
                    cycle_hours_used += 0.5
                    shift_window += 0.5
                    hours_since_break = 0

            elif not dropoff_done:
                if 70 - cycle_hours_used < PICKUP_DROPOFF_TIME:
                    cycle_hours_used = 70
                    continue
                if MAX_WINDOW_PER_DAY - shift_window < PICKUP_DROPOFF_TIME:
                    shift_window = MAX_WINDOW_PER_DAY
                    continue
                add_event("dropoff", PICKUP_DROPOFF_TIME, location=dropoff_location)
                cycle_hours_used += PICKUP_DROPOFF_TIME
                shift_window += PICKUP_DROPOFF_TIME
                dropoff_done = True
                hours_since_break = 0
                break # Trip is complete!

        # End of day → mandatory rest if trip is not completely done
        if remaining_drive_to_pickup > 0 or not pickup_done or remaining_drive_to_dropoff > 0 or not dropoff_done:
            add_event("sleeper", REQUIRED_REST)

    # =============================
    # BUILD LOGS (SAFE 24H)
    # =============================
    total_days = day

    for d in range(1, total_days + 1):
        day_events = [e for e in events if e["day"] == d]

        driving = sum(e["duration_hours"] for e in day_events if e["type"] == "driving")
        sleeper = sum(e["duration_hours"] for e in day_events if e["type"] == "sleeper")
        on_duty = sum(
            e["duration_hours"]
            for e in day_events
            if e["type"] in ["pickup", "dropoff", "fuel", "break"]
        )
        # off_duty includes both explicit off_duty events (34-hr restart) and leftover hours
        explicit_off_duty = sum(e["duration_hours"] for e in day_events if e["type"] == "off_duty")

        total = driving + sleeper + on_duty + explicit_off_duty

        if total > 24:
            # Cap sleeper first, preserve explicit off_duty
            sleeper = max(0, 24 - driving - on_duty - explicit_off_duty)

        off_duty = explicit_off_duty + max(0, 24 - driving - sleeper - on_duty - explicit_off_duty)

        log_days.append({
            "day": d,
            "driving_hours": round(driving, 2),
            "on_duty_not_driving_hours": round(on_duty, 2),
            "sleeper_berth_hours": round(sleeper, 2),
            "off_duty_hours": round(off_duty, 2),
            "events": day_events
        })

    total_driving_hours = sum(d["driving_hours"] for d in log_days)
    total_on_duty_hours = sum(d["on_duty_not_driving_hours"] for d in log_days)

    return {
        "total_days": total_days,
        "total_miles": round(distance_to_pickup + distance_to_dropoff),
        "deadhead_miles": round(distance_to_pickup),
        "loaded_miles": round(distance_to_dropoff),
        "total_driving_hours": round(total_driving_hours, 1),
        "total_duty_hours": round(total_driving_hours + total_on_duty_hours, 1),
        "events": events,
        "log_days": log_days
    }