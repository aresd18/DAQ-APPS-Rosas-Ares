/*
  APPS (Accelerator Pedal Position Sensor)
  Formula SAE - Rule T.4.2

  Hardware:
  - ESP32 DevKit V1
  - 2 Potentiometers (APPS Sensors)
  - LCD 16x2 I2C

  This firmware:
  - Reads both pedal sensors
  - Converts voltage to percentage
  - Checks APPS plausibility
  - Displays information on LCD
  - Streams telemetry to the PC at 100 Hz
*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------- LCD ----------------

const int LCD_ADDRESS = 0x27;
const int LCD_COLUMNS = 16;
const int LCD_ROWS = 2;

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLUMNS, LCD_ROWS);

// ---------------- Pins ----------------

const int SENSOR1_PIN = 32;
const int SENSOR2_PIN = 33;

// ---------------- ADC ----------------

const int ADC_MAX = 4095;
const float VREF = 3.3;

// ---------------- Sensor Calibration ----------------

// Sensor 1
const float SENSOR1_VOLT_MIN = 0.0;
const float SENSOR1_VOLT_MAX = 3.0;

// Sensor 2
const float SENSOR2_VOLT_MIN = 0.5;
const float SENSOR2_VOLT_MAX = 3.3;

// ---------------- Safety ----------------

const float DIFF_THRESHOLD = 10.0;
const unsigned long FAULT_DELAY_MS = 100;

// ---------------- Variables ----------------

float sensor1_volt = 0;
float sensor2_volt = 0;

float sensor1_percent = 0;
float sensor2_percent = 0;

bool motor_status = true;
bool fault_active = false;

unsigned long fault_start_time = 0;

// =====================================================

void setup() {

  Serial.begin(115200);

  pinMode(SENSOR1_PIN, INPUT);
  pinMode(SENSOR2_PIN, INPUT);

  lcd.init();
  lcd.backlight();

  lcd.setCursor(0,0);
  lcd.print("APPS System");

  lcd.setCursor(0,1);
  lcd.print("F-SAE T.4.2");

  delay(2000);

  lcd.clear();

  Serial.println("SYSTEM_READY");
}

// =====================================================

void loop() {

  readSensors();

  updateSafetyLogic();

  updateDisplay();

  sendTelemetry();

  delay(10);

}

// =====================================================

void readSensors(){

  int raw1 = analogRead(SENSOR1_PIN);
  int raw2 = analogRead(SENSOR2_PIN);

  sensor1_volt = raw1 * (VREF / ADC_MAX);
  sensor2_volt = raw2 * (VREF / ADC_MAX);

  sensor1_percent = mapSensor1(sensor1_volt);
  sensor2_percent = mapSensor2(sensor2_volt);

}

// =====================================================

float mapSensor1(float voltage){

  float percent =
  ((voltage - SENSOR1_VOLT_MIN) /
  (SENSOR1_VOLT_MAX - SENSOR1_VOLT_MIN)) * 100.0;

  return constrain(percent,0.0,100.0);

}

float mapSensor2(float voltage){

  float percent =
  ((voltage - SENSOR2_VOLT_MIN) /
  (SENSOR2_VOLT_MAX - SENSOR2_VOLT_MIN)) * 100.0;

  return constrain(percent,0.0,100.0);

}

// =====================================================

void updateSafetyLogic(){

  float difference =
  abs(sensor1_percent - sensor2_percent);

  if(difference > DIFF_THRESHOLD){

      if(!fault_active){

          fault_active = true;
          fault_start_time = millis();

          Serial.println("EVENT,FAULT_TIMER_STARTED");

      }

      if(millis() - fault_start_time >= FAULT_DELAY_MS){

          if(motor_status){

              motor_status = false;

              Serial.println("EVENT,MOTOR_OFF");

          }

      }

  }
  else{

      fault_active = false;

      // El motor NO vuelve a encender automáticamente

  }

}

// =====================================================

void updateDisplay(){

  lcd.setCursor(0,0);

  lcd.print("S1:");
  lcd.print(sensor1_percent,0);
  lcd.print("% ");

  lcd.print("S2:");
  lcd.print(sensor2_percent,0);
  lcd.print("% ");

  lcd.setCursor(0,1);

  if(motor_status){

      if(fault_active){

          lcd.print("Fault ");

          lcd.print(millis()-fault_start_time);

          lcd.print("ms   ");

      }
      else{

          lcd.print("Motor: ON     ");

      }

  }
  else{

      lcd.print("!!! ALERT !!! ");

  }

}

// =====================================================

void sendTelemetry(){

  float difference =
  abs(sensor1_percent - sensor2_percent);

  Serial.print("DATA,");

  Serial.print(millis());

  Serial.print(",");

  Serial.print(sensor1_volt,3);

  Serial.print(",");

  Serial.print(sensor2_volt,3);

  Serial.print(",");

  Serial.print(sensor1_percent,2);

  Serial.print(",");

  Serial.print(sensor2_percent,2);

  Serial.print(",");

  Serial.print(difference,2);

  Serial.print(",");

  Serial.println(motor_status ? 1 : 0);

}