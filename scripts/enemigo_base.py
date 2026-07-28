from ursina import Entity, load_texture, time, Vec3, raycast, distance, scene, curve
import math

class EnemigoBase(Entity):
    def __init__(self, ruta_modelo, ruta_textura, base_folder='', prefix='', **kwargs):
        super().__init__(**kwargs)
        
        # --- SISTEMA DE ANIMACIÓN ACTOR PANDA3D ---
        from direct.actor.Actor import Actor
        
        if base_folder and prefix:
            self.actor = Actor(
                base_folder + prefix + 'Axe_Breathe_and_Look_Around_withSkin.glb',
                {
                    'idle': base_folder + prefix + 'Axe_Breathe_and_Look_Around_withSkin.glb',
                    'walk': base_folder + prefix + 'Walking_withSkin.glb',
                    'run': base_folder + prefix + 'Running_withSkin.glb',
                    'run_fast': base_folder + prefix + 'run_fast_8_withSkin.glb',
                    'attack': base_folder + prefix + 'Left_Hook_from_Guard_withSkin.glb',
                    'pain': base_folder + prefix + 'Head_Hold_in_Pain_withSkin.glb',
                    'die': base_folder + prefix + 'Zombie_Scream_withSkin.glb'
                }
            )
            # Vincular el Actor a esta Entidad de Ursina
            self.actor.reparentTo(self)
            self.actor.setScale(1.5) # Escala base al tamaño del jugador
            self.actor.setH(180) # Rotar 180 grados igual que el modelo antiguo
            
            # --- OPTIMIZACIÓN: Pre-cargar animaciones ---
            try:
                for anim in ['walk', 'run', 'run_fast', 'attack', 'pain', 'die']:
                    self.actor.getAnimControl(anim)
            except:
                pass
            
            # Estado inicial
            self.estado_animacion = 'idle'
            self.actor.loop('idle')
        else:
            # Fallback en caso de que un jefe siga usando el sistema viejo
            self.actor = None
            self.modelo_visual = Entity(parent=self, model=ruta_modelo, scale=0.01, rotation_y=180)
            if ruta_textura:
                t = load_texture(ruta_textura)
                if t: self.modelo_visual.set_texture(t._texture, 1)

            
        # --- COLISIONADOR ---
        from ursina import BoxCollider
        # Al no tener 'model' propio (sino un hijo escalado), definimos su tamaño de hitbox a mano.
        self.collider = BoxCollider(self, center=Vec3(0, 1, 0), size=Vec3(2, 3, 2))
        
        # --- ATRIBUTOS BASE ---
        self.velocidad = 0
        self.vida = 0
        self.vida_maxima = None
        
        # --- UI DE SALUD (BARRA FLOTANTE) ---
        from ursina import color
        self.barra_vida_fondo = Entity(
            parent=self,
            model='quad',
            color=color.black,
            scale=(2, 0.2, 1),
            position=(0, 3, 0),
            billboard=True # Siempre mira a la cámara
        )
        self.barra_vida_roja = Entity(
            parent=self.barra_vida_fondo,
            model='quad',
            color=color.red,
            scale=(1, 1, 1),
            position=(0, 0, -0.01),
            origin_x=-0.5, # Ancla a la izquierda
            x=-0.5
        )
        
        # --- IA Y FÍSICAS ---
        self.gravedad = 60
        self.velocidad_y = 0
        self.velocidad_salto = 15
        self.en_suelo = False
        
        self.distancia_deteccion = 50
        self.distancia_ataque = 2.5
        self.tiempo_entre_ataques = 1.5
        self.ultimo_ataque = 0
        self.jugador_objetivo = None
        
        self.curando = False
        self.curado = False
        
        self.ultimo_tiempo_esquiva = 0
        self.direccion_esquiva = 0
        
        # Optimización: Reducir raycasts
        self.tiempo_ultimo_raycast = 0
        self.obstaculo_enfrente = False

    def buscar_jugador(self):
        # Importación local para evitar importaciones circulares
        from scripts.jugador import Jugador
        for e in scene.entities:
            if isinstance(e, Jugador):
                return e
        return None

    def cambiar_animacion(self, anim, loop=True):
        if self.actor and self.estado_animacion != anim:
            self.estado_animacion = anim
            if loop:
                self.actor.loop(anim)
            else:
                self.actor.play(anim)

    def update(self):
        if self.curando and not self.curado:
            return
        elif self.curado:
            self.cambiar_animacion('idle')
            return

        # Buscar jugador si no lo tenemos aún
        if not self.jugador_objetivo:
            self.jugador_objetivo = self.buscar_jugador()
            if not self.jugador_objetivo:
                return # Si no hay jugador, el enemigo se queda quieto
                
        # --- CULLING ESPACIAL DE RENDIMIENTO ---
        # Si el enemigo está a más de 1000 metros del jugador, no calculamos IA ni físicas (Ahorra muchísimos FPS)
        if distance(self.position, self.jugador_objetivo.position) > 1000:
            return

        dist_jugador = distance(self, self.jugador_objetivo)
        
        # --- FÍSICAS DE GRAVEDAD OPTIMIZADAS ---
        # Eliminamos el costoso raycast() por cada frame por cada enemigo.
        # Ya que las arenas son planas en y=0, simplemente chocamos matemáticamente con el suelo.
        if self.y <= 0 and self.velocidad_y <= 0:
            self.y = 0
            self.velocidad_y = 0
            self.en_suelo = True
        else:
            self.velocidad_y -= self.gravedad * time.dt
            self.y += self.velocidad_y * time.dt
            self.en_suelo = False
            
        en_movimiento = False
        
        # --- LÓGICA DE IA ---
        if dist_jugador < self.distancia_deteccion:
            # Mirar al jugador en 2D (solo rotación Y)
            self.look_at_2d(self.jugador_objetivo.position, 'y')
            
            # Comportamiento dependiendo de la distancia
            if dist_jugador > self.distancia_ataque:
                # 1. Caminar hacia el jugador
                
                # OPTIMIZACIÓN DE RAYCAST: Solo revisar obstáculos 5 veces por segundo, no 60.
                if time.time() - self.tiempo_ultimo_raycast > 0.2:
                    self.tiempo_ultimo_raycast = time.time()
                    hit_obstaculo = raycast(self.position + Vec3(0, 0.5, 0), direction=self.forward, distance=2, ignore=(self, self.jugador_objetivo))
                    self.obstaculo_enfrente = hit_obstaculo.hit and hit_obstaculo.distance <= 0.5
                    
                    if hit_obstaculo.hit and self.en_suelo:
                        # Saltar obstáculo
                        self.velocidad_y = self.velocidad_salto
                        self.en_suelo = False
                
                # MICRO-PAUSA POST ATAQUE: Si acaba de atacar, se queda quieto 1 segundo
                if time.time() - self.ultimo_ataque > 1.0:
                    # Moverse hacia adelante si no hay pared frente a su cara
                    if not self.obstaculo_enfrente:
                        self.position += self.forward * self.velocidad * time.dt
                        en_movimiento = True
                        
                        # IA: ESQUIVA ALEATORIA (DASH LATERAL)
                        # Cada 3 segundos, tiene un 30% de probabilidad de hacer un dash a un lado
                        if time.time() - self.ultimo_tiempo_esquiva > 3.0:
                            import random
                            self.ultimo_tiempo_esquiva = time.time()
                            if random.random() < 0.3:
                                self.direccion_esquiva = random.choice([-1, 1])
                            else:
                                self.direccion_esquiva = 0
                                
                        # Aplicar esquiva si está activa
                        if time.time() - self.ultimo_tiempo_esquiva < 0.5 and self.direccion_esquiva != 0:
                            # Se mueve hacia los lados (self.right) a gran velocidad
                            self.position += self.right * (self.velocidad * 2.5) * self.direccion_esquiva * time.dt
            else:
                # 2. Atacar al jugador
                self.atacar()
                
        # --- ANIMACIONES PROCEDIMENTALES ---
        if self.actor:
            if time.time() - self.ultimo_ataque < 1.0:
                # Mantener animación de ataque
                pass
            elif self.en_suelo:
                if en_movimiento:
                    # Dependiendo de la velocidad, elige caminar o correr
                    if self.velocidad > 15:
                        self.cambiar_animacion('run_fast')
                    elif self.velocidad > 6:
                        self.cambiar_animacion('run')
                    else:
                        self.cambiar_animacion('walk')
                else:
                    self.cambiar_animacion('idle')
            else:
                self.cambiar_animacion('idle') # O alguna pose de salto si hubiera
        else:
            # Fallback para sistema viejo
            pass

    def recibir_dano(self, cantidad):
        if self.curando:
            return
            
        if self.vida_maxima is None:
            self.vida_maxima = max(1, self.vida) # Captura la vida máxima inicial
            
        self.vida -= cantidad
        
        if self.actor:
            self.cambiar_animacion('pain', loop=False)
            self.ultimo_ataque = time.time() # Reusamos este timer para que no sobreescriba la animación de dolor
        
        # --- KNOCKBACK (EMPUJE FÍSICO) ---
        if self.jugador_objetivo:
            # Calculamos el vector que va desde el jugador hasta el enemigo (dirección de la bala)
            direccion_empuje = self.position - self.jugador_objetivo.position
            direccion_empuje.y = 0 # No lo empujamos hacia el cielo
            if direccion_empuje.length() > 0:
                direccion_empuje = direccion_empuje.normalized()
                # Lo empujamos 1.5 metros hacia atrás bruscamente
                self.animate_position(self.position + (direccion_empuje * 1.5), duration=0.15, curve=curve.out_expo)
        
        # Actualizar visualmente la barra
        porcentaje = max(0, self.vida / self.vida_maxima)
        self.barra_vida_roja.scale_x = porcentaje
        
        print(f"¡Enemigo dañado! Vida restante: {self.vida}")
        if self.vida <= 0:
            self.curar()

    def cambiar_textura_y_bajar(self):
        from ursina import load_texture, color
        import random
        # Usamos cualquier textura de personaje que NO sea villano (ni l, ni o)
        texturas_civiles = ['a','b','c','d','e','f','g','h','i','j','k','m','n','p','q','r']
        textura_elegida = random.choice(texturas_civiles)
        tex = load_texture(f'assets/modelos/textures/texture-{textura_elegida}.png')
        
        if self.actor:
            # Los mutantes GLB no pueden cambiar de textura tan fácil por sus UVs complejos
            # Así que los dejamos amarillos o los ocultamos (hacemos que desaparezcan)
            self.actor.setColorScale(1, 1, 1, 1)
        else:
            if tex:
                self.modelo_visual.set_texture(tex._texture, 1)
            # Devolver el color a normal
            self.modelo_visual.color = color.white
        
        # Volver al piso
        self.animate_y(self.y - 3, duration=0.5)
        
        self.curado = True

    def curar(self):
        self.curando = True
        
        # --- SISTEMA DE DROPS (POWERUPS PROVISIONALES) ---
        import random
        from scripts.powerups import PowerUp
        
        # Check if first enemy defeated
        import __main__ as main
        if not getattr(main, 'primer_enemigo_derrotado', False):
            main.primer_enemigo_derrotado = True
            PowerUp(tipo='arma', position=self.position)
        else:
            # Probabilidad de soltar un objeto (ej. 60% de soltar algo)
            if random.random() < 0.60:
                # Puedes ajustar los pesos, por ejemplo es más común la munición o vida que un botiquín entero
                tipo_drop = random.choices(
                    population=['vida', 'botiquin', 'municion'],
                    weights=[0.4, 0.2, 0.4],
                    k=1
                )[0]
                # Spawnear el powerup en la posición actual del enemigo
                PowerUp(tipo=tipo_drop, position=self.position)
            
        # Detenemos al enemigo
        self.velocidad = 0
        self.jugador_objetivo = None 
        
        # Ocultamos la barra de vida al morir
        from ursina import destroy, color
        destroy(self.barra_vida_fondo)
        
        if self.actor:
            self.cambiar_animacion('die', loop=False)
            self.actor.setColorScale(1, 1, 0, 1) # Amarillo estático
        else:
            self.modelo_visual.animate_color(color.yellow, duration=1.5)
        
        # Secuencia de curación (flotar hacia el cielo y brillar)
        self.animate_rotation_y(self.rotation_y + 1080, duration=1.5)
        self.animate_y(self.y + 3, duration=1.5)
        
        from ursina import Sequence, Func, Wait
        Sequence(
            Wait(1.5),
            Func(self.cambiar_textura_y_bajar)
        ).start()

    def atacar(self):
        if time.time() - self.ultimo_ataque > self.tiempo_entre_ataques:
            # Dañar al jugador
            if self.jugador_objetivo:
                if hasattr(self.jugador_objetivo, 'recibir_dano'):
                    self.jugador_objetivo.recibir_dano(10)
                else:
                    self.jugador_objetivo.vida -= 10
                    
                self.jugador_objetivo.texto_vida.text = f'SALUD: {self.jugador_objetivo.vida}'
                
                if self.jugador_objetivo.vida < 40:
                    from ursina import color
                    self.jugador_objetivo.texto_vida.color = color.red
                    
                if self.jugador_objetivo.vida <= 0:
                    print("¡HAS MUERTO!")
                    from ursina import application
                    application.quit()
                    
            self.ultimo_ataque = time.time()
            
            # Pose de ataque rápida (levanta los brazos)
            if self.actor:
                self.cambiar_animacion('attack', loop=False)
            else:
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-60)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(-60)