from scripts.enemigo_base import EnemigoBase

class VillanoO(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            ruta_modelo='',
            ruta_textura='',
            base_folder='assets/modelos/villians/mutant3/',
            prefix='Meshy_AI_Orion_Sys_Ice_Mutant__biped_Animation_',
            **kwargs
        )
        self.vida = 250
        self.velocidad_normal = 2.5 # Súper lento (30% de la velocidad del jugador)
        self.velocidad = self.velocidad_normal