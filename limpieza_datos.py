import pandas as pd
import unicodedata
import re
import difflib

# Función para limpiar texto, quitar tildes y números de lista
def normalize_text(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'^\d+[\.\-\s]*', '', text) 
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.strip()

# Función para convertir "Nombre(s) Apellidos" a "Apellidos Nombre(s)"
def restructure_name(name):
    if pd.isna(name): return ""
    parts = str(name).strip().split()
    if len(parts) >= 3:
        surnames = " ".join(parts[-2:])
        names = " ".join(parts[:-2])
        return f"{surnames} {names}"
    return name 

# 1. Cargar la lista general de alumnos
df_alum = pd.read_csv("alumnosfasbit-evento.csv")
# Renombramos las columnas genéricamente porque incluye a ambas carreras
df_alum = df_alum.rename(columns={df_alum.columns[0]: 'Nombre_Original', df_alum.columns[1]: 'Correo'})
df_alum = df_alum.dropna(subset=['Nombre_Original'])
df_alum['norm_name'] = df_alum['Nombre_Original'].apply(normalize_text)

# 2. Cargar la lista de graduación (Excel)
df_grad = pd.read_excel("graduacion.xlsx", sheet_name='graduacion')

# 3. Función modular para procesar cualquier carrera
def process_career(career_col, career_name):
    df_c = df_grad[[career_col]].dropna(subset=[career_col])
    df_c['norm_name'] = df_c[career_col].apply(normalize_text)
    
    matched_data = []
    alum_norm_list = df_alum['norm_name'].tolist()
    
    for _, row in df_c.iterrows():
        name_grad = row['norm_name']
        if not name_grad: continue
        
        # Intento 1: Match exacto
        exact_match = df_alum[df_alum['norm_name'] == name_grad]
        
        if not exact_match.empty:
            matched_row = exact_match.iloc[0]
            matched_data.append({
                'Carrera': career_name,
                'Nombre_Formateado': restructure_name(matched_row['Nombre_Original']).upper(),
                'Correo': matched_row['Correo']
            })
        else:
            # Intento 2: Match difuso (Fuzzy matching) para "errores de dedo"
            closest = difflib.get_close_matches(name_grad, alum_norm_list, n=1, cutoff=0.6)
            if closest:
                matched_row = df_alum[df_alum['norm_name'] == closest[0]].iloc[0]
                matched_data.append({
                    'Carrera': career_name,
                    'Nombre_Formateado': restructure_name(matched_row['Nombre_Original']).upper(),
                    'Correo': matched_row['Correo']
                })
            else:
                # Si no se encuentra correo, conservar el nombre limpio de la lista de graduación
                clean_name = re.sub(r'^\d+[\.\-\s]*', '', str(row[career_col])).strip()
                matched_data.append({
                    'Carrera': career_name,
                    'Nombre_Formateado': restructure_name(clean_name).upper(),
                    'Correo': 'No encontrado'
                })
                
    df_res = pd.DataFrame(matched_data)
    # Ordenar alfabéticamente dentro de la misma carrera
    if not df_res.empty:
        df_res = df_res.sort_values(by='Nombre_Formateado').reset_index(drop=True)
    return df_res

# 4. Procesar y ordenar Biología e Ingeniería por separado
df_bio = process_career('BIOLOGIA', 'BIOLOGÍA')
df_ing = process_career('INGENIERIA', 'INGENIERÍA')

# 5. Crear una fila separadora para cumplir con la división solicitada
separator = pd.DataFrame([{'Carrera': '---', 'Nombre_Formateado': '--- SEPARADOR ---', 'Correo': '---'}])

# 6. Unir los bloques: Biología primero, separador, Ingeniería después
df_final = pd.concat([df_bio, separator, df_ing], ignore_index=True)

# 7. Exportar los archivos finales
df_final.to_csv("asistentes_completos_ordenados.csv", index=False, encoding='utf-8')
df_final.to_excel("asistentes_completos_ordenados.xlsx", index=False)

print("¡Archivos completos generados con éxito!")