import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.spatial import ConvexHull
import warnings
warnings.filterwarnings('ignore')

# Configurar graficas
plt.style.use('seaborn-v0_8-darkgrid')

print("="*60)
print("ANALISIS DE TELEMETRIA - FORMULA SAE")
print("="*60)

# ============================================
# PASO 1: CARGAR TU ARCHIVO
# ============================================
print("\nCargando archivo...")

ruta_archivo = "/Users/herarosas/Ares/DAQ_APPS/Ejercicio2_Telemetria/RFAD_DATA.csv"

try:
    df = pd.read_csv(ruta_archivo)
    print(f"Archivo cargado: {len(df)} filas, {len(df.columns)} columnas")
except Exception as e:
    print(f"Error al cargar: {e}")
    exit()

# ============================================
# PASO 2: VER COLUMNAS (para confirmar)
# ============================================
print("\n" + "="*60)
print("COLUMNAS ENCONTRADAS")
print("="*60)

print("\nLista de columnas:")
for i, col in enumerate(df.columns):
    print(f"   {i+1}. {col}")

print("\nPrimeras 3 filas:")
print(df.head(3))

# ============================================
# PASO 3: SELECCIONAR Y RENOMBRAR COLUMNAS
# ============================================
print("\n" + "="*60)
print("ADAPTANDO COLUMNAS PARA ANALISIS")
print("="*60)

# Verificar que las columnas necesarias existen
columnas_requeridas = ['Timestamp', 'speed_kmph', 'accel_x', 'accel_y', 'brake_pressure', 'throttle']
columnas_faltantes = []

for col in columnas_requeridas:
    if col not in df.columns:
        columnas_faltantes.append(col)

if columnas_faltantes:
    print(f"FALTAN COLUMNAS: {columnas_faltantes}")
    print("\nColumnas disponibles:", df.columns.tolist())
    exit()

# Crear nuevo dataframe con solo las columnas necesarias
df_analisis = df[columnas_requeridas].copy()

# Renombrar a nombres estandar
df_analisis = df_analisis.rename(columns={
    'Timestamp': 'timestamp',
    'speed_kmph': 'speed_kmph',
    'accel_x': 'accel_x',
    'accel_y': 'accel_y',
    'brake_pressure': 'brake_pressure',
    'throttle': 'throttle'
})

print("Columnas seleccionadas:")
print(df_analisis.columns.tolist())

# ============================================
# PASO 4: CALCULAR FRECUENCIA DE MUESTREO
# ============================================
print("\n" + "="*60)
print("FRECUENCIA DE MUESTREO")
print("="*60)

dt = np.diff(df_analisis['timestamp'].values)
dt_median = np.median(dt)
fs = 1 / dt_median

print(f"   - Intervalo promedio: {dt_median*1000:.1f} ms")
print(f"   - Frecuencia de muestreo: {fs:.1f} Hz")

# ============================================
# PASO 5: FILTRO PASA-BAJAS
# ============================================
print("\n" + "="*60)
print("APLICANDO FILTRO PASA-BAJAS")
print("="*60)

def butter_lowpass(cutoff, fs, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs, order=4):
    if len(data) == 0 or np.all(np.isnan(data)):
        return data
    
    b, a = butter_lowpass(cutoff, fs, order=order)
    data_clean = data.copy()
    mask_nan = np.isnan(data_clean)
    
    if np.any(mask_nan):
        data_clean[mask_nan] = np.nanmean(data_clean)
    
    try:
        y = filtfilt(b, a, data_clean)
        y[mask_nan] = np.nan
        return y
    except Exception as e:
        print(f"   Error en filtro: {e}")
        return data

cutoff_freq = 15
order = 4

print(f"   - Frecuencia de corte: {cutoff_freq} Hz")
print(f"   - Orden del filtro: {order}")
print(f"   - Justificacion: Elimina ruido de alta frecuencia (> {cutoff_freq} Hz)")

df_analisis['accel_x_filt'] = lowpass_filter(
    df_analisis['accel_x'].values, cutoff_freq, fs, order
)
df_analisis['accel_y_filt'] = lowpass_filter(
    df_analisis['accel_y'].values, cutoff_freq, fs, order
)

df_analisis['g_comb'] = np.sqrt(
    df_analisis['accel_x_filt']**2 + df_analisis['accel_y_filt']**2
)

g_max = df_analisis['g_comb'].max()
g_cruda = np.sqrt(df_analisis['accel_x']**2 + df_analisis['accel_y']**2)
g_max_cruda = g_cruda.max()

print(f"\n   G maxima (filtrada): {g_max:.3f} g")
print(f"   G maxima (cruda): {g_max_cruda:.3f} g")
print(f"   Reduccion de picos: {g_max_cruda - g_max:.3f} g")

# ============================================
# PASO 6: GRAFICA 1 - COMPARACION FILTRO
# ============================================
print("\nGenerando grafica comparativa...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

ax = axes[0,0]
ax.plot(df_analisis['timestamp'], df_analisis['accel_x'], 
        label='Crudo', alpha=0.4, color='gray', linewidth=0.5)
ax.plot(df_analisis['timestamp'], df_analisis['accel_x_filt'], 
        label='Filtrado', color='blue', linewidth=1.5)
ax.set_title('Aceleracion X - Comparacion')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Aceleracion (g)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[0,1]
ax.plot(df_analisis['timestamp'], df_analisis['accel_y'], 
        label='Crudo', alpha=0.4, color='gray', linewidth=0.5)
ax.plot(df_analisis['timestamp'], df_analisis['accel_y_filt'], 
        label='Filtrado', color='orange', linewidth=1.5)
ax.set_title('Aceleracion Y - Comparacion')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Aceleracion (g)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1,0]
ax.plot(df_analisis['timestamp'], g_cruda, 
        label='Crudo', alpha=0.4, color='gray', linewidth=0.5)
ax.plot(df_analisis['timestamp'], df_analisis['g_comb'], 
        label='Filtrado', color='red', linewidth=1.5)
ax.axhline(g_max, color='black', linestyle='--', alpha=0.7,
           label=f'G max filtrada: {g_max:.2f} g')
ax.set_title('Magnitud G Combinada')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('G (g)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1,1]
g_clean = df_analisis['g_comb'].dropna()
if len(g_clean) > 0:
    ax.hist(g_clean, bins=50, color='red', alpha=0.7, edgecolor='black')
    ax.axvline(g_max, color='black', linestyle='--', linewidth=2)
    ax.set_title(f'Distribucion de G - Max: {g_max:.2f} g')
    ax.set_xlabel('G (g)')
    ax.set_ylabel('Frecuencia')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comparacion_filtro.png', dpi=150, bbox_inches='tight')
print("   Guardada: comparacion_filtro.png")
plt.show()

# ============================================
# PASO 7: DIAGRAMA G-G
# ============================================
print("\n" + "="*60)
print("DIAGRAMA G-G (HUELLA DE FRICCION)")
print("="*60)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
x_plot = df_analisis['accel_x_filt'].dropna().values
y_plot = df_analisis['accel_y_filt'].dropna().values

if len(x_plot) > 3:
    ax.scatter(x_plot, y_plot, s=1, alpha=0.3, color='blue')
    
    try:
        points = np.column_stack([x_plot, y_plot])
        hull = ConvexHull(points)
        for simplex in hull.simplices:
            ax.plot(points[simplex, 0], points[simplex, 1], 
                   'r-', alpha=0.5, linewidth=1)
        ax.fill(points[hull.vertices, 0], points[hull.vertices, 1], 
                'red', alpha=0.1)
    except:
        print("   No se pudo calcular envolvente")
    
    ax.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax.axvline(0, color='black', linestyle='--', alpha=0.3)
    ax.set_title('Diagrama G-G (Huella de friccion)')
    ax.set_xlabel('Aceleracion Lateral (g)')
    ax.set_ylabel('Aceleracion Longitudinal (g)')
    ax.grid(True, alpha=0.3)
    ax.axis('equal')

ax2 = axes[1]

if len(x_plot) > 0:
    left_mask = x_plot < 0
    right_mask = x_plot > 0
    left_vals = y_plot[left_mask] if np.any(left_mask) else []
    right_vals = y_plot[right_mask] if np.any(right_mask) else []
    
    if len(left_vals) > 0 and len(right_vals) > 0:
        bp = ax2.boxplot([left_vals, right_vals], 
                         labels=['Izquierda', 'Derecha'], 
                         patch_artist=True)
        bp['boxes'][0].set_facecolor('skyblue')
        bp['boxes'][1].set_facecolor('lightgreen')
        ax2.set_title('Distribucion de G Longitudinal por Lado')
        ax2.set_ylabel('Aceleracion Longitudinal (g)')
        ax2.grid(True, alpha=0.3)
        
        mean_left = np.mean(left_vals)
        mean_right = np.mean(right_vals)
        asymmetry = (mean_right - mean_left) / max(abs(mean_left), abs(mean_right)) * 100
        
        ax2.text(0.5, 0.95, f'Asimetria: {asymmetry:.1f}%', 
                transform=ax2.transAxes, ha='center', fontsize=12,
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        print(f"\n   ASIMETRIA DIRECCIONAL:")
        print(f"      - Media (izquierda): {mean_left:.3f} g")
        print(f"      - Media (derecha): {mean_right:.3f} g")
        print(f"      - Asimetria: {asymmetry:.1f}%")
        
        if abs(asymmetry) > 10:
            print("   ASIMETRIA SIGNIFICATIVA (>10%)")
            print("      - Posible causa: Desbalance en suspension")
            print("      - Recomendacion: Revisar alineacion")
        elif abs(asymmetry) > 5:
            print("   ASIMETRIA MODERADA (5-10%)")
            print("      - Recomendacion: Monitorear evolucion")
        else:
            print("   ASIMETRIA ACEPTABLE (<5%)")
            print("      - La instrumentacion esta balanceada")

plt.tight_layout()
plt.savefig('diagrama_gg.png', dpi=150, bbox_inches='tight')
print("   Guardada: diagrama_gg.png")
plt.show()

# ============================================
# PASO 8: DETECCION DE FALLAS
# ============================================
print("\n" + "="*60)
print("DETECCION DE FALLAS")
print("="*60)

print("\n1) PERDIDA DE SEÑAL (accel_y):")

nan_mask = np.isnan(df_analisis['accel_y'].values)
nan_groups = []

if np.any(nan_mask):
    padded = np.concatenate(([0], nan_mask.astype(int), [0]))
    diffs = np.diff(padded)
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0] - 1
    
    for start, end in zip(starts, ends):
        if start < len(df_analisis) and end < len(df_analisis):
            t_start = df_analisis['timestamp'].iloc[start]
            t_end = df_analisis['timestamp'].iloc[end]
            duration = (t_end - t_start) * 1000
            
            if duration > 100:
                nan_groups.append((t_start, t_end, duration))
                print(f"   Perdida: {t_start:.2f}s - {t_end:.2f}s (duracion: {duration:.0f}ms)")

if not nan_groups:
    print("   No se detectaron perdidas sostenidas (>100ms)")

print("\n2) VIOLACION FRENO + ACELERADOR:")

umbral_freno = 3.0
umbral_acel = 10.0

df_analisis['brake_bool'] = df_analisis['brake_pressure'] > umbral_freno
df_analisis['throttle_bool'] = df_analisis['throttle'] > umbral_acel
violation = df_analisis['brake_bool'] & df_analisis['throttle_bool']
violation_groups = []

if violation.any():
    padded = np.concatenate(([0], violation.astype(int), [0]))
    diffs = np.diff(padded)
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0] - 1
    
    for start, end in zip(starts, ends):
        if start < len(df_analisis) and end < len(df_analisis):
            t_start = df_analisis['timestamp'].iloc[start]
            t_end = df_analisis['timestamp'].iloc[end]
            duration = (t_end - t_start) * 1000
            
            if duration > 100:
                violation_groups.append((t_start, t_end, duration))
                print(f"   Violacion: {t_start:.2f}s - {t_end:.2f}s (duracion: {duration:.0f}ms)")

if not violation_groups:
    print("   No se detectaron violaciones sostenidas (>100ms)")

# ============================================
# PASO 9: GRAFICA DE FALLAS
# ============================================
print("\nGenerando grafica de eventos...")

fig, axes = plt.subplots(3, 1, figsize=(15, 10))

ax = axes[0]
ax.plot(df_analisis['timestamp'], df_analisis['accel_x_filt'], 
        label='accel_x', color='blue', linewidth=1)
ax.plot(df_analisis['timestamp'], df_analisis['accel_y_filt'], 
        label='accel_y', color='orange', linewidth=1)

for start, end, _ in nan_groups:
    ax.axvspan(start, end, color='red', alpha=0.2)
    ax.text((start+end)/2, ax.get_ylim()[1]*0.9, 'PERDIDA', 
            color='red', ha='center', fontsize=10, fontweight='bold')

ax.set_title('Senales Inerciales - Eventos de Falla')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Aceleracion (g)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.plot(df_analisis['timestamp'], df_analisis['brake_pressure'], 
        label='Freno', color='red', linewidth=1)
ax.plot(df_analisis['timestamp'], df_analisis['throttle'], 
        label='Acelerador', color='purple', linewidth=1)

for start, end, _ in violation_groups:
    ax.axvspan(start, end, color='orange', alpha=0.3)
    ax.text((start+end)/2, ax.get_ylim()[1]*0.9, 'VIOLACION', 
            color='orange', ha='center', fontsize=10, fontweight='bold')

ax.set_title('Pedales - Violaciones de Plausibilidad')
ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('Presion / %')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[2]
ax2 = ax.twinx()

ax.plot(df_analisis['timestamp'], df_analisis['g_comb'], 
        color='green', linewidth=1.5, label='G combinada')
ax2.plot(df_analisis['timestamp'], df_analisis['speed_kmph'], 
         color='gray', linewidth=1, alpha=0.7, label='Velocidad')

ax.set_xlabel('Tiempo (s)')
ax.set_ylabel('G (g)', color='green')
ax2.set_ylabel('Velocidad (km/h)', color='gray')
ax.tick_params(axis='y', labelcolor='green')
ax2.tick_params(axis='y', labelcolor='gray')
ax.set_title('G Combinada y Velocidad')
ax.grid(True, alpha=0.3)

if not np.isnan(g_max):
    ax.axhline(g_max, color='black', linestyle='--', alpha=0.5, 
               label=f'G max = {g_max:.2f} g')
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig('eventos_fallas.png', dpi=150, bbox_inches='tight')
print("   Guardada: eventos_fallas.png")
plt.show()

# ============================================
# PASO 10: REPORTE TECNICO
# ============================================
print("\n" + "="*60)
print("GENERANDO REPORTE TECNICO")
print("="*60)

vel_max = df_analisis['speed_kmph'].max()
vel_media = df_analisis['speed_kmph'].mean()
duracion = df_analisis['timestamp'].max() - df_analisis['timestamp'].min()

# Construir reporte sin usar \n dentro de f-strings
reporte = "=== REPORTE TECNICO DE ANALISIS DE TELEMETRIA ===\n\n"
reporte += "1. RESUMEN EJECUTIVO\n"
reporte += f"   - Archivo: RFAD_DATA.csv\n"
reporte += f"   - Muestras: {len(df_analisis):,}\n"
reporte += f"   - Duracion: {duracion:.1f} segundos\n"
reporte += f"   - Frecuencia: {fs:.1f} Hz\n"
reporte += f"   - Velocidad maxima: {vel_max:.1f} km/h\n"
reporte += f"   - Velocidad media: {vel_media:.1f} km/h\n"
reporte += f"   - G maxima (limpia): {g_max:.3f} g\n"
reporte += f"   - G maxima (cruda): {g_max_cruda:.3f} g\n\n"

reporte += "2. ACONDICIONAMIENTO DE SEÑAL\n"
reporte += f"   - Filtro aplicado: Butterworth pasa-bajas\n"
reporte += f"   - Frecuencia de corte: {cutoff_freq} Hz\n"
reporte += f"   - Orden: {order}\n"
reporte += f"   - Justificacion: Elimina ruido estructural de alta frecuencia (> {cutoff_freq} Hz)\n"
reporte += "   - El valor crudo es enganoso porque amplifica picos de ruido\n\n"

reporte += "3. DIAGRAMA G-G (HUELLA DE FRICCION)\n"
reporte += f"   - Asimetria detectada: {abs(asymmetry):.1f}%\n"
if abs(asymmetry) > 10:
    reporte += "   - Diagnostico: ASIMETRIA SIGNIFICATIVA (>10%)\n"
elif abs(asymmetry) > 5:
    reporte += "   - Diagnostico: ASIMETRIA MODERADA (5-10%)\n"
else:
    reporte += "   - Diagnostico: SIMETRIA ACEPTABLE (<5%)\n"
if abs(asymmetry) > 10:
    reporte += "   - Posible desbalance en suspension o alineacion\n\n"
else:
    reporte += "   - Comportamiento dentro de lo esperado\n\n"

reporte += "4. FALLAS DETECTADAS\n"
reporte += "   A) Perdida de señal (sensor inercial):\n"
reporte += f"      - Eventos: {len(nan_groups)}\n"
if nan_groups:
    for start, end, dur in nan_groups:
        reporte += f"      - {start:.2f}s a {end:.2f}s (duracion: {dur:.0f}ms)\n"
else:
    reporte += "      - No se detectaron perdidas sostenidas (>100ms)\n"

reporte += "\n   B) Violaciones de plausibilidad (freno + acelerador):\n"
reporte += f"      - Eventos: {len(violation_groups)}\n"
if violation_groups:
    for start, end, dur in violation_groups:
        reporte += f"      - {start:.2f}s a {end:.2f}s (duracion: {dur:.0f}ms)\n"
else:
    reporte += "      - No se detectaron violaciones sostenidas (>100ms)\n"

reporte += "\n5. ACCIONES RECOMENDADAS\n"
if abs(asymmetry) > 10:
    reporte += "   - Revisar sistema de suspension y alineacion (asimetria >10%)\n"
else:
    reporte += "   - Suspension dentro de parametros normales\n"
if len(nan_groups) > 0:
    reporte += "   - Verificar conexiones del sensor inercial\n"
else:
    reporte += "   - Sistema de sensores operando correctamente\n"
if len(violation_groups) > 0:
    reporte += "   - Investigar eventos de freno+acelerador\n"
else:
    reporte += "   - Sistema de pedales operando correctamente\n"
if fs < 200:
    reporte += "   - Considerar aumentar frecuencia de muestreo\n"
else:
    reporte += "   - Frecuencia de muestreo adecuada\n"

reporte += "\n6. CONCLUSION\n"
if abs(asymmetry) > 10:
    reporte += "   El analisis de telemetria revela que el vehiculo presenta una asimetria direccional que requiere atencion.\n"
    reporte += "   Se recomienda realizar revision mecanica antes de la siguiente sesion.\n"
else:
    reporte += "   El analisis de telemetria revela que el vehiculo presenta un comportamiento dinamico dentro de parametros aceptables.\n"
    reporte += "   Se sugiere mantener el monitoreo continuo.\n"
if len(nan_groups) > 0:
    reporte += "   Los sensores inerciales muestran problemas de integridad.\n"
else:
    reporte += "   La instrumentacion opera correctamente.\n"
if len(violation_groups) > 0:
    reporte += "   Se detectaron violaciones de seguridad.\n"
else:
    reporte += "   No se detectaron violaciones de seguridad.\n"

reporte += "\n7. METADATOS\n"
reporte += f"   - Fecha de analisis: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
reporte += "   - Herramientas: Python 3, Pandas, NumPy, SciPy, Matplotlib\n"

print(reporte)

with open('reporte_tecnico.txt', 'w', encoding='utf-8') as f:
    f.write(reporte)
print("   Guardado: reporte_tecnico.txt")

df_analisis.to_csv('data_procesada.csv', index=False)
print("   Guardado: data_procesada.csv")

print("\n" + "="*60)
print("ANALISIS COMPLETADO CON EXITO")
print("="*60)

print("\nARCHIVOS GENERADOS:")
print("   1. data_procesada.csv - Datos con filtro aplicado")
print("   2. reporte_tecnico.txt - Reporte tecnico")
print("   3. comparacion_filtro.png - Grafica comparativa")
print("   4. diagrama_gg.png - Diagrama G-G")
print("   5. eventos_fallas.png - Eventos de falla")