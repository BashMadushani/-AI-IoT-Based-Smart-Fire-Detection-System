import sqlite3
import requests

from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Smart Fire Detection System",
    version="1.0"
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = "fire_detection.db"


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

# IMPORTANT:
# Put your NEW Telegram BotFather token here.
# DO NOT share your token with anyone.

TELEGRAM_BOT_TOKEN = "8872147562:AAE6kKR-JwXrVoCT6TA37ZLzKWFZ2IbRvSE"

TELEGRAM_CHAT_ID = "8595434574"


# Prevent repeated alerts for exactly the same condition
last_alert_key = None


# ============================================================
# DATABASE CREATION
# ============================================================

def create_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT,

            temperature REAL,

            humidity REAL,

            gas INTEGER,

            flame INTEGER,

            ir INTEGER,

            risk_score INTEGER,

            risk_level TEXT,

            emergency_action TEXT

        )
    """)

    connection.commit()
    connection.close()


create_database()


# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_risk(
    temperature,
    humidity,
    gas,
    flame,
    ir
):

    score = 0

    reasons = []

    # --------------------------------------------------------
    # TEMPERATURE CONDITION
    # --------------------------------------------------------

    if temperature >= 40:

        score += 30

        reasons.append(
            f"High Temperature ({temperature:.1f} C)"
        )


    # --------------------------------------------------------
    # MQ-2 GAS CONDITION
    # --------------------------------------------------------

    if gas >= 600:

        score += 30

        reasons.append(
            f"High Gas Level (MQ-2: {gas})"
        )


    # --------------------------------------------------------
    # FLAME CONDITION
    #
    # IMPORTANT:
    # Backend expects:
    #
    # flame = 1  -> Flame DETECTED
    # flame = 0  -> Flame CLEAR
    #
    # ESP32 must convert its Active-LOW raw value
    # before sending JSON.
    # --------------------------------------------------------

    if flame == 1:

        score += 40

        reasons.append(
            "Flame Detected"
        )


    # --------------------------------------------------------
    # COUNT MAIN FIRE CONDITIONS
    # --------------------------------------------------------

    major_conditions = 0

    if temperature >= 40:
        major_conditions += 1

    if gas >= 600:
        major_conditions += 1

    if flame == 1:
        major_conditions += 1


    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    if major_conditions == 3:

        risk_level = "HIGH"

        action = (
            "IMMEDIATE EMERGENCY RESPONSE REQUIRED"
        )


    elif major_conditions >= 1:

        risk_level = "MEDIUM"

        action = (
            "INSPECT AREA AND MONITOR SENSORS"
        )


    else:

        risk_level = "LOW"

        action = (
            "CONTINUE MONITORING"
        )


    # Maximum score = 100
    score = min(score, 100)


    return (
        score,
        risk_level,
        action,
        reasons
    )


# ============================================================
# SEND TELEGRAM ALERT
# ============================================================

def send_telegram_alert(
    temperature,
    humidity,
    gas,
    flame,
    ir,
    risk_score,
    risk_level,
    reasons
):

    # --------------------------------------------------------
    # CHECK TELEGRAM CONFIGURATION
    # --------------------------------------------------------

    if (
        not TELEGRAM_BOT_TOKEN
        or not TELEGRAM_CHAT_ID
    ):

        print(
            "Telegram credentials are not configured."
        )

        return False


    # --------------------------------------------------------
    # SENSOR STATUS
    # --------------------------------------------------------

    flame_status = (
        "DETECTED"
        if flame == 1
        else "CLEAR"
    )

    ir_status = (
        "DETECTED"
        if ir == 1
        else "CLEAR"
    )


    # --------------------------------------------------------
    # TRIGGER REASONS
    # --------------------------------------------------------

    if reasons:

        reason_text = "\n".join(
            f"• {reason}"
            for reason in reasons
        )

    else:

        reason_text = (
            "No abnormal fire condition detected."
        )


    # --------------------------------------------------------
    # TELEGRAM MESSAGE
    # --------------------------------------------------------

    message = f"""
🚨 SMART FIRE DETECTION ALERT 🚨

Risk Level: {risk_level}
Risk Score: {risk_score}/100

🔥 TRIGGERED CONDITIONS:
{reason_text}

📊 SENSOR VALUES

🌡 Temperature: {temperature:.1f} °C
💧 Humidity: {humidity:.1f} %
💨 MQ-2 Gas: {gas}

🔥 Flame: {flame_status}
📡 IR: {ir_status}

📍 Location:
KFC Garment Factory
Malabe

⚠️ Please inspect the area immediately.
"""


    # --------------------------------------------------------
    # TELEGRAM API
    # --------------------------------------------------------

    url = (
        "https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}"
        "/sendMessage"
    )


    try:

        response = requests.post(

            url,

            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },

            timeout=10
        )


        if response.ok:

            print(
                f"Telegram {risk_level} alert sent."
            )

            return True


        print(
            "Telegram error:",
            response.text
        )

        return False


    except Exception as error:

        print(
            "Telegram connection error:",
            error
        )

        return False


# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
def dashboard():

    try:

        with open(
            "dashboard.html",
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()


    except FileNotFoundError:

        return HTMLResponse(

            content=(
                "<h1>dashboard.html not found</h1>"
                "<p>"
                "Make sure dashboard.html is in the same "
                "folder as main.py."
                "</p>"
            ),

            status_code=404
        )


# ============================================================
# EVENT HISTORY PAGE
# ============================================================

@app.get(
    "/event-history",
    response_class=HTMLResponse
)
def event_history_page():

    try:

        with open(
            "event_history.html",
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()


    except FileNotFoundError:

        return HTMLResponse(

            content=(
                "<h1>event_history.html not found</h1>"
            ),

            status_code=404
        )


# ============================================================
# EMERGENCY CONTACT PAGE
# ============================================================

@app.get(
    "/emergency-contact",
    response_class=HTMLResponse
)
def emergency_contact_page():

    try:

        with open(
            "emergency_contact.html",
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()


    except FileNotFoundError:

        return HTMLResponse(

            content=(
                "<h1>emergency_contact.html not found</h1>"
            ),

            status_code=404
        )


# ============================================================
# EMERGENCY CONTACT DATA
# ============================================================

@app.get("/emergency-contact-data")
def emergency_contact_data():

    return {

        "status": "success",

        "contact": {

            "primary_contact": "Officer",

            "primary_phone": "Not Configured",

            "secondary_contact": "Not Configured",

            "secondary_phone": "Not Configured",

            "building": "KFC Garment Factory",

            "location": "Malabe",

            "gps_status": "GPS MODULE POSTPONED"

        }

    }


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "status": "online",

        "system":
            "Smart Fire Detection and "
            "Emergency Response System",

        "message":
            "Backend is working"

    }


# ============================================================
# TEST
# ============================================================

@app.get("/test")
def test():

    return {

        "status": "success",

        "message":
            "Backend test successful"

    }


# ============================================================
# RECEIVE ESP32 SENSOR DATA
# ============================================================

@app.post("/sensor-data")
def receive_sensor_data(data: dict):

    global last_alert_key


    # --------------------------------------------------------
    # READ SENSOR DATA
    # --------------------------------------------------------

    temperature = float(
        data.get(
            "temperature",
            0
        )
    )


    humidity = float(
        data.get(
            "humidity",
            0
        )
    )


    gas = int(
        data.get(
            "gas",
            0
        )
    )


    flame = int(
        data.get(
            "flame",
            0
        )
    )


    ir = int(
        data.get(
            "ir",
            0
        )
    )


    # --------------------------------------------------------
    # CALCULATE RISK
    # --------------------------------------------------------

    (
        risk_score,
        risk_level,
        action,
        reasons
    ) = calculate_risk(

        temperature,

        humidity,

        gas,

        flame,

        ir

    )


    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # --------------------------------------------------------
    # SAVE TO DATABASE
    # --------------------------------------------------------

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO sensor_events (

            timestamp,
            temperature,
            humidity,
            gas,
            flame,
            ir,
            risk_score,
            risk_level,
            emergency_action

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        timestamp,

        temperature,

        humidity,

        gas,

        flame,

        ir,

        risk_score,

        risk_level,

        action

    ))


    connection.commit()
    connection.close()


    # ========================================================
    # TELEGRAM ALERT
    # ========================================================

    if reasons:

        # Create unique key based on active conditions
        alert_key = "|".join(reasons)


        # Send only when condition changes
        if alert_key != last_alert_key:

            send_telegram_alert(

                temperature,

                humidity,

                gas,

                flame,

                ir,

                risk_score,

                risk_level,

                reasons

            )

            last_alert_key = alert_key


    else:

        # System returned to normal
        last_alert_key = None


    # --------------------------------------------------------
    # PRINT DATA TO CMD
    # --------------------------------------------------------

    print()
    print("========================================")
    print("       RECEIVED SENSOR DATA")
    print("========================================")
    print(f"Temperature : {temperature:.2f} C")
    print(f"Humidity    : {humidity:.2f} %")
    print(f"MQ-2 Gas    : {gas}")
    print(
        f"Flame       : "
        f"{'DETECTED' if flame == 1 else 'CLEAR'}"
    )
    print(
        f"IR          : "
        f"{'DETECTED' if ir == 1 else 'CLEAR'}"
    )
    print(f"Risk Score  : {risk_score}/100")
    print(f"Risk Level  : {risk_level}")
    print(f"Action      : {action}")
    print(
        f"Conditions  : "
        f"{', '.join(reasons) if reasons else 'NONE'}"
    )
    print("========================================")
    print()


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "status": "success",

        "message":
            "Sensor data saved successfully",

        "data": {

            "timestamp":
                timestamp,

            "temperature":
                temperature,

            "humidity":
                humidity,

            "gas":
                gas,

            "flame":
                flame,

            "ir":
                ir,

            "risk_score":
                risk_score,

            "risk_level":
                risk_level,

            "emergency_action":
                action,

            "triggered_conditions":
                reasons

        }

    }


# ============================================================
# LATEST SENSOR DATA
# ============================================================

@app.get("/latest")
def latest_sensor_data():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            timestamp,
            temperature,
            humidity,
            gas,
            flame,
            ir,
            risk_score,
            risk_level,
            emergency_action

        FROM sensor_events

        ORDER BY id DESC

        LIMIT 1
    """)


    row = cursor.fetchone()

    connection.close()


    if row is None:

        return {

            "status":
                "no_data",

            "message":
                "No sensor data available"

        }


    return {

        "status":
            "success",

        "data": {

            "timestamp":
                row[0],

            "temperature":
                row[1],

            "humidity":
                row[2],

            "gas":
                row[3],

            "flame":
                row[4],

            "ir":
                row[5],

            "risk_score":
                row[6],

            "risk_level":
                row[7],

            "emergency_action":
                row[8]

        }

    }


# ============================================================
# EVENT HISTORY
# ============================================================

@app.get("/events")
def event_history():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            timestamp,
            temperature,
            humidity,
            gas,
            flame,
            ir,
            risk_score,
            risk_level,
            emergency_action

        FROM sensor_events

        ORDER BY id DESC

        LIMIT 50
    """)


    rows = cursor.fetchall()

    connection.close()


    events = []


    for row in rows:

        events.append({

            "timestamp":
                row[0],

            "temperature":
                row[1],

            "humidity":
                row[2],

            "gas":
                row[3],

            "flame":
                row[4],

            "ir":
                row[5],

            "risk_score":
                row[6],

            "risk_level":
                row[7],

            "emergency_action":
                row[8]

        })


    return {

        "status":
            "success",

        "events":
            events

    }


# ============================================================
# REGISTERED EMERGENCY LOCATION
# ============================================================

@app.get("/location")
def emergency_location():

    return {

        "status": "success",

        "location": {

            "building":
                "KFC Garment Factory",

            "location":
                "Malabe",

            "responsible_person":
                "Officer",

            "maps_url":
                "https://maps.app.goo.gl/S6Aw7hNWRy9yRJ3a7"

        }

    }


# ============================================================
# ESP32 CONNECTION STATUS
# ============================================================

@app.get("/esp32-status")
def esp32_status():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute("""
        SELECT timestamp
        FROM sensor_events
        ORDER BY id DESC
        LIMIT 1
    """)


    row = cursor.fetchone()

    connection.close()


    # --------------------------------------------------------
    # NO SENSOR DATA
    # --------------------------------------------------------

    if row is None:

        return {

            "status":
                "offline",

            "message":
                "No ESP32 sensor data available",

            "last_update":
                None

        }


    last_update_string = row[0]


    # --------------------------------------------------------
    # CONVERT TIMESTAMP
    # --------------------------------------------------------

    try:

        last_update = datetime.strptime(

            last_update_string,

            "%Y-%m-%d %H:%M:%S"

        )


        seconds_since_update = (

            datetime.now()
            - last_update

        ).total_seconds()


    except Exception:

        return {

            "status":
                "offline",

            "message":
                "Unable to determine ESP32 status",

            "last_update":
                last_update_string

        }


    # --------------------------------------------------------
    # ONLINE
    # --------------------------------------------------------

    if seconds_since_update <= 10:

        return {

            "status":
                "online",

            "message":
                "ESP32 is connected",

            "last_update":
                last_update_string,

            "seconds_since_update":
                round(
                    seconds_since_update,
                    1
                )

        }


    # --------------------------------------------------------
    # OFFLINE
    # --------------------------------------------------------

    return {

        "status":
            "offline",

        "message":
            "ESP32 connection lost",

        "last_update":
            last_update_string,

        "seconds_since_update":
            round(
                seconds_since_update,
                1
            )

    }


# ============================================================
# TELEGRAM TEST
# ============================================================

@app.get("/telegram-test")
def telegram_test():

    if (
        not TELEGRAM_BOT_TOKEN
        or not TELEGRAM_CHAT_ID
    ):

        return {

            "status": "error",

            "message":
                "Telegram Bot Token or Chat ID is missing"

        }


    test_message = """
✅ SMART FIRE DETECTION SYSTEM

Telegram connection test successful.

Backend is connected to Telegram.

📍 Location:
KFC Garment Factory
Malabe
"""


    url = (
        "https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}"
        "/sendMessage"
    )


    try:

        response = requests.post(

            url,

            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": test_message
            },

            timeout=10

        )


        result = response.json()


        if response.ok and result.get("ok"):

            return {

                "status": "success",

                "message":
                    "Telegram test message sent successfully"

            }


        return {

            "status": "error",

            "message":
                "Telegram API returned an error",

            "telegram_response":
                result

        }


    except Exception as error:

        return {

            "status": "error",

            "message":
                "Telegram connection failed",

            "error":
                str(error)

        }

@app.get("/emergency-contact-data")
def emergency_contact_data():
    return {
        "status": "success",

        "contact": {

            # Main responsible person
            "primary_contact": "Safety Officer",
            "primary_phone": "071 234 5678",

            # Secondary responsible person
            "secondary_contact": "Factory Manager",
            "secondary_phone": "077 234 5678",

            # Registered location
            "building": "KFC Garment Factory",
            "location": "Malabe",
            "gps_status": "GPS MODULE POSTPONED",

            # Emergency Services
            "police": {
                "name": "Sri Lanka Police",
                "phone": "119"
            },

            "fire": {
                "name": "Fire & Rescue Service",
                "phone": "110"
            },

            "ambulance": {
                "name": "Suwaseriya Ambulance",
                "phone": "1990"
            },

            "hospital": {
                "name": "Nearest Hospital",
                "phone": "Not Configured"
            }
        }
    }