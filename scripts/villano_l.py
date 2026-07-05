from scripts.enemigo_base import EnemigoBase

class VillanoL(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            # Usamos el modelo sano del jugador...
            ruta_modelo='assets/modelos/character-j.fbx',
            # ...pero le pegamos la textura del villano L
            ruta_textura='assets/modelos/textures/texture-l.png',
            **kwargs
        )
        self.vida = 100
        self.velocidad = 15