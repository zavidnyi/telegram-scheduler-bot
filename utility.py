def generate_event_text(event: dict):
    event_output = "<b>Name</b>: " + event["event_name"] + "\n"
    event_output += "<b>Time</b>: " + event["event_time"] + "\n"
    event_output += "<b>Day</b>: " + event["event_wday"] + "\n"
    event_output += "<b>Location</b>: " + event["event_location"] + "\n"
    event_output += "<b>Additional Information</b>: " + event["event_extra"] + "\n"
    return event_output
