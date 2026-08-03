from ursina import Entity, color, time, Vec3, destroy, distance

def precargar_modelos_powerups():
    from ursina import load_model
    mapa_modelos = [
        'salud_maxima.glb', 'municion_maxima.glb', 'baja_instantanea.glb',
        'bomba_atomica.glb', 'balas_rapidas.glb', 'recarga_rapida.glb',
        'velocidad_extrema.glb'
    ]
    for archivo in mapa_modelos:
        load_model(f'assets/modelos/objetos_con_meshy/powerups/{archivo}')

class PowerUp(Entity):
    def __init__(self, tipo, position, **kwargs):
        super().__init__(position=position, **kwargs)
        self.tipo = tipo # 'vida', 'botiquin', 'municion'
        
        # Geometría básica para placeholder (fácil de reemplazar por modelo real)
        self.y = position.y + 1.2 # Flotar más arriba sobre el suelo
        
        mapa_modelos = {
            'max_salud': 'salud_maxima.glb',
            'max_municion': 'municion_maxima.glb',
            'insta_kill': 'baja_instantanea.glb',
            'bomba': 'bomba_atomica.glb',
            'doble_cadencia': 'balas_rapidas.glb',
            'recarga_rapida': 'recarga_rapida.glb',
            'velocidad': 'velocidad_extrema.glb'
        }
        
        if self.tipo == 'arma':
            self.model = 'assets/modelos/objetos_con_meshy/arma.glb'
            self.scale = 0.2
            self.color = color.white
        elif self.tipo in mapa_modelos:
            self.model = f'assets/modelos/objetos_con_meshy/powerups/{mapa_modelos[self.tipo]}'
            self.scale = 0.65 # Reducido de 1.0 para que se vean más pequeños
            self.color = color.white 
        else:
            self.model = 'cube'
            self.scale = 0.35
            self.color = color.white
            
        self.collider = 'box'
            
        self.tiempo_vida = 15.0 # Desaparecer después de 15 segundos para no llenar la memoria
        self.creacion = time.time()
        
        # Animación de flotar (girar constantemente)
        self.animate_rotation_y(360, duration=2, loop=True)
        
        # Efectos eliminados para dejar solo el objeto base
        
    def update(self):
        # Desaparecer si pasa su tiempo de vida
        if time.time() - self.creacion > self.tiempo_vida:
            destroy(self)
            return
            
        # Importación local para evitar dependencias circulares
        from scripts.jugador import Jugador
        # Comprobar colisión por distancia (más óptimo para placeholders rápidos que el sistema de físicas complejo)
        jugador = Jugador.instancia
        if jugador:
            # Si el jugador está cerca (radio de recogida)
            dist = distance(self.position, jugador.position)
            if dist < 2.0:
                self.recoger(jugador)
                    
    def recoger(self, jugador):
        # Lógica al recoger el powerup
        if self.tipo == 'max_salud':
            jugador.vida = getattr(jugador, 'vida_maxima', 100)
            if hasattr(jugador, 'mostrar_mensaje_powerup'): jugador.mostrar_mensaje_powerup("¡SALUD MÁXIMA!")
        elif self.tipo == 'max_municion':
            if hasattr(jugador, 'armas_inventario'):
                for arma in jugador.armas_inventario:
                    arma['balas_cargador'] = arma.get('max_cargador', 25)
                    arma['balas_reserva'] = arma.get('max_reserva', 300)
                if hasattr(jugador, 'actualizar_hud_municion'): jugador.actualizar_hud_municion()
            elif hasattr(jugador, 'balas_cargador'):
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
        vida_max = getattr(jugador, 'vida_maxima', 100)
        if hasattr(jugador, 'texto_vida'):
            jugador.texto_vida.text = f'{max(0, int(jugador.vida))} / {vida_max}'
        if hasattr(jugador, 'barra_vida_fg'):
            jugador.barra_vida_fg.scale_x = max(jugador.vida / float(vida_max), 0.0)
            
        # Reproducir sonido general de powerup si existiera
        
        # Destruir el powerup
        destroy(self)
