import subprocess
import csv
import os
import sys
import time
import numpy as np

# Configuracion
NUM_REPETICIONES = 25  # Veces que se repite cada experimento para estabilidad
ARCHIVO_ENTRADA_C = "resultados_mpi.csv"
ARCHIVO_DATOS_FINAL = "resultado_final_graficar.csv"

def eliminar_atipicos(registros, columna='Tiempo'):
    """
    Elimina outliers usando Rango Intercuartil (IQR).
    Recibe una lista de diccionarios.
    """
    if not registros:
        return []
        
    valores = [float(r[columna]) for r in registros]
    
    Q1 = np.quantile(valores, 0.25)
    Q3 = np.quantile(valores, 0.75)
    IQR = Q3 - Q1
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR
    
    return [r for r in registros if limite_inferior <= float(r[columna]) <= limite_superior]

def ejecutar_experimentos(ejecutable, max_procs):
    print(f"Ejecutando experimentos con '{ejecutable}' hasta {max_procs} procesos.")
    print(f"Repeticiones por configuracion: {NUM_REPETICIONES}")
    print("-" * 50)
    
    # Limpiar resultados anteriores si existen
    if os.path.exists(ARCHIVO_DATOS_FINAL):
        try:
            os.remove(ARCHIVO_DATOS_FINAL)
        except OSError:
            pass

    if os.path.exists(ARCHIVO_ENTRADA_C):
        try:
            os.remove(ARCHIVO_ENTRADA_C)
        except OSError:
            pass

    datos_crudos = []
    tiempo_inicio = time.time()

    # Bucle principal: varia el numero de procesos de 1 a max_procs
    for n in range(1, max_procs + 1):
        print(f"\n[Configuracion: {n} Procesos]")
        
        # Bucle de repeticiones para estadistica
        for corrida in range(NUM_REPETICIONES):
            print(f"  Corrida {corrida + 1}/{NUM_REPETICIONES}...", end='\r')
            
            try:
                # Ejecutar comando MPI: mpiexec -n <n> <ejecutable>
                # Ocultamos stdout/stderr para no ensuciar la consola, solo nos importa el CSV
                cmd = ['mpiexec', '-n', str(n), ejecutable]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            except subprocess.CalledProcessError as e:
                print(f"\n  Error ejecutando comando: {e}")
                continue 
            except Exception as e:
                print(f"\n  Ocurrio un error: {e}")
                continue 
        
        print("") # Salto de linea al terminar la barra de progreso

    tiempo_total = time.time() - tiempo_inicio
    print("-" * 50)
    print(f"Recoleccion de datos finalizada en {tiempo_total:.2f}s.")
    
    # Leer el archivo acumulado generado por el programa C
    if os.path.exists(ARCHIVO_ENTRADA_C):
        with open(ARCHIVO_ENTRADA_C, mode='r', newline='') as infile:
            reader = csv.DictReader(infile)
            for fila in reader:
                # Filtrar cabeceras repetidas (el C escribe cabecera en cada ejecucion)
                if fila['NMuestras'] == 'NMuestras':
                    continue
                datos_crudos.append(fila)
    else:
        print(f"Error: No se encontro {ARCHIVO_ENTRADA_C} tras la ejecucion.")
        return
    
    if not datos_crudos:
        print("Error: No se recolectaron datos. Revisa tu ejecutable y MPI.")
        return

    print(f"Total de registros crudos: {len(datos_crudos)}")

    # Procesamiento: Eliminar atipicos y promediar
    print("Procesando datos (Eliminando outliers y promediando)...")
    
    # Agrupar por (NProcesos, NMuestras)
    datos_agrupados = {}
    for registro in datos_crudos:
        clave = (int(registro['NProcesos']), int(registro['NMuestras']))
        if clave not in datos_agrupados:
            datos_agrupados[clave] = []
        datos_agrupados[clave].append(registro)

    filas_promediadas = []
    for (n_procs, n_muestras), grupo in datos_agrupados.items():
        # Filtrar outliers basado en 'Tiempo'
        grupo_limpio = eliminar_atipicos(grupo, 'Tiempo')
        
        if not grupo_limpio:
            continue 
        
        # Calcular promedios
        avg_tiempo = np.mean([float(r['Tiempo']) for r in grupo_limpio])
        avg_pi = np.mean([float(r['Pi_Estimado']) for r in grupo_limpio])
        avg_error = np.mean([float(r['Error']) for r in grupo_limpio])
        
        filas_promediadas.append({
            'NMuestras': n_muestras,
            'NProcesos': n_procs,
            'Tiempo': avg_tiempo,
            'Pi_Estimado': avg_pi,
            'Error': avg_error
        })

    # Calcular SpeedUp (T1 / Tp)
    # Primero identificamos el tiempo serial (T1) para cada tamaño de muestra
    tiempos_serial = {}
    for fila in filas_promediadas:
        if fila['NProcesos'] == 1:
            tiempos_serial[fila['NMuestras']] = fila['Tiempo']

    # Ahora calculamos el SpeedUp para cada fila
    for fila in filas_promediadas:
        t1 = tiempos_serial.get(fila['NMuestras'])
        if t1 is not None and fila['Tiempo'] > 0:
            fila['SpeedUp'] = t1 / fila['Tiempo']
        else:
            fila['SpeedUp'] = 0.0 # Valor por defecto si no se puede calcular

    # Ordenar para que el CSV final quede prolijo
    datos_finales = sorted(filas_promediadas, key=lambda x: (x['NProcesos'], x['NMuestras']))
    
    # Guardar dataset final
    with open(ARCHIVO_DATOS_FINAL, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['NMuestras', 'NProcesos', 'Tiempo', 'SpeedUp', 'Pi_Estimado', 'Error'])
        writer.writeheader()
        writer.writerows(datos_finales)
        
    print(f"EXITO: Resultados promediados guardados en '{ARCHIVO_DATOS_FINAL}'")
    print("Ahora puedes ejecutar 'visualizar_resultados.py' para graficar.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python ejecutar_experimentos.py <nombre_ejecutable> <max_procesos>")
        print("Ejemplo: python ejecutar_experimentos.py a.out 6")
        sys.exit(1)
    
    nombre_exe = sys.argv[1]
    try:
        max_procesos = int(sys.argv[2])
    except ValueError:
        print("Error: El maximo de procesos debe ser un entero.")
        sys.exit(1)
        
    ejecutar_experimentos(nombre_exe, max_procesos)
