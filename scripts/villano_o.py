from scripts.enemigo_base import EnemigoBase

class VillanoO(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            # Usamos el modelo sano del jugador...
            ruta_modelo='assets/modelos/character-j.fbx',
            # ...pero le pegamos la textura del villano O
            ruta_textura='assets/modelos/textures/texture-o.png',
            **kwargs
        )
        self.vida = 250
        self.velocidad = 5