from ursina import Entity, load_texture, time, Vec3, raycast, distance, scene, curve
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
        if ruta_textura:
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

    def buscar_jugador(self):
        # Importación local para evitar importaciones circulares
        from scripts.jugador import Jugador
        for e in scene.entities:
            if isinstance(e, Jugador):
                return e
        return None

    def update(self):
        if self.curando and not self.curado:
            # Mientras está flotando, no hace nada
            return
        elif self.curado:
            # Ya es un ciudadano sano, solo respira suavemente
            t = time.time() * 2
            if not self.brazo_izq.isEmpty():
                self.brazo_izq.setP(math.sin(t) * 5)
                self.brazo_der.setP(-math.sin(t) * 5)
                self.pierna_izq.setP(0)
                self.pierna_der.setP(0)
                self.torso.setP(0)
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

    def recibir_dano(self, cantidad):
        if self.curando:
            return
            
        if self.vida_maxima is None:
            self.vida_maxima = max(1, self.vida) # Captura la vida máxima inicial
            
        self.vida -= cantidad
        
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
        if tex:
            self.modelo_visual.set_texture(tex._texture, 1)
        
        # Volver al piso
        self.animate_y(self.y - 3, duration=0.5)
        
        # Devolver el color a normal
        self.modelo_visual.color = color.white
        
        self.curado = True

    def curar(self):
        self.curando = True
        
        # Detenemos al enemigo
        self.velocidad = 0
        self.jugador_objetivo = None 
        
        # Ocultamos la barra de vida al morir
        from ursina import destroy, color
        destroy(self.barra_vida_fondo)
        
        # Animación de curación celestial
        self.animate_rotation_y(self.rotation_y + 1080, duration=1.5)
        self.animate_y(self.y + 3, duration=1.5)
        self.modelo_visual.animate_color(color.yellow, duration=1.5)
        
        from ursina import Sequence, Func, Wait
        Sequence(
            Wait(1.5),
            Func(self.cambiar_textura_y_bajar)
        ).start()

    def atacar(self):
        if time.time() - self.ultimo_ataque > self.tiempo_entre_ataques:
            # Dañar al jugador
            if self.jugador_objetivo:
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
            if not self.brazo_izq.isEmpty(): self.brazo_izq.setP(-60)
            if not self.brazo_der.isEmpty(): self.brazo_der.setP(-60)