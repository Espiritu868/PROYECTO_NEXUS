from ursina import *
app = Ursina()
import random

image_path = f"scripts/backgrounds/back1.png"
textura = load_texture(image_path)

pantalla_carga = Sprite(
    texture=textura,
    parent=camera.ui,
    z=-1
)

if textura:
    # Ajustar para que quepa en la pantalla
    ratio = textura.width / textura.height
    escala_y = 100 / textura.height
    
    if ratio > window.aspect_ratio:
        # Ancha: ajustar al ancho de la ventana
        escala = (window.aspect_ratio * 100) / textura.width
    else:
        # Alta o igual: ajustar al alto de la ventana
        escala = 100 / textura.height
        
    pantalla_carga.scale = escala
else:
    pantalla_carga = None

terminar = False

def input(key):
    global terminar
    if key == 'space':
        terminar = True
    if key == 'escape':
        application.quit()

def update():
    global pantalla_carga
    if terminar and pantalla_carga:
        print("Destruyendo pantalla de carga...")
        pantalla_carga.enabled = False
        pantalla_carga.visible = False
        destroy(pantalla_carga)
        pantalla_carga = None

app.run()
