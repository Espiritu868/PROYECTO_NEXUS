from ursina import Entity, load_texture, time, Vec3, raycast, distance, scene
import math

class EnemigoBase(Entity):
    def __init__(self, ruta_modelo, ruta_textura, **kwargs):
        super().__init__(**kwargs)
        
        # --- DIBUJADO CRUDO ---
        self.modelo_visual = Entity(
            parent=self,
            model=ruta_modelo, 
            scale=(0.01, 0.01, 0.01),
            rotation_y=180 # Alineado con la rotación del FBX original (igual que el jugador)
        )
        
        # --- EL RAYO LÁSER TEXTURIZADOR (OVERRIDE) ---
        textura_real = load_texture(ruta_textura)
        
        if textura_real:
            # Forzamos la textura para evitar que salgan blancos
            self.modelo_visual.set_texture(textura_real._texture, 1)
        else:
            print(f"❌ Advertencia: No se encontró la textura en {ruta_textura}")
            
        # --- EXTREMIDADES PARA ANIMACIÓN ---
        # Buscamos las piezas del modelo (los villanos usan el mismo FBX que el jugador)
        self.pierna_izq = self.modelo_visual.find('**/leg-left')
        self.pierna_der = self.modelo_visual.find('**/leg-right')
        self.brazo_izq = self.modelo_visual.find('**/arm-left')
        self.brazo_der = self.modelo_visual.find('**/arm-right')
        self.torso = self.modelo_visual.find('**/torso')
            
        # --- COLISIONADOR ---
        self.collider = 'box'
        
        # --- ATRIBUTOS BASE ---
        self.velocidad = 0
        self.vida = 0
        
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

    def buscar_jugador(self):
        # Importación local para evitar importaciones circulares
        from scripts.jugador import Jugador
        for e in scene.entities:
            if isinstance(e, Jugador):
                return e
        return None

    def update(self):
        # Buscar jugador si no lo tenemos aún
        if not self.jugador_objetivo:
            self.jugador_objetivo = self.buscar_jugador()
            if not self.jugador_objetivo:
                return # Si no hay jugador, el enemigo se queda quieto
                
        dist_jugador = distance(self, self.jugador_objetivo)
        
        # --- FÍSICAS DE GRAVEDAD ---
        self.velocidad_y -= self.gravedad * time.dt
        hit_info = raycast(self.position + Vec3(0, 1.5, 0), direction=(0, -1, 0), ignore=(self,))
        
        if hit_info.hit and hit_info.distance <= (1.6 - (self.velocidad_y * time.dt)):
            self.y = hit_info.world_point.y
            self.velocidad_y = 0
            self.en_suelo = True
        else:
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
                # Revisar si hay un obstáculo enfrente para saltar
                obstaculo = raycast(self.position + Vec3(0, 0.5, 0), direction=self.forward, distance=2, ignore=(self, self.jugador_objetivo))
                
                if obstaculo.hit and self.en_suelo:
                    # Saltar obstáculo
                    self.velocidad_y = self.velocidad_salto
                    self.en_suelo = False
                
                # Moverse hacia adelante si no hay pared frente a su cara
                if not obstaculo.hit or obstaculo.distance > 0.5:
                    self.position += self.forward * self.velocidad * time.dt
                    en_movimiento = True
            else:
                # 2. Atacar al jugador
                self.atacar()
                
        # --- ANIMACIONES PROCEDIMENTALES ---
        # Si acaba de atacar, evitamos sobreescribir la pose de ataque un par de frames
        if time.time() - self.ultimo_ataque < 0.2:
            pass # Mantiene la pose de ataque
        elif self.en_suelo:
            if en_movimiento:
                # Animación de caminar
                frecuencia = 10
                amplitud = 25
                t = time.time() * frecuencia
                if not self.pierna_izq.isEmpty(): self.pierna_izq.setP(math.sin(t) * amplitud)
                if not self.pierna_der.isEmpty(): self.pierna_der.setP(-math.sin(t) * amplitud)
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-math.sin(t) * amplitud)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(math.sin(t) * amplitud)
            else:
                # Pose de descanso
                if not self.pierna_izq.isEmpty(): self.pierna_izq.setP(0)
                if not self.pierna_der.isEmpty(): self.pierna_der.setP(0)
                if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(0)
                if not self.brazo_der.isEmpty(): self.brazo_der.setP(0)
        else:
            # Animación de salto
            if not self.pierna_izq.isEmpty(): self.pierna_izq.setP(-20)
            if not self.pierna_der.isEmpty(): self.pierna_der.setP(-20)
            if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(15)
            if not self.brazo_der.isEmpty(): self.brazo_der.setP(15)

    def atacar(self):
        if time.time() - self.ultimo_ataque > self.tiempo_entre_ataques:
            print("¡El enemigo te ataca!")
            # TODO: Reducir vida al jugador
            self.ultimo_ataque = time.time()
            
            # Pose de ataque rápida (levanta los brazos)
            if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-60)
            if not self.brazo_der.isEmpty(): self.brazo_der.setP(-60)