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
        self.velocidad_normal = 5
        self.velocidad = self.velocidad_normal
        self.temporizador_embestida = 0 # Para que ataque casi de inmediato
        self.embistiendo = False
        self.preparando = False
        
    def update(self):
        from ursina import time, color, invoke
        super().update()
        
        if self.vida <= 0 or self.curando:
            return
            
        if not self.jugador_objetivo:
            return
            
        if not self.embistiendo and not self.preparando:
            # Embestir cada 5 segundos
            if time.time() - self.temporizador_embestida > 5:
                self.preparando = True
                self.velocidad = 0 # Se detiene para cargar el ataque
                if self.actor:
                    self.actor.setColorScale(1, 0, 0, 1) # Rojo puro
                else:
                    self.modelo_visual.set_color_scale((1, 0, 0, 1)) # Rojo puro
                invoke(self.iniciar_embestida, delay=1.0) # Tarda 1 segundo en cargar
                
    def iniciar_embestida(self):
        from ursina import invoke
        if self.vida <= 0 or self.curando:
            return
        self.preparando = False
        self.embistiendo = True
        self.velocidad = 45 # Velocidad de embestida
        
        invoke(self.terminar_embestida, delay=0.5) # Embiste durante medio segundo
        
    def terminar_embestida(self):
        from ursina import color, time
        self.embistiendo = False
        self.temporizador_embestida = time.time()
        if self.actor:
            self.actor.setColorScale(1, 1, 1, 1) # Vuelve al color normal
        else:
            self.modelo_visual.set_color_scale((1, 1, 1, 1)) # Vuelve al color normal
        self.temporizador_embestida = time.time()