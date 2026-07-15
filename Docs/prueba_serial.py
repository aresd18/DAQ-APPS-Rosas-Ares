import serial
import time

PUERTO = '/dev/cu.usbserial-110'  # <--- CAMBIA POR TU PUERTO
BAUDRATE = 115200

print("🔌 Intentando conectar al ESP32...")

try:
    ser = serial.Serial(PUERTO, BAUDRATE, timeout=1)
    time.sleep(2)
    print("✅ Conectado. Esperando datos...")
    print("Escribe 'start' y luego 'print' en el Monitor Serie.")
    print("Luego CIERRA el Monitor Serie para ver los datos aquí.")
    
    while True:
        if ser.in_waiting > 0:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            if linea:
                print(f"📨 Recibido: {linea}")
                
except serial.SerialException as e:
    print(f"❌ Error: {e}")
except KeyboardInterrupt:
    print("👋 Terminado.")