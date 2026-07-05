from ursina import *

class Servidor(Entity):
    def __init__(self, position, rotation_y=0):
        super().__init__(
            # ¡CRÍTICO! Usar el .glb que sacaste de Blender, NO el .obj original
            model='assets/modelos/server_blender.glb', 
            position=position,
            rotation_y=rotation_y,
            scale=(5, 5, 5), 
            color=color.dark_gray,
            collider='box'
        )