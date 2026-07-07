from ursina import Entity, load_texture
from direct.actor.Actor import Actor

class Sobreviviente(Entity):
    def __init__(self, ruta_textura, **kwargs):
        super().__init__(**kwargs)
        
        # Ahora que tenemos formato GLB compatible, instanciamos el Actor animado!
        self.actor = Actor('assets/texturas/survivors/Model/characterMedium.glb', {
            'idle': 'assets/texturas/survivors/Animations/idle.glb'
        })
        self.actor.reparentTo(self)
        self.actor.setScale(1.5)
        # El loader GLTF de Panda3D automáticamente corrige el eje Z-up, por lo que 
        # solo necesitamos rotarlo 180 grados en Y (Hpr) para que vea al frente.
        self.actor.setHpr(180, 0, 0) 
        self.actor.loop('idle') # Animación infinita!
        
        textura_real = load_texture(ruta_textura)
        if textura_real:
            self.actor.setTexture(textura_real._texture, 1)
        else:
            print(f"❌ Advertencia: No se encontró la textura del sobreviviente en {ruta_textura}")
