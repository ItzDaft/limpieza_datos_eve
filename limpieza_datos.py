import pandas as pd
import unicodedata
import re
import difflib

def normalize_text(text):
    if pd.isna(text): return ""
    text = str(text).strip()
    text = re.sub(r'^\d+[\.\-\s]*', '', text) 
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.strip()

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
df_alum = df_alum.rename(columns={df_alum.columns[0]: 'Nombre_Original', df_alum.columns[1]: 'Correo'})
df_alum = df_alum.dropna(subset=['Nombre_Original'])
# NUEVO: Eliminar posibles repetidos en la lista base
df_alum = df_alum.drop_duplicates(subset=['Nombre_Original']) 
df_alum['norm_name'] = df_alum['Nombre_Original'].apply(normalize_text)

# 2. Cargar la lista de graduación (Excel)
df_grad = pd.read_excel("graduacion.xlsx", sheet_name='graduacion')

def process_career(career_col, career_name):
    df_c = df_grad[[career_col]].dropna(subset=[career_col])
    # NUEVO: Eliminar duplicados directos en la lista de graduación (dobles registros)
    df_c = df_c.drop_duplicates(subset=[career_col])
    df_c['norm_name'] = df_c[career_col].apply(normalize_text)
    
    matched_data = []
    alum_norm_list = df_alum['norm_name'].tolist()
    
    for _, row in df_c.iterrows():
        name_grad = row['norm_name']
        if not name_grad: continue
        
        exact_match = df_alum[df_alum['norm_name'] == name_grad]
        
        if not exact_match.empty:
            matched_row = exact_match.iloc[0]
            matched_data.append({
                'Carrera': career_name,
                'Nombre_Formateado': restructure_name(matched_row['Nombre_Original']).upper(),
                'Correo': matched_row['Correo']
            })
        else:
            closest = difflib.get_close_matches(name_grad, alum_norm_list, n=1, cutoff=0.6)
            if closest:
                matched_row = df_alum[df_alum['norm_name'] == closest[0]].iloc[0]
                matched_data.append({
                    'Carrera': career_name,
                    'Nombre_Formateado': restructure_name(matched_row['Nombre_Original']).upper(),
                    'Correo': matched_row['Correo']
                })
            else:
                clean_name = re.sub(r'^\d+[\.\-\s]*', '', str(row[career_col])).strip()
                matched_data.append({
                    'Carrera': career_name,
                    'Nombre_Formateado': restructure_name(clean_name).upper(),
                    'Correo': 'No encontrado'
                })
                
    df_res = pd.DataFrame(matched_data)
    if not df_res.empty:
        # NUEVO: Filtro final definitivo para evitar repetidos por cualquier cruce
        df_res = df_res.drop_duplicates(subset=['Nombre_Formateado'], keep='first')
        df_res = df_res.sort_values(by='Nombre_Formateado').reset_index(drop=True)
    return df_res

# 3. Procesar
df_bio = process_career('BIOLOGIA', 'BIOLOGÍA')
df_ing = process_career('INGENIERIA', 'INGENIERÍA')

# 4. Unir
separator = pd.DataFrame([{'Carrera': '---', 'Nombre_Formateado': '--- SEPARADOR ---', 'Correo': '---'}])
df_final = pd.concat([df_bio, separator, df_ing], ignore_index=True)

# 5. Exportar
df_final.to_csv("asistentes_sin_repetidos.csv", index=False, encoding='utf-8')
df_final.to_excel("asistentes_sin_repetidos.xlsx", index=False)

print("¡Archivos generados y limpiados con éxito!")