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
                    'walk': base_folder + prefix + 'Slow_Orc_Walk_withSkin.glb',
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
            self.actor.setShaderAuto() # Fuerza el Shader de Panda3D para permitir Hardware Skinning
            
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
        self.emergiendo = False
        
        self.ultimo_tiempo_esquiva = 0
        self.direccion_esquiva = 0
        
        # Optimización: Reducir raycasts y desincronizarlos
        self.tiempo_ultimo_raycast = time.time() - random.uniform(0.0, 0.2)
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

    def emerger(self):
        from ursina import invoke
        self.emergiendo = True
        self.y = -3
        self.animate_position((self.x, 0, self.z), duration=1.5)
        invoke(lambda: setattr(self, 'emergiendo', False), delay=1.5)

    def update(self):
        if self.emergiendo:
            return

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
                
        # --- AI THROTTLING (Desacelerador Cerebral) ---
        if not hasattr(self, 'tiempo_ia'):
            self.tiempo_ia = random.uniform(0.0, 0.1)
            self.debe_moverse = False
            
        self.tiempo_ia += time.dt
        
        # --- LÓGICA DE IA (Se ejecuta a 3 FPS para movimientos más orgánicos) ---
        if self.tiempo_ia >= 0.33:
            self.tiempo_ia = 0
            
            # OPTIMIZACIÓN: Usar posicion_rastreo (breadcrumb)
            posicion_objetivo = getattr(self.jugador_objetivo, 'posicion_rastreo', self.jugador_objetivo.position)
            
            dx_rastreo = posicion_objetivo.x - self.x
            dz_rastreo = posicion_objetivo.z - self.z
            
            # Si está suficientemente cerca del jugador real O cerca de alcanzar el rastro, rastrear directamente al jugador
            if dist_jugador < 8.0 or (dx_rastreo*dx_rastreo + dz_rastreo*dz_rastreo) < 9.0:
                posicion_objetivo = self.jugador_objetivo.position
                
            # --- INTELIGENCIA DE NAVEGACIÓN (EVITAR MUROS Y SATURACIÓN) ---
            if hasattr(self, 'gestor_padre') and self.gestor_padre:
                cx = self.gestor_padre.centro_x
                cz = self.gestor_padre.centro_z
                
                rel_z = self.z - cz
                obj_rel_z = posicion_objetivo.z - cz
                rel_x = self.x - cx
                
                # Las arenas tienen muros en Z=-100, Z=0, Z=100. Solo se pueden cruzar por el centro (X = cx).
                # Dividimos el mapa en "zonas" horizontales cada 100 metros.
                zona_zombi = int(math.floor((rel_z + 100) / 100.0))
                zona_obj = int(math.floor((obj_rel_z + 100) / 100.0))
                
                # Si el zombi y el jugador están separados por uno de estos muros
                if zona_zombi != zona_obj:
                    # Histéresis: una vez decide ir al pasillo, no se rinde hasta estar bien adentro
                    if abs(rel_x) > 35:
                        self.buscando_pasillo = True
                        
                    if getattr(self, 'buscando_pasillo', False):
                        if abs(rel_x) < 20: # Ya está seguro en el centro
                            self.buscando_pasillo = False
                        else:
                            from ursina import Vec3
                            # Apunta hacia el pasillo central
                            dir_z = 20 if obj_rel_z > rel_z else -20
                            posicion_objetivo = Vec3(cx, self.y, self.z + dir_z)
                else:
                    self.buscando_pasillo = False
                
            dx = posicion_objetivo.x - self.x
            dz = posicion_objetivo.z - self.z
            dist_2d_sq = dx*dx + dz*dz
            
            if dist_2d_sq > 0.1: # Tolerancia para evitar temblores
                # Mirar al jugador en 2D (solo rotación Y)
                self.look_at_2d(posicion_objetivo, 'y')
            
            # Comportamiento dependiendo de la distancia
            if dist_jugador > self.distancia_ataque:
                # Caminar hacia el jugador
                if time.time() - self.ultimo_ataque > 1.0:
                    self.debe_moverse = True
                else:
                    self.debe_moverse = False
            else:
                self.debe_moverse = False
                self.atacar()
                
            # --- ANIMACIONES PROCEDIMENTALES ---
            if self.actor:
                if time.time() - self.ultimo_ataque < 1.0:
                    # Mantener animación de ataque
                    pass
                elif self.en_suelo:
                    if self.debe_moverse:
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
                    
        # --- MOVIMIENTO Y FÍSICAS FLUIDAS (Se ejecuta a 60 FPS) ---
        if getattr(self, 'debe_moverse', False):
            # --- DESPLAZAMIENTO FLUIDO ---
            self.position += self.forward * self.velocidad * time.dt
            
            # --- REPELENCIA MATEMÁTICA O(1) DE PAREDES (CERO RAYCASTS) ---
            if hasattr(self, 'gestor_padre') and self.gestor_padre:
                cx = self.gestor_padre.centro_x
                cz = self.gestor_padre.centro_z
                rel_x = self.x - cx
                rel_z = self.z - cz
                margen = 2.0 # Hitbox del zombi + margen seguro para evitar clip
                
                # Evaluamos zonas
                if abs(rel_x) <= 50 - margen:
                    # Zona del pasillo central (puede cruzar los límites Z de la arena)
                    pass
                else:
                    # No está en el pasillo, choca con las paredes frontales y traseras de la arena (+/- 100)
                    if rel_z > 100 - margen: self.z = cz + 100 - margen
                    if rel_z < -100 + margen: self.z = cz - 100 + margen
                    
                    # Choca con los límites laterales de la arena (+/- 100)
                    if rel_x > 100 - margen: self.x = cx + 100 - margen
                    if rel_x < -100 + margen: self.x = cx - 100 + margen
                    
                    # Choca con la pared divisoria horizontal central (z = 0)
                    if abs(rel_z) < margen:
                        if rel_z > 0: self.z = cz + margen
                        else: self.z = cz - margen
                        
                # Si está cruzando por la zona de Z > 100 o Z < -100 (dentro del pasillo de transición)
                # Topará con las paredes laterales del pasillo
                if abs(rel_z) > 100 - margen:
                    if rel_x > 50 - margen: self.x = cx + 50 - margen
                    if rel_x < -50 + margen: self.x = cx - 50 + margen
                    
                # --- REPULSIÓN ENTRE ZOMBIS (Evita que se fusionen en uno solo) ---
                for otro in self.gestor_padre.enemigos:
                    if otro is not self and otro.enabled and getattr(otro, 'vida', 0) > 0:
                        dx_e = self.x - otro.x
                        dz_e = self.z - otro.z
                        dist_sq = dx_e*dx_e + dz_e*dz_e
                        if dist_sq < 2.25: # 1.5 metros al cuadrado
                            if dist_sq == 0.0:
                                self.x += random.uniform(-0.1, 0.1)
                                self.z += random.uniform(-0.1, 0.1)
                            else:
                                dist_e = math.sqrt(dist_sq)
                                fuerza = (1.5 - dist_e) / 1.5
                                self.x += (dx_e / dist_e) * fuerza * 1.5 * time.dt
                                self.z += (dz_e / dist_e) * fuerza * 1.5 * time.dt
                                
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
            self.procesar_muerte()
            self.curar()

    def procesar_muerte(self):
        if self.jugador_objetivo and hasattr(self.jugador_objetivo, 'ganar_monedas'):
            self.jugador_objetivo.ganar_monedas(100)
            
        import __main__ as main
        if hasattr(main, 'power_up_service') and main.power_up_service:
            drop = main.power_up_service.procesar_muerte_enemigo(100, self.position)
            if drop:
                from scripts.powerups import PowerUp
                PowerUp(tipo=drop['tipo_powerup'], position=drop['posicion'])

        # (Este método fue eliminado porque los enemigos ahora se destruyen completamente para ahorrar RAM)
        pass

    def curar(self):
        self.curando = True
        
        # Detenemos al enemigo
        self.velocidad = 0
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
            
            # Reintegrar a la pool O(1) del gestor_padre
            if hasattr(self, 'gestor_padre') and self.gestor_padre:
                if self not in self.gestor_padre.enemigos_reciclables:
                    self.gestor_padre.enemigos_reciclables.append(self)
                    
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