import pandas as pd
import unicodedata
import re
import difflib

# Función para limpiar texto para comparaciones exactas
def normalize_text(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'^\d+[\.\-\s]*', '', text) 
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.strip()

# Función para pasar de Nombre Apellidos -> Apellidos Nombres
def restructure_name(name):
    if pd.isna(name): return ""
    parts = str(name).strip().split()
    if len(parts) >= 3:
        surnames = " ".join(parts[-2:])
        names = " ".join(parts[:-2])
        return f"{surnames} {names}"
    return name 

# 1. Cargar la lista final corregida manualmente
# (Asegúrate de que el archivo se llame exactamente así en tu carpeta)
df_current = pd.read_csv("asistentes_sin_repetidos.csv")

# Agregamos la columna sillas_invitados y marcamos con 1
# Si es la fila separadora, le dejamos un guion
df_current['sillas_invitados'] = df_current['Nombre_Formateado'].apply(
    lambda x: '---' if 'SEPARADOR' in str(x) else 1
)

# Listas de control para evitar duplicados al revisar
# Limpiamos los correos y nombres del CSV manual para cruzarlos después
correos_actuales = [str(c).strip().lower() for c in df_current['Correo'].dropna() if str(c).strip() != '---']
nombres_actuales_norm = [normalize_text(n) for n in df_current['Nombre_Formateado'].dropna()]

# 2. Cargar la lista general de alumnos (correos)
df_alum = pd.read_csv("alumnosfasbit-evento.csv")
df_alum = df_alum.rename(columns={df_alum.columns[0]: 'Nombre_Original', df_alum.columns[1]: 'Correo'})
df_alum = df_alum.dropna(subset=['Nombre_Original'])
df_alum = df_alum.drop_duplicates(subset=['Nombre_Original']) 

faltantes = []

# 3. Identificar quiénes faltan
for _, row in df_alum.iterrows():
    correo_alum = str(row['Correo']).strip().lower()
    nombre_alum_norm = normalize_text(row['Nombre_Original'])
    
    # Verificación 1: Por correo electrónico exacto
    if correo_alum in correos_actuales and correo_alum != 'nan':
        continue # Ya está en la lista manual, lo saltamos
        
    # Verificación 2: Por similitud de nombre
    # Volteamos el nombre a "Apellidos Nombres" para que la comparación sea justa
    nombre_volteado = normalize_text(restructure_name(row['Nombre_Original']))
    
    # Buscamos si hay un nombre muy similar en la lista actual
    closest = difflib.get_close_matches(nombre_volteado, nombres_actuales_norm, n=1, cutoff=0.7)
    
    if closest:
        continue # Ya está en la lista manual (tal vez con otro correo), lo saltamos
        
    # Si pasa los filtros, significa que NO ESTÁ en las dos listas (solo en la del evento)
    nombre_final_formateado = restructure_name(row['Nombre_Original']).upper()
    
    faltantes.append({
        'Carrera': 'NO ESPECIFICADO (Faltante)',
        'Nombre_Formateado': nombre_final_formateado,
        'Correo': row['Correo'],
        'sillas_invitados': 0
    })

# 4. Procesar los faltantes si existen
if faltantes:
    df_faltantes = pd.DataFrame(faltantes)
    
    # Ordenamos a los faltantes alfabéticamente
    df_faltantes = df_faltantes.drop_duplicates(subset=['Nombre_Formateado'])
    df_faltantes = df_faltantes.sort_values(by='Nombre_Formateado').reset_index(drop=True)
    
    # Creamos un separador para indicar que los siguientes son los que no estaban en pagos
    separador_faltantes = pd.DataFrame([{
        'Carrera': '---', 
        'Nombre_Formateado': '--- SOLO EN LISTA CORREOS ---', 
        'Correo': '---',
        'sillas_invitados': '---'
    }])
    
    # Unimos la lista original, el nuevo separador y los faltantes
    df_final = pd.concat([df_current, separador_faltantes, df_faltantes], ignore_index=True)
else:
    # Si no hay faltantes, solo guardamos el original con el "1" agregado
    df_final = df_current

# 5. Exportar el resultado final
df_final.to_csv("lista_final_con_sillas.csv", index=False, encoding='utf-8')
df_final.to_excel("lista_final_con_sillas.xlsx", index=False)

print(f"Proceso completado. Se encontraron {len(faltantes)} personas que solo estaban en la lista de correos.")