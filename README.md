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
- **Otros:** Protoboard, cable Dupont

## Funcionamiento:

### Calibración Asimétrica
|    Sensor    |Rango de voltaje|Mapeo a porcentaje|
|--------------|----------------|------------------|
|Sensor 2 (D32)|    0V - 3.0V   |     0% - 100%    |
|Sensor 1 (D33)|   0.5V - 3.3V  |     0% - 100%    |

### Lógica de seguridad
1.**Lectura:** Se toman 2 lecturas por sensor (100 Hz)
2.**Comparación:** Se calcula la diferencia porcentual
3.**Umbral:** Si la diferencia > 10%, se activa el contador de falla
4.**Retardo:** Si la falla persiste ≥ 100 ms, se apaga el motor 
5.**Recuperación:** La falla se resetea cuando los sensores vuelven a coincidir

### Visualización en LCD
- **Línea 1:** "S1: XX% S2: XX%"
- **Línea 2:** "Motor: ON" o "!!!ALERTA!!!

## Desarrollo
- **Fechas:** 13 - 17 de julio de 2026
- **Equipo DAQ - Fórmula SAE**

## Autor
- **Ares Daniel Rosas Flores**