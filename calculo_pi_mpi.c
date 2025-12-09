#define _USE_MATH_DEFINES
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

int main(int argc, char** argv) {
    
    int rango, n_procs;
    // Puntos a evaluar. Nota: Despues de 10^7 falla en PC local, probar mas en servidor (probado con exito hasta 10^9).
    long long puntos_prueba[] = {100, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000};
    long long cant_muestras = sizeof(puntos_prueba) / sizeof(puntos_prueba[0]);
    long long total_dentro_circulo = 0; 

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rango);
    MPI_Comm_size(MPI_COMM_WORLD, &n_procs);

    FILE *archivo_csv = NULL;
    
    // El proceso ROOT se encarga de crear el archivo y escribir el titulo de las filas.
    if (rango == 0) {
        archivo_csv = fopen("resultados_mpi.csv", "a");
        if (archivo_csv == NULL) {
            fprintf(stderr, "Error creando el archivo resultados_mpi.csv\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        
        fprintf(archivo_csv, "NMuestras,Tiempo,NProcesos,Pi_Estimado,Error\n");
    }   

    // Iteramos por cada valor de puntos_prueba 
    for (int i = 0; i < cant_muestras; i++) {
        long long total_puntos = puntos_prueba[i];
        double tiempo_paralelo = 0.0;
        
        double inicio_paralelo = MPI_Wtime();

        // Division del trabajo
        long long puntos_por_proc = total_puntos / n_procs;
        long long resto_division = total_puntos % n_procs;
        long long local_dentro_circulo = 0;

        // Repartir el resto entre los primeros procesos
        if (rango < resto_division) {
            puntos_por_proc++;
        }

        // Asignacion dinamica de memoria para los puntos
        double *x = (double *)malloc(puntos_por_proc * sizeof(double));
        double *y = (double *)malloc(puntos_por_proc * sizeof(double));

        if (x == NULL || y == NULL) {
            fprintf(stderr, "Fallo de memoria en rango %d. Solicitados: %lld\n", rango, puntos_por_proc);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        // Semilla unica para cada proceso para intentar evitar numeros repetidos entre procesos
        unsigned int semilla = time(NULL) + rango; 
        srand(semilla);

        // Generar puntos aleatorios en [-1, 1] y contar los que caen dentro del circulo unitario
        for (long long j = 0; j < puntos_por_proc; j++) {
            x[j] = ((double)rand() / RAND_MAX) * 2.0 - 1.0;
            y[j] = ((double)rand() / RAND_MAX) * 2.0 - 1.0;
            
            // Verificar si el punto esta dentro del circulo
            if (x[j] * x[j] + y[j] * y[j] <= 1.0) {
                local_dentro_circulo++;
            }
        }
        
        
        free(x);
        free(y);
        
        // Sumar los resultados parciales de todos los procesos en el proceso raiz
        MPI_Reduce(&local_dentro_circulo, &total_dentro_circulo, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);
        
        // El raiz ya tiene los resultado, calcula PI, el error y guarda en el CSV
        if (rango == 0) {
            double pi_estimado = 4.0 * (double)total_dentro_circulo / (double)total_puntos;
            double error_abs = fabs(pi_estimado - M_PI);
            tiempo_paralelo = MPI_Wtime() - inicio_paralelo;
            
            fprintf(archivo_csv, "%lld,%.15f,%d,%.15f,%.15f\n", total_puntos, tiempo_paralelo, n_procs, pi_estimado, error_abs);
        }
    }
//Cierra el archivo CSV en el proceso ROOT solo despues de haber pasado por todos los cant_puntos
    if (rango == 0) {
        fclose(archivo_csv);
    }
    
    MPI_Finalize();
    return 0;
}
