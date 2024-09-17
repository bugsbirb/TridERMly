from datetime import datetime, timedelta

def strtotime(duration: int):
            now = datetime.now()
            DurationValue = int(duration[:-1])
            DurationUnit = duration[-1]
            DurationSeconds = DurationValue
            if DurationUnit == "s":
                DurationSeconds *= 1
            elif DurationUnit == "m":
                DurationSeconds *= 60
            elif DurationUnit == "h":
                DurationSeconds *= 3600
            elif DurationUnit == "d":
                DurationSeconds *= 86400
            elif DurationUnit == "w":
                DurationSeconds *= 604800    

            return now + timedelta(seconds = DurationSeconds)
            
            