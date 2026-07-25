from ursina import *
from direct.actor.Actor import Actor

import gltf._converter
from panda3d.core import Texture
original_load_texture = gltf._converter.Converter.load_texture

def patched_load_texture(self, texid, gltf_tex, gltf_data):
    try:
        original_load_texture(self, texid, gltf_tex, gltf_data)
    except RuntimeError as e:
        print(f"Ignorando textura faltante: {e}")
        self.textures[texid] = Texture()

gltf._converter.Converter.load_texture = patched_load_texture

app = Ursina()

base_path = 'assets/modelos/villians/mutant1/'

# El Actor de Panda3D necesita el modelo principal, y un diccionario con los nombres de animación y sus rutas
# Nota: Ursina puede necesitar que envolvamos el Actor en un Entity para integrarlo fácilmente a su sistema, 
# pero podemos probar que el Actor funcione directamente primero, o simplemente asignarlo como hijo de un Entity.

actor = Actor(
    base_path + 'Meshy_AI_Rock_Mutant_Optimized_biped_Animation_Axe_Breathe_and_Look_Around_withSkin.glb',
    {
        'walk': base_path + 'Meshy_AI_Rock_Mutant_Optimized_biped_Animation_Walking_withSkin.glb',
        'run': base_path + 'Meshy_AI_Rock_Mutant_Optimized_biped_Animation_Running_withSkin.glb'
    }
)

# Envolver en Entity
ent = Entity(position=(0, 0, 5))
actor.reparentTo(ent)
actor.loop('walk')

def update():
    ent.rotation_y += time.dt * 20

EditorCamera()

# Quit after 2 seconds automatically to just test loading doesn't crash
invoke(application.quit, delay=2.0)

app.run()
