from ursina import Ursina, Entity, camera, window, load_texture
from panda3d.core import loadPrcFileData

loadPrcFileData('', 'textures-power-2 none')

app = Ursina()

tex = load_texture('scripts/backgrounds/back1.png')
if tex:
    print(f"\n[DEBUG] TEXTURE LOADED: {tex.name}")
    print(f"[DEBUG] Ursina Texture Size: {tex.width} x {tex.height}")
    
    # Panda3D internal texture info
    pt = tex._texture
    print(f"[DEBUG] Panda3D Texture Orig Size: {pt.getOrigFileXSize()} x {pt.getOrigFileYSize()}")
    print(f"[DEBUG] Panda3D Texture Expected Size: {pt.getXSize()} x {pt.getYSize()}")
    print(f"[DEBUG] Panda3D Texture Format: {pt.getFormat()}")
else:
    print("\n[DEBUG] TEXTURE FAILED TO LOAD!")

pantalla_carga = Entity(parent=camera.ui, model='quad', texture=tex, z=10)
pantalla_carga.scale = (window.aspect_ratio, 1)

print(f"\n[DEBUG] Window aspect ratio: {window.aspect_ratio}")
print(f"[DEBUG] pantalla_carga scale: {pantalla_carga.scale}")
print(f"[DEBUG] pantalla_carga texture_scale: {pantalla_carga.texture_scale}")

import sys
sys.exit(0)
