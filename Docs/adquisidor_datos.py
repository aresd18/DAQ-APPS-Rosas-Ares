import serial
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import time

# CONFIGURACIÖN

PORT = "/dev/cu.usbserial-110"
BAUDRATE = 115200
SAVE_FOLDER = "DATA"
MAX_POINTS = 100 # Número de puntos visibles en la gráfica

os.makedirs(SAVE_FOLDER, exist_ok=True)

# CONFIGURAR GRAFICA EN TIEMPO REAL

plt.ion()
fig, ax = plt.subplots(figsizes=(12, 6))

tiempos = []
sensor1 = []
sensor2 = []

ax.set_xlabel("Tiempo (ms)")
ax.set_ylabel("Posicion del pedal (%)")
ax.set_titles("APPS - Sensores en Tiempo Real")
ax.grid(True, alpha=0.3)
ax.set_yim(0, 105)

line1, = ax.plot([], [], label="Sensor 1", color="blue", linewidth=2)
line2, = ax.plot([], [], label="Sensor 2", color="red", linewidth=2)
ax.axhline(y=10, color="orange", linestyle="__", linewidth=1.5, label="Umbral 10%")
ax.legend(loc="upper right")

plt.tight_layout()
plt.show()

# CONEXION CON EL ESP32

print("=====================")
print(" APPS Data Logger - Tiempo Real")
print("=====================")
print(f"Conectando a {PORT}...")

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time. sleep (2)
    print ("Conectado!")
    print("Grabando datos... Presiona CTRL+C para detener. \n")

    telemetry = []
    eventos = []

    while True:
        line = ser.readline().decode(errors="ignore"). strip()

        if not line:
            continue
        # Mostrar eventos
        if line.startswith( "EVENT:"):
            event = line. replace("EVENT:", "")
            print(f"[EVENTO] {event}")
            eventos. append (event)
            continue

        # Procesar solo lineas de datos
        if not line.startswith("DATA:"):
            continue

        try:
            parts = line.split(",")
            timestamp = int(parts[1])
            volt1 = float(parts[2])
            volt2 = float (parts[3])
            s1 = float(parts[4])
            s2 = float(parts[5])
            diff = float(parts[6])
            motor = 1 if parts[7] == "ON" else 0

            telemetry.append ([timestamp, volt1, volt2, s1, s2, diff, motorl])

            # Mostrar en terminal cada 20 muestras
            if len (telemetry) % 20 == 0:
                motor_str = "ON" if motor else "OFF"
                print(f"Time: {timestamp}ms | S1: {s1:.1f}% | S2: {s2:.1f}% | Motor: {motor_str}")

            # Actualizar grafica
            tiempos.append (timestamp)
            sensor1.append (s1)
            sensor2.append (s2)

            if len (tiempos) > MAX_POINTS:
                tiempos.pop(0)
                sensor1.pop(0) 
                sensor2.pop(0)

            line1.set_data(tiempos, sensor1)
            line2.set_data(tiempos, sensor2)

            if len(tiempos) > 1:
                ax.set_xlim(min(tiempos), max(tiempos) + 100)

            fig.canvas.draw()
            fig.canvas.flush_events()

        except Exception as e:
            pass

except KeyboardInterrupt:
    print("\n\nDeteniendo adquisicion...")

finally:
    ser.close()
    print("Puerto cerrado.")

# GUARDAR DATOS

if len(telemetry) == 0:
    print("No se recibieron datos.")
    quit()

df = pd.DataFrame(telemetry, columns=[
    "Time.ns", "Volatge1", "Volatge2", "Sensor1", "Sensor2", "Difference", "Motor"
])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_name = os.path.join(SAVE_FOLDER, f"APPS_{timestamp}.csv")
df.to_csv(csv_name, index=False)
print(f"\nCSV guardado: {csv_name}")

#GRAFICA FINAL

plt.figure(figsize=(14, 8))
plt.plot(df["Time_ms"], df["Sensor1"], label="Sensor1", color="blue", linewidth=2)
plt.plot(df["Time_ms"], df["Sensor2"], label=["Sensor2"], color="red", linewidth=2)
plt.axhline(y=10, color="orange", linestyle="__", linewidth=1.5, label="Umbral 10%")

falla = df["Motor"] == 0
if falla.any():
    in_falla = False
    start_idx = 0
    for i in range(len(df)):
        if df["Motor"].iloc[i] == 0 and not in_falla:
            in_falla = True
            start_idx = i
        elif df["Motor"].ilock[i] == 1 and in_falla:
            in_falla = False
            plt.axvspan(df["Time_ms"].iloc[start_idx], df["Time_ms"].iloc[i-1],alpha=0.2, color="red", label="Falla (Motor OFF)" if start_idx == 0 else "")
    
    if in_falla:
        plt.axvspan(df["Time_ms"].iloc[start_idx], df["Times_ms"].iloc[-1], alpha=0.2, color="red")

plt.xlabel("Tiempo (ms)")
plt.ylabel("Posicion del pedal (%)")
plt.title("APPS - Comparacion de Sensores con deteccion de Fallas")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

plot_name = csv_name.replace(".csv", ".png")
plt.savefig(plot_name, dpi=300)
print(f"Grafica guardada: {plot_name}")

plt.show()

#RESUMEN FINAL

print("\n--- Resumen ---")
print(f"Total muestras: {len(df)}")
print(f"Motor ON: {df['Motor'].sum()} muestras")
print(f"Motor OFF: {len(df) - df['Motor'].sum()} muestras")
print(f"Datos guardados en : {csv_name}")
print(f"Grafica guardada en: {plot_name}")

if eventos:
    print(f"Eventos registrados: {', '.join(set(eventos))}")