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
        # Hitbox más ajustada (1.2 en lugar de 2.0) para evitar bloquear el paso en pasillos
        self.collider = BoxCollider(self, center=Vec3(0, 1, 0), size=Vec3(1.2, 3, 1.2))
        
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
            billboard=True,
            enabled=False
        )
        self.barra_vida_roja = Entity(
            parent=self.barra_vida_fondo,
            model='quad',
            color=color.red,
            scale=(1, 1, 1),
            position=(0, 0, -0.01),
            origin_x=-0.5,
            x=-0.5,
            enabled=False
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
        # El enemigo SIEMPRE sabe dónde estás y te busca activamente
        if True:
            # 1. FIX: Evitar que el enemigo de vueltas locas si el jugador le salta encima
            dx = self.jugador_objetivo.x - self.x
            dz = self.jugador_objetivo.z - self.z
            dist_2d_sq = dx*dx + dz*dz
            
            if dist_2d_sq > 1.0: # 1 metro cuadrado = 1 metro de radio
                # Mirar al jugador en 2D (solo rotación Y)
                self.look_at_2d(self.jugador_objetivo.position, 'y')
            
            # Comportamiento dependiendo de la distancia
            # Si el jugador está muy lejos en 3D, pero justo encima en 2D, NO avanzamos (evita sobrepasar y dar giros violentos)
            if dist_jugador > self.distancia_ataque and dist_2d_sq > 1.0:
                # 1. Caminar hacia el jugador
                
                # MICRO-PAUSA POST ATAQUE: Si acaba de atacar, se queda quieto 1 segundo
                if time.time() - self.ultimo_ataque > 1.0:
                    
                    # 2. FIX: Lógica de Paredes/Rodeo combinada y fluida
                    hit_avance = raycast(self.position + Vec3(0, 0.5, 0), direction=self.forward, distance=self.velocidad * time.dt + 0.8, ignore=(self, self.jugador_objetivo))
                    
                    if not hit_avance.hit:
                        # Camino libre, avanzar directo hacia el jugador
                        self.position += self.forward * self.velocidad * time.dt
                        en_movimiento = True
                    else:
                        # Hay una pared. Intentar rodearla (Deslizarse por el borde)
                        if self.en_suelo:
                            self.velocidad_y = self.velocidad_salto # Saltar por si es un obstáculo pequeño
                            self.en_suelo = False
                        
                        import random
                        # Cambiar de idea ocasionalmente para evitar ciclos infinitos
                        if not hasattr(self, 'direccion_rodeo') or random.random() < 0.05:
                            self.direccion_rodeo = random.choice([-1, 1])
                            
                        direccion_lateral = self.right * getattr(self, 'direccion_rodeo', 1)
                        hit_lateral = raycast(self.position + Vec3(0, 0.5, 0), direction=direccion_lateral, distance=(self.velocidad * 1.5) * time.dt + 1.0, ignore=(self, self.jugador_objetivo))
                        
                        if not hit_lateral.hit:
                            # Bordeando la pared a mayor velocidad para compensar el desvío
                            self.position += direccion_lateral * (self.velocidad * 1.5) * time.dt
                            en_movimiento = True
                        else:
                            # Atrapado en una esquina (hay pared enfrente y a los lados) -> dar la vuelta
                            self.direccion_rodeo *= -1

                        # IA: ESQUIVA ALEATORIA (DASH LATERAL)
                        if not hasattr(self, 'ultimo_tiempo_esquiva'):
                            self.ultimo_tiempo_esquiva = 0
                            self.direccion_esquiva = 0
                            
                        if time.time() - self.ultimo_tiempo_esquiva > 3.0:
                            self.ultimo_tiempo_esquiva = time.time()
                            if random.random() < 0.3:
                                self.direccion_esquiva = random.choice([-1, 1])
                            else:
                                self.direccion_esquiva = 0
                                
                        if time.time() - self.ultimo_tiempo_esquiva < 0.5 and self.direccion_esquiva != 0:
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
            
        # Insta-Kill check
        if self.jugador_objetivo and hasattr(self.jugador_objetivo, 'powerups_activos') and 'insta_kill' in self.jugador_objetivo.powerups_activos:
            cantidad = 9999
            
        if self.vida_maxima is None:
            self.vida_maxima = max(1, self.vida) # Captura la vida máxima inicial
            
        self.vida -= cantidad
        
        self.barra_vida_fondo.enabled = True
        self.barra_vida_roja.enabled = True
        
        if self.actor:
            self.cambiar_animacion('pain', loop=False)
            self.ultimo_ataque = time.time() # Reusamos este timer para que no sobreescriba la animación de dolor
        
        # --- KNOCKBACK (EMPUJE FÍSICO) ---
        if self.jugador_objetivo:
            direccion_empuje = self.position - self.jugador_objetivo.position
            direccion_empuje.y = 0
            if direccion_empuje.length() > 0:
                direccion_empuje = direccion_empuje.normalized()
                from ursina import raycast
                # Evitar que el knockback lo meta dentro de una pared
                hit_kb = raycast(self.position + Vec3(0, 0.5, 0), direction=direccion_empuje, distance=2.0, ignore=(self, self.jugador_objetivo))
                
                if not hit_kb.hit:
                    # Sin pared, retroceso completo
                    self.animate_position(self.position + (direccion_empuje * 1.5), duration=0.15, curve=curve.out_expo)
                else:
                    # Si hay pared, retrocede solo lo permitido sin atravesarla
                    dist_segura = max(0, hit_kb.distance - 0.5)
                    if dist_segura > 0:
                        self.animate_position(self.position + (direccion_empuje * dist_segura), duration=0.15, curve=curve.out_expo)
        
        # Actualizar visualmente la barra
        porcentaje = max(0, self.vida / self.vida_maxima)
        self.barra_vida_roja.scale_x = porcentaje
        
        print(f"¡Enemigo dañado! Vida restante: {self.vida}")
        if self.vida <= 0:
            self.curar()

        # (Este método fue eliminado porque los enemigos ahora se destruyen completamente para ahorrar RAM)
        pass

    def curar(self):
        self.curando = True
        
        # --- SISTEMA DE DROPS (POWERUPS ZOMBIES) ---
        import random
        from scripts.powerups import PowerUp
        
        # Probabilidad de soltar un objeto (ej. 60% de soltar algo)
        if random.random() < 0.60:
            tipo_drop = random.choices(
                population=['max_salud', 'max_municion', 'insta_kill', 'bomba', 'doble_cadencia', 'recarga_rapida', 'velocidad'],
                weights=[0.15, 0.20, 0.15, 0.10, 0.15, 0.15, 0.10],
                k=1
            )[0]
            # Spawnear el powerup en la posición actual del enemigo
            PowerUp(tipo=tipo_drop, position=self.position)
            
        # Detenemos al enemigo
        self.velocidad = 0
        if self.jugador_objetivo and hasattr(self.jugador_objetivo, 'ganar_monedas'):
            self.jugador_objetivo.ganar_monedas(100)
        self.jugador_objetivo = None 
        
        # Ocultamos la barra de vida al morir en lugar de destruirla para poder reciclarla
        from ursina import color
        self.barra_vida_fondo.enabled = False
        self.barra_vida_roja.enabled = False
        
        if self.actor:
            self.cambiar_animacion('die', loop=False)
            self.actor.setColorScale(1, 1, 0, 1) # Amarillo estático
        else:
            self.modelo_visual.animate_color(color.yellow, duration=1.5)
        
        # En lugar de destruir al enemigo y causar lag al instanciar uno nuevo, lo reciclamos
        from ursina import invoke
        def hacer_reciclable():
            self.listo_para_reciclar = True
            self.position = (0, -2000, 0) # Ocultar muy profundo para activar culling espacial
            self.enabled = False # Desactiva físicas, update y renderizado
            if self.actor: self.actor.hide()
            else: self.modelo_visual.enabled = False
        invoke(hacer_reciclable, delay=1.5)


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
                    from ursina import scene, application
                    encontrado = False
                    for e in scene.entities:
                        if type(e).__name__ == 'PantallaMuerte':
                            e.mostrar()
                            encontrado = True
                            break
                    if not encontrado:
                        application.quit()
                    
            self.ultimo_ataque = time.time()
            
            # Pose de ataque rápida (levanta los brazos)
            if self.actor:
                self.cambiar_animacion('attack', loop=False)
            else:
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-60)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(-60)