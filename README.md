<p align="center"><img src="./img/iphone-sn-banner.png"  alt=" " /></p>
<h1 align="center"> iPhone to Social Networking </h1> 
<h4 align="right">December 25</h4>

<p>
  <img src="https://img.shields.io/badge/OS-Windows%2011-blue">
  <img src="https://img.shields.io/badge/Python%20-V13.12.10-orange">
</p>

<br>

# Table of contents
- [Table of contents](#table-of-contents)
- [Use](#use)
- [Scripts](#scripts)
- [Troubleshooting](#troubleshooting)

<br>

Editar de forma más eficiente y rapido las imagenes HEIC de mi iphone para mis redes sociales. Desde la consola de Windows.

<br>

# Use
1. Descarga los archivos a la carpeta a trabajar:
2. Correr instalador desde la consola: 
```bash
# Desde Gitbash
./install.bat

# Desde CMD
cmd.exe /c install.bat

# Desde Powershell
./install.bat
```
3. Activa el entorno virtual:
```bash
# Desde Gitbash
source venv/Scripts/activate

# Desde el CMD
venv\Scripts\activate

# Desde PowerShell
.\venv\Scripts\Activate.ps1
```
4. Corre los comandos para editar las fotos:
```bash
python heic-to-jpeg.py # convierte la imagen heic a jpeg
python cut-photo.py # deja la foto cuadrada equivalente a 1080x1080 px
```
5. Desactivar el entorno virtual
```bash
# Desde Gitbash /CMD /PowerShell
deactivate
```
<br>

# Scripts
***cut-photo.py***
```bash
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sys

# Extensiones de imagen soportadas
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')

class ImageCropper:
    def __init__(self, root, image_paths):
        self.root = root
        self.image_paths = image_paths
        self.current_index = 0
        
        self.root.title("Recortador de Fotos para Redes Sociales")
        self.root.geometry("800x600")
        self.root.configure(bg='black')

        # Variables de estado
        self.original_image = None
        self.display_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        
        # Variables del recuadro de recorte (en coordenadas de la imagen original)
        self.crop_x = 0
        self.crop_y = 0
        self.crop_size = 0  # Lado del cuadrado

        # Configuración del Canvas
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bindings de teclas
        self.root.bind("<Left>", lambda e: self.move_crop(-10, 0))
        self.root.bind("<Right>", lambda e: self.move_crop(10, 0))
        self.root.bind("<Up>", lambda e: self.move_crop(0, -10))
        self.root.bind("<Down>", lambda e: self.move_crop(0, 10))
        # Movimiento fino con Shift
        self.root.bind("<Shift-Left>", lambda e: self.move_crop(-1, 0))
        self.root.bind("<Shift-Right>", lambda e: self.move_crop(1, 0))
        self.root.bind("<Shift-Up>", lambda e: self.move_crop(0, -1))
        self.root.bind("<Shift-Down>", lambda e: self.move_crop(0, 1))
        
        self.root.bind("<Return>", self.save_and_next)
        self.root.bind("<Escape>", self.close_app)

        # Cargar la primera imagen
        self.load_next_image()

    def load_next_image(self):
        if self.current_index >= len(self.image_paths):
            messagebox.showinfo("Finalizado", "¡Has terminado de recortar todas las fotos de la carpeta!")
            self.root.quit()
            return

        self.current_image_path = self.image_paths[self.current_index]
        
        try:
            self.original_image = Image.open(self.current_image_path)
            
            # Verificar orientación EXIF para que no salgan rotadas
            try:
                from PIL import ExifTags, ImageOps
                self.original_image = ImageOps.exif_transpose(self.original_image)
            except:
                pass

            # Inicializar recorte al cuadrado máximo posible
            w, h = self.original_image.size
            self.crop_size = min(w, h)
            
            # Centrar el recorte inicialmente
            self.crop_x = (w - self.crop_size) // 2
            self.crop_y = (h - self.crop_size) // 2

            self.update_display()
            self.root.title(f"Editando ({self.current_index + 1}/{len(self.image_paths)}): {os.path.basename(self.current_image_path)} - [ENTER] Guardar y Siguiente | [ESC] Salir")

        except Exception as e:
            print(f"Error cargando {self.current_image_path}: {e}")
            self.current_index += 1
            self.load_next_image()

    def update_display(self):
        if not self.original_image:
            return

        # Calcular tamaño para mostrar en pantalla sin deformar
        canvas_width = self.root.winfo_width()
        canvas_height = self.root.winfo_height()
        
        # Si la ventana aún no se ha dibujado, usar valores por defecto
        if canvas_width <= 1: canvas_width = 800
        if canvas_height <= 1: canvas_height = 600

        img_w, img_h = self.original_image.size
        
        # Calcular factor de escala para ajustar al canvas
        scale_w = canvas_width / img_w
        scale_h = canvas_height / img_h
        self.scale_factor = min(scale_w, scale_h) * 0.9 # 90% para dejar margen

        new_w = int(img_w * self.scale_factor)
        new_h = int(img_h * self.scale_factor)

        resized_img = self.original_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")
        
        # Centrar imagen en canvas
        x_offset = (canvas_width - new_w) // 2
        y_offset = (canvas_height - new_h) // 2
        
        self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.photo_image)

        # Dibujar el recuadro de recorte
        # Convertir coordenadas reales a coordenadas de pantalla
        rect_x1 = x_offset + (self.crop_x * self.scale_factor)
        rect_y1 = y_offset + (self.crop_y * self.scale_factor)
        rect_x2 = rect_x1 + (self.crop_size * self.scale_factor)
        rect_y2 = rect_y1 + (self.crop_size * self.scale_factor)

        # Dibujar rectángulo rojo (zona de corte)
        self.canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, outline="red", width=3)
        
        # Oscurecer el área exterior (opcional, visualmente ayuda)
        # (Simplificado: solo mostramos el recuadro rojo para rendimiento rápido)

    def move_crop(self, dx, dy):
        img_w, img_h = self.original_image.size
        
        new_x = self.crop_x + dx
        new_y = self.crop_y + dy

        # Validar límites para que el cuadro no se salga de la imagen
        if new_x < 0: new_x = 0
        if new_y < 0: new_y = 0
        if new_x + self.crop_size > img_w: new_x = img_w - self.crop_size
        if new_y + self.crop_size > img_h: new_y = img_h - self.crop_size

        self.crop_x = new_x
        self.crop_y = new_y
        self.update_display()

    def save_and_next(self, event=None):
        if not self.original_image:
            return

        # Realizar el recorte en la imagen original (alta calidad)
        box = (self.crop_x, self.crop_y, self.crop_x + self.crop_size, self.crop_y + self.crop_size)
        cropped_img = self.original_image.crop(box)

        # Guardar sobreescribiendo el archivo original
        try:
            # Preservar calidad según formato
            img_format = self.original_image.format
            
            if img_format == 'JPEG':
                cropped_img.save(self.current_image_path, quality="keep", subsampling=0)
            else:
                cropped_img.save(self.current_image_path)
            
            print(f"Guardado: {self.current_image_path}")
            
        except Exception as e:
            # Fallback si quality='keep' falla
            print(f"Advertencia al guardar (intentando método estándar): {e}")
            cropped_img.save(self.current_image_path, quality=95)

        # Pasar a la siguiente imagen
        self.current_index += 1
        self.load_next_image()

    def close_app(self, event=None):
        self.root.quit()

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
                    # Si ya es cuadrada (con un margen de error de 1 pixel), la saltamos
                    if abs(w - h) > 1:
                        images_to_process.append(full_path)
            except Exception as e:
                print(f"No se pudo leer {file}: {e}")

    return images_to_process

if __name__ == "__main__":
    images = get_images_to_process()

    if not images:
        # Crear una ventana raíz temporal solo para mostrar el mensaje
        root = tk.Tk()
        root.withdraw() # Ocultar ventana principal
        messagebox.showinfo("Información", "No hay imágenes pendientes de recortar en esta carpeta.\n(Todas las imágenes ya son cuadradas o no hay imágenes).")
        root.destroy()
        sys.exit()

    root = tk.Tk()
    # Maximizar ventana si es posible
    try:
        root.state('zoomed') # Windows
    except:
        try:
            root.attributes('-zoomed', True) # Linux
        except:
            pass # Mac u otros
            
    app = ImageCropper(root, images)
    
    # Hook para redimensionar ventana
    root.bind("<Configure>", lambda e: app.update_display())
    
    root.mainloop()
```


<br>

# Troubleshooting
> :warning: **Warning:**

<br>

---

<div>
  <p>
    <img  align="top" width="42" style="padding:0px 0px 0px 0px;" src="./img/carjavi.png"/> Copyright &nbsp;&copy; 2023 Instinto Digital <a href="https://carjavi.github.io/" title="carjavi.github">carjavi</a>
  </p>
</div>

<p align="center">
    <a href="https://instintodigital.net/" target="_blank"><img src="./img/developer.png" height="100" alt="www.instintodigital.net"></a>
</p>




