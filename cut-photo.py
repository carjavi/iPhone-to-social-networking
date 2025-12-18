import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sys
import shutil

# Extensiones de imagen soportadas
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
BACKUP_FOLDER = "OLD_image"

class ImageCropper:
    def __init__(self, root, image_paths):
        self.root = root
        self.image_paths = image_paths
        self.current_index = 0
        
        # Crear carpeta de respaldo si no existe
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)
            print(f"Carpeta creada: {BACKUP_FOLDER}")
        
        self.root.title("Recortador de Fotos - cut-photo.py")
        self.root.geometry("800x600")
        self.root.configure(bg='black')

        # Variables de estado
        self.original_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        
        # Variables del recuadro
        self.crop_x = 0
        self.crop_y = 0
        self.crop_size = 0

        # Canvas
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bindings
        self.root.bind("<Left>", lambda e: self.move_crop(-10, 0))
        self.root.bind("<Right>", lambda e: self.move_crop(10, 0))
        self.root.bind("<Up>", lambda e: self.move_crop(0, -10))
        self.root.bind("<Down>", lambda e: self.move_crop(0, 10))
        self.root.bind("<Shift-Left>", lambda e: self.move_crop(-1, 0))
        self.root.bind("<Shift-Right>", lambda e: self.move_crop(1, 0))
        self.root.bind("<Shift-Up>", lambda e: self.move_crop(0, -1))
        self.root.bind("<Shift-Down>", lambda e: self.move_crop(0, 1))
        
        self.root.bind("<Return>", self.save_and_next)
        self.root.bind("<Escape>", self.close_app)

        # Cargar primera imagen
        self.load_next_image()

    def load_next_image(self):
        if self.current_index >= len(self.image_paths):
            messagebox.showinfo("Finalizado", "¡Has terminado de recortar todas las fotos!")
            self.cleanup_and_exit()
            return

        self.current_image_path = self.image_paths[self.current_index]
        
        try:
            self.original_image = Image.open(self.current_image_path)
            
            # Corregir orientación EXIF
            try:
                from PIL import ExifTags, ImageOps
                self.original_image = ImageOps.exif_transpose(self.original_image)
            except:
                pass

            # Inicializar recorte
            w, h = self.original_image.size
            self.crop_size = min(w, h)
            self.crop_x = (w - self.crop_size) // 2
            self.crop_y = (h - self.crop_size) // 2

            self.update_display()
            self.root.title(f"Editando ({self.current_index + 1}/{len(self.image_paths)}): {os.path.basename(self.current_image_path)} - [ENTER] Guardar | [ESC] Salir")

        except Exception as e:
            print(f"Error cargando {self.current_image_path}: {e}")
            self.current_index += 1
            self.load_next_image()

    def update_display(self):
        if not self.original_image: return

        canvas_width = self.root.winfo_width()
        canvas_height = self.root.winfo_height()
        if canvas_width <= 1: canvas_width = 800
        if canvas_height <= 1: canvas_height = 600

        img_w, img_h = self.original_image.size
        scale_w = canvas_width / img_w
        scale_h = canvas_height / img_h
        self.scale_factor = min(scale_w, scale_h) * 0.9

        new_w = int(img_w * self.scale_factor)
        new_h = int(img_h * self.scale_factor)

        resized_img = self.original_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")
        x_offset = (canvas_width - new_w) // 2
        y_offset = (canvas_height - new_h) // 2
        
        self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.photo_image)

        # Dibujar recuadro
        rect_x1 = x_offset + (self.crop_x * self.scale_factor)
        rect_y1 = y_offset + (self.crop_y * self.scale_factor)
        rect_x2 = rect_x1 + (self.crop_size * self.scale_factor)
        rect_y2 = rect_y1 + (self.crop_size * self.scale_factor)

        self.canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, outline="red", width=3)

    def move_crop(self, dx, dy):
        img_w, img_h = self.original_image.size
        new_x = self.crop_x + dx
        new_y = self.crop_y + dy

        if new_x < 0: new_x = 0
        if new_y < 0: new_y = 0
        if new_x + self.crop_size > img_w: new_x = img_w - self.crop_size
        if new_y + self.crop_size > img_h: new_y = img_h - self.crop_size

        self.crop_x = new_x
        self.crop_y = new_y
        self.update_display()

    def backup_original_image(self):
        """Crea una copia de la imagen original en OLD_image con sufijo _old"""
        try:
            filename = os.path.basename(self.current_image_path)
            name, ext = os.path.splitext(filename)
            
            # Nombre nuevo: foto_old.jpg
            backup_name = f"{name}_old{ext}"
            backup_path = os.path.join(BACKUP_FOLDER, backup_name)
            
            # Copiar archivo preservando metadatos
            shutil.copy2(self.current_image_path, backup_path)
            print(f"Backup creado: {backup_path}")
            return True
        except Exception as e:
            print(f"Error creando backup: {e}")
            return False

    def save_and_next(self, event=None):
        if not self.original_image: return

        # 1. Hacer Backup ANTES de modificar
        self.backup_original_image()

        # 2. Recortar
        box = (self.crop_x, self.crop_y, self.crop_x + self.crop_size, self.crop_y + self.crop_size)
        cropped_img = self.original_image.crop(box)

        # 3. Guardar (Sobrescribir original)
        try:
            img_format = self.original_image.format
            if img_format == 'JPEG':
                cropped_img.save(self.current_image_path, quality="keep", subsampling=0)
            else:
                cropped_img.save(self.current_image_path)
            print(f"Imagen recortada guardada: {self.current_image_path}")
        except Exception as e:
            print(f"Error guardando (fallback): {e}")
            cropped_img.save(self.current_image_path, quality=95)

        self.current_index += 1
        self.load_next_image()

    def close_app(self, event=None):
        self.cleanup_and_exit()

    def cleanup_and_exit(self):
        """Cierra la ventana y mueve el script a OLD_image"""
        self.root.destroy()
        
        try:
            # Obtener ruta del script actual
            current_script_path = os.path.abspath(sys.argv[0])
            script_filename = os.path.basename(current_script_path)
            
            # Definir destino
            destination_path = os.path.join(BACKUP_FOLDER, script_filename)
            
            # Mover el script
            print(f"Moviendo script a: {destination_path}")
            shutil.move(current_script_path, destination_path)
            
        except Exception as e:
            print(f"No se pudo mover el script (puede que esté bloqueado por el sistema): {e}")
        
        sys.exit()

def get_images_to_process():
    current_dir = os.getcwd()
    all_files = os.listdir(current_dir)
    images_to_process = []

    print(f"Escaneando carpeta: {current_dir}")

    for file in all_files:
        if file.lower().endswith(VALID_EXTENSIONS):
            full_path = os.path.join(current_dir, file)
            try:
                with Image.open(full_path) as img:
                    w, h = img.size
                    # Solo procesar si NO es cuadrada
                    if abs(w - h) > 1:
                        images_to_process.append(full_path)
            except Exception as e:
                pass

    return images_to_process

if __name__ == "__main__":
    images = get_images_to_process()

    if not images:
        # Si no hay imágenes, igual intentamos mover el script y salir
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)
            
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Información", "No hay imágenes para recortar.\nEl programa se moverá a la carpeta OLD_image.")
        root.destroy()
        
        # Lógica de movimiento manual ya que no instanciamos la clase
        try:
            current_script = os.path.abspath(sys.argv[0])
            shutil.move(current_script, os.path.join(BACKUP_FOLDER, os.path.basename(current_script)))
        except:
            pass
        sys.exit()

    root = tk.Tk()
    try:
        root.state('zoomed')
    except:
        try:
            root.attributes('-zoomed', True)
        except:
            pass
            
    app = ImageCropper(root, images)
    root.bind("<Configure>", lambda e: app.update_display())
    root.mainloop()