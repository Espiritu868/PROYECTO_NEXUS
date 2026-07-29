from ursina import Entity, camera, Vec3, held_keys, time, raycast, mouse, clamp, load_texture, Text, color, destroy
from direct.actor.Actor import Actor
import math

class Bala(Entity):
    def __init__(self, posicion_inicial, direccion, dano, jugador_obj, **kwargs):
        super().__init__(
            model='sphere',
            color=color.yellow,
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
            destroy(self)

class Jugador(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = (1, 1, 1)
        self.origin_y = 0 
        
        # --- 1. CARGA DEL MODELO ANIMADO GLB (TRABAJADOR DE PLANTA) ---
        ruta_base = "assets/modelos/personajes_principales/trabajador_de_planta/"
        
        self.modelo_visual = Entity(parent=self, rotation_y=180) # Rotamos 180 para que mire al frente
        
        try:
            self.actor = Actor(
                ruta_base + "worker_idle.glb",
                {
                    'idle': ruta_base + 'worker_idle.glb',
                    'walk': ruta_base + 'worker_walk.glb',
                    'walk_back': ruta_base + 'worker_walk_back.glb',
                    'run': ruta_base + 'worker_run.glb',
                    'dash': ruta_base + 'worker_dash.glb',
                    'slash': ruta_base + 'worker_slash.glb',
                    'uppercut': ruta_base + 'worker_uppercut.glb',
                    'kick': ruta_base + 'worker_kick.glb',
                    'hit': ruta_base + 'worker_hit.glb',
                    'dead': ruta_base + 'worker_dead.glb'
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
                for anim in ['walk', 'walk_back', 'run', 'dash', 'slash', 'uppercut', 'kick', 'hit', 'dead']:
                    self.actor.getAnimControl(anim)
            except:
                pass
            
            # Amplificamos un poco la escala (1.6) para que sea tamaño humano promedio
            self.modelo_visual.scale = 1.6 
            
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
        self.velocidad_salto = 22
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
        self.esta_muerto = False
        self.barra_vida_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0.1, 0.1, 0.1, 0.9), scale=(0.25, 0.015), position=(0, -0.45))
        self.barra_vida_fg = Entity(parent=self.barra_vida_bg, model='quad', color=color.rgba(0.0, 0.8, 0.0, 1.0), scale=(1, 1), position=(-0.5, 0), origin=(-0.5, 0))
        self.texto_vida = Text(parent=camera.ui, text=f'{self.vida} / 100', position=(0, -0.42), origin=(0, 0), scale=0.9, color=color.white)
        self.mira = Entity(parent=camera.ui, model='quad', scale=(0.01, 0.01), color=color.white, texture='circle')
        
        self.dano_ataque = 35
        self.atacando = False
        self.rango_ataque = 4.5 # Metros
        self.tiene_arma = False
        self.arma_entidad = None
        self.ultimo_disparo = 0
        
        # --- NUEVO: SISTEMA DE MUNICIÓN ---
        self.balas_cargador_max = 25
        self.balas_cargador = 25
        self.balas_reserva_max = 300
        self.balas_reserva = 300
        self.recargando = False
        self.texto_municion = Text(parent=camera.ui, text=f'{self.balas_cargador} / {self.balas_reserva}', position=(0.6, -0.42), origin=(0, 0), scale=1.5, color=color.white)
        self.texto_municion.enabled = False
        
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
        
        # --- 11. CHEATS ---
        self.invulnerable = False
        self.teclas_escritas = ""
        
        # --- 12. POWERUPS UI ---
        self.powerup_texto = Text(parent=camera.ui, text='', position=(-0.60, -0.35), origin=(-0.5, -0.5), scale=1, color=color.white)
        self.powerup_texto.enabled = False
        
        self.powerups_activos = {}
        self.tiempo_mensaje_powerup = 0

    def input(self, key):
        if self.esta_muerto: return
        
        # CHEAT CODE: ASNAEB
        if len(key) == 1 and key.isalpha():
            self.teclas_escritas += key.lower()
            if len(self.teclas_escritas) > 6:
                self.teclas_escritas = self.teclas_escritas[-6:]
            if self.teclas_escritas == "asnaeb":
                self.invulnerable = not self.invulnerable
                self.teclas_escritas = "" # Reset
                print(f"Modo Invulnerable: {'ON' if self.invulnerable else 'OFF'}")
        
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
            if self.balas_cargador < self.balas_cargador_max and self.balas_reserva > 0:
                self.recargar()
                    
        if key == 'c' and self.dash_disponible and not self.haciendo_dash and not self.atacando:
            self.iniciar_dash()

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
        from ursina import invoke
        invoke(self.terminar_ataque, delay=0.8)

    def terminar_ataque(self):
        if self.esta_muerto: return
        self.atacando = False
        self.cambiar_animacion('idle')

    def equipar_arma(self, modelo_existente=None):
        if self.tiene_arma:
            return
        self.tiene_arma = True
        self.texto_municion.enabled = True
        # El arma flota al lado derecho del jugador
        if modelo_existente:
            self.arma_entidad = modelo_existente
            self.arma_entidad.parent = self
            self.arma_entidad.collider = None
            self.arma_entidad.position = (0.8, 1.2, 0.5)
            self.arma_entidad.scale = 0.1
            self.arma_entidad.rotation = (0, 0, 0)
            if hasattr(self.arma_entidad, 'animations'):
                for seq in self.arma_entidad.animations:
                    seq.pause()
                    seq.kill()
            self.arma_entidad.animations = []
        else:
            self.arma_entidad = Entity(parent=self, model='assets/modelos/objetos_con_meshy/arma.glb', position=(0.8, 1.2, 0.5), scale=0.1)
        
    def recargar(self):
        self.recargando = True
        self.texto_municion.text = "Recargando..."
        self.texto_municion.color = color.yellow
        
        tiempo_recarga = 1.5
        if 'recarga_rapida' in self.powerups_activos:
            tiempo_recarga = 0.75
            
        from ursina import invoke
        invoke(self._finalizar_recarga, delay=tiempo_recarga)

    def _finalizar_recarga(self):
        if self.esta_muerto: return
        self.recargando = False
        
        balas_faltantes = self.balas_cargador_max - self.balas_cargador
        if self.balas_reserva >= balas_faltantes:
            self.balas_reserva -= balas_faltantes
            self.balas_cargador = self.balas_cargador_max
        else:
            self.balas_cargador += self.balas_reserva
            self.balas_reserva = 0
            
        self.texto_municion.color = color.white
        self.actualizar_hud_municion()

    def actualizar_hud_municion(self):
        if not self.recargando:
            self.texto_municion.text = f'{self.balas_cargador} / {self.balas_reserva}'
            if self.balas_cargador <= 5:
                self.texto_municion.color = color.red
            else:
                self.texto_municion.color = color.white

    def disparar(self):
        if self.recargando: return
        
        if self.balas_cargador <= 0:
            if self.balas_reserva > 0:
                self.recargar()
            else:
                self.texto_municion.text = "¡SIN MUNICIÓN!"
                self.texto_municion.color = color.red
            return
            
        cadencia = 0.2
        if 'doble_cadencia' in self.powerups_activos:
            cadencia = 0.1
            
        if time.time() - self.ultimo_disparo < cadencia:
            return
        self.ultimo_disparo = time.time()
        
        self.balas_cargador -= 1
        self.actualizar_hud_municion()
        self.ultimo_disparo = time.time()
        
        origen_disparo = self.arma_entidad.world_position if self.arma_entidad else self.world_position + Vec3(0, 1.5, 0)
        direccion_disparo = camera.forward # Dispara hacia donde mira la cámara
        
        # Retroceso visual básico
        if self.arma_entidad:
            self.arma_entidad.animate_position((0.8, 1.2, 0.3), duration=0.05)
            self.arma_entidad.animate_position((0.8, 1.2, 0.5), duration=0.1, delay=0.05)
        
        Bala(posicion_inicial=origen_disparo, direccion=direccion_disparo, dano=35, jugador_obj=self)

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
        
        from ursina import invoke
        invoke(self.terminar_dash, delay=0.3) 
        invoke(self.recuperar_dash, delay=self.dash_cooldown)

    def terminar_dash(self):
        if self.esta_muerto: return
        self.haciendo_dash = False
        self.cambiar_animacion('idle')

    def recuperar_dash(self):
        self.dash_disponible = True

    def recibir_dano(self, cantidad):
        if self.esta_muerto or self.invulnerable: return
        self.vida -= cantidad
        
        # Hit reaction
        if self.actor and not self.atacando and not self.haciendo_dash:
            self.actor.play('hit')
            self.estado_animacion = 'hit'
            from ursina import invoke
            invoke(lambda: self.cambiar_animacion('idle') if not self.esta_muerto and not self.atacando else None, delay=0.5)

        if self.vida <= 0:
            self.morir()

    def morir(self):
        self.esta_muerto = True
        self.vida = 0
        if self.actor:
            self.actor.play('dead')
            self.estado_animacion = 'dead'
        
        # Efecto visual de muerte (cae la cámara o se pinta la pantalla)
        self.barra_vida_fg.color = color.black

    def cambiar_animacion(self, nombre_animacion):
        if not self.actor or self.atacando or self.haciendo_dash or self.esta_muerto:
            return
            
        # Prevenir reiniciar la misma animación si ya está corriendo
        if self.estado_animacion != nombre_animacion:
            # Si es hit, play. Si es movimiento, loop.
            if nombre_animacion in ['hit', 'dead', 'uppercut', 'slash', 'kick', 'dash']:
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
        self.texto_vida.text = f'{max(0, self.vida)} / 100'
        self.barra_vida_fg.scale_x = max(self.vida / 100.0, 0.0)
        
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
                
        if self.esta_muerto:
            return
            
        # Limitar dt para evitar glitches físicos durante picos de lag (como al cargar el juego)
        dt = min(time.dt, 0.05)

        # --- CONTROL DE CÁMARA ---
        if held_keys['control']:
            self.pivot_camara.rotation_y = 180
            giro_mouse = 0 
        else:
            self.pivot_camara.rotation_y = 0
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
                
        # Detener movimiento si estamos atacando fuerte
        if self.atacando:
            direccion = Vec3(0,0,0)
            
        desplazamiento = direccion * velocidad * dt
        
        # --- FISICAS DE COLISIÓN HORIZONTAL ---
        if desplazamiento.x != 0:
            dir_x = 1 if desplazamiento.x > 0 else -1
            if not raycast(self.position + Vec3(0, 1.0, 0), direction=(dir_x, 0, 0), distance=1.0, ignore=(self,)).hit:
                self.x += desplazamiento.x
                
        if desplazamiento.z != 0:
            dir_z = 1 if desplazamiento.z > 0 else -1
            if not raycast(self.position + Vec3(0, 1.0, 0), direction=(0, 0, dir_z), distance=1.0, ignore=(self,)).hit:
                self.z += desplazamiento.z

        # --- FISICAS DE GRAVEDAD Y SALTO ---
        if held_keys['space'] and self.en_suelo and not self.atacando and not self.haciendo_dash:
            self.velocidad_y = self.velocidad_salto
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
        if hasattr(main, 'gestores_arena'):
            for gestor in main.gestores_arena:
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

        # --- MOTOR DE NIEVE CONTINUA ---
        # (SISTEMA DE NIEVE ELIMINADO)