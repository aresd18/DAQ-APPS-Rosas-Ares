/*
  APPS (Accelerator Pedal Position Sensor) System
  Formula SAE - Rule T.4.2
  With Data Logging Capability - CSV Format
*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// LCD
const int LCD_ADDRESS = 0x27;
const int LCD_COLUMNS = 16;
const int LCD_ROWS = 2;

// Sensor pins
const int SENSOR1_PIN = 32;
const int SENSOR2_PIN = 33;

// Sensor Calibration (Asymmetric)
const float SENSOR1_VOLT_MIN = 0.0;
const float SENSOR1_VOLT_MAX = 3.0;
const float SENSOR2_VOLT_MIN = 0.5;
const float SENSOR2_VOLT_MAX = 3.3;

// ADC
const int ADC_MAX = 4095;
const float VREF = 3.3;

// Safety Parameters
const float DIFF_THRESHOLD = 10.0;
const unsigned long FAULT_DELAY_MS = 100;

// Data Logging
const int MAX_SAMPLES = 1000;
float log_sensor1[MAX_SAMPLES];
float log_sensor2[MAX_SAMPLES];
unsigned long log_time[MAX_SAMPLES];
int log_count = 0;
bool logging_active = false;

// Global Variables
LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLUMNS, LCD_ROWS);

float sensor1_percent = 0.0;
float sensor2_percent = 0.0;
float sensor1_volt = 0.0;
float sensor2_volt = 0.0;

unsigned long fault_start_time = 0;
bool fault_active = false;
bool motor_status = true;

void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.backlight();
  lcd.clear();

  pinMode(SENSOR1_PIN, INPUT);
  pinMode(SENSOR2_PIN, INPUT);

  motor_status = true;

  lcd.setCursor(0, 0);
  lcd.print("APPS System");
  lcd.setCursor(0, 1);
  lcd.print("F-SAE T.4.2");
  delay(2000);
  lcd.clear();

  Serial.println("=== APPS SYSTEM READY ===");
  Serial.println("Commands:");
  Serial.println("  'start' - Start logging");
  Serial.println("  'stop'  - Stop logging");
  Serial.println("  'print' - Print logged data");
  Serial.println("  'clear' - Clear log buffer");
}

void loop() {
  // Check for serial commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "start") {
      startLogging();
    } else if (command == "stop") {
      stopLogging();
    } else if (command == "print") {
      printLogData();
    } else if (command == "clear") {
      log_count = 0;
      Serial.println("Log cleared");
    }
  }

  readSensors();
  updateSafetyLogic();
  updateDisplay();
  printDebugInfo();
  logData();
  delay(10);
}

void readSensors() {
  int raw1 = analogRead(SENSOR1_PIN);
  int raw2 = analogRead(SENSOR2_PIN);

  sensor1_volt = raw1 * (VREF / ADC_MAX);
  sensor2_volt = raw2 * (VREF / ADC_MAX);

  sensor1_percent = mapSensor1(sensor1_volt);
  sensor2_percent = mapSensor2(sensor2_volt);
}

float mapSensor1(float voltage) {
  float percent = ((voltage - SENSOR1_VOLT_MIN) /
                   (SENSOR1_VOLT_MAX - SENSOR1_VOLT_MIN)) * 100.0;
  return constrain(percent, 0.0, 100.0);
}

float mapSensor2(float voltage) {
  float percent = ((voltage - SENSOR2_VOLT_MIN) /
                   (SENSOR2_VOLT_MAX - SENSOR2_VOLT_MIN)) * 100.0;
  return constrain(percent, 0.0, 100.0);
}

void updateSafetyLogic() {
  float difference = abs(sensor1_percent - sensor2_percent);

  if (difference > DIFF_THRESHOLD) {
    if (!fault_active) {
      fault_active = true;
      fault_start_time = millis();
      Serial.println("WARNING: Fault detected, starting 100ms timer");
    }

    if (millis() - fault_start_time >= FAULT_DELAY_MS) {
      if (motor_status) {
        motor_status = false;
        Serial.println("ALERT: Motor shutdown - fault confirmed (100ms)");
      }
    }
  } else {
    if (fault_active) {
      fault_active = false;
      Serial.println("INFO: Fault cancelled - sensors synchronized before 100ms");
    }

    if (!motor_status) {
      motor_status = true;
      Serial.println("INFO: Motor restarted - sensors synchronized");
    }
  }
}

void updateDisplay() {
  float difference = abs(sensor1_percent - sensor2_percent);

  lcd.setCursor(0, 0);
  lcd.print("S1:");
  lcd.print(sensor1_percent, 0);
  lcd.print("% S2:");
  lcd.print(sensor2_percent, 0);
  lcd.print("%");

  lcd.setCursor(0, 1);

  if (logging_active) {
    lcd.print("REC ");
    lcd.print(log_count);
    lcd.print("/");
    lcd.print(MAX_SAMPLES);
    lcd.print(" ");
  } else if (motor_status) {
    lcd.print("Motor: ON     ");
    if (fault_active) {
      lcd.setCursor(0, 1);
      lcd.print("Fault ");
      lcd.print(millis() - fault_start_time);
      lcd.print("ms   ");
    }
  } else {
    lcd.print("!!! ALERT !!! ");
  }
}

void printDebugInfo() {
  float difference = abs(sensor1_percent - sensor2_percent);

  Serial.print("DATA:");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(sensor1_volt, 3);
  Serial.print(",");
  Serial.print(sensor2_volt, 3);
  Serial.print(",");
  Serial.print(sensor1_percent, 1);
  Serial.print(",");
  Serial.print(sensor2_percent, 1);
  Serial.print(",");
  Serial.print(difference, 1);
  Serial.print(",");
  Serial.print(motor_status ? "ON" : "OFF");

  if (fault_active) {
    Serial.print(",");
    Serial.print(millis() - fault_start_time);
    Serial.print("ms");
  }
  Serial.println();
}

void startLogging() {
  log_count = 0;
  logging_active = true;
  Serial.println("DATA LOG: Started recording");
}

void stopLogging() {
  logging_active = false;
  Serial.println("DATA LOG: Stopped recording");
  Serial.print("Total samples: ");
  Serial.println(log_count);
}

void logData() {
  if (logging_active && log_count < MAX_SAMPLES) {
    log_sensor1[log_count] = sensor1_percent;
    log_sensor2[log_count] = sensor2_percent;
    log_time[log_count] = millis();
    log_count++;
  }
}

void printLogData() {
  Serial.println("=== DATA LOG ===");
  Serial.println("Time(ms),Sensor1(%),Sensor2(%)");
  for (int i = 0; i < log_count; i++) {
    Serial.print(log_time[i]);
    Serial.print(",");
    Serial.print(log_sensor1[i]);
    Serial.print(",");
    Serial.println(log_sensor2[i]);
  }
  Serial.println("=== END LOG ===");
}