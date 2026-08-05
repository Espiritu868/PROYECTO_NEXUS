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
        self.vida_maxima = 250
        self.vida = 250
        self.velocidad = 3.5 # Aumentada (antes 2.5)
        self.velocidad_normal = 3.5