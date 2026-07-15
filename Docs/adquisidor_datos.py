import serial
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# ===========================
# CONFIGURACIÓN
# ===========================

PORT = "/dev/cu.usbserial-110"      # Cambia si tu puerto cambia
BAUDRATE = 115200

SAVE_FOLDER = "Data"

os.makedirs(SAVE_FOLDER, exist_ok=True)

# ===========================

print("--------------------------------")
print(" APPS Data Logger")
print("--------------------------------")

print("Connecting...")

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

print("Connected!")
print("Recording...")
print("Press CTRL+C to finish.\n")

telemetry = []

try:

    while True:

        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        # Mostrar eventos importantes
        if line.startswith("EVENT"):

            print(line)

            continue

        # Solo procesar datos
        if not line.startswith("DATA"):
            continue

        try:

            parts = line.split(",")

            timestamp = int(parts[1])

            volt1 = float(parts[2])
            volt2 = float(parts[3])

            sensor1 = float(parts[4])
            sensor2 = float(parts[5])

            difference = float(parts[6])

            motor = int(parts[7])

            telemetry.append([
                timestamp,
                volt1,
                volt2,
                sensor1,
                sensor2,
                difference,
                motor
            ])

        except Exception:

            pass

except KeyboardInterrupt:

    print("\nStopping acquisition...")

finally:

    ser.close()

# ===========================
# GUARDAR CSV
# ===========================

if len(telemetry) == 0:

    print("No data received.")

    quit()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

csv_name = os.path.join(
    SAVE_FOLDER,
    f"APPS_{timestamp}.csv"
)

df = pd.DataFrame(
    telemetry,
    columns=[
        "Time_ms",
        "Voltage1",
        "Voltage2",
        "Sensor1_percent",
        "Sensor2_percent",
        "Difference",
        "Motor"
    ]
)

df.to_csv(csv_name, index=False)

print(f"CSV saved:\n{csv_name}")

# ===========================
# GRAFICAR
# ===========================

plt.figure(figsize=(12,6))

plt.plot(
    df["Time_ms"],
    df["Sensor1_percent"],
    label="Sensor 1"
)

plt.plot(
    df["Time_ms"],
    df["Sensor2_percent"],
    label="Sensor 2"
)

plt.xlabel("Time (ms)")
plt.ylabel("Pedal Position (%)")

plt.title("APPS Sensor Comparison")

plt.grid(True)

plt.legend()

plot_name = csv_name.replace(".csv",".png")

plt.savefig(plot_name, dpi=300)

plt.show()

print(f"Plot saved:\n{plot_name}")