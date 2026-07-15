# Sistema APPS - Formula SAE
## Descripción
Sistema de validación de plausibilidad para el pedal de acelerador (APPS) de un vehículo de Fórmula SAE. Implementa redundancia de sensores con dos potenciómetros, lógica de seguridad con retardo de 100ms y visualización en LCD.

**Regla T.4.2 de Fórmula SAE;**
> T.4.2.2: Two or more electrically separate sensors must be used as APPSs. A single OEM type APPS with two completely separate sensors in a single housing is acceptable.
> T.4.2.4: Implausibility is defined as a deviation of more than 10% Pedal Travel between the sensores or other failure as defined in this Section T.4.2. Use of values larger than 10% Pedal Travel require justification in the ETC Systems Form and may not be approved.
> T.4.2.5: If an Implausibility occurs between the values af the APPSs and persists for more than 100 msec, the power to the (IC) Electronic Throttle / (EV) Motor(s) must be immediately stopped completely.

## Requisitos de Hardware
- **Microcontrolador:** ESP32 DevKit V1
- **Sensores:** 2 potenciómetros de 10 kΩ (simulan APPS)
- **Display:** LCD 16x2 con módulo I2C
- **Resistencias:** 2 de 10 kΩ
- **Otros:** Protoboard, cables Dupont

## Diagrama de Conexiones
|Componente|Pin ESP32|
|----------|---------|
|LCD VCC   |VIN      |
|LCD GND   |GND|
|LCD SDA|D21|
|LCD SCL|D22|
|Potenciómetro 1 (izq)|GND|
|Potenciómetro 1 (cent)|D32|
|Potenciómetro 1 (der)|3V3|
|Potenciómetro 2 (izq)|GND|
|Potenciómetro 2 (cent)|D33|
|Potenciómetro 2 (der)|3V3|
|Resistencias (10kΩ)|D32/D33 a GND|

## Calibración del sistema
### Escala asimétrica (Requerimiento T.4.2)
Para cumplir con la normativa de Fórmula SAE, cada sensor tiene un rango de voltaje diferente:
|Sensor|Voltaje mínimo|Voltaje máximo|Mapeo|
|------|--------------|--------------|-----|
|Sensor 1 (GPI032)|0.0V|3.0V|0% - 100%|
|Sensor 2 (GPI033)|0.5V|3.3V|0% - 100%|

Esta asimetría permite detectar cortocircuitos. Si un sensor se queda fijo en 0V o 3.3V (por un cable roto o un corto), el otro sensor sigue funcionando y el sistema detecta la falla al comparar ambos valores.

### Procedimiento de calibración
1. Se conectó el ESP32 a la computadora por USB.
2. Se abrió el Monitor Serie (115200 baudios).
3. Se giró el potenciómetro 1 al mínimo, en la lectura dió ~0.0V.
4. Se giró el potenciómetro 1 al máximo, en la lectura dió ~3.0V.
5. Se repitió el proceso con el potenciómetro 2.
6. Se hizo una medida para ambos sensores, donde mostraran 0% en reposo y 100% a fondo.

## Lógica de seguridad
El sistema implementa la siguiente lógica para garantizar la seguridad del vehiculo y el piloto:
 
1. **Lectura:** Se toman 2 lecturas por sensor (100 Hz)
2. **Comparación:** Se calcula la diferencia porcentual
3. **Umbral:** Si la diferencia > 10%, se activa el contador de falla
4. **Retardo:** Si la falla persiste ≥ 100 ms, se apaga el motor 
5. **Recuperación:** La falla se resetea cuando los sensores vuelven a coincidir

## 📊 Resultados de Pruebas
| Prueba | Sensor 1 | Sensor 2 | Diferencia | Resultado |
|--------|----------|----------|------------|-----------|
| 1 | 10% | 10% | 0% | ✅ Motor ON |
| 2 | 10% | 11% | 1% | ✅ Motor ON |
| 3 | 10% | 19% | 9% | ✅ Motor ON |
| 4 | 10% | 20% | 10% | ❌ Motor OFF (100ms) |
| 5 | 10% | 50% | 40% | ❌ Motor OFF (100ms) |
| 6 | 20% | 20% | 0% | ✅ Motor ON (restablece) |

### Visualización en LCD
- **Línea 1:** "S1: XX% S2: XX%"
- **Línea 2:** "Motor: ON" o "!!!ALERTA!!!

## Desarrollo
- **Fechas:** 13 - 17 de julio de 2026
- **Equipo DAQ - Fórmula SAE**

## Autor
- **Ares Daniel Rosas Flores**