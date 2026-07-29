from ursina import Entity, color, time, Vec3, destroy, distance

class PowerUp(Entity):
    def __init__(self, tipo, position, **kwargs):
        super().__init__(position=position, **kwargs)
        self.tipo = tipo # 'vida', 'botiquin', 'municion'
        
        # Geometría básica para placeholder (fácil de reemplazar por modelo real)
        self.y = position.y + 0.5 # Flotar un poco sobre el suelo
        
        if self.tipo == 'arma':
            self.model = 'assets/modelos/objetos_con_meshy/arma.glb'
            self.scale = 0.3
            self.color = color.white
        else:
            self.model = 'cube'
            self.scale = 0.5
            
        self.collider = 'box'
        
        # Colores identificativos
        if self.tipo == 'max_salud':
            self.color = color.green
        elif self.tipo == 'max_municion':
            self.color = color.yellow
        elif self.tipo == 'insta_kill':
            self.color = color.red
        elif self.tipo == 'bomba':
            self.color = color.orange
        elif self.tipo == 'doble_cadencia':
            self.color = color.magenta
        elif self.tipo == 'recarga_rapida':
            self.color = color.blue
        elif self.tipo == 'velocidad':
            self.color = color.azure
        elif self.tipo != 'arma':
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
        if self.tipo == 'max_salud':
            jugador.vida = 100
            if hasattr(jugador, 'mostrar_mensaje_powerup'): jugador.mostrar_mensaje_powerup("¡SALUD MÁXIMA!")
        elif self.tipo == 'max_municion':
            if hasattr(jugador, 'balas_cargador'):
                jugador.balas_cargador = getattr(jugador, 'balas_cargador_max', 25)
                jugador.balas_reserva = getattr(jugador, 'balas_reserva_max', 300)
                if hasattr(jugador, 'actualizar_hud_municion'): jugador.actualizar_hud_municion()
            if hasattr(jugador, 'mostrar_mensaje_powerup'): jugador.mostrar_mensaje_powerup("¡MUNICIÓN MÁXIMA!")
        elif self.tipo == 'bomba':
            if hasattr(jugador, 'mostrar_mensaje_powerup'): jugador.mostrar_mensaje_powerup("¡BOMBA TÁCTICA!")
            from ursina import scene
            for e in scene.entities:
                if hasattr(e, 'vida') and hasattr(e, 'recibir_dano') and e != jugador and e.y > -100:
                    e.recibir_dano(9999) # Matar a todos los enemigos activos
        elif self.tipo == 'arma':
            if hasattr(jugador, 'equipar_arma'):
                jugador.equipar_arma(modelo_existente=self)
            self.tiempo_vida = 999999
            if hasattr(self, 'update'):
                self.update = lambda: None
            return
        elif self.tipo in ['velocidad', 'insta_kill', 'doble_cadencia', 'recarga_rapida']:
            if hasattr(jugador, 'activar_powerup'):
                nombres = {
                    'velocidad': 'Velocidad Extrema', 
                    'insta_kill': 'Baja Instantánea', 
                    'doble_cadencia': 'Doble Cadencia',
                    'recarga_rapida': 'Recarga Rápida'
                }
                jugador.activar_powerup(self.tipo, duracion=20.0, nombre_mostrar=nombres.get(self.tipo, self.tipo))
            
        # Actualizar la interfaz de usuario del jugador para reflejar cambios en salud
        if hasattr(jugador, 'texto_vida'):
            jugador.texto_vida.text = f'{max(0, jugador.vida)} / 100'
        if hasattr(jugador, 'barra_vida_fg'):
            jugador.barra_vida_fg.scale_x = max(jugador.vida / 100.0, 0.0)
            
        # Reproducir sonido general de powerup si existiera
        
        # Destruir el powerup
        destroy(self)
