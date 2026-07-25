from ursina import Ursina, Entity, camera, window
from panda3d.core import Texture
import sys

app = Ursina()
imagen = 'scripts/backgrounds/back1.png'
pantalla = Entity(parent=camera.ui, model='quad', texture=imagen, scale=(window.aspect_ratio, 1))

def update():
    print(f"Texture name: {pantalla.texture.name if pantalla.texture else 'None'}")
    sys.exit(0)

app.run()
