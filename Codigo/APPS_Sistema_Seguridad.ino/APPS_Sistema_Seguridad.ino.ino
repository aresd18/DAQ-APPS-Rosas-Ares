#include <Wire.h>
#include <LiquidCrystal_I2C.h>
// Configuración del LCD (dirección I2C 0x27, 16 columnas x 2 filas)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Configuración de pines de los sensores
const int sensor1Pin = 32; // GPI032
const int sensor2Pin = 33; // GPI033

//Variables para la lógica de seguridad
float percent1_prev = 0;
float percent2_prev = 0;
unsigned long fallaInicio = 0;
bool fallaActiva = false;
bool motorEncendido = true;

void setup() {
  Serial.begin(115200);

  // Inicializar LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();

  // Configuración de pines
  pinMode(sensor1Pin, INPUT);
  pinMode(sensor2Pin, INPUT);

  // Mensaje de inicio
  lcd.setCursor(0, 0);
  lcd.print("Sistema APPS");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...");
  delay(2000);
  lcd.clear();
}

void loop() {
  //1. Leer sensores
  int raw1 = analogRead(sensor1Pin);
  int raw2 = analogRead(sensor2Pin);

  //2. Convertir a voltaje (0-3.3V)
  float volt1 = raw1 * (3.3 / 4095.0);
  float volt2 = raw2 * (3.3 / 4095.0);
  
  //Convertir a porcentaje (escala común y asimétrica)
  //Sensor 1: 0V -> 0%, 3.0V -> 100%

  float percent1 = (volt1 / 3.0) * 100.0;
  if (percent1 < 0) percent1 = 0;
  if (percent1 > 100) percent1 = 100;

  //Sensor 2: 0.5V -> 0%, 3.3V -> 100%
  float percent2 = ((volt2 - 0.5) / (3.3 - 0.5)) * 100.0;
  if (percent2 < 0) percent2 = 0;
  if (percent2 > 100) percent2 = 100;

  //2. Mostrar en monitor serie
  Serial.print("S1(V): ");
  Serial.print(volt1);
  Serial.print(" | S2(V): ");
  Serial.print(volt2);
  Serial.print(" | %1: ");
  Serial.print(percent1);
  Serial.print(" | %2: ");
  Serial.print(percent2);
  Serial.print(" | Motor: ");
  Serial.print(motorEncendido ? "ON " : "OFF ");

  //3. Mostrar en LCD
  lcd.setCursor(0, 0);
  lcd.print("S1: ");
  lcd.print(percent1, 1);
  lcd.print("% S2:");
  lcd.print(percent2, 1);
  lcd.print("%");

  lcd.setCursor(0,1);
  if (motorEncendido) {
    lcd.print("Motor: ON ");
  } else {
    lcd.print("Motor: OFF");
  }

  //4. Lógica de seguridad (APPS)
  float diferencia = abs(percent1 - percent2);
  int umbral = 10; //10% de diferencia máxima permitida

  if (diferencia > umbral) {
    //Si hay diferencia, inicia el contandor de falla
    if (!fallaActiva) {
      fallaActiva = true;
      fallaInicio = millis();
    }

    //Si la falla dura más de 100 ms, apagar motor
    if (millis() - fallaInicio >= 100) {
      motorEncendido = false;
      Serial.println("*** ALERTA: FALLA DETECTADA - MOTOR APAGADO***");

      //Mostrar alerta en LCD
      lcd.setCursor(0, 1);
      lcd.print("!!!ALERTA!!!");
    }
  } else {
    //Si los sensores vuelven a coincidir, resetear falla
    fallaActiva = false;
    //El motor no se enciende automáticamente por seguridad
    //(requiere reinicio manual)
  }

  delay(10); //leer cada 10 ms
}