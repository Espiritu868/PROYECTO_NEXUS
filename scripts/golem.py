from ursina import Entity, color, time, Vec3, destroy
from direct.actor.Actor import Actor

class GolemBoss(Entity):
    def __init__(self, vida_maxima_override=None, **kwargs):
        super().__init__(**kwargs)
        
        # --- CARGA DEL MODELO ANIMADO GLB ---
        ruta_base = "assets/modelos/villians/golem/"
        
        self.modelo_visual = Entity(parent=self)
        
        try:
            # Usamos golem_walk.glb como base (contiene malla y esqueleto)
            # Y mapeamos las animaciones desde los otros archivos
            self.actor = Actor(
                ruta_base + "golem_walk.glb",
                {
                    'idle': ruta_base + 'golem_idle.glb',
                    'walk': ruta_base + 'golem_walk.glb',
                    'run': ruta_base + 'golem_run.glb',
                    'attack': ruta_base + 'golem_attack.glb',
                    'arise': ruta_base + 'golem_arise.glb'
                }
            )
            self.actor.reparentTo(self.modelo_visual)
            
            # Animación inicial
            self.actor.loop('idle')
            self.estado_actual = 'idle'
            
            # Hacer que se vea más brillante (Multiplicamos los colores x1.5)
            self.actor.setColorScale(1.5, 1.5, 1.5, 1)
            
        except Exception as e:
            print(f"=================================")
            print(f"ERROR CARGANDO EL GOLEM GLB: {e}")
            print(f"=================================")
            self.actor = None
            self.modelo_visual.model = 'cube'
            self.modelo_visual.color = color.red
            self.estado_actual = 'error'
        
        # Rotamos para que nos vea de frente (Meshy suele exportar de espaldas o invertido)
        self.modelo_visual.rotation_y = 180
        
        # Hacemos al jefe masivo
        self.modelo_visual.scale = 3.5
        
        # Hitbox masivo para el jefe
        from ursina import BoxCollider
        self.collider = BoxCollider(self, center=Vec3(0, 2.5, 0), size=Vec3(3, 5, 3))
        
        # --- SISTEMA DE COMBATE (VIDA Y DAÑO) ---
        self.vida_maxima = vida_maxima_override if vida_maxima_override else 1000
        self.vida = self.vida_maxima
        self.velocidad_caminar = 2.0
        self.velocidad_correr = 5.0
        self.rango_ataque = 5.0
        self.tiempo_vivo = 0.0
        self.ultimo_ataque = 0
        self.tiempo_entre_ataques = 3.0
        self.esta_muerto = False
        
        # Barra de vida del Jefe UI
        self.barra_vida_fondo = Entity(parent=self, model='quad', color=color.black, scale=(4, 0.4), y=6, billboard=True)
        self.barra_vida_roja = Entity(parent=self.barra_vida_fondo, model='quad', color=color.red, scale=(1, 1), x=-0.5, origin=(-0.5, 0), z=-0.01)

    def recibir_dano(self, cantidad):
        if self.esta_muerto:
            return
            
        self.vida -= cantidad
        
        # Actualizar visualmente la barra
        porcentaje = max(0, self.vida / self.vida_maxima)
        self.barra_vida_roja.scale_x = porcentaje
        
        print(f"¡Golem dañado! Vida restante: {self.vida}")
        
        if self.vida <= 0:
            self.morir()

    def morir(self):
        self.esta_muerto = True
        print("¡El Golem ha caído!")
        
        from ursina import destroy, color
        destroy(self.barra_vida_fondo)
        
        # --- DROP POWERUP ---
        from scripts.powerups import PowerUp
        import random
        tipos = ['max_salud', 'max_municion', 'insta_kill', 'bomba', 'doble_cadencia', 'recarga_rapida', 'velocidad']
        PowerUp(random.choice(tipos), position=self.position)
        
        if self.actor:
            # Usar la animación arise invertida si no hay una animación de muerte directa, o simplemente frenarlo
            self.actor.stop()
            self.actor.setColorScale(0.3, 0.3, 0.3, 1) # Se vuelve piedra grisácea
            
            # Secuencia de caída
            self.animate_rotation_x(90, duration=1.0)
            self.animate_y(self.y - 1, duration=1.0)
            
            # Desactivar colisiones para que el jugador pueda pasar por encima
            if hasattr(self, 'collider') and self.collider:
                self.collider.clear()


    def emerger(self):
        from ursina import invoke
        self.estado_actual = 'arise'
        if self.actor:
            self.actor.play('arise')
        # La animación de arise dura aprox 2-3 segundos, bloqueamos a la IA ese tiempo
        self.tiempo_emergiendo = 3.0

    def update(self):
        if self.esta_muerto:
            return
            
        # Bloquear IA si está emergiendo
        if getattr(self, 'tiempo_emergiendo', 0) > 0:
            self.tiempo_emergiendo -= time.dt
            if self.tiempo_emergiendo <= 0:
                self.estado_actual = 'idle'
                if self.actor:
                    self.actor.loop('idle')
            return
            
        if self.estado_actual == 'dead':
            return
            
        # --- IA DEL GOLEM ---
        import __main__ as main
        if hasattr(main, 'jugador_principal'):
            jugador = main.jugador_principal
            if jugador.esta_muerto:
                return
                
            direccion = jugador.position - self.position
            direccion.y = 0 
            distancia = direccion.length()
            
            objetivo = Vec3(jugador.x, self.y, jugador.z)
            self.look_at(objetivo)
            
            # --- COMBATE ---
            if distancia <= self.rango_ataque:
                if time.time() - self.ultimo_ataque > self.tiempo_entre_ataques:
                    self.estado_actual = 'attack'
                    self.ultimo_ataque = time.time()
                    if self.actor:
                        self.actor.play('attack')
                    # Dañar al jugador
                    jugador.recibir_dano(40)
                    
                    # Regresar a idle después del golpe
                    from ursina import invoke
                    invoke(lambda: setattr(self, 'estado_actual', 'idle'), delay=1.0)
            else:
                if self.estado_actual != 'attack':
                    if distancia > 20:
                        self.estado_actual = 'run'
                    else:
                        self.estado_actual = 'walk'
                    
            # --- MOVIMIENTO Y ANIMACIONES ---
            if self.estado_actual == 'run':
                if self.actor and self.actor.getCurrentAnim() != 'run':
                    self.actor.loop('run')
                self.position += self.forward * self.velocidad_correr * time.dt
            elif self.estado_actual == 'walk':
                if self.actor and self.actor.getCurrentAnim() != 'walk':
                    self.actor.loop('walk')
                self.position += self.forward * self.velocidad_caminar * time.dt
            elif self.estado_actual == 'idle':
                if self.actor and self.actor.getCurrentAnim() != 'idle':
                    self.actor.loop('idle')
