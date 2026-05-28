# CarJavi TermGUI — Interfaz TUI modular (compatible con: CMD, PowerShell, Terminal-VScode)
# @author: Carlos Briceño <carjavi@hotmail.com>
# @date: 27-05-2026
# @copyright: Copyright (c) 2026 www.carjavi.com
# @version: V4.2
# @library:
#   pip install PyTermGUI
#   pip install pillow
#   pip install pillow-heif

from __future__ import annotations

import atexit
import os
import shutil
import signal
import sys
import traceback
from argparse import ArgumentParser, Namespace
from typing import Callable


# ============================================================
# ENTORNO DE COLOR
# ============================================================

os.environ["COLORTERM"] = "truecolor"
os.environ["TERM"]      = "xterm-256color"


# ============================================================
# AUTO-INSTALACIÓN DE DEPENDENCIAS
# ============================================================

def _ensure_dependencies() -> None:
    """
    Lee el bloque ``@library:`` del encabezado del propio script,
    detecta librerías faltantes e instala las que no estén disponibles
    usando el mismo intérprete Python activo (respeta virtualenvs).
    Reinicia el proceso tras la instalación para que los imports sean válidos.

    Raises:
        SystemExit: Si pip falla al instalar alguna dependencia.
    """
    import importlib
    import re
    import subprocess

    _IMPORT_OVERRIDES: dict[str, str] = {
        "pillow":          "PIL",
        "pillow-heif":     "pillow_heif",
        "scikit-learn":    "sklearn",
        "python-dateutil": "dateutil",
        "pyyaml":          "yaml",
        "opencv-python":   "cv2",
        "pytermgui":       "pytermgui",
    }

    pip_packages: list[str] = []
    try:
        with open(__file__, encoding="utf-8") as _f:
            in_block = False
            for raw in _f:
                line = raw.strip()
                if not line.startswith("#"):
                    break
                content = line.lstrip("#").strip()
                if content.startswith("@library:"):
                    after = content[len("@library:"):].strip()
                    if after and after != "No external dependencies":
                        m = re.match(r"pip\s+install\s+(.+)", after)
                        if m:
                            pip_packages.append(m.group(1).strip())
                    in_block = True
                    continue
                if in_block:
                    if content.startswith("@"):
                        break
                    m = re.match(r"-?\s*pip\s+install\s+(.+)", content)
                    if m:
                        pip_packages.append(m.group(1).strip())
    except Exception:
        return

    if not pip_packages:
        return

    missing: list[str] = []
    for spec in pip_packages:
        base        = re.split(r"[=<>!;]", spec)[0].strip().lower()
        import_name = _IMPORT_OVERRIDES.get(base, base.replace("-", "_"))
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(spec)

    if not missing:
        return

    print("\n[carjavi TUI] Dependencias faltantes detectadas:")
    for pkg in missing:
        print(f"  • {pkg}")
    print()

    for pkg in missing:
        print(f"  Instalando: {pkg} ...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("OK")
        else:
            print("ERROR")
            print(result.stderr.strip())
            sys.exit(1)

    print("\n[carjavi TUI] Dependencias listas. Iniciando...\n")
    os.execv(sys.executable, [sys.executable] + sys.argv)


_ensure_dependencies()

import pytermgui as ptg  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════
#
#   SECCIÓN 1 — CONFIGURACIÓN
#   ► Edita esta sección para personalizar o reutilizar la app.
#   ► No es necesario tocar nada fuera de este bloque.
#
# ════════════════════════════════════════════════════════════════════════════


# ── 1.1  Identidad visual ────────────────────────────────────────────────────

APP_HEADER_TEXT:  str = "  carjavi TermGUI  "
APP_WINDOW_TITLE: str = "Main Menu"

# Logo ASCII. Cada string = 1 línea. Usa "" para líneas en blanco.
APP_LOGO_LINES: list[str] = [
    "                             d8b                   d8b ",
    "                             Y8P                   Y8P",
    "",
    "  .d8888b  8888b.  888d888  8888  8888b.  888  888 888",
    " d88P'        '88b 888P'    '888     '88b 888  888 888 ",
    " 888      .d888888 888       888 .d888888 Y88  88P 888 ",
    " Y88b.    888  888 888       888 888  888  Y8bd8P  888 ",
    "  'Y8888P 'Y888888 888       888 'Y888888   Y88P   888 ",
    "                             888                       ",
    "                            d88P                       ",
    "                          888P'                        ",
    "",
]


# ── 1.2  Funciones del menú ──────────────────────────────────────────────────
#
# Cada función es autocontenida: sus constantes y helpers están adentro.
# Puedes copiar una función completa a otro script sin dependencias externas.
#
# Firma obligatoria:
#   def option_N(
#       manager: ptg.WindowManager,
#       set_progress: Callable[[float], None],
#   ) -> None:
#
# • set_progress(0.0…1.0) actualiza la barra de progreso en tiempo real.
# • _show_message() y _show_error() están disponibles (motor, Sección 2).


def option_1(
    manager: ptg.WindowManager,
    set_progress: Callable[[float], None],
) -> None:
    """
    Convierte todos los archivos .heic de la carpeta actual a JPEG y mueve
    los originales a subcarpeta HEIC/.

    Args:
        manager: WindowManager activo de la TUI.
        set_progress: Callback para actualizar la barra (0.0–1.0).
    """
    # ── Configuración ────────────────────────────────────────────────────────
    quality:    int = 95       # calidad JPEG de salida (1–95)
    output_ext: str = ".jpeg"  # extensión del archivo convertido

    # ── Lógica ───────────────────────────────────────────────────────────────
    import pillow_heif
    from PIL import Image

    pillow_heif.register_heif_opener()
    input_folder = os.getcwd()
    set_progress(0.05)

    heic_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".heic")]

    if not heic_files:
        _show_message(manager, "HEIC → JPEG",
                      "No se encontraron archivos .heic\nen la carpeta actual.")
        return

    total = len(heic_files)
    converted: list[str] = []
    failed:    list[str] = []

    for i, filename in enumerate(heic_files):
        set_progress(0.10 + 0.70 * (i / total))
        input_path      = os.path.join(input_folder, filename)
        output_filename = os.path.splitext(filename)[0] + output_ext
        output_path     = os.path.join(input_folder, output_filename)
        try:
            image = Image.open(input_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(output_path, "JPEG", quality=quality, optimize=True)
            converted.append(filename)
        except Exception:
            failed.append(filename)

    set_progress(0.82)

    if converted:
        heic_folder = os.path.join(input_folder, "HEIC")
        os.makedirs(heic_folder, exist_ok=True)
        for filename in converted:
            try:
                shutil.move(os.path.join(input_folder, filename),
                            os.path.join(heic_folder, filename))
            except Exception:
                pass

    set_progress(0.95)

    lines = [
        f"Carpeta:     {input_folder}",
        f"Convertidos: {len(converted)}",
        f"Errores:     {len(failed)}",
    ]
    if failed:
        lines.append(f"Con error: {', '.join(failed)}")
    _show_message(manager, "HEIC → JPEG completado", "\n".join(lines))


def option_2(
    manager: ptg.WindowManager,
    set_progress: Callable[[float], None],
) -> None:
    """
    Lanza el recortador de fotos como ventana GUI independiente.
    La TUI permanece activa mientras el recortador está abierto.
    Controles: ←→↑↓ mover | Shift+flechas ajuste fino | ENTER guardar | ESC salir.

    Args:
        manager: WindowManager activo de la TUI.
        set_progress: Callback para actualizar la barra (0.0–1.0).
    """
    import inspect
    import subprocess
    import tempfile
    import textwrap

    # ── Configuración ────────────────────────────────────────────────────────
    VALID_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
    BACKUP_FOLDER:    str              = "OLD_image"

    # ── Clase recortadora GUI ─────────────────────────────────────────────────
    class ImageCropper:
        """
        Herramienta interactiva de recorte cuadrado usando tkinter.
        Procesa cada imagen no cuadrada y guarda el recorte sobreescribiendo
        el original (con backup en BACKUP_FOLDER/).
        """

        def __init__(self, root: object, image_paths: list) -> None:
            import tkinter as tk

            self.root          = root
            self.image_paths   = image_paths
            self.current_index = 0

            if not os.path.exists(BACKUP_FOLDER):
                os.makedirs(BACKUP_FOLDER)

            self.root.title("Recortador de Fotos")
            self.root.geometry("800x600")
            self.root.configure(bg="black")

            self.original_image = None
            self.photo_image    = None
            self.scale_factor   = 1.0
            self.crop_x         = 0
            self.crop_y         = 0
            self.crop_size      = 0

            self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
            self.canvas.pack(fill=tk.BOTH, expand=True)

            self.root.bind("<Left>",        lambda e: self.move_crop(-10, 0))
            self.root.bind("<Right>",       lambda e: self.move_crop(10, 0))
            self.root.bind("<Up>",          lambda e: self.move_crop(0, -10))
            self.root.bind("<Down>",        lambda e: self.move_crop(0, 10))
            self.root.bind("<Shift-Left>",  lambda e: self.move_crop(-1, 0))
            self.root.bind("<Shift-Right>", lambda e: self.move_crop(1, 0))
            self.root.bind("<Shift-Up>",    lambda e: self.move_crop(0, -1))
            self.root.bind("<Shift-Down>",  lambda e: self.move_crop(0, 1))
            self.root.bind("<Return>", self.save_and_next)
            self.root.bind("<Escape>", self.close_app)

            self.load_next_image()

        def load_next_image(self) -> None:
            import tkinter.messagebox as messagebox
            from PIL import Image

            if self.current_index >= len(self.image_paths):
                messagebox.showinfo("Finalizado", "¡Terminaste de recortar todas las fotos!")
                self.cleanup_and_exit()
                return

            self.current_image_path = self.image_paths[self.current_index]
            try:
                self.original_image = Image.open(self.current_image_path)
                try:
                    from PIL import ImageOps
                    self.original_image = ImageOps.exif_transpose(self.original_image)
                except Exception:
                    pass

                w, h           = self.original_image.size
                self.crop_size = min(w, h)
                self.crop_x    = (w - self.crop_size) // 2
                self.crop_y    = (h - self.crop_size) // 2

                self.update_display()
                self.root.title(
                    f"Editando ({self.current_index + 1}/{len(self.image_paths)}): "
                    f"{os.path.basename(self.current_image_path)}"
                    "  |  [ENTER] Guardar  [ESC] Salir"
                )
            except Exception as e:
                print(f"Error cargando {self.current_image_path}: {e}")
                self.current_index += 1
                self.load_next_image()

        def update_display(self) -> None:
            import tkinter as tk
            from PIL import Image, ImageTk

            if not self.original_image:
                return

            cw = self.root.winfo_width()
            ch = self.root.winfo_height()
            if cw <= 1: cw = 800
            if ch <= 1: ch = 600

            iw, ih            = self.original_image.size
            self.scale_factor = min(cw / iw, ch / ih) * 0.9
            nw = int(iw * self.scale_factor)
            nh = int(ih * self.scale_factor)

            resized          = self.original_image.resize((nw, nh), Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(resized)

            self.canvas.delete("all")
            xo = (cw - nw) // 2
            yo = (ch - nh) // 2
            self.canvas.create_image(xo, yo, anchor=tk.NW, image=self.photo_image)

            rx1 = xo + self.crop_x * self.scale_factor
            ry1 = yo + self.crop_y * self.scale_factor
            rx2 = rx1 + self.crop_size * self.scale_factor
            ry2 = ry1 + self.crop_size * self.scale_factor
            self.canvas.create_rectangle(rx1, ry1, rx2, ry2, outline="red", width=3)

        def move_crop(self, dx: int, dy: int) -> None:
            iw, ih      = self.original_image.size
            self.crop_x = max(0, min(self.crop_x + dx, iw - self.crop_size))
            self.crop_y = max(0, min(self.crop_y + dy, ih - self.crop_size))
            self.update_display()

        def backup_original_image(self) -> None:
            try:
                filename    = os.path.basename(self.current_image_path)
                name, ext   = os.path.splitext(filename)
                backup_path = os.path.join(BACKUP_FOLDER, f"{name}_old{ext}")
                shutil.copy2(self.current_image_path, backup_path)
            except Exception as e:
                print(f"Error creando backup: {e}")

        def save_and_next(self, event: object = None) -> None:
            from PIL import Image

            if not self.original_image:
                return

            self.backup_original_image()

            box     = (self.crop_x, self.crop_y,
                       self.crop_x + self.crop_size, self.crop_y + self.crop_size)
            cropped = self.original_image.crop(box)

            try:
                if self.original_image.format == "JPEG":
                    cropped.save(self.current_image_path, quality="keep", subsampling=0)
                else:
                    cropped.save(self.current_image_path)
            except Exception:
                cropped.save(self.current_image_path, quality=95)

            self.current_index += 1
            self.load_next_image()

        def close_app(self, event: object = None) -> None:
            self.cleanup_and_exit()

        def cleanup_and_exit(self) -> None:
            self.root.destroy()
            sys.exit(0)

    # ── Helper: escanear imágenes no cuadradas ────────────────────────────────
    def get_images_to_process(folder: str = ".") -> list:
        from PIL import Image

        target = os.path.abspath(folder)
        result = []
        for filename in os.listdir(target):
            if not filename.lower().endswith(VALID_EXTENSIONS):
                continue
            full_path = os.path.join(target, filename)
            try:
                with Image.open(full_path) as img:
                    w, h = img.size
                    if abs(w - h) > 1:
                        result.append(full_path)
            except Exception:
                pass
        return result

    # ── Helper: lanzar recortador en subproceso aislado ───────────────────────
    def launch_cut_photo(working_dir: str) -> None:
        header = "\n".join([
            "import tkinter as tk",
            "import tkinter.messagebox as messagebox",
            "from PIL import Image, ImageTk, ImageOps",
            "import os, sys, shutil",
            "",
            f"VALID_EXTENSIONS = {VALID_EXTENSIONS!r}",
            f"BACKUP_FOLDER    = {BACKUP_FOLDER!r}",
            "",
        ])

        main_block = (
            "\n\nif __name__ == '__main__':\n"
            "    images = get_images_to_process('.')\n"
            "    if not images:\n"
            "        root = tk.Tk()\n"
            "        root.withdraw()\n"
            "        messagebox.showinfo('Información', 'No hay imágenes para recortar.')\n"
            "        root.destroy()\n"
            "        sys.exit(0)\n"
            "    root = tk.Tk()\n"
            "    try:\n"
            "        root.state('zoomed')\n"
            "    except Exception:\n"
            "        try:\n"
            "            root.attributes('-zoomed', True)\n"
            "        except Exception:\n"
            "            pass\n"
            "    app = ImageCropper(root, images)\n"
            "    try:\n"
            "        root.bind('<Configure>', lambda e: app.update_display())\n"
            "        root.mainloop()\n"
            "    except Exception:\n"
            "        pass\n"
        )

        # textwrap.dedent elimina la indentación de clases/funciones anidadas
        # antes de escribirlas al script temporal.
        class_src = textwrap.dedent(inspect.getsource(ImageCropper))
        func_src  = textwrap.dedent(inspect.getsource(get_images_to_process))
        full_code = header + class_src + "\n\n" + func_src + main_block

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(full_code)
                tmp_path = f.name

            atexit.register(
                lambda p=tmp_path: os.unlink(p) if os.path.exists(p) else None
            )

            popen_kwargs: dict = dict(
                cwd=working_dir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            subprocess.Popen([sys.executable, tmp_path], **popen_kwargs)

        except Exception:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            raise

    # ── Lógica principal ──────────────────────────────────────────────────────
    working_dir = os.getcwd()
    images      = get_images_to_process(working_dir)

    if not images:
        _show_message(manager, "Cut Photo",
                      "No hay imágenes para recortar\nen la carpeta actual.")
        return

    launch_cut_photo(working_dir)
    _show_message(
        manager, "Cut Photo",
        f"Se encontraron {len(images)} imagen(es) no cuadrada(s).\n\n"
        "La ventana de recorte se abrió.\n"
        "Vuelve aquí cuando termines.",
    )


def option_3(
    manager: ptg.WindowManager,
    set_progress: Callable[[float], None],
) -> None:
    """
    Borra la carpeta HEIC del directorio actual.

    Args:
        manager: WindowManager activo de la TUI.
        set_progress: Callback para actualizar la barra (0.0–1.0).
    """
    # ── Configuración ────────────────────────────────────────────────────────
    folder_name: str = "HEIC"

    # ── Lógica ───────────────────────────────────────────────────────────────
    target = os.path.join(os.getcwd(), folder_name)
    set_progress(0.2)

    if not os.path.isdir(target):
        _show_message(manager, "Delete HEIC folder",
                      f"La carpeta {folder_name} no existe\nen el directorio actual.")
        return

    set_progress(0.6)
    shutil.rmtree(target)
    set_progress(0.95)
    _show_message(manager, "Delete HEIC folder",
                  f"Carpeta eliminada:\n{target}")


def option_4(
    manager: ptg.WindowManager,
    set_progress: Callable[[float], None],
) -> None:
    """
    Borra la carpeta OLD_image del directorio actual.

    Args:
        manager: WindowManager activo de la TUI.
        set_progress: Callback para actualizar la barra (0.0–1.0).
    """
    # ── Configuración ────────────────────────────────────────────────────────
    folder_name: str = "OLD_image"

    # ── Lógica ───────────────────────────────────────────────────────────────
    target = os.path.join(os.getcwd(), folder_name)
    set_progress(0.2)

    if not os.path.isdir(target):
        _show_message(manager, "Delete OLD_image folder",
                      f"La carpeta {folder_name} no existe\nen el directorio actual.")
        return

    set_progress(0.6)
    shutil.rmtree(target)
    set_progress(0.95)
    _show_message(manager, "Delete OLD_image folder",
                  f"Carpeta eliminada:\n{target}")


# ── 1.3  Mapa del menú ──────────────────────────────────────────────────────
# Registra aquí las funciones en el menú. Orden: (etiqueta, función, atajo).
# NOTA: Python requiere que las funciones estén definidas antes de este bloque.
#
#    ┌─ Etiqueta del botón ──────────────┬─ Función ──┬─ Atajo ─┐
MENU_ITEMS: list[tuple[str, Callable, str]] = [
    ("1) Convert HEIC to JPG",            option_1,    "1"     ),
    ("2) Cut Photo",                       option_2,    "2"     ),
    ("3) Delete HEIC folder",              option_3,    "3"     ),
    ("4) Delete OLD_image folder",         option_4,    "4"     ),
]





# ════════════════════════════════════════════════════════════════════════════
#
#   SECCIÓN 2 — MOTOR DE INTERFAZ
#   ► No modificar.
#
# ════════════════════════════════════════════════════════════════════════════


# ── Paleta de colores ────────────────────────────────────────────────────────

PALETTE_LIGHT:  str = "#d79921"
PALETTE_MID:    str = "#b57614"
PALETTE_DARK:   str = "#3c3836"
PALETTE_DARKER: str = "#1d2021"
TEXT_COLOR:     str = "#ebdbb2"

# Ancho del Container del menú calculado desde el label más largo de MENU_ITEMS.
# Garantiza que ningún botón quede cortado.
_longest_label:        int = max((len(lbl) for lbl, _, _ in MENU_ITEMS), default=20)
_MENU_CONTAINER_WIDTH: int = int(max(60, _longest_label * 2 + 14) * 1.2)


# ── Restauración del terminal ────────────────────────────────────────────────

def _restore_terminal() -> None:
    """Restaura el terminal a estado normal (modo canónico, cursor visible)."""
    try:
        sys.stdout.write("\033[?1049l\033[?25h\033[0m")
        sys.stdout.flush()
    except Exception:
        pass


def _signal_handler(sig: int, frame: object) -> None:
    """
    Manejador de señales SIGINT/SIGTERM.

    Args:
        sig: Número de señal recibida.
        frame: Frame de ejecución al momento de la señal.
    """
    _restore_terminal()
    sys.exit(0)


atexit.register(_restore_terminal)
signal.signal(signal.SIGINT, _signal_handler)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, _signal_handler)


# ── Patches de estabilidad — PyTermGUI 7.1.0 ────────────────────────────────

def _patch_pytermgui_bugs() -> None:
    """
    Corrige bugs conocidos de PyTermGUI 7.1.0 mediante monkey-patching.

    Bug 1: KeyError 'scroll_down'/'scroll_up' en Button → inyectar listas vacías.
    Bug 2: TypeError en Container/Splitter.handle_key con selected_index=None
           → wrap que retorna False y absorbe TypeError/IndexError/KeyError.
    """
    import functools

    for scroll_key in ("scroll_down", "scroll_up"):
        if scroll_key not in ptg.Button.keys:
            ptg.Button.keys[scroll_key] = []

    def _wrap_handle_key(cls: type) -> None:
        """
        Reemplaza cls.handle_key con versión protegida contra None index.

        Args:
            cls: Clase de widget a parchear.
        """
        original = cls.handle_key

        @functools.wraps(original)
        def _safe(self: object, key: str) -> bool:
            if getattr(self, "selected_index", None) is None:
                return False
            try:
                return original(self, key)
            except (TypeError, IndexError, KeyError):
                return False

        cls.handle_key = _safe

    for widget_cls in (ptg.Container, ptg.Splitter):
        if hasattr(widget_cls, "handle_key"):
            _wrap_handle_key(widget_cls)


# ── Argumentos CLI ───────────────────────────────────────────────────────────

def _process_arguments(argv: list[str] | None = None) -> Namespace:
    """
    Procesa argumentos de línea de comandos.

    Args:
        argv: Lista de argumentos. Si es None usa sys.argv.

    Returns:
        Namespace con los argumentos parseados.
    """
    parser = ArgumentParser(description="CarJavi TermGUI")
    return parser.parse_args(argv)


# ── Aliases de estilo ────────────────────────────────────────────────────────

def _create_aliases() -> None:
    """Define aliases TIM de color y tipografía para el tema de la aplicación."""
    ptg.tim.alias("app.text",             TEXT_COLOR)
    ptg.tim.alias("app.header",           f"bold @{PALETTE_MID} {TEXT_COLOR}")
    ptg.tim.alias("app.header.fill",      f"@{PALETTE_LIGHT}")
    ptg.tim.alias("app.title",            f"bold {PALETTE_LIGHT}")
    ptg.tim.alias("app.button.label",     f"bold @{PALETTE_DARK} {TEXT_COLOR}")
    ptg.tim.alias("app.button.highlight", f"bold @{PALETTE_LIGHT} black")
    ptg.tim.alias("app.footer",           f"@{PALETTE_DARKER}")
    ptg.tim.alias("app.error",            "bold red")
    ptg.tim.alias("app.logo",             f"bold {PALETTE_LIGHT}")


# ── Configuración de widgets ─────────────────────────────────────────────────

def _configure_widgets() -> None:
    """Configura estilos globales de widgets y aplica patches de estabilidad."""
    ptg.boxes.DOUBLE.set_chars_of(ptg.Window)
    ptg.boxes.ROUNDED.set_chars_of(ptg.Container)

    ptg.Button.styles.label             = "app.button.label"
    ptg.Button.styles.highlight         = "app.button.highlight"
    ptg.Button.set_char("delimiter", [" ", ""])  # alineación izquierda
    ptg.Label.styles.value              = "app.text"
    ptg.Window.styles.border__corner    = PALETTE_LIGHT
    ptg.Container.styles.border__corner = PALETTE_MID
    ptg.Splitter.set_char("separator", " ")

    _patch_pytermgui_bugs()


# ── Layout ───────────────────────────────────────────────────────────────────

def _define_layout() -> ptg.Layout:
    """
    Define layout en tres zonas: Header (1 línea), Body, Footer (1 línea).

    Returns:
        Objeto Layout configurado.
    """
    layout = ptg.Layout()
    layout.add_slot("Header", height=1)
    layout.add_break()
    layout.add_slot("Body")
    layout.add_break()
    layout.add_slot("Footer", height=1)
    return layout


# ── Modales ──────────────────────────────────────────────────────────────────

def _show_message(
    manager: ptg.WindowManager,
    title: str,
    message: str,
) -> None:
    """
    Muestra un modal informativo centrado con botón Cerrar.

    Args:
        manager: WindowManager activo.
        title: Título del modal.
        message: Cuerpo del mensaje.
    """
    def _on_close() -> None:
        modal.close()
        if _active_tracker is not None:
            _active_tracker.reset()

    btn = ptg.Button("Volver al menú", lambda *_: _on_close())
    btn.parent_align = ptg.HorizontalAlignment.CENTER

    # Cada línea como widget separado: evita que un Label multi-línea
    # subestime su height y provoque overflow HIDE que oculta el botón.
    msg_widgets = [ptg.Label(line) for line in message.split("\n")]

    modal = ptg.Window(
        f"[app.title]{title}",
        "",
        *msg_widgets,
        "",
        "",
        ptg.Container(btn),
        "",
        width=55,
    ).center()
    modal.select(0)
    manager.add(modal)


def _show_error(
    manager: ptg.WindowManager,
    error: Exception,
) -> None:
    """
    Muestra un modal de error centrado.

    Args:
        manager: WindowManager activo.
        error: Excepción capturada.
    """
    def _on_close_err() -> None:
        modal.close()
        if _active_tracker is not None:
            _active_tracker.reset()

    btn_err = ptg.Button("Volver al menú", lambda *_: _on_close_err())
    btn_err.parent_align = ptg.HorizontalAlignment.CENTER

    err_widgets = [ptg.Label(line) for line in str(error).split("\n")]

    modal = ptg.Window(
        "[app.error]ERROR",
        "",
        *err_widgets,
        "",
        "",
        ptg.Container(btn_err),
        "",
        width=70,
    ).center()
    modal.select(0)
    manager.add(modal)


# ── Salida ───────────────────────────────────────────────────────────────────

def _confirm_quit(manager: ptg.WindowManager) -> None:
    """
    Muestra modal de confirmación antes de salir.

    Args:
        manager: WindowManager activo.
    """
    modal = ptg.Window(
        "[app.title]¿Deseas salir?",
        "",
        ptg.Splitter(
            ptg.Button("Sí", lambda *_: manager.stop()),
            ptg.Button("No", lambda *_: modal.close()),
        ),
        width=40,
    ).center()
    modal.select(1)
    manager.add(modal)


# ── Barra de progreso ────────────────────────────────────────────────────────

class ProgressTracker:
    """
    Barra de progreso basada en ptg.Label, actualizable en tiempo real.

    Rango: 0.0 (0%) a 1.0 (100%).

    Attributes:
        widget: Label de PyTermGUI que se añade a la ventana.

    Example:
        tracker = ProgressTracker()
        window = ptg.Window(tracker.widget)
        tracker.progress = 0.5
    """

    def __init__(self, bar_width: int = 40) -> None:
        """
        Inicializa la barra.

        Args:
            bar_width: Columnas del bloque de barras (sin contar etiqueta).
        """
        self._bar_width: int   = max(10, bar_width)
        self._progress: float  = 0.0
        self.widget: ptg.Label = ptg.Label(self._render())

    @property
    def progress(self) -> float:
        """Valor actual (0.0–1.0)."""
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        """
        Actualiza el progreso y redibuja el widget.

        Args:
            value: Nuevo valor; se clampea entre 0.0 y 1.0.
        """
        self._progress    = max(0.0, min(1.0, float(value)))
        self.widget.value = self._render()

    def _render(self) -> str:
        """
        Genera el string con markup PTG.

        Returns:
            String con markup de color listo para ptg.Label.
        """
        filled: int = int(self._bar_width * self._progress)
        empty: int  = self._bar_width - filled
        pct: int    = int(self._progress * 100)

        return (
            f"[{PALETTE_LIGHT}]" + "█" * filled + "[/]"
            + f"[{PALETTE_DARK}]" + "░" * empty + "[/]"
            + f"  [bold {PALETTE_LIGHT}]{pct:3d}%[/]"
        )

    def reset(self) -> None:
        """Resetea a 0%."""
        self.progress = 0.0

    def complete(self) -> None:
        """Lleva a 100%."""
        self.progress = 1.0


# Referencia al tracker activo; la actualiza _safe_action antes de cada llamada
# para que _show_message/_show_error puedan resetearlo al cerrar el modal.
_active_tracker: "ProgressTracker | None" = None


def _calc_bar_width() -> int:
    """
    Calcula el ancho de la barra como 80% del terminal (mínimo 20).

    Returns:
        Número de columnas para el bloque de barras.
    """
    cols: int = shutil.get_terminal_size(fallback=(80, 24)).columns
    return max(20, int(cols * 0.8) - 6)


# ── Ejecución protegida ──────────────────────────────────────────────────────

def _safe_action(
    manager: ptg.WindowManager,
    tracker: ProgressTracker,
    fn: Callable[[ptg.WindowManager, Callable[[float], None]], None],
) -> None:
    """
    Ejecuta fn con ciclo completo de progreso:
      1. Reset → 0%.
      2. Llama fn(manager, set_progress).
      3. Fuerza 100% al terminar (éxito o error).

    Los errores se muestran en modal sin romper la TUI.

    Args:
        manager: WindowManager activo.
        tracker: Barra de progreso a controlar.
        fn: Función de menú a ejecutar.
    """
    global _active_tracker
    _active_tracker = tracker
    tracker.reset()

    def set_progress(value: float) -> None:
        """
        Callback de progreso para la función de menú.

        Args:
            value: Valor entre 0.0 y 1.0.
        """
        tracker.progress = value

    try:
        fn(manager, set_progress)
    except KeyboardInterrupt:
        raise
    except Exception as error:
        traceback.print_exc()
        _show_error(manager, error)
    finally:
        tracker.complete()


# ── Ventana principal ────────────────────────────────────────────────────────

def _create_main_window(
    manager: ptg.WindowManager,
) -> tuple[ptg.Window, ProgressTracker]:
    """
    Construye la ventana principal leyendo MENU_ITEMS, APP_LOGO_LINES y
    APP_WINDOW_TITLE. Genera dinámicamente botones, grid 2 columnas,
    atajos de teclado y barra de progreso.

    Args:
        manager: WindowManager activo.

    Returns:
        Tupla (ventana, ProgressTracker compartido por todas las opciones).
    """
    tracker = ProgressTracker(bar_width=_calc_bar_width())

    # ── Botones ──────────────────────────────────────────────────────────────
    buttons: list[ptg.Button] = []
    for label, fn, _ in MENU_ITEMS:
        btn = ptg.Button(
            label,
            lambda *_, _fn=fn: _safe_action(manager, tracker, _fn),
        )
        btn.parent_align = ptg.HorizontalAlignment.LEFT
        buttons.append(btn)

    # ── Grid 2 columnas ──────────────────────────────────────────────────────
    rows: list = []
    for i in range(0, len(buttons), 2):
        pair = buttons[i : i + 2]
        rows.append(ptg.Splitter(*pair) if len(pair) == 2 else pair[0])
        if i + 2 < len(buttons):
            rows.append("")

    menu = ptg.Container(*rows, static_width=_MENU_CONTAINER_WIDTH)

    # ── Logo ─────────────────────────────────────────────────────────────────
    logo_widgets = [
        ptg.Label(f"[app.logo]{line}" if line else "")
        for line in APP_LOGO_LINES
    ]

    # ── Ventana principal ────────────────────────────────────────────────────
    window = ptg.Window(
        *logo_widgets,
        f"[app.title]{APP_WINDOW_TITLE}",
        "",
        menu,
        "",
        ptg.Label(f"[{PALETTE_MID}]Progress:"),
        tracker.widget,
        "",
    )
    window.pos = (2, 2)
    window.select(0)

    # ── Atajos de teclado ────────────────────────────────────────────────────
    for _, fn, shortcut in MENU_ITEMS:
        if shortcut:
            window.bind(
                shortcut,
                lambda *_, _fn=fn: _safe_action(manager, tracker, _fn),
            )

    return window, tracker


# ── Main ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    """
    Punto de entrada. Inicializa la TUI y lanza el event loop.

    Args:
        argv: Argumentos CLI opcionales. Si es None usa sys.argv.
    """
    _process_arguments(argv)
    _create_aliases()
    _configure_widgets()

    try:
        with ptg.WindowManager() as manager:

            manager.layout = _define_layout()

            # ── Header ───────────────────────────────────────────────────────
            header = ptg.Window(
                f"[app.header]{APP_HEADER_TEXT}",
                box="EMPTY",
                is_persistant=True,
            )
            header.styles.fill = "app.header.fill"
            manager.add(header)

            # ── Footer ───────────────────────────────────────────────────────
            footer = ptg.Window(
                ptg.Button("Exit", lambda *_: _confirm_quit(manager)),
                box="EMPTY",
            )
            footer.styles.fill = "app.footer"
            manager.add(footer, assign="footer")

            # ── Body ─────────────────────────────────────────────────────────
            main_window, _tracker = _create_main_window(manager)
            manager.add(main_window, assign="body")

    except KeyboardInterrupt:
        pass

    except Exception as error:
        traceback.print_exc()
        print("\nERROR:", error)

    finally:
        _restore_terminal()


# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main(sys.argv[1:])
