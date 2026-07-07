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
        self.velocidad = self.velocidad_normal
        self.modelo_visual.set_color_scale((1, 1, 1, 1)) # Color normal
        self.temporizador_embestida = time.time()