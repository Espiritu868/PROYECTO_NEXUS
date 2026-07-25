from ursina import Entity, Vec3, time, distance, color, destroy, raycast
from direct.actor.Actor import Actor
import math
import random

class BolaFuego(Entity):
    def __init__(self, posicion_inicial, direccion, boss, **kwargs):
        super().__init__(
            model='sphere',
            color=color.orange,
            scale=1.5,
            position=posicion_inicial,
            collider='sphere',
            **kwargs
        )
        self.direccion = direccion.normalized()
        self.velocidad = 40
        self.boss = boss
        self.tiempo_creacion = time.time()
        
        # Efecto visual de brillo
        from ursina import PointLight
        self.luz = PointLight(parent=self, color=color.orange)

    def update(self):
        if time.time() - self.tiempo_creacion > 5.0:
            destroy(self)
            return
            
        desplazamiento = self.direccion * self.velocidad * time.dt
        
        # Comprobar impacto (raycast un poco hacia adelante)
        hit_info = raycast(self.position, self.direccion, distance=self.velocidad * time.dt + 1.0, ignore=(self, self.boss, self.boss.modelo_visual))
        
        if hit_info.hit:
            self.explotar(hit_info.world_point)
        else:
            self.position += desplazamiento
            
    def explotar(self, punto_impacto):
        # Explosión AOE (Area de Efecto)
        radio_explosion = 5.0
        dano_explosion = 40
        
        if self.boss and self.boss.jugador_objetivo and not self.boss.jugador_objetivo.esta_muerto:
            dist = distance(punto_impacto, self.boss.jugador_objetivo.position)
            if dist < radio_explosion:
                self.boss.jugador_objetivo.recibir_dano(dano_explosion)
                
        # TODO: Añadir partículas de explosión visual (ahora solo destruimos el proyectil)
        destroy(self)

class DragonBoss(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(position=position, **kwargs)
        
        self.y_suelo = position[1]
        self.y = self.y_suelo
        
        # El dragón es colosal. Escala 4.0
        self.modelo_visual = Entity(parent=self, rotation_y=180, scale=4.0)
        
        ruta_base = "assets/modelos/villians/dragon/"
        try:
            self.actor = Actor(
                ruta_base + "dragon_idle.glb",
                {
                    'idle': ruta_base + 'dragon_idle.glb',
                    'walk': ruta_base + 'dragon_walk.glb',
                    'run': ruta_base + 'dragon_run.glb',
                    'arise': ruta_base + 'dragon_arise.glb',
                    'sweep': ruta_base + 'dragon_attack_sweep.glb',
                    'spell': ruta_base + 'dragon_spell.glb',
                    'taunt': ruta_base + 'dragon_taunt.glb',
                    'takeoff': ruta_base + 'dragon_takeoff.glb',
                    'fly_idle': ruta_base + 'dragon_fly_idle.glb',
                    'land': ruta_base + 'dragon_land.glb',
                    'hit': ruta_base + 'dragon_hit.glb',
                    'dead': ruta_base + 'dragon_dead.glb'
                }
            )
            self.actor.reparentTo(self.modelo_visual)
            self.actor.play('arise')
            self.estado_animacion = 'arise'
            self.actor.setBlend(frameBlend=True)
        except Exception as e:
            print(f"Error cargando Dragón: {e}")
            self.actor = None
            self.modelo_visual.model = 'cube'
            self.modelo_visual.color = color.black
            self.estado_animacion = 'error'

        self.vida_maxima = 1000
        self.vida = self.vida_maxima
        self.fase = 1 # Fase 1: Suelo, Fase 2: Cielo
        
        self.velocidad_caminar = 8
        self.velocidad_correr = 25
        self.velocidad_vuelo = 35
        
        # IA y Tiempos
        self.jugador_objetivo = None
        self.distancia_deteccion = 150
        
        self.cooldown_ataque = 2.5
        self.ultimo_ataque = time.time()
        
        # UI Barra de vida masiva
        self.barra_vida_bg = Entity(parent=self, model='quad', color=color.black, scale=(5, 0.4), position=(0, 7.0, 0), billboard=True)
        self.barra_vida_fg = Entity(parent=self.barra_vida_bg, model='quad', color=color.rgba(0.8, 0.1, 0.1, 1), scale=(1, 1), position=(-0.5, 0, -0.01), origin=(-0.5, 0))

        # Al terminar arise, pasamos a idle
        from ursina import invoke
        invoke(self.volver_a_idle, delay=3.0)

    def buscar_jugador(self):
        from scripts.jugador import Jugador
        from ursina import scene
        for e in scene.entities:
            if isinstance(e, Jugador):
                return e
        return None

    def recibir_dano(self, cantidad):
        if self.estado_animacion == 'dead' or self.estado_animacion == 'arise': return
        
        self.vida -= cantidad
        
        porcentaje = max(0, self.vida / self.vida_maxima)
        self.barra_vida_fg.scale_x = porcentaje
        
        if self.vida <= 0:
            self.morir()
        else:
            # Cambio de fase al 50%
            if self.vida <= self.vida_maxima / 2 and self.fase == 1:
                self.iniciar_fase_dos()
                return

            # Hit reaction ligero (no interrumpe vuelo ni ataques potentes)
            if self.fase == 1 and self.estado_animacion in ['idle', 'walk', 'run'] and self.actor:
                self.cambiar_animacion('hit')
                from ursina import invoke
                invoke(self.volver_a_idle, delay=0.5)

    def iniciar_fase_dos(self):
        self.fase = 2
        self.cambiar_animacion('takeoff')
        
        # Elevar al dragón físicamente (animación + movimiento real)
        self.animate_y(self.y_suelo + 25, duration=1.5)
        
        from ursina import invoke
        invoke(lambda: self.cambiar_animacion('fly_idle'), delay=1.5)

    def volver_a_idle(self):
        if self.estado_animacion != 'dead':
            if self.fase == 1:
                self.cambiar_animacion('idle')
            else:
                self.cambiar_animacion('fly_idle')

    def morir(self):
        self.cambiar_animacion('dead')
        self.barra_vida_fg.color = color.black
        
        # Si estaba volando, cae en picada
        if self.y > self.y_suelo + 1:
            self.animate_y(self.y_suelo, duration=1.0)
            
        if hasattr(self, 'collider'):
            destroy(self.collider)

    def cambiar_animacion(self, nueva_anim):
        if not self.actor or self.estado_animacion == 'dead': return
        
        if self.estado_animacion != nueva_anim:
            if nueva_anim in ['idle', 'walk', 'run', 'fly_idle']:
                self.actor.loop(nueva_anim)
            else:
                self.actor.play(nueva_anim)
            self.estado_animacion = nueva_anim

    def lanzar_bola_fuego(self):
        if self.estado_animacion == 'dead' or not self.jugador_objetivo: return
        self.cambiar_animacion('spell')
        
        # Ajustamos el origen (boca del dragón aproximadamente)
        offset_boca = self.position + Vec3(0, 5, 0) + self.forward * 4
        dir_hacia_jugador = (self.jugador_objetivo.position + Vec3(0,1,0)) - offset_boca
        
        from ursina import invoke
        invoke(lambda: BolaFuego(offset_boca, dir_hacia_jugador, self) if self.estado_animacion != 'dead' else None, delay=0.8)
        
        # Volver a idle
        invoke(self.volver_a_idle, delay=1.8)

    def ataque_cuerpo_a_cuerpo(self):
        if self.estado_animacion == 'dead' or not self.jugador_objetivo: return
        self.cambiar_animacion('sweep')
        
        # Daño masivo de área frontal
        from ursina import invoke
        def aplicar_dano():
            if self.estado_animacion == 'dead' or not self.jugador_objetivo: return
            dist = distance(self.position, self.jugador_objetivo.position)
            if dist < 12: # Rango enorme del dragón
                self.jugador_objetivo.recibir_dano(40)
        
        invoke(aplicar_dano, delay=0.6)
        invoke(self.volver_a_idle, delay=1.5)

    def ataque_picada(self):
        if self.estado_animacion == 'dead' or not self.jugador_objetivo: return
        self.cambiar_animacion('land')
        
        # Cae brutalmente donde estaba el jugador
        pos_objetivo = Vec3(self.jugador_objetivo.x, self.y_suelo, self.jugador_objetivo.z)
        
        self.animate_position(pos_objetivo, duration=0.8)
        
        from ursina import invoke
        def explosion_aterrizaje():
            if self.estado_animacion == 'dead': return
            dist = distance(self.position, self.jugador_objetivo.position)
            if dist < 15:
                self.jugador_objetivo.recibir_dano(60)
            
            # Subir de nuevo después de 3 segundos de masacrar en tierra
            invoke(self.iniciar_fase_dos, delay=3.0)
            
        invoke(explosion_aterrizaje, delay=0.8)

    def update(self):
        if self.estado_animacion == 'dead' or self.estado_animacion == 'arise':
            return
            
        # Animación flotante suave en Fase 2
        if self.fase == 2 and self.estado_animacion == 'fly_idle':
            self.y = (self.y_suelo + 25) + math.sin(time.time() * 2) * 1.5

        if not self.jugador_objetivo:
            self.jugador_objetivo = self.buscar_jugador()
            return
            
        if self.jugador_objetivo.esta_muerto:
            self.volver_a_idle()
            return

        dist = distance(self.position, self.jugador_objetivo.position)
        
        # IA Fase 1 (Tierra)
        if self.fase == 1 and self.estado_animacion in ['idle', 'walk', 'run']:
            self.look_at_2d(self.jugador_objetivo.position, 'y')
            
            puede_atacar = (time.time() - self.ultimo_ataque > self.cooldown_ataque)
            
            if dist < 10 and puede_atacar:
                self.ataque_cuerpo_a_cuerpo()
                self.ultimo_ataque = time.time()
                self.cooldown_ataque = random.uniform(2.0, 3.5)
            elif dist > 10 and dist < 40 and puede_atacar:
                # 30% chance de escupir fuego, 70% de correr a aplastar
                if random.random() < 0.3:
                    self.lanzar_bola_fuego()
                    self.ultimo_ataque = time.time()
                else:
                    direccion = (self.jugador_objetivo.position - self.position).normalized()
                    direccion.y = 0
                    self.position += direccion * self.velocidad_correr * time.dt
                    self.cambiar_animacion('run')
            elif dist >= 40:
                direccion = (self.jugador_objetivo.position - self.position).normalized()
                direccion.y = 0
                self.position += direccion * self.velocidad_caminar * time.dt
                self.cambiar_animacion('walk')
            else:
                self.cambiar_animacion('idle')

        # IA Fase 2 (Aire)
        elif self.fase == 2 and self.estado_animacion == 'fly_idle':
            # Mirar al jugador en 3D
            dir_hacia_jugador = (self.jugador_objetivo.position - self.position).normalized()
            self.look_at_2d(self.position + dir_hacia_jugador, 'y')
            
            puede_atacar = (time.time() - self.ultimo_ataque > self.cooldown_ataque)
            
            if puede_atacar:
                # 70% chance de escupir fuego, 30% chance de picada brutal
                if random.random() < 0.7:
                    self.lanzar_bola_fuego()
                else:
                    self.ataque_picada()
                    
                self.ultimo_ataque = time.time()
                self.cooldown_ataque = random.uniform(3.0, 5.0)
            else:
                # Flotar orbitando o persiguiendo suavemente
                dist_horizontal = distance(Vec3(self.x, 0, self.z), Vec3(self.jugador_objetivo.x, 0, self.jugador_objetivo.z))
                if dist_horizontal > 20:
                    dir_horizontal = Vec3(dir_hacia_jugador.x, 0, dir_hacia_jugador.z).normalized()
                    self.position += dir_horizontal * self.velocidad_vuelo * time.dt
