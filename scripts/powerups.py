from ursina import Entity, color, time, Vec3, destroy, distance

class PowerUp(Entity):
    def __init__(self, tipo, position, **kwargs):
        super().__init__(position=position, **kwargs)
        self.tipo = tipo # 'vida', 'botiquin', 'municion'
        
        # Geometría básica para placeholder (fácil de reemplazar por modelo real)
        self.model = 'cube'
        self.scale = 0.5
        self.y = position.y + 0.5 # Flotar un poco sobre el suelo
        self.collider = 'box'
        
        # Colores identificativos provisionales
        if self.tipo == 'vida':
            self.color = color.red
        elif self.tipo == 'botiquin':
            self.color = color.green
        elif self.tipo == 'municion':
            self.color = color.yellow
        else:
            self.color = color.white
            
        self.tiempo_vida = 15.0 # Desaparecer después de 15 segundos para no llenar la memoria
        self.creacion = time.time()
        
        # Animación de flotar (girar constantemente)
        self.animate_rotation_y(360, duration=2, loop=True)
        
    def update(self):
        # Desaparecer si pasa su tiempo de vida
        if time.time() - self.creacion > self.tiempo_vida:
            destroy(self)
            return
            
        # Importación local para evitar dependencias circulares
        from scripts.jugador import Jugador
        from ursina import scene
        
        # Comprobar colisión por distancia (más óptimo para placeholders rápidos que el sistema de físicas complejo)
        for e in scene.entities:
            if isinstance(e, Jugador):
                # Si el jugador está cerca (radio de recogida)
                dist = distance(self.position, e.position)
                if dist < 2.0:
                    self.recoger(e)
                    break
                    
    def recoger(self, jugador):
        # Lógica al recoger el powerup
        if self.tipo == 'vida':
            jugador.vida = min(jugador.vida + 10, 100)
            print("¡Recogiste una pequeña porción de Vida (+10)!")
        elif self.tipo == 'botiquin':
            jugador.vida = min(jugador.vida + 50, 100)
            print("¡Recogiste un Botiquín (+50 Vida)!")
        elif self.tipo == 'municion':
            # Asumimos que el jugador tendrá atributo municion en el futuro o en otro script
            if not hasattr(jugador, 'municion'):
                jugador.municion = 0
            jugador.municion += 30
            print(f"¡Recogiste Munición! (Munición actual: {jugador.municion})")
            
        # Actualizar la interfaz de usuario del jugador para reflejar cambios en salud
        if hasattr(jugador, 'texto_vida'):
            jugador.texto_vida.text = f'{max(0, jugador.vida)} / 100'
        if hasattr(jugador, 'barra_vida_fg'):
            jugador.barra_vida_fg.scale_x = max(jugador.vida / 100.0, 0.0)
            
        destroy(self)
