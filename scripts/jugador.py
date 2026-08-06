from ursina import Entity, camera, Vec3, held_keys, time, raycast, mouse, clamp, load_texture, Text, color, destroy, invoke, scene, Audio
from direct.actor.Actor import Actor
import math

class Bala(Entity):
    def __init__(self, posicion_inicial, direccion, dano, jugador_obj, color_bala=color.yellow, **kwargs):
        super().__init__(
            model='sphere',
            color=color_bala,
            scale=0.1,
            position=posicion_inicial,
            **kwargs
        )
        self.direccion = direccion
        self.velocidad = 150
        self.dano = dano
        self.vida_util = 2.0
        self.creacion = time.time()
        self.jugador_obj = jugador_obj
        self.color_bala = color_bala
        
    def update(self):
        self.position += self.direccion * self.velocidad * time.dt
        if time.time() - self.creacion > self.vida_util:
            destroy(self)
            return
            
        hit_info = raycast(self.position, self.direccion, distance=self.velocidad * time.dt, ignore=(self, self.jugador_obj, self.jugador_obj.modelo_visual, self.jugador_obj.pivot_camara))
        if hit_info.hit:
            entidad = hit_info.entity
            if hasattr(entidad, 'recibir_dano'):
                entidad.recibir_dano(self.dano)
            
            # Efecto visual de impacto
            particula = Entity(model='cube', color=self.color_bala, scale=0.15, position=hit_info.world_point, unlit=True)
            particula.animate_scale(0, duration=0.3)
            destroy(particula, delay=0.3)
            
            destroy(self)

class CampoFuerzaProtector(Entity):
    def __init__(self, jugador_obj, color_campo, **kwargs):
        super().__init__(
            parent=jugador_obj,
            model='sphere',
            color=color_campo,
            scale=0, # Inicia en 0 para expandirse de a poco
            alpha=0.3,
            double_sided=True,
            collider=None, # IMPORTANTE: Sin colisionador para no atrapar al jugador
            **kwargs
        )
        self.jugador = jugador_obj
        self.animate_scale(80, duration=1.5) # Expansión épica hasta 80m de diámetro
        
    def update(self):
        import __main__ as main
        from ursina import time
        radio_actual = self.scale_x / 2.0 # El radio va creciendo junto con la escala
        
        # OPTIMIZACIÓN: Solo revisar a los enemigos de la arena en la que está el jugador
        if hasattr(main, 'coordinador') and main.coordinador:
            indice_jugador = int(round(self.jugador.z / main.coordinador.offset_z))
            if hasattr(main, 'gestores_arena') and 0 <= indice_jugador < len(main.gestores_arena):
                gestor = main.gestores_arena[indice_jugador]
                for enemigo in gestor.enemigos:
                    if enemigo.enabled and hasattr(enemigo, 'vida') and enemigo.vida > 0:
                        dir_vector = enemigo.world_position - self.jugador.world_position
                        dist = dir_vector.length()
                        if dist < radio_actual:
                            dir_vector.y = 0 # Solo empuje horizontal
                            if dir_vector.length() > 0:
                                push_dir = dir_vector.normalized()
                            else:
                                push_dir = self.jugador.forward
                            enemigo.position += push_dir * 25 * time.dt # Fuerte empuje hacia atrás

class Jugador(Entity):
    instancia = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Jugador.instancia = self
        self.scale = (1, 1, 1)
        self.origin_y = 0 
        
        # --- 1. CARGA DEL MODELO ANIMADO GLB (AGENTE SAS) ---
        ruta_base = "assets/modelos/personajes_principales/agente_sas/"
        
        self.modelo_visual = Entity(parent=self, rotation_y=180) # Rotamos 180 para que mire al frente
        
        try:
            self.actor = Actor(
                ruta_base + "sas_modelo.glb",
                {
                    'idle': ruta_base + 'sas_idle.glb',
                    'walk': ruta_base + 'sas_walk.glb',
                    'walk_back': ruta_base + 'sas_walk_back.glb',
                    'run': ruta_base + 'sas_run.glb',
                    'dash': ruta_base + 'sas_dash.glb',
                    'jump': ruta_base + 'sas_jump.glb',
                    'slash': ruta_base + 'sas_slash.glb',
                    'uppercut': ruta_base + 'sas_idle.glb', # Fallback temporal
                    'kick': ruta_base + 'sas_idle.glb', # Fallback temporal
                    'hit': ruta_base + 'sas_hit.glb',
                    'dead': ruta_base + 'sas_dead.glb',
                    'drinking': ruta_base + 'sas_drinking.glb'
                }
            )
            self.actor.reparentTo(self.modelo_visual)
            self.actor.loop('idle')
            self.estado_animacion = 'idle'
            self.actor.setBlend(frameBlend=True) # Suaviza las transiciones
            
            # --- OPTIMIZACIÓN: Pre-cargar animaciones ---
            # Para evitar que el juego dé un tirón la primera vez que se ejecuta un ataque o dash,
            # obligamos a Panda3D a procesar (bind) las animaciones silenciosamente al iniciar.
            try:
                for anim in ['walk', 'walk_back', 'run', 'dash', 'slash', 'uppercut', 'kick', 'hit', 'dead', 'drinking']:
                    self.actor.getAnimControl(anim)
            except:
                pass
            
            # Amplificamos la escala (120) validada por el usuario
            self.modelo_visual.scale = (120, 120, 120)           
            
            # --- SEGUIMIENTO DE HUESO PARA EL ARMA ---
            try:
                hueso = self.actor.exposeJoint(None, 'modelRoot', 'mixamorig:RightHand')
                if not hueso:
                    hueso = self.actor.exposeJoint(None, 'modelRoot', 'RightHand')
                self.mano_derecha_hueso = hueso
            except Exception as e:
                print("Error vinculando hueso de mano:", e)
                self.mano_derecha_hueso = None
                
        except Exception as e:
            print(f"=================================")
            print(f"ERROR CARGANDO EL JUGADOR GLB: {e}")
            print(f"=================================")
            self.actor = None
            self.modelo_visual.model = 'cube'
            self.modelo_visual.color = color.white
            self.estado_animacion = 'error'

        # --- 4. CONFIGURACIÓN DE MOVIMIENTO ---
        self.velocidad_caminar = 8
        self.velocidad_correr = 16
        
        self.gravedad = 60
        self.velocidad_salto = 12
        self.velocidad_y = 0
        self.en_suelo = False
        
        # --- 5. CONFIGURACIÓN DE CÁMÁRA TERCERA PERSONA ---
        self.pivot_camara = Entity(parent=self, y=1.5) # Altura de los hombros
        camera.parent = self.pivot_camara
        
        self.distancia_camara_objetivo = 6.0 # Distancia por defecto (estilo RE/GTA)
        # Desplazamos la cámara a la derecha (X=1.8) para la vista sobre el hombro
        camera.position = (1.8, 0.5, -self.distancia_camara_objetivo) 
        camera.rotation = (0, 0, 0) # Mirar al frente, paralelo al jugador
        
        # Ampliamos el FOV (Campo de visión) para que la pantalla no se sienta tan apretada
        # (Ajustado a 70 para evitar el efecto 'Ojo de pez' que distorsiona los tamaños a lo lejos)
        camera.fov = 70 
        
        mouse.locked = True 

        # --- 6. SISTEMA DE COMBATE (MELEE) ---
        self.vida = 100
        self.vida_maxima = 100
        self.esta_muerto = False
        
        # Diccionario maestro de estadísticas y offsets por arma
        self.stats_por_arma = {
            'M1911': {
                'pos_idle': Vec3(-0.032, 0.051, 0.437),
                'pos_move': Vec3(-0.077, 0.033, 0.364),
                'rot': Vec3(2.785, 82.343, 0.000),
                'escala': 0.167,
                'bala': Vec3(0.186, 1.815, 0.624),
                'dano': 25, 'cadencia': 0.3, 'tiempo_recarga': 1.0, 
                'cargador': 8, 'reserva': 200, 'color': color.yellow, 'rafaga': 1
            },
            'SCAR': {
                'pos_idle': Vec3(0.000, 0.000, 0.233),
                'pos_move': Vec3(0.000, 0.000, 0.233),
                'rot': Vec3(0.000, 79.770, 0.000),
                'escala': 0.559,
                'bala': Vec3(0.136, 1.774, 0.797),
                'dano': 45, 'cadencia': 0.1, 'tiempo_recarga': 2.5, 
                'cargador': 30, 'reserva': 300, 'color': color.orange, 'rafaga': 1, 'automatico': True
            },
            'RAYGUN': {
                'pos_idle': Vec3(0.012, 0.067, 0.363),
                'pos_move': Vec3(0.012, 0.067, 0.363),
                'rot': Vec3(0.000, 90.110, 0.000),
                'escala': 0.256,
                'bala': Vec3(0.194, 1.851, 0.789),
                'dano': 120, 'cadencia': 0.25, 'tiempo_recarga': 2.0, 
                'cargador': 20, 'reserva': 160, 'color': color.green, 'rafaga': 1
            },
            'RAYGUN_MK2': {
                'pos_idle': Vec3(0.000, 0.072, 0.397),
                'pos_move': Vec3(0.000, 0.072, 0.397),
                'rot': Vec3(0.000, 81.010, 0.000),
                'escala': 0.302,
                'bala': Vec3(0.183, 1.838, 0.675),
                'dano': 90, 'cadencia': 0.35, 'tiempo_recarga': 2.0, 
                'cargador': 21, 'reserva': 168, 'color': color.green, 'rafaga': 2
            }
        }
        
        # Valores activos (se sobreescriben al cargar un arma)
        self.arma_offset_rot = Vec3(0, 0, 0)
        self.arma_escala = 0.1
        self.arma_offset_pos_idle = Vec3(0,0,0)
        self.arma_offset_pos_move = Vec3(0,0,0)
        self.arma_offset_pos_actual = Vec3(0,0,0)
        self.bala_offset = Vec3(0,0,0)
        
        self.modo_debug_editando = 'ARMA' # 'ARMA' o 'BALA'
        self.offsets_por_arma = {}
        self.camara_frontal = False
        
        self.texto_debug_arma = Text(parent=camera.ui, text="", position=(-0.85, 0.45), scale=1, color=color.yellow, background=True)
        self.debug_bala_visual = Entity(model='sphere', color=color.red, scale=0.05, parent=scene, unlit=True, enabled=False)
        
        self.debug_timer = 0
        self.barra_vida_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0.1, 0.1, 0.1, 0.9), scale=(0.25, 0.015), position=(0, -0.45))
        self.barra_vida_fg = Entity(parent=self.barra_vida_bg, model='quad', color=color.rgba(0.0, 0.8, 0.0, 1.0), scale=(1, 1), position=(-0.5, 0), origin=(-0.5, 0))
        self.texto_vida = Text(parent=camera.ui, text=f'{self.vida} / {self.vida_maxima}', position=(0, -0.42), origin=(0, 0), scale=0.9, color=color.white)
        self.mira = Entity(parent=camera.ui, model='quad', scale=(0.01, 0.01), color=color.white, texture='circle')
        
        self.dano_ataque = 35
        self.atacando = False
        self.rango_ataque = 4.5 # Metros
        self.tiene_arma = False
        self.arma_entidad = None
        self.ultimo_disparo = 0
        
        # --- PRECARGA DE AUDIOS DE ARMAS ---
        self.sonido_m1911 = Audio('assets/sonidos/sonido_pistola.mpeg', autoplay=False)
        self.sonido_scar = Audio('assets/sonidos/sonido scar.mp3', autoplay=False)
        self.sonido_raygun = Audio('assets/sonidos/disparos rain gun.mp3', autoplay=False)
        
        # --- NUEVO: SISTEMA DE MUNICIÓN E INVENTARIO ---
        self.armas_inventario = [] # Lista de diccionarios con info de cada arma
        self.indice_arma_actual = 0
        self.recargando = False
        
        # --- HUD FUTURISTA DE MUNICIÓN (ARCO TACÓMETRO) ---
        import math
        from ursina import window
        
        self.hud_armas_bg = Entity(parent=camera.ui, position=(0.60, -0.28), enabled=False)
        
        # Anillos de fondo y cristal translúcido (camera.ui en Ursina ya mantiene la proporción 1:1)
        Entity(parent=self.hud_armas_bg, model='circle', color=color.rgba(0, 0.15, 0.35, 0.5), scale=(0.35, 0.35), unlit=True)
        self.anillo_interior = Entity(parent=self.hud_armas_bg, model='circle', color=color.rgba(0.0, 0.03, 0.08, 0.9), scale=(0.31, 0.31), unlit=True) 
        
        self.texto_nombre_arma = Text(parent=self.hud_armas_bg, text='ARMA', position=(0, 0.05), scale=1.3, color=color.cyan, origin=(0, 0))
        self.texto_municion = Text(parent=self.hud_armas_bg, text='0 / 0', position=(0, -0.04), scale=2.5, color=color.white, origin=(0, 0))
        
        self.barritas_municion = []
        self.num_barras_hud = 45
        radio_barras = 0.16 # Movidas al borde
        angulo_inicio = 220 # Empieza abajo a la izquierda
        angulo_fin = -40    # Termina abajo a la derecha
        
        rango = angulo_inicio - angulo_fin
        
        for i in range(self.num_barras_hud):
            ang_grados = angulo_inicio - (i * (rango / (self.num_barras_hud - 1)))
            ang_rad = math.radians(ang_grados)
            
            x_pos = math.cos(ang_rad) * radio_barras
            y_pos = math.sin(ang_rad) * radio_barras
            
            barrita = Entity(
                parent=self.hud_armas_bg,
                model='quad',
                color=color.cyan,
                scale=(0.02, 0.005),
                position=(x_pos, y_pos),
                # +90 hace que sean tangentes (acostadas sobre la curva)
                rotation_z=ang_grados + 90,
                unlit=True
            )
            self.barritas_municion.append(barrita)
        
        # --- 7. LINTERNA TÁCTICA (SPOTLIGHT) ---
        from ursina import SpotLight
        self.linterna = SpotLight(parent=camera, position=(0, 0, 0), color=color.white, shadows=False)
        
        # --- 8. ESQUIVA TÁCTICA Y ESTADOS ---
        self.dash_disponible = True
        self.dash_cooldown = 1.5
        self.haciendo_dash = False
        self.dash_direccion = Vec3(0,0,0)
        self.congelado = False
        
        # --- 9. SISTEMA DE NIEVE SUPER OPTIMIZADO ---
        import random
        self.copos_nieve = []
        # --- 9. (ELIMINADO SISTEMA DE CLIMA) ---
        
        # --- 10. RADAR TÁCTICO (ESCÁNER BIOLÓGICO) ---
        self.radar_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0.0, 0.15, 0.0, 0.85), scale=(0.25, 0.25), position=(-0.7, 0.35))
        Entity(parent=self.radar_bg, model='quad', color=color.rgba(0.0, 0.7, 0.0, 0.4), scale=(1, 0.01), z=-0.01)
        Entity(parent=self.radar_bg, model='quad', color=color.rgba(0.0, 0.7, 0.0, 0.4), scale=(0.01, 1), z=-0.01)
        Entity(parent=self.radar_bg, model='circle', color=color.rgba(0.0, 0.9, 0.0, 0.2), scale=(0.8, 0.8), z=-0.01)
        
        self.radar_jugador = Entity(parent=self.radar_bg, model='arrow', color=color.cyan, scale=(0.06, 0.06), z=-0.03)
        self.puntos_radar = [Entity(parent=self.radar_bg, model='circle', color=color.red, scale=(0.05, 0.05), enabled=False, z=-0.02) for _ in range(40)]
        self.punto_radar_mesa = Entity(parent=self.radar_bg, model='circle', color=color.yellow, scale=(0.06, 0.06), enabled=False, z=-0.04)
        self.punto_radar_caja = Entity(parent=self.radar_bg, model='quad', color=color.magenta, scale=(0.05, 0.05), enabled=False, z=-0.04)
        
        # --- NUEVO: SISTEMA DE MONEDAS ---
        self.monedas = 0
        self.texto_monedas = Text(parent=camera.ui, text=f'MONEDAS: {self.monedas}', position=(-0.7, 0.15), origin=(0, 0), scale=0.9, color=color.gold)
        
        # --- ENEMIGOS RESTANTES ---
        self.texto_enemigos = Text(parent=camera.ui, text='ENEMIGOS: 0', position=(-0.7, 0.20), origin=(0, 0), scale=0.9, color=color.red)
        
        # --- NUEVO: SISTEMA DE RONDAS (IMÁGENES) ---
        self.ronda_actual = 1
        self.img_ronda_1 = Entity(parent=camera.ui, model='quad', texture='scripts/backgrounds/rouds/I.png', scale=(0.2, 0.2), position=(-0.73, -0.42))
        self.img_ronda_2 = Entity(parent=camera.ui, model='quad', texture=None, scale=(0.2, 0.2), position=(-0.73, -0.42), enabled=False)
        self.img_ronda_3 = Entity(parent=camera.ui, model='quad', texture=None, scale=(0.2, 0.2), position=(-0.73, -0.42), enabled=False)
        
        # --- 11. CHEATS ---
        self.invulnerable = False
        self.teclas_escritas = ""
        
        # --- 12. POWERUPS UI ---
        self.powerup_texto = Text(parent=camera.ui, text='', position=(-0.60, -0.35), origin=(-0.5, -0.5), scale=1, color=color.white)
        self.powerup_texto.enabled = False
        
        self.powerups_activos = {}
        self.tiempo_mensaje_powerup = 0
        
        # --- 13. SISTEMA DE PERKS (BEBIDAS) ---
        self.max_armas = 2
        self.vidas_extra = 0
        self.perks_comprados = []
        self.ui_perks_iconos = []

    def input(self, key):
        if self.esta_muerto: return
        
        if key == 'control':
            self.camara_frontal = not self.camara_frontal

        # CHEAT CODES
        if len(key) == 1 and key.isalnum():
            self.teclas_escritas += key.lower()
            if len(self.teclas_escritas) > 15:
                self.teclas_escritas = self.teclas_escritas[-15:]
            if self.teclas_escritas.endswith("asnaeb"):
                self.invulnerable = not self.invulnerable
                self.teclas_escritas = "" # Reset
                print(f"Modo Invulnerable: {'ON' if self.invulnerable else 'OFF'}")
            elif self.teclas_escritas.endswith("hesoyam"):
                self.ganar_monedas(100000)
                self.teclas_escritas = "" # Reset
                print("Cheat HESOYAM activado: +100,000 Monedas")
                
        if key == 'enter':
            import re
            match = re.search(r'round(\d+)$', self.teclas_escritas)
            if match:
                numero = int(match.group(1))
                self.teclas_escritas = "" # Reset
                
                import __main__ as main
                if hasattr(main, 'gestores_arena') and hasattr(main, 'coordinador'):
                    indice_arena = int(round(self.z / main.coordinador.offset_z))
                    if 0 <= indice_arena < len(main.gestores_arena):
                        gestor = main.gestores_arena[indice_arena]
                        gestor.ronda_actual = max(1, numero - 1)
                        
                        # Matar a todos los enemigos menos 1
                        enemigos_vivos = [e for e in gestor.enemigos if e.enabled and hasattr(e, 'vida') and e.vida > 0]
                        for e in enemigos_vivos[1:]:
                            e.vida = 0
                            e.esta_muerto = True
                            if hasattr(e, 'morir'): e.morir()
                            
                        gestor.spawns_pendientes = 0
                        print(f"Cheat ROUND activado: Saltando a ronda {numero} cuando muera el último zombie.")
        
        # --- ZOOM CON RUEDA DEL RATÓN ---
        if key == 'scroll up':
            self.distancia_camara_objetivo -= 1.5
        elif key == 'scroll down':
            self.distancia_camara_objetivo += 1.5
            
        # Limitamos el zoom (mínimo 4m para no entrar al cuerpo, máximo 30m)
        self.distancia_camara_objetivo = clamp(self.distancia_camara_objetivo, 4.0, 30.0)
        
        if key == 'left mouse down':
            if self.tiene_arma and not self.haciendo_dash:
                self.disparar()
            elif not self.atacando and not self.haciendo_dash:
                self.iniciar_ataque()
                
        if key == 'r' and self.tiene_arma and not self.recargando:
            self.recargar()
            
        if key == 'q' and self.tiene_arma and not self.recargando:
            siguiente_idx = (self.indice_arma_actual + 1) % len(self.armas_inventario)
            self.cambiar_arma(siguiente_idx)
            
        if key == '1' and self.tiene_arma and not self.recargando:
            self.cambiar_arma(0)
            
        if key == '2' and self.tiene_arma and not self.recargando:
            self.cambiar_arma(1)
                    
        if key == 'c' and self.dash_disponible and not self.haciendo_dash and not self.atacando:
            self.iniciar_dash()
            
        if key == 'v' and not self.atacando and not self.haciendo_dash:
            self.ataque_melee()

    def ataque_melee(self):
        self.atacando = True
        
        # Animación de ataque
        if self.actor:
            self.actor.setPlayRate(2.0, 'slash') # Animación el doble de rápida
            self.actor.play('slash')
            self.estado_animacion = 'slash'
            
        # Detección de colisión (cuerpo a cuerpo)
        # Hacemos raycast en la dirección forward del jugador a corta distancia
        import __main__ as main
        
        # Calculamos distancia con todos los enemigos vivos para simular daño de área cuerpo a cuerpo en frente
        if hasattr(main, 'gestores_arena') and main.gestores_arena:
            # Buscar en la arena actual
            indice_jugador = int(round(self.z / main.coordinador.offset_z)) if hasattr(main, 'coordinador') and main.coordinador else 0
            if 0 <= indice_jugador < len(main.gestores_arena):
                gestor = main.gestores_arena[indice_jugador]
                for enemigo in gestor.enemigos:
                    if enemigo and enemigo.enabled and hasattr(enemigo, 'vida') and enemigo.vida > 0:
                        distancia = (enemigo.world_position - self.world_position).length()
                        if distancia < self.rango_ataque:
                            # Comprobar si el enemigo está en frente nuestro
                            dir_al_enemigo = (enemigo.world_position - self.world_position).normalized()
                            # Producto punto para ver si el ángulo es menor a ~45 grados (cos 45 = 0.707)
                            if self.forward.dot(dir_al_enemigo) > 0.5:
                                enemigo.recibir_dano(self.dano_ataque * 2) # Doble daño por cuchillo
                                
                                # Efecto visual de sangre o golpe
                                from ursina import Entity, color, destroy
                                particula = Entity(model='cube', color=color.red, scale=0.3, position=enemigo.world_position + Vec3(0, 1.5, 0), unlit=True)
                                particula.animate_scale(0, duration=0.3)
                                destroy(particula, delay=0.3)

        # El ataque ahora es el doble de rápido (0.4s en lugar de 0.8s)
        invoke(self.terminar_ataque, delay=0.4)

    def actualizar_hud_ronda(self):
        ronda = self.ronda_actual
        from ursina import load_texture
        if ronda <= 9:
            romanos = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
            texto = romanos[ronda - 1]
            self.img_ronda_1.texture = load_texture(f'scripts/backgrounds/rouds/{texto}.png')
            self.img_ronda_1.position = (-0.73, -0.42)
            self.img_ronda_1.enabled = True
            
            self.img_ronda_2.enabled = False
            self.img_ronda_3.enabled = False
        else:
            ronda_str = str(ronda)
            if len(ronda_str) == 2:
                self.img_ronda_1.texture = load_texture(f'scripts/backgrounds/rouds/{ronda_str[0]}.png')
                self.img_ronda_1.position = (-0.78, -0.42)
                self.img_ronda_1.enabled = True
                
                self.img_ronda_2.texture = load_texture(f'scripts/backgrounds/rouds/{ronda_str[1]}.png')
                self.img_ronda_2.position = (-0.68, -0.42)
                self.img_ronda_2.enabled = True
                
                self.img_ronda_3.enabled = False
            elif len(ronda_str) >= 3:
                self.img_ronda_1.texture = load_texture(f'scripts/backgrounds/rouds/{ronda_str[0]}.png')
                self.img_ronda_1.position = (-0.81, -0.42)
                self.img_ronda_1.enabled = True
                
                self.img_ronda_2.texture = load_texture(f'scripts/backgrounds/rouds/{ronda_str[1]}.png')
                self.img_ronda_2.position = (-0.73, -0.42)
                self.img_ronda_2.enabled = True
                
                self.img_ronda_3.texture = load_texture(f'scripts/backgrounds/rouds/{ronda_str[2]}.png')
                self.img_ronda_3.position = (-0.65, -0.42)
                self.img_ronda_3.enabled = True

    def iniciar_ataque(self):
        self.atacando = True
        
        # Elegimos el uppercut como ataque principal
        if self.actor:
            self.actor.play('uppercut')
            self.estado_animacion = 'uppercut'
            
        # Hacemos daño a los enemigos frente a nosotros (Melee)
        hit_info = raycast(self.position + Vec3(0,1,0), self.forward, distance=self.rango_ataque, ignore=(self, self.pivot_camara, self.modelo_visual))
        if hit_info.hit:
            entidad = hit_info.entity
            if hasattr(entidad, 'recibir_dano'):
                entidad.recibir_dano(self.dano_ataque)
                
        # El uppercut dura más o menos 1 segundo. Bloqueamos otras acciones por ese tiempo.
        invoke(self.terminar_ataque, delay=0.8)

    def terminar_ataque(self):
        if self.esta_muerto: return
        self.atacando = False
        self.cambiar_animacion('idle')

    def equipar_arma(self, modelo_existente=None, id_arma='M1911'):
        if not modelo_existente:
            modelo_existente = Entity(model='assets/modelos/objetos_con_meshy/arma.glb')
            
        # ANCLAJE AL JUGADOR (Evita el bug de Euler, hereda la rotación del jugador pero no la escala del hueso)
        modelo_existente.parent = self
        modelo_existente.collider = None

        # Detener CUALQUIER animación residual del powerup (como el giro infinito)
        if hasattr(modelo_existente, 'sequences'):
            for seq in modelo_existente.sequences:
                seq.pause()
                seq.kill()
            modelo_existente.sequences = []
            
        if hasattr(modelo_existente, 'animations'):
            for seq in modelo_existente.animations:
                seq.pause()
                seq.kill()
        modelo_existente.animations = []
        
        id_arma = id_arma.upper()
        stats = self.stats_por_arma.get(id_arma, self.stats_por_arma['M1911'])
        
        nueva_arma_data = {
            'entidad': modelo_existente,
            'id_arma': id_arma,
            'balas_cargador': stats['cargador'],
            'balas_reserva': stats['reserva'],
            'max_cargador': stats['cargador'],
            'max_reserva': stats['reserva'],
            'dano': stats['dano'],
            'cadencia': stats['cadencia'],
            'tiempo_recarga': stats['tiempo_recarga'],
            'color': stats['color'],
            'rafaga': stats['rafaga'],
            'automatico': stats.get('automatico', False)
        }
        
        if len(self.armas_inventario) < self.max_armas:
            self.armas_inventario.append(nueva_arma_data)
            self.cambiar_arma(len(self.armas_inventario) - 1)
        else:
            arma_antigua = self.armas_inventario[self.indice_arma_actual]
            destroy(arma_antigua['entidad'])
            self.armas_inventario[self.indice_arma_actual] = nueva_arma_data
            self.cambiar_arma(self.indice_arma_actual)
            
        self.tiene_arma = True
        self.hud_armas_bg.enabled = True
        self.texto_nombre_arma.enabled = True
        self.texto_municion.enabled = True

    def cambiar_arma(self, nuevo_indice):
        if self.recargando or not self.armas_inventario or nuevo_indice >= len(self.armas_inventario):
            return
            
        if self.arma_entidad:
            self.arma_entidad.enabled = False
            
        self.indice_arma_actual = nuevo_indice
        arma_data = self.armas_inventario[self.indice_arma_actual]
        self.arma_entidad = arma_data['entidad']
        self.arma_entidad.enabled = True
        
        self.actualizar_hud_municion()
        self.cargar_offsets_arma()

    def cargar_offsets_arma(self):
        if not getattr(self, 'armas_inventario', None) or self.indice_arma_actual >= len(self.armas_inventario):
            return
            
        arma_data = self.armas_inventario[self.indice_arma_actual]
        id_arma = arma_data.get('id_arma', 'M1911')
        
        if id_arma not in self.stats_por_arma:
            # Creamos un perfil en blanco usando la M1911 de base si no existe
            self.stats_por_arma[id_arma] = self.stats_por_arma['M1911'].copy()
            self.stats_por_arma[id_arma]['pos_idle'] = Vec3(0,0,0)
            self.stats_por_arma[id_arma]['pos_move'] = Vec3(0,0,0)
            self.stats_por_arma[id_arma]['bala'] = Vec3(0,0,0)
            
        data = self.stats_por_arma[id_arma]
        self.arma_offset_pos_idle = Vec3(*data['pos_idle'])
        self.arma_offset_pos_move = Vec3(*data['pos_move'])
        self.arma_offset_pos_actual = Vec3(*data['pos_idle'])
        self.arma_offset_rot = Vec3(*data['rot'])
        self.arma_escala = data['escala']
        self.bala_offset = Vec3(*data['bala'])

    def recargar(self):
        arma_data = self.armas_inventario[self.indice_arma_actual]
        if arma_data['balas_cargador'] >= arma_data['max_cargador'] or arma_data['balas_reserva'] <= 0:
            return
            
        self.recargando = True
        self.texto_municion.text = "Recargando..."
        self.texto_municion.color = color.yellow
        
        tiempo_recarga = arma_data.get('tiempo_recarga', 1.5)
        if 'recarga_rapida' in self.powerups_activos:
            tiempo_recarga = tiempo_recarga / 2.0
            
        if not hasattr(self, '_recarga_id'):
            self._recarga_id = 0
        self._recarga_id += 1
        current_id = self._recarga_id
        
        invoke(lambda: self._finalizar_recarga() if self._recarga_id == current_id else None, delay=tiempo_recarga)

    def _finalizar_recarga(self):
        if self.esta_muerto: return
        self.recargando = False
        
        arma_data = self.armas_inventario[self.indice_arma_actual]
        balas_faltantes = arma_data['max_cargador'] - arma_data['balas_cargador']
        
        if arma_data['balas_reserva'] >= balas_faltantes:
            arma_data['balas_reserva'] -= balas_faltantes
            arma_data['balas_cargador'] = arma_data['max_cargador']
        else:
            arma_data['balas_cargador'] += arma_data['balas_reserva']
            arma_data['balas_reserva'] = 0
            
        self.texto_municion.color = color.white
        self.actualizar_hud_municion()

    def actualizar_hud_municion(self):
        if not self.recargando and self.armas_inventario:
            arma_data = self.armas_inventario[self.indice_arma_actual]
            self.texto_municion.text = f"{arma_data['balas_cargador']} / {arma_data['balas_reserva']}"
            self.texto_nombre_arma.text = arma_data.get('id_arma', 'ARMA')
            
            cargador_actual = arma_data['balas_cargador']
            max_cargador = arma_data['max_cargador']
            
            total_barras = self.num_barras_hud
            
            # Determinar color basado en si le quedan pocas balas (< 20%)
            color_barras = color.cyan
            if cargador_actual <= int(max_cargador * 0.2):
                color_barras = color.red
                self.texto_municion.color = color.red
                self.texto_nombre_arma.color = color.red
                self.anillo_interior.color = color.rgba(0.3, 0.0, 0.0, 0.9)
            else:
                self.texto_municion.color = color.white
                self.texto_nombre_arma.color = color.cyan
                self.anillo_interior.color = color.rgba(0.0, 0.03, 0.08, 0.9)
                
            # Calcular cuántas barras deben estar iluminadas
            porcentaje_lleno = cargador_actual / max_cargador if max_cargador > 0 else 0
            barras_llenas = int(porcentaje_lleno * total_barras)
            
            for i in range(total_barras):
                self.barritas_municion[i].enabled = True
                if i < barras_llenas:
                    self.barritas_municion[i].color = color_barras
                else:
                    self.barritas_municion[i].color = color.rgba(0.2, 0.2, 0.2, 0.5)

    def disparar(self):
        if self.recargando or getattr(self, 'disparando_rafaga', False) or not self.armas_inventario: return
        
        arma_data = self.armas_inventario[self.indice_arma_actual]
        if arma_data['balas_cargador'] <= 0:
            if arma_data['balas_reserva'] > 0:
                self.recargar()
            else:
                self.texto_municion.text = "¡SIN MUNICIÓN!"
                self.texto_municion.color = color.red
            return
            
        cadencia = arma_data.get('cadencia', 0.2)
        if 'doble_cadencia' in self.powerups_activos:
            cadencia = cadencia / 2.0
            
        if time.time() - getattr(self, 'ultimo_disparo', 0) < cadencia:
            return
            
        self.ultimo_disparo = time.time()
        
        rafaga = arma_data.get('rafaga', 1)
        if rafaga > 1:
            self.disparando_rafaga = True
            self._ejecutar_disparo(rafaga)
        else:
            self._ejecutar_disparo(1)

    def _ejecutar_disparo(self, rafagas_restantes):
        if self.esta_muerto or not self.armas_inventario:
            self.disparando_rafaga = False
            return
            
        arma_data = self.armas_inventario[self.indice_arma_actual]
        
        if arma_data['balas_cargador'] <= 0:
            self.disparando_rafaga = False
            return
            
        arma_data['balas_cargador'] -= 1
        self.actualizar_hud_municion()
        
        # --- RECARGA AUTOMÁTICA AL VACIAR CARGADOR ---
        if arma_data['balas_cargador'] <= 0 and arma_data.get('balas_reserva', 0) > 0:
            self.recargar()
            
        # --- AUDIO DE DISPARO ---
        id_arma = arma_data.get('id_arma')
        if id_arma == 'RAYGUN':
            self.sonido_raygun.stop()
            self.sonido_raygun.play()
        elif id_arma == 'RAYGUN_MK2':
            Audio('assets/sonidos/disparo_mark2.mp3', autoplay=True)
        elif id_arma == 'SCAR':
            self.sonido_scar.stop()
            self.sonido_scar.play()
        elif id_arma == 'M1911':
            self.sonido_m1911.play()
        
        # 1. Origen físico del disparo (el cañón del arma)
        origen_disparo = self.world_position + self.up * self.bala_offset.y + self.right * self.bala_offset.x + self.forward * self.bala_offset.z
        
        # 2. ¿A qué está apuntando el punto blanco (mira) realmente?
        hit_mira = raycast(camera.world_position, camera.forward, distance=1000, ignore=(self, self.modelo_visual, self.pivot_camara))
        
        if hit_mira.hit:
            punto_objetivo = hit_mira.world_point
        else:
            punto_objetivo = camera.world_position + camera.forward * 1000
            
        # 3. La bala viaja en diagonal desde el arma hacia el objetivo visual
        direccion_disparo = (punto_objetivo - origen_disparo).normalized()
        
        # Retroceso visual básico
        if self.arma_entidad:
            import random
            offset_y = random.uniform(1.1, 1.25)
            self.arma_entidad.animate_position((0.8, offset_y, 0.3), duration=0.03)
            self.arma_entidad.animate_position((0.8, 1.2, 0.5), duration=0.07, delay=0.03)
        
        dano = arma_data.get('dano', 35)
        color_bala = arma_data.get('color', color.yellow)
        Bala(posicion_inicial=origen_disparo, direccion=direccion_disparo, dano=dano, jugador_obj=self, color_bala=color_bala)
        
        if 'doble_cadencia' in self.powerups_activos:
            # Disparamos una segunda bala paralela para el powerup
            Bala(posicion_inicial=origen_disparo + self.right * 0.1, direccion=direccion_disparo, dano=dano, jugador_obj=self, color_bala=color_bala)
            
        rafagas_restantes -= 1
        if rafagas_restantes > 0:
            invoke(lambda: self._ejecutar_disparo(rafagas_restantes), delay=0.08) # 0.08s entre balas de ráfaga
        else:
            self.disparando_rafaga = False

    def iniciar_dash(self):
        dir_actual = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) + 
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()
        
        if dir_actual.length() == 0:
            dir_actual = self.forward
            
        self.dash_direccion = dir_actual
        self.haciendo_dash = True
        self.dash_disponible = False
        
        if self.actor:
            self.actor.play('dash')
            self.estado_animacion = 'dash'
        
        self.pivot_camara.animate_rotation_z(15 if held_keys['a'] else -15, duration=0.1)
        self.pivot_camara.animate_rotation_z(0, duration=0.2, delay=0.1)
        
        invoke(self.terminar_dash, delay=0.3) 
        invoke(self.recuperar_dash, delay=self.dash_cooldown)

    def terminar_dash(self):
        if self.esta_muerto: return
        self.haciendo_dash = False
        self.cambiar_animacion('idle')

    def recuperar_dash(self):
        self.dash_disponible = True

    def ganar_monedas(self, cantidad):
        self.monedas += cantidad
        self.texto_monedas.text = f'MONEDAS: {self.monedas}'

    def recibir_dano(self, cantidad):
        if self.esta_muerto or self.invulnerable: return
        self.vida -= cantidad
        
        # Hit reaction
        if self.actor and not self.atacando and not self.haciendo_dash:
            self.actor.play('hit')
            self.estado_animacion = 'hit'
            invoke(lambda: self.cambiar_animacion('idle') if not self.esta_muerto and not self.atacando else None, delay=0.5)

        if self.vida <= 0:
            self.morir()

    def morir(self):
        if self.vidas_extra > 0:
            # Mecánica Quick Revive
            self.vidas_extra -= 1
            self.vida = self.vida_maxima
            print("¡Te has salvado por la bebida azul!")
            self.invulnerable = True
            invoke(lambda: setattr(self, 'invulnerable', False), delay=3.0)
            
            # Quitar la bebida azul de la UI si se gastó
            if 'azul' in self.perks_comprados:
                self.perks_comprados.remove('azul')
                self.actualizar_ui_perks()
            return
            
        self.esta_muerto = True
        self.vida = 0
        if self.actor:
            self.actor.play('dead')
            self.estado_animacion = 'dead'
        
        # Efecto visual de muerte (cae la cámara o se pinta la pantalla)
        self.barra_vida_fg.color = color.black
        
        # Activar pantalla de muerte
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

    def cambiar_animacion(self, nombre_animacion):
        if not self.actor or self.atacando or self.haciendo_dash or self.esta_muerto:
            return
            
        # Prevenir reiniciar la misma animación si ya está corriendo
        if self.estado_animacion != nombre_animacion:
            # Si es hit, play. Si es movimiento, loop.
            if nombre_animacion in ['hit', 'dead', 'uppercut', 'slash', 'kick', 'dash', 'jump']:
                self.actor.play(nombre_animacion)
            else:
                self.actor.loop(nombre_animacion)
            self.estado_animacion = nombre_animacion

    def mostrar_mensaje_powerup(self, mensaje):
        self.powerup_texto.text = mensaje
        self.powerup_texto.enabled = True
        self.tiempo_mensaje_powerup = 3.0
        
    def activar_powerup(self, tipo, duracion, nombre_mostrar):
        if tipo in self.powerups_activos:
            self.powerups_activos[tipo]['restante'] = duracion
            self.powerups_activos[tipo]['total'] = duracion
            return
            
        # Determinar posición en la lista
        idx = len(self.powerups_activos)
        y_pos = -0.45 + (idx * 0.05)
        
        bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,0.8), scale=(0.25, 0.02), position=(-0.47, y_pos))
        
        # Asignar color dependiendo del tipo
        fg_color = color.white
        if tipo == 'velocidad': fg_color = color.azure
        elif tipo == 'insta_kill': fg_color = color.red
        elif tipo == 'doble_cadencia': fg_color = color.yellow
        elif tipo == 'recarga_rapida': fg_color = color.blue
        
        fg = Entity(parent=bg, model='quad', color=fg_color, scale=(1, 1), position=(-0.5, 0), origin=(-0.5, 0))
        texto = Text(parent=camera.ui, text=nombre_mostrar, position=(-0.60, y_pos + 0.015), origin=(-0.5, -0.5), scale=0.8, color=color.white)
        
        self.powerups_activos[tipo] = {
            'restante': duracion, 'total': duracion, 'nombre': nombre_mostrar,
            'bg': bg, 'fg': fg, 'texto': texto
        }
        
        if tipo == 'velocidad':
            self.velocidad_caminar *= 1.5
            self.velocidad_correr *= 1.5

    def desactivar_powerup(self, tipo):
        if tipo not in self.powerups_activos:
            return
            
        datos = self.powerups_activos.pop(tipo)
        destroy(datos['bg'])
        destroy(datos['texto'])
        
        if tipo == 'velocidad':
            self.velocidad_caminar /= 1.5
            self.velocidad_correr /= 1.5
            
        self._reposicionar_powerups_ui()

    def _reposicionar_powerups_ui(self):
        idx = 0
        for t, datos in self.powerups_activos.items():
            y_pos = -0.45 + (idx * 0.05)
            datos['bg'].y = y_pos
            datos['texto'].y = y_pos + 0.015
            idx += 1

    def update(self):
        # --- ACTUALIZAR BARRA DE VIDA ---
        self.texto_vida.text = f'{max(0, int(self.vida))} / {self.vida_maxima}'
        self.barra_vida_fg.scale_x = max(self.vida / float(self.vida_maxima), 0.0)
        
        # --- ACTUALIZAR POWERUPS ---
        if self.tiempo_mensaje_powerup > 0:
            self.tiempo_mensaje_powerup -= time.dt
            if self.tiempo_mensaje_powerup <= 0:
                self.powerup_texto.enabled = False

        powerups_a_eliminar = []
        for tipo, datos in self.powerups_activos.items():
            datos['restante'] -= time.dt
            if datos['restante'] <= 0:
                powerups_a_eliminar.append(tipo)
            else:
                datos['fg'].scale_x = max(datos['restante'] / datos['total'], 0.0)

        for tipo in powerups_a_eliminar:
            self.desactivar_powerup(tipo)
                
        # --- ACTUALIZAR RONDA Y ENEMIGOS ---
        import __main__ as main
        if hasattr(main, 'coordinador') and main.coordinador:
            indice_arena = int(round(self.z / main.coordinador.offset_z))
            
            if hasattr(main, 'gestores_arena') and 0 <= indice_arena < len(main.gestores_arena):
                gestor = main.gestores_arena[indice_arena]
                
                ronda_calculada = getattr(gestor, 'ronda_actual', 1)
                
                if ronda_calculada != self.ronda_actual:
                    self.ronda_actual = ronda_calculada
                    self.actualizar_hud_ronda()
                    
                vivos = sum(1 for e in gestor.enemigos if e.enabled and hasattr(e, 'vida') and e.vida > 0)
                faltantes = vivos + getattr(gestor, 'spawns_pendientes', 0)
                self.texto_enemigos.text = f'ENEMIGOS: {faltantes}'


        if self.esta_muerto:
            return
            
        # --- SISTEMA DE RASTREO (BREADCRUMBING PARA IA) ---
        from ursina import distance
        if not hasattr(self, 'posicion_rastreo'):
            self.posicion_rastreo = self.position
        
        # Solo actualizamos la posición objetivo para la horda si nos movemos más de 2 metros
        if distance(self.position, self.posicion_rastreo) > 2.0:
            self.posicion_rastreo = self.position
            
        # --- DISPARO AUTOMÁTICO ---
        if held_keys['left mouse']:
            if getattr(self, 'tiene_arma', False) and not getattr(self, 'haciendo_dash', False):
                if getattr(self, 'armas_inventario', None):
                    arma_data = self.armas_inventario[self.indice_arma_actual]
                    # Solo disparamos automáticamente si tiene munición (evita recarga automática al mantener presionado)
                    if arma_data.get('automatico', False) and arma_data.get('balas_cargador', 0) > 0:
                        self.disparar()
            
        # Limitar dt para evitar glitches físicos durante picos de lag (como al cargar el juego)
        dt = min(time.dt, 0.05)
        
        # --- SEGUIMIENTO EXACTO DEL ARMA A LA MANO (CON INTERPOLACIÓN IDLE/MOVE) ---
        is_moving = held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d']
        target_pos = self.arma_offset_pos_move if is_moving else self.arma_offset_pos_idle
        self.arma_offset_pos_actual = lerp(self.arma_offset_pos_actual, target_pos, dt * 10)
        
        if getattr(self, 'tiene_arma', False) and getattr(self, 'arma_entidad', None) and getattr(self, 'mano_derecha_hueso', None):
            pos_mano = self.mano_derecha_hueso.getPos(scene)
            offset_global = (self.right * self.arma_offset_pos_actual.x) + (self.up * self.arma_offset_pos_actual.y) + (self.forward * self.arma_offset_pos_actual.z)
            self.arma_entidad.world_position = pos_mano + offset_global
            self.arma_entidad.rotation = self.arma_offset_rot
            self.arma_entidad.scale = self.arma_escala

        # --- MODO DEBUG MAESTRO (MANTENER ALT) ---
        if held_keys['alt'] and getattr(self, 'tiene_arma', False):
            if held_keys['1']: self.modo_debug_editando = 'ARMA'
            if held_keys['2']: self.modo_debug_editando = 'BALA'
            
            arma_data = self.armas_inventario[self.indice_arma_actual]
            id_arma = arma_data.get('id_arma', 'DEFAULT')
            
            velocidad_mov = 0.5 * dt
            velocidad_rot = 100 * dt
            velocidad_escala = 0.1 * dt
            
            if self.modo_debug_editando == 'ARMA':
                self.debug_bala_visual.enabled = False
                self.texto_debug_arma.text = f"[MODO DEBUG: {id_arma}]\n[1] ARMA | [2] BALA\n\nMover Arma:\nAdelante/Atras: I / K\nIzq/Der: J / L\nArriba/Abajo: U / O\n\nRotar:\nArriba/Abajo (Pitch): Flechas\nLados (Yaw): Flechas\nGirar (Roll): N / M\n\nEscala: + / -\nGuardar: P"
                
                # Posición (I/K=Z, J/L=X, U/O=Y)
                if held_keys['i']: self.arma_offset_pos_idle.z += velocidad_mov; self.arma_offset_pos_move.z += velocidad_mov
                if held_keys['k']: self.arma_offset_pos_idle.z -= velocidad_mov; self.arma_offset_pos_move.z -= velocidad_mov
                if held_keys['j']: self.arma_offset_pos_idle.x -= velocidad_mov; self.arma_offset_pos_move.x -= velocidad_mov
                if held_keys['l']: self.arma_offset_pos_idle.x += velocidad_mov; self.arma_offset_pos_move.x += velocidad_mov
                if held_keys['u']: self.arma_offset_pos_idle.y += velocidad_mov; self.arma_offset_pos_move.y += velocidad_mov
                if held_keys['o']: self.arma_offset_pos_idle.y -= velocidad_mov; self.arma_offset_pos_move.y -= velocidad_mov

                # Rotación (Flechas = X/Y, N/M = Z)
                if held_keys['up arrow']: self.arma_offset_rot.x += velocidad_rot
                if held_keys['down arrow']: self.arma_offset_rot.x -= velocidad_rot
                if held_keys['left arrow']: self.arma_offset_rot.y -= velocidad_rot
                if held_keys['right arrow']: self.arma_offset_rot.y += velocidad_rot
                if held_keys['n']: self.arma_offset_rot.z -= velocidad_rot
                if held_keys['m']: self.arma_offset_rot.z += velocidad_rot

                # Escala (+/-)
                if held_keys['+']: self.arma_escala += velocidad_escala
                if held_keys['-']: self.arma_escala -= velocidad_escala
                
            elif self.modo_debug_editando == 'BALA':
                self.debug_bala_visual.enabled = True
                self.texto_debug_arma.text = f"[MODO DEBUG: {id_arma}]\n[1] ARMA | [2] BALA\n\nMover Origen de Bala:\nAdelante/Atras: I / K\nIzq/Der: J / L\nArriba/Abajo: U / O\n\nGuardar Consola: P"
                
                origen = self.world_position + self.up * self.bala_offset.y + self.right * self.bala_offset.x + self.forward * self.bala_offset.z
                self.debug_bala_visual.world_position = origen
                
                # Posición (I/K=Z, J/L=X, U/O=Y)
                if held_keys['i']: self.bala_offset.z += velocidad_mov
                if held_keys['k']: self.bala_offset.z -= velocidad_mov
                if held_keys['j']: self.bala_offset.x -= velocidad_mov
                if held_keys['l']: self.bala_offset.x += velocidad_mov
                if held_keys['u']: self.bala_offset.y += velocidad_mov
                if held_keys['o']: self.bala_offset.y -= velocidad_mov

            # Guardar el estado actual en el diccionario
            self.offsets_por_arma[id_arma] = {
                'pos_idle': self.arma_offset_pos_idle,
                'pos_move': self.arma_offset_pos_move,
                'rot': self.arma_offset_rot,
                'escala': self.arma_escala,
                'bala': self.bala_offset
            }

            # Imprimir en consola con la tecla P
            if held_keys['p']:
                print("\n==================================")
                print(f"VALORES PERFECTOS PARA: {id_arma}")
                print(f"                'pos_idle': Vec3({self.arma_offset_pos_idle.x:.3f}, {self.arma_offset_pos_idle.y:.3f}, {self.arma_offset_pos_idle.z:.3f}),")
                print(f"                'pos_move': Vec3({self.arma_offset_pos_move.x:.3f}, {self.arma_offset_pos_move.y:.3f}, {self.arma_offset_pos_move.z:.3f}),")
                print(f"                'rot': Vec3({self.arma_offset_rot.x:.3f}, {self.arma_offset_rot.y:.3f}, {self.arma_offset_rot.z:.3f}),")
                print(f"                'escala': {self.arma_escala:.3f},")
                print(f"                'bala': Vec3({self.bala_offset.x:.3f}, {self.bala_offset.y:.3f}, {self.bala_offset.z:.3f})")
                print("==================================\n")
        else:
            self.debug_bala_visual.enabled = False
            if hasattr(self, 'texto_debug_arma'):
                self.texto_debug_arma.text = ""
        if self.camara_frontal:
            self.pivot_camara.rotation_y = 180
            self.pivot_camara.position = (1, 1.5, -4)
            giro_mouse = 0
        else:
            if self.estado_animacion == 'drinking':
                self.pivot_camara.rotation_y += mouse.velocity[0] * 40
                self.pivot_camara.position = (0, 1.5, 0)
                giro_mouse = 0
                self._camara_rotada_bebiendo = True
            else:
                if getattr(self, '_camara_rotada_bebiendo', False):
                    self.rotation_y += self.pivot_camara.rotation_y
                    self._camara_rotada_bebiendo = False
                self.pivot_camara.rotation_y = 0
                self.pivot_camara.position = (1, 1.5, 0)
                giro_mouse = mouse.velocity[0] * 40
        
        self.rotation_y += giro_mouse
        self.pivot_camara.rotation_x -= mouse.velocity[1] * 40
        
        self.pivot_camara.rotation_x = clamp(self.pivot_camara.rotation_x, -5, 55)
        
        # --- PREVENCIÓN DE CÁMARA ATRAVESANDO PAREDES Y ZOOM DINÁMICO ---
        direccion_camara = -self.pivot_camara.forward
        # Hacemos el raycast desde la posición local en X, Y de la cámara para que no atraviese paredes por el lado
        origen_raycast = self.pivot_camara.world_position + (self.pivot_camara.right * camera.x) + (self.pivot_camara.up * camera.y)
        hit_camara = raycast(origen_raycast, direccion_camara, distance=self.distancia_camara_objetivo, ignore=(self, self.modelo_visual, self.pivot_camara))
        
        if hit_camara.hit:
            # Si choca con pared, acercamos la cámara
            distancia_real = hit_camara.distance - 0.5
            camera.z = -clamp(distancia_real, 2.0, self.distancia_camara_objetivo)
        else:
            # Transición suave del zoom
            camera.z = -self.distancia_camara_objetivo

        # --- CÁLCULO DE DIRECCIÓN Y ANIMACIÓN ---
        corriendo = held_keys['shift']
        velocidad = self.velocidad_correr if corriendo else self.velocidad_caminar
        
        # Efecto de estado: Congelado
        if self.congelado:
            velocidad *= 0.5
            
        input_y = held_keys['w'] - held_keys['s']
        input_x = held_keys['d'] - held_keys['a']
        
        direccion = Vec3(
            self.forward * input_y + 
            self.right * input_x
        ).normalized()
        
        if self.haciendo_dash:
            velocidad = 45 
            direccion = self.dash_direccion
            
        # Gestor de Animaciones
        if not self.atacando and not self.haciendo_dash and self.en_suelo:
            if input_y == 0 and input_x == 0:
                self.cambiar_animacion('idle')
            elif input_y < 0:
                self.cambiar_animacion('walk_back')
            elif corriendo:
                self.cambiar_animacion('run')
            else:
                self.cambiar_animacion('walk')
                
        # Detener movimiento si estamos atacando fuerte, pero permitir caminar lento al beber
        if self.atacando:
            if self.estado_animacion == 'drinking':
                velocidad = self.velocidad_caminar * 0.5
            else:
                direccion = Vec3(0,0,0)
            
        desplazamiento = direccion * velocidad * dt
        
        # --- FISICAS DE COLISIÓN HORIZONTAL ---
        entidades_ignoradas = (self, self.modelo_visual)
        if hasattr(self, 'campo_fuerza') and self.campo_fuerza:
            entidades_ignoradas += (self.campo_fuerza,)
            
        if desplazamiento.x != 0:
            dir_x = 1 if desplazamiento.x > 0 else -1
            dist_x = abs(desplazamiento.x) + 0.35
            hit_x = raycast(self.position + Vec3(0, 1.0, 0), direction=(dir_x, 0, 0), distance=dist_x, ignore=entidades_ignoradas)
            if not hit_x.hit:
                self.x += desplazamiento.x
            elif hasattr(hit_x.entity, 'jugador_objetivo'):
                # Empujar suavemente al enemigo para abrirnos paso si estamos acorralados
                hit_x.entity.x += desplazamiento.x * 0.8
                self.x += desplazamiento.x * 0.8
                
        if desplazamiento.z != 0:
            dir_z = 1 if desplazamiento.z > 0 else -1
            dist_z = abs(desplazamiento.z) + 0.35
            hit_z = raycast(self.position + Vec3(0, 1.0, 0), direction=(0, 0, dir_z), distance=dist_z, ignore=entidades_ignoradas)
            if not hit_z.hit:
                self.z += desplazamiento.z
            elif hasattr(hit_z.entity, 'jugador_objetivo'):
                hit_z.entity.z += desplazamiento.z * 0.8
                self.z += desplazamiento.z * 0.8

        # --- FISICAS DE GRAVEDAD Y SALTO ---
        if held_keys['space'] and self.en_suelo and not self.atacando and not self.haciendo_dash:
            self.velocidad_y = self.velocidad_salto
            self.cambiar_animacion('jump')
            self.en_suelo = False
            
        self.velocidad_y -= self.gravedad * dt
        hit_info = raycast(self.position + Vec3(0, 1.0, 0), direction=(0, -1, 0), ignore=(self,))
        
        if hit_info.hit and hit_info.distance <= (1.0 - (self.velocidad_y * dt)):
            self.y = hit_info.world_point.y
            self.velocidad_y = 0
            self.en_suelo = True
        else:
            self.y += self.velocidad_y * dt
            self.en_suelo = False
            
        # --- ACTUALIZAR RADAR TÁCTICO BIOLÓGICO ---
        import __main__ as main
        indice_punto = 0
        if hasattr(main, 'gestores_arena') and hasattr(main, 'coordinador') and main.coordinador:
            indice_actual = int(round(self.z / main.coordinador.offset_z))
            if 0 <= indice_actual < len(main.gestores_arena):
                gestor = main.gestores_arena[indice_actual]
                for enemigo in gestor.enemigos:
                    if enemigo.enabled and hasattr(enemigo, 'vida') and enemigo.vida > 0:
                        dir_vector = enemigo.position - self.position
                        dir_xz = Vec3(dir_vector.x, 0, dir_vector.z)
                        distancia = dir_xz.length()
                        
                        if distancia < 250 and indice_punto < len(self.puntos_radar):
                            local_z = dir_xz.dot(self.forward) 
                            local_x = dir_xz.dot(self.right)   
                            
                            punto = self.puntos_radar[indice_punto]
                            punto.enabled = True
                            punto.x = clamp(local_x * 0.0018, -0.45, 0.45)
                            punto.y = clamp(local_z * 0.0018, -0.45, 0.45)
                            indice_punto += 1
                            
        for i in range(indice_punto, len(self.puntos_radar)):
            self.puntos_radar[i].enabled = False

        # --- RADAR DE MESA DE TRABAJO ---
        if hasattr(main, 'mesa_trabajo') and main.mesa_trabajo and not getattr(main.mesa_trabajo, 'destroyed', False):
            dir_vector = main.mesa_trabajo.world_position - self.position
            dir_xz = Vec3(dir_vector.x, 0, dir_vector.z)
            distancia = dir_xz.length()
            if distancia < 250:
                local_z = dir_xz.dot(self.forward) 
                local_x = dir_xz.dot(self.right)   
                self.punto_radar_mesa.enabled = True
                self.punto_radar_mesa.x = clamp(local_x * 0.0018, -0.45, 0.45)
                self.punto_radar_mesa.y = clamp(local_z * 0.0018, -0.45, 0.45)
            else:
                self.punto_radar_mesa.enabled = False
        else:
            self.punto_radar_mesa.enabled = False

        # --- RADAR DE CAJA MISTERIOSA ---
        if hasattr(main, 'caja_misteriosa') and main.caja_misteriosa and not getattr(main.caja_misteriosa, 'destroyed', False):
            dir_vector = main.caja_misteriosa.world_position - self.position
            dir_xz = Vec3(dir_vector.x, 0, dir_vector.z)
            distancia = dir_xz.length()
            if distancia < 250:
                local_z = dir_xz.dot(self.forward) 
                local_x = dir_xz.dot(self.right)   
                self.punto_radar_caja.enabled = True
                self.punto_radar_caja.x = clamp(local_x * 0.0018, -0.45, 0.45)
                self.punto_radar_caja.y = clamp(local_z * 0.0018, -0.45, 0.45)
            else:
                self.punto_radar_caja.enabled = False
        else:
            self.punto_radar_caja.enabled = False

        # --- MOTOR DE NIEVE CONTINUA ---
        # (SISTEMA DE NIEVE ELIMINADO)

    def comprar_bebida(self, tipo):
        if tipo in self.perks_comprados:
            return # Ya la tiene
            
        self.perks_comprados.append(tipo)
        
        if tipo == 'azul':
            self.vidas_extra += 1
        elif tipo == 'roja':
            self.vida_maxima = 200
            self.vida = 200
            self.barra_vida_bg.scale = (0.50, 0.015) # Hacemos la barra visualmente el doble de larga
        elif tipo == 'verde':
            self.max_armas = 3
            
        self.actualizar_ui_perks()
        print(f"Bebida {tipo} adquirida.")
        
        # Animación de beber y Campo de Fuerza
        if self.actor:
            if hasattr(self, 'arma_entidad') and self.arma_entidad:
                self.arma_entidad.enabled = False
            self.actor.setPlayRate(1.0, 'drinking')
            self.actor.play('drinking')
            self.estado_animacion = 'drinking'
            self.atacando = True # bloquea el movimiento
            
            # Generar campo de fuerza
            color_campo = color.white
            if tipo == 'azul': color_campo = color.cyan
            elif tipo == 'roja': color_campo = color.red
            elif tipo == 'verde': color_campo = color.green
            
            self.campo_fuerza = CampoFuerzaProtector(self, color.rgba(*color_campo.rgba[:3], 100))
            
            # La animación hacia adelante dura unos 2 segundos
            invoke(self.reversa_bebida, delay=2.0)

    def reversa_bebida(self):
        if self.actor and not self.esta_muerto:
            self.actor.setPlayRate(-1.5, 'drinking') # Reversa rápida para mejor transición
            self.actor.play('drinking')
            
        invoke(self.terminar_animacion_bebida, delay=1.2)

    def terminar_animacion_bebida(self):
        self.atacando = False
        if self.actor and not self.esta_muerto:
            self.actor.setPlayRate(1.0, 'drinking') # Restaurar play rate
            self.cambiar_animacion('idle')
            if hasattr(self, 'arma_entidad') and self.arma_entidad:
                self.arma_entidad.enabled = True
                
        # El círculo protector se queda por 3 segundos extra
        invoke(self.destruir_campo_fuerza, delay=3.0)

    def destruir_campo_fuerza(self):
        if hasattr(self, 'campo_fuerza') and self.campo_fuerza:
            self.campo_fuerza.animate_scale(0, duration=0.5)
            destroy(self.campo_fuerza, delay=0.5)
            self.campo_fuerza = None

    def actualizar_ui_perks(self):
        # Limpiar iconos anteriores
        for icono in self.ui_perks_iconos:
            destroy(icono)
        self.ui_perks_iconos.clear()
        
        # Dibujar iconos centrados en la parte inferior de la pantalla
        total_perks = len(self.perks_comprados)
        espaciado = 0.05
        ancho_total = (total_perks - 1) * espaciado
        x_base = -(ancho_total / 2)
        
        for i, perk in enumerate(self.perks_comprados):
            color_icono = color.white
            if perk == 'azul': color_icono = color.cyan
            elif perk == 'roja': color_icono = color.red
            elif perk == 'verde': color_icono = color.green
            
            icono = Entity(
                parent=camera.ui,
                model='circle',
                color=color_icono,
                scale=(0.04, 0.04),
                position=(x_base + (i * espaciado), -0.38) # Arriba de la barra de vida
            )
            self.ui_perks_iconos.append(icono)