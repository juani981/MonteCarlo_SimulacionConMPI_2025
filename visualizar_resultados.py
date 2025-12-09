import csv
import matplotlib.pyplot as plt
import os
import numpy as np

ARCHIVO_DATOS = 'resultado_final_graficar.csv'

def generar_graficos():
    print("Generando graficos...")
    
    if not os.path.exists(ARCHIVO_DATOS):
        print(f"Error: No se encontro {ARCHIVO_DATOS}. Ejecuta primero el script de experimentos.")
        return

    # Cargar datos
    datos = []
    with open(ARCHIVO_DATOS, mode='r') as infile:
        reader = csv.DictReader(infile)
        for fila in reader:
            fila['NMuestras'] = int(fila['NMuestras'])
            fila['Tiempo'] = float(fila['Tiempo'])
            fila['NProcesos'] = int(fila['NProcesos'])
            fila['Pi_Estimado'] = float(fila['Pi_Estimado'])
            fila['Error'] = float(fila['Error'])
            datos.append(fila)
    
    if not datos:
        print("Error: El archivo CSV esta vacio.")
        return

    # --- 1. Grafico de Convergencia (Pi_Estimado vs NMuestras) ---
    # Usamos NProcesos=1 como base
    datos_serial = [r for r in datos if r['NProcesos'] == 1]
    
    if datos_serial:
        datos_serial.sort(key=lambda r: r['NMuestras'])
        
        muestras = [r['NMuestras'] for r in datos_serial]
        pi_estimado = [r['Pi_Estimado'] for r in datos_serial]
        error = [r['Error'] for r in datos_serial]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
        fig.suptitle('Convergencia de la Estimación de Pi (NProcesos=1)', fontsize=16)

        # Subplot 1: Estimacion
        ax1.plot(muestras, pi_estimado, marker='o', linestyle='-')
        ax1.axhline(y=np.pi, color='r', linestyle='--', label='Valor Real de Pi')
        ax1.set_xscale('log')
        ax1.set_title('Estimación de Pi vs. Número de Muestras')
        ax1.set_xlabel('Número de Muestras (N)')
        ax1.set_ylabel('Pi Estimado')
        ax1.grid(True, which="both", linestyle='--', linewidth=0.5)
        ax1.legend()
        
        # Subplot 2: Error
        ax2.plot(muestras, error, marker='s', linestyle='-', color='C1')
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax2.set_title('Error Absoluto vs. Número de Muestras')
        ax2.set_xlabel('Número de Muestras (N)')
        ax2.set_ylabel('Error Absoluto (escala log)')
        ax2.grid(True, which="both", linestyle='--', linewidth=0.5)
        
        ruta_salida = 'plot_convergencia_y_error.png'
        plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
        print(f"  Guardado: {ruta_salida}")
        plt.close(fig)
    else:
        print("  Aviso: No hay datos para NProcesos=1, saltando grafico de convergencia.")

    # --- 2. Grafico de Speedup ---
    tiempos_serial = {r['NMuestras']: r['Tiempo'] for r in datos if r['NProcesos'] == 1}
    if not tiempos_serial:
        print("  Error: No se encontro linea base (NProcesos=1) para calcular Speedup.")
        return

    datos_speedup = []
    for registro in datos:
        n_muestras = registro['NMuestras']
        if n_muestras in tiempos_serial:
            tiempo_base = tiempos_serial[n_muestras]
            speedup = tiempo_base / registro['Tiempo']
            eficiencia = speedup / registro['NProcesos']
            datos_speedup.append({**registro, 'Speedup': speedup, 'Eficiencia': eficiencia})

    # Agrupar por Muestras
    datos_graficar_agrupados = {}
    for registro in datos_speedup:
        clave = registro['NMuestras']
        if clave not in datos_graficar_agrupados:
            datos_graficar_agrupados[clave] = []
        datos_graficar_agrupados[clave].append(registro)
    
    plt.figure(figsize=(10, 6))
    
    muestras_unicas = sorted(datos_graficar_agrupados.keys())
    colores = plt.cm.viridis(np.linspace(0, 1, len(muestras_unicas)))
    
    for i, muestra in enumerate(muestras_unicas):
        subconjunto = sorted(datos_graficar_agrupados[muestra], key=lambda r: r['NProcesos'])
        eje_x_procs = [r['NProcesos'] for r in subconjunto]
        eje_y_speedup = [r['Speedup'] for r in subconjunto]
        plt.plot(eje_x_procs, eje_y_speedup, marker='o', linestyle='-', label=f'N={muestra}', color=colores[i])

    # Linea ideal
    todos_procs = sorted(list(set(r['NProcesos'] for r in datos)))
    max_procs = max(todos_procs) if todos_procs else 1
    plt.plot([1, max_procs], [1, max_procs], 'k--', label='Ideal (y=x)')
    
    plt.xlabel('Numero de Procesos')
    plt.ylabel('Speedup')
    plt.title('Speedup vs Numero de Procesos')
    plt.legend(title='Muestras')
    plt.grid(True, linestyle='--', alpha=0.7)
    if todos_procs: plt.xticks(todos_procs)
    
    ruta_salida = 'plot_speedup.png'
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    print(f"  Guardado: {ruta_salida}")
    plt.close()
    
    # --- 3. Grafico de Eficiencia ---
    plt.figure(figsize=(10, 6))
    
    for i, muestra in enumerate(muestras_unicas):
        subconjunto = sorted(datos_graficar_agrupados[muestra], key=lambda r: r['NProcesos'])
        eje_x_procs = [r['NProcesos'] for r in subconjunto]
        eje_y_eficiencia = [r['Eficiencia'] for r in subconjunto]
        plt.plot(eje_x_procs, eje_y_eficiencia, marker='s', linestyle='-', label=f'N={muestra}', color=colores[i])
        
    plt.axhline(1.0, color='red', linestyle='--', label='Ideal')
    
    plt.xlabel('Numero de Procesos')
    plt.ylabel('Eficiencia')
    plt.title('Eficiencia Paralela (Speedup / N)')
    plt.legend(title='Muestras')
    plt.grid(True, linestyle='--', alpha=0.7)
    if todos_procs: plt.xticks(todos_procs)
    plt.ylim(0, 1.2)
    
    ruta_salida = 'plot_eficiencia.png'
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    print(f"  Guardado: {ruta_salida}")
    plt.close()

if __name__ == "__main__":
    generar_graficos()
