from ursina import Entity, camera, Vec3, held_keys, time, raycast, mouse, clamp, load_texture
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

    def update(self):
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
        
        # --- CÁLCULO DE DIRECCIÓN ---
        corriendo = held_keys['shift']
        velocidad = self.velocidad_correr if corriendo else self.velocidad_caminar
        
        direccion = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) + 
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()
        
        desplazamiento = direccion * velocidad * time.dt
        
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