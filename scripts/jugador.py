from ursina import Entity, camera, Vec3, held_keys, time, raycast, mouse, clamp, load_texture, Text, color
import math

class Jugador(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = (1, 1, 1)
        self.origin_y = -0.5 
        
        # --- 1. CARGA DEL MODELO BASE ---
        self.modelo_visual = Entity(
            parent=self,
            model='assets/modelos/character-j.fbx',
            scale=(0.01, 0.01, 0.01),
            rotation_y=180
        )
        
        # --- 2. FORZAR LA TEXTURA CORREGIDA ---
        textura_real = load_texture('assets/modelos/textures/texture-j.png')
        if textura_real:
            self.modelo_visual.set_texture(textura_real._texture, 1)
        else:
            print("❌ Advertencia: No se encontró la textura del jugador.")

        # --- 3. IDENTIFICACIÓN DE EXTREMIDADES PARA ANIMACIÓN ---
        # Buscamos las piezas internas del FBX usando las rutas que reveló el escáner
        self.pierna_izq = self.modelo_visual.find('**/leg-left')
        self.pierna_der = self.modelo_visual.find('**/leg-right')
        self.brazo_izq = self.modelo_visual.find('**/arm-left')
        self.brazo_der = self.modelo_visual.find('**/arm-right')
        self.torso = self.modelo_visual.find('**/torso')
        self.cabeza = self.modelo_visual.find('**/head')

        # --- 4. CONFIGURACIÓN DE MOVIMIENTO ---
        self.velocidad_caminar = 20
        self.velocidad_correr = 45
        
        self.gravedad = 60
        self.velocidad_salto = 22
        self.velocidad_y = 0
        self.en_suelo = False
        
        # --- 5. CONFIGURACIÓN DE CÁMÁRA TERCERA PERSONA ---
        self.pivot_camara = Entity(parent=self, y=3) 
        camera.parent = self.pivot_camara
        camera.position = (0, 0.5, -12) 
        camera.look_at(self.pivot_camara)
        
        mouse.locked = True 

        # --- 6. SISTEMA DE COMBATE (VIDA Y MIRA) ---
        self.vida = 100
        # Barra de salud gráfica mucho más pequeña y elegante
        self.barra_vida_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0.1, 0.1, 0.1, 0.9), scale=(0.25, 0.015), position=(0, -0.45))
        self.barra_vida_fg = Entity(parent=self.barra_vida_bg, model='quad', color=color.rgba(0.0, 0.8, 0.0, 1.0), scale=(1, 1), position=(-0.5, 0), origin=(-0.5, 0))
        self.texto_vida = Text(parent=camera.ui, text=f'{self.vida} / 100', position=(0, -0.42), origin=(0, 0), scale=0.9, color=color.white)
        self.mira = Entity(parent=camera.ui, model='quad', scale=(0.01, 0.01), color=color.red, texture='circle')
        self.dano_ataque = 25
        
        # --- 7. LINTERNA TÁCTICA (SPOTLIGHT) ---
        from ursina import SpotLight
        # Acompaña a la cámara para perforar la niebla
        self.linterna = SpotLight(parent=camera, position=(0, 0, 0), color=color.white, shadows=False)
        
        # --- 8. ESQUIVA TÁCTICA (DASH) ---
        self.dash_disponible = True
        self.dash_cooldown = 1.5
        self.haciendo_dash = False
        self.dash_direccion = Vec3(0,0,0)
        
        # --- 9. SISTEMA DE NIEVE OPTIMIZADO (GPU-LIKE WORLD SPACE) ---
        import random
        self.copos_nieve = []
        for i in range(250): # 250 copos es súper ligero para la CPU
            copo = Entity(
                model='quad',
                scale=random.uniform(0.05, 0.12),
                color=color.rgba(255, 255, 255, 180),
                billboard=True, # Siempre miran a la cámara
                unlit=True # Brillan en la oscuridad para que la linterna no sea obligatoria para verlos
            )
            # Spawnean en un radio MASIVO para que al correr no los alcances a rebasar tan rápido
            copo.position = self.position + Vec3(random.uniform(-100, 100), random.uniform(0, 80), random.uniform(-100, 100))
            copo.velocidad_caida = random.uniform(15, 35) # Caen súper rápido simulando tormenta
            copo.desvio_viento = random.uniform(-6, 6)
            self.copos_nieve.append(copo)
            
        # --- 10. RADAR TÁCTICO (ESCÁNER BIOLÓGICO) ---
        # Radar (25% de la pantalla, como estaba originalmente)
        self.radar_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0.0, 0.15, 0.0, 0.85), scale=(0.25, 0.25), position=(-0.7, 0.35))
        
        # Mejoras estéticas: Cuadrícula fina y anillo de escáner
        Entity(parent=self.radar_bg, model='quad', color=color.rgba(0.0, 0.7, 0.0, 0.4), scale=(1, 0.01), z=-0.01)
        Entity(parent=self.radar_bg, model='quad', color=color.rgba(0.0, 0.7, 0.0, 0.4), scale=(0.01, 1), z=-0.01)
        Entity(parent=self.radar_bg, model='circle', color=color.rgba(0.0, 0.9, 0.0, 0.2), scale=(0.8, 0.8), z=-0.01)
        
        # El jugador
        self.radar_jugador = Entity(parent=self.radar_bg, model='arrow', color=color.cyan, scale=(0.06, 0.06), z=-0.03)
        self.puntos_radar = [Entity(parent=self.radar_bg, model='circle', color=color.red, scale=(0.05, 0.05), enabled=False, z=-0.02) for _ in range(40)]

    def input(self, key):
        if key == 'left mouse down':
            # Disparar láser invisible (raycast)
            # Ignoramos completamente todo el cuerpo y cámara del jugador
            hit_info = raycast(camera.world_position, camera.forward, distance=150, ignore=(self, self.pivot_camara, self.modelo_visual))
            if hit_info.hit:
                entidad = hit_info.entity
                if hasattr(entidad, 'recibir_dano'):
                    entidad.recibir_dano(self.dano_ataque)
                    
        if key == 'c' and self.dash_disponible and not self.haciendo_dash:
            self.iniciar_dash()

    def iniciar_dash(self):
        # Determinar dirección de esquiva según teclas
        dir_actual = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) + 
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()
        
        if dir_actual.length() == 0:
            dir_actual = self.forward # Hacia adelante por defecto si no pulsa nada
            
        self.dash_direccion = dir_actual
        self.haciendo_dash = True
        self.dash_disponible = False
        
        # Inclinación épica de cámara al esquivar
        self.pivot_camara.animate_rotation_z(15 if held_keys['a'] else -15, duration=0.1)
        self.pivot_camara.animate_rotation_z(0, duration=0.2, delay=0.1)
        
        from ursina import invoke
        invoke(self.terminar_dash, delay=0.15) # Dura poco
        invoke(self.recuperar_dash, delay=self.dash_cooldown)

    def terminar_dash(self):
        self.haciendo_dash = False

    def recuperar_dash(self):
        self.dash_disponible = True

    def update(self):
        # --- ACTUALIZAR BARRA DE VIDA ---
        self.texto_vida.text = f'{max(0, self.vida)} / 100'
        self.barra_vida_fg.scale_x = max(self.vida / 100.0, 0.0)
        
        # --- CONTROL DE CÁMARA ---
        if held_keys['control']:
            self.pivot_camara.rotation_y = 180
            giro_mouse = 0 
        else:
            self.pivot_camara.rotation_y = 0
            giro_mouse = mouse.velocity[0] * 40

        self.rotation_y += giro_mouse
        self.pivot_camara.rotation_x -= mouse.velocity[1] * 40
        
        # ¡EL TRUCO DE LA CÁMARA! 
        # Limitamos el mínimo a -5 grados. Así la cámara nunca bajará del nivel del piso.
        self.pivot_camara.rotation_x = clamp(self.pivot_camara.rotation_x, -5, 55)
        
        # --- PREVENCIÓN DE CÁMARA ATRAVESANDO PAREDES ---
        # Lanzamos un rayo hacia atrás desde el pivote de la cámara
        direccion_camara = -self.pivot_camara.forward
        hit_camara = raycast(self.pivot_camara.world_position, direccion_camara, distance=12, ignore=(self, self.modelo_visual, self.pivot_camara))
        
        if hit_camara.hit:
            # Si choca con una pared u obstáculo, acercamos la cámara
            camera.z = -(hit_camara.distance - 0.5)
        else:
            # Si no hay pared, mantenemos la distancia original
            camera.z = -12

        # --- CÁLCULO DE DIRECCIÓN ---
        corriendo = held_keys['shift']
        velocidad = self.velocidad_correr if corriendo else self.velocidad_caminar
        
        direccion = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) + 
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()
        
        if self.haciendo_dash:
            velocidad = 150 # Impulso bestial táctico
            direccion = self.dash_direccion # Bloqueamos la dirección durante el dash
            
        desplazamiento = direccion * velocidad * time.dt
        
        # --- ACTUALIZAR RADAR TÁCTICO BIOLÓGICO ---
        import main
        indice_punto = 0
        if hasattr(main, 'gestores_arena'):
            for gestor in main.gestores_arena:
                for enemigo in gestor.enemigos:
                    if enemigo.enabled and enemigo.vida > 0:
                        dir_vector = enemigo.position - self.position
                        dir_xz = Vec3(dir_vector.x, 0, dir_vector.z)
                        distancia = dir_xz.length()
                        
                        # Rango del escáner: 250 metros (abarca más de media arena)
                        if distancia < 250 and indice_punto < len(self.puntos_radar):
                            # MAGIA VECTORIAL: Producto Punto (Dot Product)
                            local_z = dir_xz.dot(self.forward) 
                            local_x = dir_xz.dot(self.right)   
                            
                            punto = self.puntos_radar[indice_punto]
                            punto.enabled = True
                            # Escalar al radar: 250m -> 0.45 unidades locales (0.45 / 250 = 0.0018)
                            punto.x = clamp(local_x * 0.0018, -0.45, 0.45)
                            punto.y = clamp(local_z * 0.0018, -0.45, 0.45)
                            indice_punto += 1
                            
        # Apagar los puntos no usados para no gastar recursos
        for i in range(indice_punto, len(self.puntos_radar)):
            self.puntos_radar[i].enabled = False

        # --- FÍSICAS DE COLISIÓN HORIZONTAL ---
        if desplazamiento.x != 0:
            dir_x = 1 if desplazamiento.x > 0 else -1
            if not raycast(self.position + Vec3(0, 1.5, 0), direction=(dir_x, 0, 0), distance=1.5, ignore=(self,)).hit:
                self.x += desplazamiento.x
                
        if desplazamiento.z != 0:
            dir_z = 1 if desplazamiento.z > 0 else -1
            if not raycast(self.position + Vec3(0, 1.5, 0), direction=(0, 0, dir_z), distance=1.5, ignore=(self,)).hit:
                self.z += desplazamiento.z

        # --- FISICAS DE GRAVEDAD Y SALTO ---
        if held_keys['space'] and self.en_suelo:
            self.velocidad_y = self.velocidad_salto
            self.en_suelo = False
            
        self.velocidad_y -= self.gravedad * time.dt
        hit_info = raycast(self.position + Vec3(0, 1.5, 0), direction=(0, -1, 0), ignore=(self,))
        
        if hit_info.hit and hit_info.distance <= (1.6 - (self.velocidad_y * time.dt)):
            self.y = hit_info.world_point.y
            self.velocidad_y = 0
            self.en_suelo = True
        else:
            self.y += self.velocidad_y * time.dt
            self.en_suelo = False
            
        # --- MOTOR DE NIEVE CONTINUA ---
        import random
        for copo in self.copos_nieve:
            copo.y -= copo.velocidad_caida * time.dt
            copo.x += copo.desvio_viento * time.dt
            
            # Si el copo cae al suelo o se queda muy atrás (más de 120 metros), reaparece en el cielo
            if copo.y < self.y - 5 or abs(copo.x - self.x) > 120 or abs(copo.z - self.z) > 120:
                copo.position = self.position + Vec3(
                    random.uniform(-100, 100), 
                    random.uniform(50, 80), 
                    random.uniform(-100, 100)
                )

        # --- MOTOR DE ANIMACIÓN PROCEDIMENTAL (MATEMÁTICA) ---
        if self.en_suelo:
            if direccion.length() > 0:
                # Si se mueve, calculamos la oscilación según si corre o camina
                frecuencia = 14 if corriendo else 8
                amplitud = 35 if corriendo else 20
                
                t = time.time() * frecuencia
                
                # Hacemos oscilar piernas y brazos de manera alterna (eje Pitch)
                if not self.pierna_izq.isEmpty(): self.pierna_izq.setP(math.sin(t) * amplitud)
                if not self.pierna_der.isEmpty(): self.pierna_der.setP(-math.sin(t) * amplitud)
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-math.sin(t) * amplitud)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(math.sin(t) * amplitud)
                
                # Un ligero cabeceo en el torso para dar realismo al correr
                if not self.torso.isEmpty(): self.torso.setP(math.sin(t * 2) * 2 + (5 if corriendo else 2))
            else:
                # IDLE: Si está quieto, regresamos las extremidades a su pose natural (0)
                if not self.pierna_izq.isEmpty(): self.pierna_izq.setP(0)
                if not self.pierna_der.isEmpty(): self.pierna_der.setP(0)
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(0)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(0)
                if not self.torso.isEmpty(): self.torso.setP(0)
        else:
            # ANIMACIÓN DE SALTO: Si está suspendido en el aire, dobla las piernas hacia atrás
            if not self.pierna_izq.isEmpty(): self.pierna_izq.setP(-20)
            if not self.pierna_der.isEmpty(): self.pierna_der.setP(-20)
            if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(15)
            if not self.brazo_der.isEmpty(): self.brazo_der.setP(15)