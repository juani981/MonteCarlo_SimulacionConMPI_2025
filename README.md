# Estimación Paralela de Pi mediante Monte Carlo y MPI

## Resumen del Proyecto

El presente trabajo aborda el uso de un algoritmo paralelo para la estimación del número Pi ($\pi$) utilizando el método de Monte Carlo. La paralelización se realiza mediante el estándar **MPI (Message Passing Interface)**, permitiendo distribuir la carga computacional (generación de puntos aleatorios y verificación de su posición) entre múltiples procesos, implementado en lenguaje C.

El objetivo principal es estudiar el comportamiento del sistema en términos de **rendimiento (Speedup y Eficiencia)** y **precisión numérica (Convergencia y Error)** al variar tanto el tamaño del problema (número de muestras) como el número de procesos.

## Objetivos

1.  **Análisis de Convergencia**: Verificar experimentalmente que el error absoluto de la estimación disminuye conforme aumenta el número de muestras ($N$).
2.  **Evaluación de Escalabilidad**:
    - **Speedup**: Medir la mejora en tiempo de ejecucion obtenida al aumentar el número de procesos respecto a la ejecución serial con 1 unico proceso.
    - **Eficiencia**: Analizar qué tan bien se aprovechan los recursos adicionales, identificando cuellos de botella (por ej: overhead de comunicación, desbalanceo de carga).
3.  - **Significancia Estadística**: Utilizar múltiples repeticiones por cada configuración y desechar el efecto de outliers para asegurar resultados fiables.

## Estructura del Repositorio

- `calculo_pi_mpi.c`: Implementa el programa paralelo usando MPI, define un arreglo con la cantidad de puntos que se van a simular y ejecuta una a una las simulaciones, devuelve los resultados en CSV.
- `ejecutar_experimentos.py`: Script de automatización. Ejecuta el binario C (pasado por parametro) N veces (configurable desde el codigo), aumentando la cantidad de procesos P hasta la cantidad deseada (pasado por parametro), haciendo NxP ejecuciones, desecha outliers y genera un CSV con los promedios para cada cantidad de procesos.
- `visualizar_resultados.py`: Genera gráficos para visualizar los resultados (Convergencia, Speedup, Eficiencia) a partir de los datos procesados anteriormente.
- `resultados_mpi.csv`: Datos crudos generados por el programa C.
- `resultado_final_graficar.csv`: Datos procesados listos para visualización.

---

## Instrucciones de Ejecución Local

### Prerrequisitos

- Compilador C compatible con MPI (`mpicc` OpenMPI).
- Python 3.x con librerías: `numpy`, `matplotlib`.

### Pasos

1.  **Compilación**:

    ```bash
    mpicc calculo_pi_mpi.c -o mpi_pi
    ```

2.  **Ejecución de Experimentos**:
    Utilice el script de Python para generar los datos. Debe indicar el nombre del ejecutable de MPI y el número máximo de procesos a utilizar.

    ```bash
    # Sintaxis: python3 ejecutar_experimentos.py <ejecutable> <max_procesos>
    python3 ejecutar_experimentos.py mpi_pi 6
    ```

    _Esto ejecutará configuraciones desde 1 hasta 6 procesos, con 25 repeticiones cada una._

3.  **Visualización**:
    Una vez finalizado el paso anterior, genere los gráficos:
    ```bash
    python visualizar_resultados.py
    ```
    Se generarán las imágenes: `plot_convergencia_y_error.png`, `plot_speedup.png`, `plot_eficiencia.png`.

---

## Ejecución en Cluster (HPC)

Para ejecutar este proyecto en un cluster remoto, se debe transferir el código fuente y los scripts de soporte.

### 1. Transferencia de Archivos (SCP)

Desde su máquina local, utilice `scp` para subir los archivos necesarios al directorio de trabajo en el cluster (reemplace `usuario@cluster.mi.org` y la ruta de destino según corresponda).

```bash
# Subir todo el directorio del proyecto (recursivo)
scp -r /ruta/local/MiProyecto usuario@cluster.mi.org:~/

# O subir archivos individuales
scp calculo_pi_mpi.c ejecutar_experimentos.py visualizar_resultados.py usuario@cluster.edu.ar:~/Proyecto/
```

### 2. Conexión y Compilación

Conéctese al cluster:

```bash
ssh usuario@cluster.edu.ar
mkdir /Proyecto
cd ~/Proyecto
```

Siga las instrucciones de compilacion y ejecucion anteriores.

**Ejemplo**:
Despues de compilar el programa en C:

```bash
python3 ejecutar_experimentos.py mpi_pi 28
```

### 3. Recuperación de Resultados

Una vez finalizado, descargue los resultados (CSV y gráficos generados) a su máquina local:

```bash
# Desde su máquina local
scp usuario@cluster.edu.ar:~/Proyecto/*.csv .
scp usuario@cluster.edu.ar:~/Proyecto/*.png .
```
