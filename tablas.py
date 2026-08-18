import pandas as pd
from openpyxl.utils import get_column_letter

# Nombre de tu archivo de entrada y el de salida
archivo_entrada = "lista_final_con_sillas.csv"
archivo_salida = "tabla_asistentes_final.xlsx"

try:
    # 1. Leer el archivo CSV
    df = pd.read_csv(archivo_entrada)
    
    # 2. Crear un "Writer" de Excel usando openpyxl
    with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
        # Exportar el DataFrame a la primera hoja de Excel
        df.to_excel(writer, index=False, sheet_name='Asistentes Evento')
        
        # 3. Ajustar el ancho de las columnas automáticamente (Estética de Tabla)
        worksheet = writer.sheets['Asistentes Evento']
        
        for idx, col in enumerate(df.columns):
            # Calcular la longitud máxima de los datos en la columna (incluyendo el título)
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            
            # Obtener la letra de la columna en Excel (A, B, C, D...)
            letra_columna = get_column_letter(idx + 1)
            
            # Asignar el ancho calculado
            worksheet.column_dimensions[letra_columna].width = max_len

    print(f"¡Éxito! Tu tabla de Excel ha sido generada y guardada como: {archivo_salida}")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{archivo_entrada}'. Asegúrate de que esté en la misma carpeta que este script.")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")