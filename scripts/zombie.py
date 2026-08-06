from scripts.enemigo_base import EnemigoBase

class Zombie(EnemigoBase):
    def __init__(self, **kwargs):
        super().__init__(
            ruta_modelo='',
            ruta_textura='',
            base_folder='assets/modelos/villians/mutant1/',
            prefix='Meshy_AI_Rock_Mutant_Optimized_biped_Animation_',
            **kwargs
        )
        self.vida = 80
        self.velocidad_normal = 9.0 # Aumentada (antes 7.6)
        self.velocidad = self.velocidad_normal
        self.frenesi = False

    def update(self):
        super().update() # Ejecutar lógica base (movimiento, gravedad, IA base)
        
        # --- FRENESÍ ZOMBIE ---
        # Si su vida baja de la mitad, se vuelve loco y corre rapidísimo
        if self.vida_maxima and self.vida < (self.vida_maxima / 2) and not self.frenesi and not self.curando:
            self.frenesi = True
            self.velocidad = self.velocidad_normal * 1.3
            
            # Sonido de frenesí (grito extendido)
            try:
                from scripts.gestor_sonidos_zombie import ZombiesAudioManager
                ZombiesAudioManager.solicitar_sonido_frenesi(self)
            except:
                pass
            
            # Efecto visual de furia (Usamos set_color_scale)
            if self.actor:
                self.actor.setColorScale(1, 0.4, 0.4, 1)
            else:
                self.modelo_visual.set_color_scale((1, 0.4, 0.4, 1))
