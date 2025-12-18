
#
# Convierte todos los archivos .heic a .jpeg en la carpeta especificada,
# luego mueve los .heic originales a una subcarpeta llamada HEIC.
# Mantiene la calidad y dimensiones originales  
#
# Uso:
# pip install pillow pillow-heif
# python heic-to-jpeg.py
#


import os
import shutil
from PIL import Image
import pillow_heif

def convert_heic_to_jpeg(input_folder='.', quality=95):
    """
    Convierte todos los archivos .heic a .jpeg en la carpeta especificada,
    luego mueve los .heic originales y el script a una subcarpeta llamada HEIC.
    """
    pillow_heif.register_heif_opener()
    
    # Obtener nombre del script actual
    script_name = os.path.basename(__file__)
    
    heic_files = [f for f in os.listdir(input_folder) 
                  if f.lower().endswith('.heic')]
    
    if not heic_files:
        print("No se encontraron archivos .heic en la carpeta especificada")
        return
    
    print(f"Se encontraron {len(heic_files)} archivos .heic")
    print(f"Usando calidad JPEG = {quality}\n")
    
    converted_files = []
    failed_files = []
    
    # Convertir archivos
    for filename in heic_files:
        try:
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + '.jpeg'
            output_path = os.path.join(input_folder, output_filename)
            
            image = Image.open(input_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            print(f"✓ Convertido: {filename} -> {output_filename}")
            converted_files.append(filename)
            
        except Exception as e:
            print(f"✗ Error al convertir {filename}: {str(e)}")
            failed_files.append(filename)
            continue
    
    # Crear carpeta HEIC y mover archivos
    if converted_files:
        heic_folder = os.path.join(input_folder, 'HEIC')
        os.makedirs(heic_folder, exist_ok=True)
        
        print(f"\nMoviendo {len(converted_files)} archivos .heic a carpeta HEIC...")
        
        for filename in converted_files:
            try:
                src = os.path.join(input_folder, filename)
                dst = os.path.join(heic_folder, filename)
                shutil.move(src, dst)
                print(f"✓ Movido: {filename}")
            except Exception as e:
                print(f"✗ Error al mover {filename}: {str(e)}")
        
        # Mover el script a la carpeta HEIC
        try:
            script_src = os.path.join(input_folder, script_name)
            script_dst = os.path.join(heic_folder, script_name)
            shutil.move(script_src, script_dst)
            print(f"\n✓ Script movido: {script_name} -> HEIC/{script_name}")
        except Exception as e:
            print(f"\n✗ Error al mover el script: {str(e)}")
    
    # Resumen
    print("\n" + "="*50)
    print(f"Conversión completada:")
    print(f"  - Convertidos exitosamente: {len(converted_files)}")
    print(f"  - Errores: {len(failed_files)}")
    if failed_files:
        print(f"  - Archivos con error: {', '.join(failed_files)}")
    print("="*50)

if __name__ == "__main__":
    print("Iniciando conversión de HEIC a JPEG...\n")
    convert_heic_to_jpeg('.', quality=95)