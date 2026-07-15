import serial
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Configuracion
PORT = "/dev/cu.usbserial-110"
BAUDRATE = 115200
SAVE_FOLDER = "Data"

os.makedirs(SAVE_FOLDER, exist_ok=True)

print("--------------------------------")
print(" APPS Data Logger")
print("--------------------------------")
print("Connecting...")

ser = serial.Serial(PORT, BAUDRATE, timeout=1)
print("Connected!")
print("Recording...")
print("Press CTRL+C to finish.\n")

telemetry = []
events = []

try:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        
        if not line:
            continue
        
        # Mostrar eventos en tiempo real
        if line.startswith("EVENT:"):
            event = line.replace("EVENT:", "")
            print(f"[EVENTO] {event}")
            events.append(event)
            continue
        
        # Procesar datos
        if not line.startswith("DATA:"):
            continue
        
        try:
            parts = line.split(",")
            timestamp = int(parts[1])
            volt1 = float(parts[2])
            volt2 = float(parts[3])
            sensor1 = float(parts[4])
            sensor2 = float(parts[5])
            diff = float(parts[6])
            motor = 1 if parts[7] == "ON" else 0
            
            telemetry.append([timestamp, volt1, volt2, sensor1, sensor2, diff, motor])
            
            # Mostrar cada 50 muestras para no saturar
            if len(telemetry) % 50 == 0:
                print(f"Time: {timestamp}ms | S1: {sensor1:.1f}% | S2: {sensor2:.1f}% | Motor: {'ON' if motor else 'OFF'}")
                
        except Exception as e:
            pass

except KeyboardInterrupt:
    print("\nStopping acquisition...")

finally:
    ser.close()

# Guardar CSV
if len(telemetry) == 0:
    print("No data received.")
    quit()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_name = os.path.join(SAVE_FOLDER, f"APPS_{timestamp}.csv")

df = pd.DataFrame(telemetry, columns=[
    "Time_ms", "Voltage1", "Voltage2", "Sensor1", "Sensor2", "Difference", "Motor"
])

df.to_csv(csv_name, index=False)
print(f"CSV saved: {csv_name}")

# Graficar con zonas de falla
plt.figure(figsize=(14, 8))

# Sensores
plt.plot(df["Time_ms"], df["Sensor1"], label="Sensor 1", color="blue", linewidth=2)
plt.plot(df["Time_ms"], df["Sensor2"], label="Sensor 2", color="red", linewidth=2)

# Umbral del 10%
plt.axhline(y=10, color="orange", linestyle="--", linewidth=1.5, label="Umbral 10%")

# Marcar zonas donde Motor = 0 (falla)
falla = df["Motor"] == 0
if falla.any():
    # Detectar bloques de falla
    in_falla = False
    start_idx = 0
    for i in range(len(df)):
        if df["Motor"].iloc[i] == 0 and not in_falla:
            in_falla = True
            start_idx = i
        elif df["Motor"].iloc[i] == 1 and in_falla:
            in_falla = False
            plt.axvspan(df["Time_ms"].iloc[start_idx], df["Time_ms"].iloc[i-1], 
                       alpha=0.2, color="red", label="Falla (Motor OFF)" if start_idx == 0 else "")
    if in_falla:
        plt.axvspan(df["Time_ms"].iloc[start_idx], df["Time_ms"].iloc[-1], 
                   alpha=0.2, color="red")

plt.xlabel("Tiempo (ms)")
plt.ylabel("Posicion del pedal (%)")
plt.title("APPS - Comparacion de Sensores con Deteccion de Fallas")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

plot_name = csv_name.replace(".csv", ".png")
plt.savefig(plot_name, dpi=300)
print(f"Plot saved: {plot_name}")

plt.show()

# Resumen
print("\n--- Resumen ---")
print(f"Total muestras: {len(df)}")
print(f"Motor ON: {df['Motor'].sum()} muestras")
print(f"Motor OFF: {len(df) - df['Motor'].sum()} muestras")
print(f"Eventos: {', '.join(set(events)) if events else 'Ninguno'}")