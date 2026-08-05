from scripts.enemigo_base import EnemigoBase

class VillanoL(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            ruta_modelo='',
            ruta_textura='',
            base_folder='assets/modelos/villians/mutant2/',
            prefix='Meshy_AI_Knight_Mutant_Optimiz_biped_Animation_',
            **kwargs
        )
        self.vida = 100
        self.velocidad = 5.8 # Aumentada (antes 4.8)
        self.distancia_ataque = 1.3 # Ahora es cuerpo a cuerpo
        self.tiempo_entre_ataques = 1.5

    # El método atacar() original se eliminó para que herede el ataque cuerpo a cuerpo base.