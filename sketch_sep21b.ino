#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
-#include <DHT.h>


// ============================================================
// Wi-Fi Settings
// ============================================================

const char* ssid = "iPhone";
const char* password = "mysbashi26";

// Laptop IP address
const char* serverUrl =
    "http://172.20.10.2:8000/sensor-data";


// ============================================================
// Optional Test Mode
// ============================================================

// false = normal project mode
// true  = Flame + IR detected will force minimum HIGH (60)
// Turn this OFF for the final project/demo.

const bool ENABLE_HIGH_TEST =false;


// ============================================================
// Sensor Pins
// ============================================================

#define DHT_PIN 4
#define DHT_TYPE DHT11

#define MQ2_PIN 34
#define FLAME_PIN 27
#define IR_PIN 25

#define BUZZER_PIN 26


// ============================================================
// LCD
// ============================================================

#define LCD_ADDRESS 0x27
#define LCD_COLUMNS 16
#define LCD_ROWS 2


// ============================================================
// Objects
// ============================================================

DHT dht(
    DHT_PIN,
    DHT_TYPE
);

LiquidCrystal_I2C lcd(
    LCD_ADDRESS,
    LCD_COLUMNS,
    LCD_ROWS
);


// ============================================================
// Risk Calculation
// Must match FastAPI backend
// ============================================================

int calculateRisk(
    float temperature,
    int gas,
    int flameDetected,
    int irDetected
) {

    int score = 0;


    // --------------------------------------------------------
    // Temperature
    // --------------------------------------------------------

    if (temperature >= 50) {

        score += 30;

    }

    else if (temperature >= 40) {

        score += 20;

    }

    else if (temperature >= 35) {

        score += 10;

    }


    // --------------------------------------------------------
    // Gas
    // --------------------------------------------------------

    if (gas >= 2500) {

        score += 30;

    }

    else if (gas >= 1500) {

        score += 20;

    }

    else if (gas >= 800) {

        score += 10;

    }


    // --------------------------------------------------------
    // Flame
    // --------------------------------------------------------

    if (flameDetected == 1) {

        score += 40;

    }


    // --------------------------------------------------------
    // IR
    // --------------------------------------------------------

    if (irDetected == 1) {

        score += 10;

    }


    // --------------------------------------------------------
    // Maximum = 100
    // --------------------------------------------------------

    if (score > 100) {

        score = 100;

    }


    return score;
}


// ============================================================
// Risk Level
// ============================================================

String getRiskLevel(
    int score
) {

    if (score >= 80) {

        return "CRITICAL";

    }

    else if (score >= 60) {

        return "HIGH";

    }

    else if (score >= 30) {

        return "MEDIUM";

    }

    else {

        return "LOW";

    }
}


// ============================================================
// Buzzer Control
// ============================================================

void controlBuzzer(
    String riskLevel
) {

    if (
        riskLevel == "HIGH" ||
        riskLevel == "CRITICAL"
    ) {

        digitalWrite(
            BUZZER_PIN,
            HIGH
        );

    }

    else {

        digitalWrite(
            BUZZER_PIN,
            LOW
        );

    }
}


// ============================================================
// LCD Display
// ============================================================

void displayRisk(
    float temperature,
    int gasValue,
    int riskScore,
    String riskLevel
) {

    lcd.clear();


    // --------------------------------------------------------
    // Line 1
    // Example: T:31.1 G:160
    // --------------------------------------------------------

    lcd.setCursor(
        0,
        0
    );

    lcd.print("T:");

    lcd.print(
        temperature,
        1
    );

    lcd.print(" G:");

    lcd.print(
        gasValue
    );


    // --------------------------------------------------------
    // Line 2
    // Example: R:MEDIUM 40
    // --------------------------------------------------------

    lcd.setCursor(
        0,
        1
    );

    lcd.print("R:");

    lcd.print(
        riskLevel
    );

    lcd.print(" ");

    lcd.print(
        riskScore
    );
}


// ============================================================
// Wi-Fi Connection
// ============================================================

bool connectWiFi() {

    if (WiFi.status() == WL_CONNECTED) {

        return true;

    }


    Serial.println();
    Serial.println("Connecting to WiFi...");


    lcd.clear();

    lcd.setCursor(
        0,
        0
    );

    lcd.print(
        "Connecting WiFi"
    );


    WiFi.begin(
        ssid,
        password
    );


    int attempts = 0;


    while (
        WiFi.status() != WL_CONNECTED &&
        attempts < 30
    ) {

        delay(500);

        Serial.print(".");

        attempts++;

    }


    Serial.println();


    if (
        WiFi.status() == WL_CONNECTED
    ) {

        Serial.println(
            "WiFi Connected!"
        );


        Serial.print(
            "ESP32 IP: "
        );

        Serial.println(
            WiFi.localIP()
        );


        lcd.clear();

        lcd.setCursor(
            0,
            0
        );

        lcd.print(
            "WiFi Connected"
        );


        lcd.setCursor(
            0,
            1
        );

        lcd.print(
            WiFi.localIP()
        );


        delay(2000);


        return true;

    }


    Serial.println(
        "WiFi connection failed!"
    );


    lcd.clear();

    lcd.setCursor(
        0,
        0
    );

    lcd.print(
        "WiFi FAILED"
    );


    return false;
}


// ============================================================
// Setup
// ============================================================

void setup() {

    // --------------------------------------------------------
    // Serial
    // --------------------------------------------------------

    Serial.begin(
        115200
    );


    delay(1000);


    // --------------------------------------------------------
    // DHT11
    // --------------------------------------------------------

    dht.begin();


    // --------------------------------------------------------
    // Flame Sensor
    // --------------------------------------------------------

    pinMode(
        FLAME_PIN,
        INPUT
    );


    // --------------------------------------------------------
    // IR Sensor
    // --------------------------------------------------------

    pinMode(
        IR_PIN,
        INPUT
    );


    // --------------------------------------------------------
    // Buzzer
    // --------------------------------------------------------

    pinMode(
        BUZZER_PIN,
        OUTPUT
    );


    digitalWrite(
        BUZZER_PIN,
        LOW
    );


    // --------------------------------------------------------
    // I2C
    // SDA = GPIO 21
    // SCL = GPIO 22
    // --------------------------------------------------------

    Wire.begin(
        21,
        22
    );


    // --------------------------------------------------------
    // LCD
    // --------------------------------------------------------

    lcd.init();

    lcd.backlight();

    lcd.clear();


    lcd.setCursor(
        0,
        0
    );

    lcd.print(
        "Fire Detection"
    );


    lcd.setCursor(
        0,
        1
    );

    lcd.print(
        "Starting..."
    );


    delay(2000);


    // --------------------------------------------------------
    // Wi-Fi
    // --------------------------------------------------------

    connectWiFi();
}


// ============================================================
// Main Loop
// ============================================================

void loop() {


    // ========================================================
    // Make sure Wi-Fi is connected
    // ========================================================

    if (
        WiFi.status() != WL_CONNECTED
    ) {

        connectWiFi();

    }


    // ========================================================
    // Read DHT11
    // ========================================================

    float temperature =
        dht.readTemperature();


    float humidity =
        dht.readHumidity();


    // --------------------------------------------------------
    // DHT11 error
    // --------------------------------------------------------

    if (
        isnan(temperature) ||
        isnan(humidity)
    ) {

        Serial.println();
        Serial.println(
            "DHT11 reading failed!"
        );


        lcd.clear();

        lcd.setCursor(
            0,
            0
        );

        lcd.print(
            "DHT11 ERROR"
        );


        digitalWrite(
            BUZZER_PIN,
            LOW
        );


        delay(2000);

        return;
    }


    // ========================================================
    // MQ-2
    // ========================================================

    int gasValue =
        analogRead(
            MQ2_PIN
        );


    // ========================================================
    // Flame Sensor
    // ========================================================

    int flameValue =
        digitalRead(
            FLAME_PIN
        );


    // Current hardware logic:
    // HIGH = flame detected
    // LOW  = no flame

    int flameDetected =
        (
            flameValue == HIGH
        )
        ? 1
        : 0;


    // ========================================================
    // IR Sensor
    // ========================================================

    int irValue =
        digitalRead(
            IR_PIN
        );


    // Current hardware logic:
    // LOW  = object detected
    // HIGH = clear

    int irDetected =
        (
            irValue == LOW
        )
        ? 1
        : 0;


    // ========================================================
    // Calculate Risk
    // ========================================================

    int riskScore =
        calculateRisk(

            temperature,

            gasValue,

            flameDetected,

            irDetected

        );


    // ========================================================
    // OPTIONAL HIGH TEST
    // ========================================================

    if (
        ENABLE_HIGH_TEST == true &&
        flameDetected == 1 &&
        irDetected == 1
    ) {

        if (riskScore < 60) {

            riskScore = 60;

        }

    }


    // ========================================================
    // Risk Level
    // ========================================================

    String riskLevel =
        getRiskLevel(
            riskScore
        );


    // ========================================================
    // Buzzer
    // ========================================================

    controlBuzzer(
        riskLevel
    );


    // ========================================================
    // LCD
    // ========================================================

    displayRisk(

        temperature,

        gasValue,

        riskScore,

        riskLevel

    );


    // ========================================================
    // Serial Monitor
    // ========================================================

    Serial.println();
    Serial.println(
        "================================"
    );


    Serial.print(
        "Temperature: "
    );

    Serial.print(
        temperature,
        2
    );

    Serial.println(
        " C"
    );


    Serial.print(
        "Humidity: "
    );

    Serial.print(
        humidity,
        2
    );

    Serial.println(
        " %"
    );


    Serial.print(
        "Gas: "
    );

    Serial.println(
        gasValue
    );


    Serial.print(
        "Flame Raw: "
    );

    Serial.println(
        flameValue
    );


    Serial.print(
        "Flame: "
    );


    if (
        flameDetected == 1
    ) {

        Serial.println(
            "DETECTED"
        );

    }

    else {

        Serial.println(
            "NOT DETECTED"
        );

    }


    Serial.print(
        "IR Raw: "
    );

    Serial.println(
        irValue
    );


    Serial.print(
        "IR: "
    );


    if (
        irDetected == 1
    ) {

        Serial.println(
            "DETECTED"
        );

    }

    else {

        Serial.println(
            "CLEAR"
        );

    }


    Serial.print(
        "Risk Score: "
    );

    Serial.println(
        riskScore
    );


    Serial.print(
        "Risk Level: "
    );

    Serial.println(
        riskLevel
    );


    Serial.print(
        "Buzzer: "
    );


    if (
        riskLevel == "HIGH" ||
        riskLevel == "CRITICAL"
    ) {

        Serial.println(
            "ON"
        );

    }

    else {

        Serial.println(
            "OFF"
        );

    }


    Serial.println(
        "================================"
    );


    // ========================================================
    // Send Data to FastAPI
    // ========================================================

    if (
        WiFi.status() == WL_CONNECTED
    ) {

        HTTPClient http;


        http.begin(
            serverUrl
        );


        http.addHeader(
            "Content-Type",
            "application/json"
        );


        http.setTimeout(
            5000
        );


        // ----------------------------------------------------
        // Create JSON
        // ----------------------------------------------------

        String jsonData = "{";


        jsonData +=
            "\"temperature\":";

        jsonData +=
            String(
                temperature,
                2
            );


        jsonData +=
            ",\"humidity\":";

        jsonData +=
            String(
                humidity,
                2
            );


        jsonData +=
            ",\"gas\":";

        jsonData +=
            String(
                gasValue
            );


        // 1 = flame detected
        // 0 = no flame

        jsonData +=
            ",\"flame\":";

        jsonData +=
            String(
                flameDetected
            );


        // 1 = object detected
        // 0 = clear

        jsonData +=
            ",\"ir\":";

        jsonData +=
            String(
                irDetected
            );


        // Additional IR information

        jsonData +=
            ",\"object_detected\":";

        jsonData +=
            (
                irDetected == 1
                ? "true"
                : "false"
            );


        // ESP32 risk score

        jsonData +=
            ",\"risk_score\":";

        jsonData +=
            String(
                riskScore
            );


        // ESP32 risk level

        jsonData +=
            ",\"risk_level\":\"";

        jsonData +=
            riskLevel;

        jsonData +=
            "\"";


        jsonData +=
            "}";


        // ----------------------------------------------------
        // Print JSON
        // ----------------------------------------------------

        Serial.println();

        Serial.println(
            "Sending data to server..."
        );

        Serial.println(
            jsonData
        );


        // ----------------------------------------------------
        // POST request
        // ----------------------------------------------------

        int httpResponseCode =
            http.POST(
                jsonData
            );


        Serial.print(
            "HTTP Response Code: "
        );

        Serial.println(
            httpResponseCode
        );


        // ----------------------------------------------------
        // Server response
        // ----------------------------------------------------

        if (
            httpResponseCode > 0
        ) {

            String response =
                http.getString();


            Serial.println(
                "Server Response:"
            );


            Serial.println(
                response
            );

        }

        else {

            Serial.print(
                "HTTP Error: "
            );

            Serial.println(
                httpResponseCode
            );

        }


        http.end();

    }

    else {

        Serial.println(
            "WiFi disconnected!"
        );

    }


    // ========================================================
    // Wait 5 seconds
    // ========================================================

    delay(5000);
}