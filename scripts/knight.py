from ursina import Entity, color, time, Vec3, destroy, held_keys
from direct.actor.Actor import Actor

class KnightBoss(Entity):
    def __init__(self, vida_maxima_override=None, **kwargs):
        super().__init__(**kwargs)
        
        # --- CARGA DEL MODELO ANIMADO GLB ---
        ruta_base = "assets/modelos/villians/knight/"
        
        self.modelo_visual = Entity(parent=self)
        
        try:
            # Usamos knight_animation_walking.glb como base (contiene malla y esqueleto)
            # Y mapeamos las animaciones desde los otros archivos
            self.actor = Actor(
                ruta_base + "knight_animation_walking.glb",
                {
                    'idle': ruta_base + 'knight_animation_walking.glb',
                    'walk': ruta_base + 'knight_animation_walking.glb',
                    'run': ruta_base + 'knight_animation_run.glb',
                    'attack': ruta_base + 'knight_attack.glb',
                    'dance': ruta_base + 'knigth_dance_boom.glb'
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
            print(f"ERROR CARGANDO EL KNIGHT GLB: {e}")
            print(f"=================================")
            self.actor = None
            self.modelo_visual.model = 'cube'
            self.modelo_visual.color = color.blue
            self.estado_actual = 'error'
        
        # Rotamos para que nos vea de frente
        self.modelo_visual.rotation_y = 180
        
        # Hacemos al jefe masivo (sin alterar Y para que sus pies se queden pegados al piso tras la marometa)
        self.modelo_visual.scale = 3.5
        
        # Hitbox
        from ursina import BoxCollider
        self.collider = BoxCollider(self, center=Vec3(0, 1.5, 0), size=Vec3(1.5, 3, 1.5))
        
        self.vida_maxima = vida_maxima_override if vida_maxima_override else 1500
        self.vida = self.vida_maxima
        self.velocidad_caminar = 3.0
        self.velocidad_correr = 6.0
        self.rango_ataque = 4.0
        self.tiempo_vivo = 0.0
        
        self.tiempo_entre_ataques = 2.5
        self.ultimo_ataque = 0

    def recibir_dano(self, cantidad):
        self.vida -= cantidad
        if self.actor:
            self.actor.setColorScale(1, 0, 0, 1) 
            from ursina import invoke
            def reset_color():
                if self.actor:
                    self.actor.clearColorScale()
            invoke(reset_color, delay=0.1)

        if self.vida <= 0 and self.estado_actual != 'dead':
            self.morir()

    def morir(self):
        self.estado_actual = 'dead'
        if self.actor:
            # No tenemos animación de morir aún, así que le ponemos la de ataque y lo destruimos
            self.actor.play('attack')
            
        # --- DROP POWERUP ---
        from scripts.powerups import PowerUp
        import random
        tipos = ['max_salud', 'max_municion', 'insta_kill', 'bomba', 'doble_cadencia', 'recarga_rapida', 'velocidad']
        PowerUp(random.choice(tipos), position=self.position)
        
        destroy(self, delay=2)

    def update(self):
        self.tiempo_vivo += time.dt
        
        if self.estado_actual == 'dead':
            return
            
        # --- IA DEL CABALLERO ---
        if not hasattr(self, 'jugador_objetivo') or self.jugador_objetivo is None:
            from scripts.jugador import Jugador
            from ursina import scene
            for e in scene.entities:
                if isinstance(e, Jugador):
                    self.jugador_objetivo = e
                    break
            else:
                return # No hay jugador todavía
                
        jugador = self.jugador_objetivo
        if jugador.esta_muerto: return
        
        direccion = jugador.position - self.position
        direccion.y = 0 
            
        objetivo = Vec3(jugador.x, self.y, jugador.z)
        
        if direccion.length() > 15:
            # Muy lejos: Correr
            if self.estado_actual != 'run' and self.estado_actual != 'attack':
                if self.actor: self.actor.loop('run')
                self.estado_actual = 'run'
            if self.estado_actual != 'attack':
                self.position += direccion.normalized() * self.velocidad_correr * time.dt
                self.look_at(objetivo)
            
        elif direccion.length() > self.rango_ataque:
            # Cerca: Caminar hacia el jugador
            if self.estado_actual != 'walk' and self.estado_actual != 'attack':
                if self.actor: self.actor.loop('walk')
                self.estado_actual = 'walk'
            if self.estado_actual != 'attack':
                self.position += direccion.normalized() * self.velocidad_caminar * time.dt
                self.look_at(objetivo)
            
        else:
            # Muy cerca: Atacar
            if time.time() - self.ultimo_ataque > self.tiempo_entre_ataques:
                if self.estado_actual != 'attack' and self.actor:
                    self.actor.play('attack')
                    self.estado_actual = 'attack'
                    self.ultimo_ataque = time.time()
                    
                    # Aplicar daño después de 0.5s para sincronizar con la espada
                    from ursina import invoke
                    def aplicar_dano():
                        if self.estado_actual != 'dead' and self.jugador_objetivo and not self.jugador_objetivo.esta_muerto:
                            d = (self.jugador_objetivo.position - self.position).length()
                            if d <= self.rango_ataque + 2:
                                self.jugador_objetivo.recibir_dano(45)
                    invoke(aplicar_dano, delay=0.5)
                    
                    # Volver a idle después del golpe
                    invoke(lambda: setattr(self, 'estado_actual', 'idle'), delay=1.5)
            else:
                if self.estado_actual != 'attack' and self.estado_actual != 'idle':
                    self.estado_actual = 'idle'
                    if self.actor: self.actor.loop('idle')
                    
            if self.estado_actual != 'attack':
                self.look_at(objetivo)
