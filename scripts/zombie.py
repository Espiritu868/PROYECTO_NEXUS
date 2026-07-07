from scripts.enemigo_base import EnemigoBase

class Zombie(EnemigoBase):
    def __init__(self, textura_zombie, **kwargs):
        super().__init__(
            ruta_modelo='assets/modelos/character-j.fbx',
            ruta_textura=textura_zombie,
            **kwargs
        )
        self.vida = 80
        self.velocidad_normal = 12
        self.velocidad = self.velocidad_normal
        self.frenesi = False

    def update(self):
        super().update() # Ejecutar lógica base (movimiento, gravedad, IA base)
        
        # --- FRENESÍ ZOMBIE ---
        # Si su vida baja de la mitad, se vuelve loco y corre rapidísimo
        if self.vida_maxima and self.vida < (self.vida_maxima / 2) and not self.frenesi and not self.curando:
            self.frenesi = True
            self.velocidad = self.velocidad_normal * 2.5 
            
            # Efecto visual de furia (Usamos set_color_scale para no borrar la textura)
            self.modelo_visual.set_color_scale((1, 0.4, 0.4, 1))
