from ursina import Entity, load_texture, time, Vec3, raycast, distance, scene, curve
import math
import random

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
        self.distancia_ataque = 1.3
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
        return Jugador.instancia

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
        dx_cull = self.position.x - self.jugador_objetivo.x
        dz_cull = self.position.z - self.jugador_objetivo.z
        if (dx_cull*dx_cull + dz_cull*dz_cull) > 1000000:
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
            
        # --- REPELENCIA FÍSICA SUAVE ---
        # Si el enemigo y el jugador se empalman mucho (< 0.8 metros), se empuja suavemente al enemigo hacia afuera
        # Esto evita que el jugador se quede "atascado" dentro de la hitbox del enemigo
        if dist_jugador < 0.8:
            vector_empuje = self.position - self.jugador_objetivo.position
            vector_empuje.y = 0
            if vector_empuje.length() > 0:
                # Un empuje de 4 m/s que escala con el framerate
                self.position += vector_empuje.normalized() * 4.0 * time.dt
                
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
                    
                    en_movimiento = True
                    
                    # --- CACHÉ DE RAYCAST (Throttling a 5 FPS para físicas) ---
                    # Revisamos el obstáculo frontal solo cada 0.2s, pero comprobando a una distancia mayor
                    entidades_ignoradas = [self, self.jugador_objetivo]
                    if hasattr(self.jugador_objetivo, 'modelo_visual'): entidades_ignoradas.append(self.jugador_objetivo.modelo_visual)
                    if hasattr(self.jugador_objetivo, 'pivot_camara'): entidades_ignoradas.append(self.jugador_objetivo.pivot_camara)
                    
                    if time.time() - getattr(self, 'tiempo_ultimo_raycast', 0) > 0.2:
                        self.tiempo_ultimo_raycast = time.time()
                        
                        distancia_proyectada = (self.velocidad * 0.2) + 1.0
                        
                        hit_avance = raycast(self.position + Vec3(0, 0.5, 0), direction=self.forward, distance=distancia_proyectada, ignore=tuple(entidades_ignoradas))
                        
                        if not hit_avance.hit or hasattr(hit_avance.entity, 'jugador_objetivo'):
                            self.obstaculo_enfrente = False
                            self.normal_pared = None
                        else:
                            self.obstaculo_enfrente = True
                            self.normal_pared = hit_avance.world_normal
                            # DEBUG: Print what the enemy is hitting
                            if hasattr(hit_avance.entity, 'name'):
                                print(f"DEBUG: Enemigo detectó obstáculo: {hit_avance.entity.name} (Tipo: {type(hit_avance.entity)})")
                            else:
                                print(f"DEBUG: Enemigo detectó obstáculo: {hit_avance.entity} (Tipo: {type(hit_avance.entity)})")
                            
                    # --- DESPLAZAMIENTO FLUIDO ---
                    if not self.obstaculo_enfrente:
                        # Camino libre
                        self.position += self.forward * self.velocidad * time.dt
                    else:
                        # --- SISTEMA DE SLIDING (Deslizamiento Matemático) ---
                        vector_mov = self.forward
                        
                        if getattr(self, 'normal_pared', None):
                            # Eliminamos del vector de movimiento la parte que empuja contra la pared
                            dot_product = vector_mov.dot(self.normal_pared)
                            vector_deslizamiento = vector_mov - (self.normal_pared * dot_product)
                            
                            if vector_deslizamiento.length() > 0:
                                vector_deslizamiento = vector_deslizamiento.normalized()
                                # Raycast rápido para confirmar que la ruta de deslizamiento está libre
                                hit_deslizamiento = raycast(self.position + Vec3(0, 0.5, 0), direction=vector_deslizamiento, distance=(self.velocidad * time.dt) + 0.5, ignore=tuple(entidades_ignoradas))
                                
                                if not hit_deslizamiento.hit or hasattr(hit_deslizamiento.entity, 'jugador_objetivo'):
                                    self.position += vector_deslizamiento * self.velocidad * time.dt
                                else:
                                    en_movimiento = False
                        else:
                            en_movimiento = False

                        # Ocasionalmente intentar saltar obstáculos bajos si está atascado
                        if not en_movimiento and self.en_suelo and random.random() < 0.1:
                            self.velocidad_y = self.velocidad_salto
                            self.en_suelo = False

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
                            direccion_esq = self.right * self.direccion_esquiva
                            dist_esq = (self.velocidad * 2.5) * time.dt
                            hit_esq = raycast(self.position + Vec3(0, 0.5, 0), direction=direccion_esq, distance=dist_esq + 1.0, ignore=tuple(entidades_ignoradas))
                            if not hit_esq.hit or hasattr(hit_esq.entity, 'jugador_objetivo'):
                                self.position += direccion_esq * dist_esq
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
                    
                # HUD and Death logic is now handled in Jugador.recibir_dano()
                    
            self.ultimo_ataque = time.time()
            
            # Pose de ataque rápida (levanta los brazos)
            if self.actor:
                self.cambiar_animacion('attack', loop=False)
            else:
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-60)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(-60)