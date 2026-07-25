from ursina import Entity, Vec3, time, distance, color, destroy, raycast, load_texture
from direct.actor.Actor import Actor
import math

class IceLaser(Entity):
    def __init__(self, posicion_inicial, forward_dir, boss, **kwargs):
        super().__init__(
            model='cube',
            color=color.rgba(0, 255, 255, 200),
            scale=(0.5, 0.5, 50),
            position=posicion_inicial + forward_dir * 25, 
            # El centro del cubo está a la mitad, así que lo desplazamos hacia adelante
            unlit=True,
            **kwargs
        )
        self.look_at(self.position + forward_dir)
        self.boss = boss
        self.tiempo_creacion = time.time()
        self.duracion = 2.0
        self.dano_por_segundo = 20
        self.forward_dir = forward_dir
        self.origen = posicion_inicial

    def update(self):
        if time.time() - self.tiempo_creacion > self.duracion or not self.boss or self.boss.estado_actual == 'dead':
            destroy(self)
            return

        # Daño continuo con Raycast
        # Lanzamos raycast a lo largo del láser
        if self.boss.jugador_objetivo and not self.boss.jugador_objetivo.esta_muerto:
            # Comprobamos distancia perpendicular al rayo o hacemos raycast ancho
            # Para simplificar, lanzamos un rayo invisible desde el origen
            hit_info = raycast(self.origen, self.forward_dir, distance=50, ignore=(self.boss, self))
            if hit_info.hit and hit_info.entity == self.boss.jugador_objetivo:
                self.boss.jugador_objetivo.recibir_dano(self.dano_por_segundo * time.dt)
                
            # Efecto visual de parpadeo
            self.color = color.rgba(0, 255, 255, int(150 + math.sin(time.time()*20)*50))

class IceAura(Entity):
    def __init__(self, posicion, duracion=5.0, jugador=None, **kwargs):
        # Aseguramos que el aura esté pegada al suelo
        super().__init__(
            model='circle',
            color=color.rgba(100, 150, 255, 120),
            scale=(10, 10, 10), # Radio de 5m (diámetro 10)
            position=Vec3(posicion.x, 0.05, posicion.z),
            rotation_x=90,
            unlit=True,
            **kwargs
        )
        self.tiempo_creacion = time.time()
        self.duracion = duracion
        self.jugador = jugador
        self.radio = 5.0

    def update(self):
        if time.time() - self.tiempo_creacion > self.duracion:
            if self.jugador:
                self.jugador.congelado = False
            destroy(self)
            return
            
        # Parpadeo suave
        self.color = color.rgba(100, 150, 255, int(80 + math.sin(time.time()*5)*40))
        
        # Lógica de congelamiento
        if self.jugador and not self.jugador.esta_muerto:
            dist = distance(self.position, Vec3(self.jugador.position.x, 0, self.jugador.position.z))
            if dist <= self.radio:
                self.jugador.congelado = True
            else:
                self.jugador.congelado = False


class BrujaBoss(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(position=position, **kwargs)
        
        self.altura_vuelo = 1.5
        self.y = self.altura_vuelo
        
        self.modelo_visual = Entity(parent=self, rotation_y=180, scale=2.8)
        
        ruta_base = "assets/modelos/villians/bruja_de_hielo/"
        try:
            self.actor = Actor(
                ruta_base + "witch_idle.glb",
                {
                    'idle': ruta_base + 'witch_idle.glb',
                    'fly': ruta_base + 'witch_fly.glb',
                    'pre_attack': ruta_base + 'witch_pre_attack.glb',
                    'laser': ruta_base + 'witch_laser.glb',
                    'aoe': ruta_base + 'witch_aoe.glb',
                    'hit': ruta_base + 'witch_hit.glb',
                    'dead': ruta_base + 'witch_dead.glb'
                }
            )
            self.actor.reparentTo(self.modelo_visual)
            self.actor.loop('idle')
            self.estado_actual = 'idle'
            self.actor.setBlend(frameBlend=True)
        except Exception as e:
            print(f"Error cargando Bruja: {e}")
            self.actor = None
            self.modelo_visual.model = 'cube'
            self.modelo_visual.color = color.cyan
            self.estado_actual = 'error'

        self.vida_maxima = 300
        self.vida = self.vida_maxima
        self.velocidad = 15
        
        # IA y Tiempos
        self.jugador_objetivo = None
        self.distancia_deteccion = 80
        
        self.cooldown_ataque = 4.0
        self.ultimo_ataque = time.time()
        
        self.cooldown_aoe = 10.0
        self.ultimo_aoe = time.time()
        
        # UI Barra de vida
        self.barra_vida_bg = Entity(parent=self, model='quad', color=color.black, scale=(3, 0.3), position=(0, 4.5, 0), billboard=True)
        self.barra_vida_fg = Entity(parent=self.barra_vida_bg, model='quad', color=color.red, scale=(1, 1), position=(-0.5, 0, -0.01), origin=(-0.5, 0))

    def buscar_jugador(self):
        from scripts.jugador import Jugador
        from ursina import scene
        for e in scene.entities:
            if isinstance(e, Jugador):
                return e
        return None

    def recibir_dano(self, cantidad):
        if self.estado_actual == 'dead': return
        self.vida -= cantidad
        
        porcentaje = max(0, self.vida / self.vida_maxima)
        self.barra_vida_fg.scale_x = porcentaje
        
        if self.vida <= 0:
            self.morir()
        else:
            # Hit reaction solo si no está tirando un hechizo crucial
            if self.estado_actual not in ['laser', 'aoe'] and self.actor:
                self.cambiar_estado('hit')
                from ursina import invoke
                invoke(self.volver_a_idle, delay=0.5)

    def volver_a_idle(self):
        if self.estado_actual != 'dead':
            self.cambiar_estado('idle')

    def morir(self):
        self.cambiar_estado('dead')
        self.barra_vida_fg.color = color.black
        
        # Efecto de caída dramática (cae al piso)
        self.animate_y(0.1, duration=1.0)
        
        # Desactivamos collider si lo tuviera (por ahora no usamos colisionadores físicos nativos, pero lo prevemos)
        if hasattr(self, 'collider'):
            destroy(self.collider)

    def cambiar_estado(self, nuevo_estado):
        if not self.actor or self.estado_actual == 'dead': return
        
        if self.estado_actual != nuevo_estado:
            if nuevo_estado in ['idle', 'fly']:
                self.actor.loop(nuevo_estado)
            else:
                self.actor.play(nuevo_estado)
            
            self.estado_actual = nuevo_estado
            
            # Inclinación fantasmagórica al volar
            if nuevo_estado == 'fly':
                self.modelo_visual.animate_rotation_x(20, duration=0.3)
            else:
                self.modelo_visual.animate_rotation_x(0, duration=0.3)

    def lanzar_laser(self):
        if self.estado_actual == 'dead' or not self.jugador_objetivo: return
        self.cambiar_estado('laser')
        
        # Apuntar al jugador (fijo, no lo sigue)
        dir_hacia_jugador = (self.jugador_objetivo.position - self.position).normalized()
        dir_hacia_jugador.y = 0
        self.look_at_2d(self.position + dir_hacia_jugador, 'y')
        
        # Esperamos que termine la animación de preparación para lanzar el láser (ej: 0.5s)
        from ursina import invoke
        invoke(lambda: IceLaser(self.position + Vec3(0,1,0), self.forward, self) if self.estado_actual != 'dead' else None, delay=0.5)
        
        # Volver a idle después de lanzar
        invoke(self.volver_a_idle, delay=2.5)

    def lanzar_aoe(self):
        if self.estado_actual == 'dead' or not self.jugador_objetivo: return
        self.cambiar_estado('aoe')
        
        from ursina import invoke
        invoke(lambda: IceAura(self.position, 6.0, self.jugador_objetivo) if self.estado_actual != 'dead' else None, delay=0.6)
        
        invoke(self.volver_a_idle, delay=2.0)

    def update(self):
        if self.estado_actual == 'dead':
            return
            
        # Animación flotante suave
        self.y = self.altura_vuelo + math.sin(time.time() * 2) * 0.3

        if not self.jugador_objetivo:
            self.jugador_objetivo = self.buscar_jugador()
            return
            
        if self.jugador_objetivo.esta_muerto:
            self.cambiar_estado('idle')
            return

        dist = distance(self.position, self.jugador_objetivo.position)
        
        if dist > self.distancia_deteccion:
            self.cambiar_estado('idle')
            return
            
        # Lógica de IA
        if self.estado_actual in ['idle', 'fly']:
            self.look_at_2d(self.jugador_objetivo.position, 'y')
            
            puede_tirar_aoe = (time.time() - self.ultimo_aoe > self.cooldown_aoe)
            puede_tirar_laser = (time.time() - self.ultimo_ataque > self.cooldown_ataque)
            
            if dist < 8 and puede_tirar_aoe:
                # Si el jugador está muy cerca, lanza el área congelante para ralentizarlo
                self.lanzar_aoe()
                self.ultimo_aoe = time.time()
                self.ultimo_ataque = time.time() # Resetea ambos para no encadenar ataques tan rápido
            
            elif dist < 30 and puede_tirar_laser:
                # Si está a distancia media, usa el pre_attack y luego el láser
                self.cambiar_estado('pre_attack')
                from ursina import invoke
                invoke(self.lanzar_laser, delay=0.8)
                self.ultimo_ataque = time.time()
                
            elif dist > 15:
                # Acercarse al jugador si está lejos
                direccion = (self.jugador_objetivo.position - self.position).normalized()
                direccion.y = 0
                self.position += direccion * self.velocidad * time.dt
                self.cambiar_estado('fly')
            else:
                self.cambiar_estado('idle')
