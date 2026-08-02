from ursina import Entity, Text, color, held_keys, destroy, time, distance, scene, invoke, Audio
import math
import random


class Grieta(Entity):
    """
    Anomalía dimensional que el jugador debe sellar manteniendo [E]
    presionado durante 3 segundos. Se cancela si el jugador se mueve
    o recibe daño durante el proceso.
    """
    TIEMPO_SELLADO = 15.0          # segundos que hay que sobrevivir dentro
    DISTANCIA_INTERACCION = 12.0   # radio de la zona de cuarentena

    def __init__(self, position=(0, 0, 0), gestor=None, **kwargs):
        super().__init__(
            model='sphere',
            color=color.rgba32(180, 30, 220, 255),   #  SIN transparencia (evita bugs de render)
            position=position,
            scale=1.8,                                #  
            collider='sphere',
            unlit=True,
            **kwargs
        )
        self.gestor = gestor
        self.sellada = False
        self.sellando = False
        self.progreso = 0.0
        self._pos_inicio = None
        self._vida_inicio = None
        self.texto_prompt = None

        #  Aro de brillo exterior (también opaco, sin alpha)
        self.glow = Entity(
            parent=self,
            model='sphere',
            color=color.rgba32(200, 100, 255, 255),
            scale=1.3,
            unlit=True,
        )

        # Círculo en el piso que delimita la zona
        self.zona_visual = Entity(
            parent=self,
            model='circle',
            color=color.rgba(255, 50, 50, 100), # Rojo semitransparente
            scale=self.DISTANCIA_INTERACCION * 2, # Diámetro
            rotation_x=90,
            y=-0.9, # Pegado al suelo
            unlit=True,
            double_sided=True
        )

        # "Partículas" simples: esferitas chicas orbitando la grieta
        self.particulas = []
        for _ in range(6):
            p = Entity(
                parent=self,
                model='sphere',
                color=color.rgba32(200, 100, 255, 220),
                scale=0.12,
                unlit=True,
            )
            self.particulas.append({
                "entity": p,
                "angulo": random.uniform(0, 360),
                "radio": random.uniform(0.9, 1.4),
                "velocidad": random.uniform(40, 90),
                "altura": random.uniform(-0.3, 0.3),
            })

        #  Sonido de energía en loop mientras esté abierta.
        #   por ahora (sin archivo de audio asignado).
        #    Cuando este el sonido, descomenta la línea de abajo
        #    y pon la ruta correcta:
        # self.sonido = Audio('assets/sonidos/grieta_energia', loop=True, autoplay=True, volume=0.4)
        self.sonido = None

    def update(self):
        if self.sellada:
            return

        self._animar_particulas()

        from scripts.jugador import Jugador
        jugador = Jugador.instancia
        if not jugador:
            return

        dist = distance(self.position, jugador.position)

        if dist < self.DISTANCIA_INTERACCION:
            self.zona_visual.color = color.rgba(50, 255, 50, 100) # Se pone verde si estás dentro
            self.progreso += time.dt
            porcentaje = min(int((self.progreso / self.TIEMPO_SELLADO) * 100), 100)
            self._mostrar_texto(f"Asegurando Zona... {porcentaje}%\n<white>¡No salgas del círculo!")

            if self.progreso >= self.TIEMPO_SELLADO:
                self._completar()
        else:
            self.zona_visual.color = color.rgba(255, 50, 50, 100) # Rojo
            if self.progreso > 0:
                self.progreso = max(0.0, self.progreso - (time.dt * 2)) # Pierdes progreso el doble de rápido si sales
                porcentaje = min(int((self.progreso / self.TIEMPO_SELLADO) * 100), 100)
                self._mostrar_texto(f"<red>¡Vuelve al círculo! Perdiendo progreso: {porcentaje}%")
            else:
                self._ocultar_texto()

    def _animar_particulas(self):
        for p in self.particulas:
            p["angulo"] += p["velocidad"] * time.dt
            rad = p["radio"]
            x = math.cos(math.radians(p["angulo"])) * rad
            z = math.sin(math.radians(p["angulo"])) * rad
            p["entity"].position = (x, p["altura"], z)

        # Pulso de brillo tipo "respirando"
        self.glow.scale = 1.4 + math.sin(time.time() * 3) * 0.15

    def _mostrar_texto(self, msj):
        if not self.texto_prompt:
            self.texto_prompt = Text(text=msj, position=(-0.35, -0.25), scale=1.3, color=color.magenta)
        else:
            self.texto_prompt.text = msj

    def _ocultar_texto(self):
        if self.texto_prompt:
            destroy(self.texto_prompt)
            self.texto_prompt = None

    def _cancelar(self, mensaje):
        self.sellando = False
        self.progreso = 0.0
        self._pos_inicio = None
        self.progreso = 0.0
        if mensaje:
            self._mostrar_texto(mensaje)

    def _completar(self):
        self.sellada = True
        self.zona_visual.enabled = False
        self._mostrar_texto("<green>¡Sector Asegurado!")
        invoke(self._ocultar_texto, delay=3)

        if self.sonido:
            self.sonido.stop()

        if self.gestor:
            self.gestor.sellar_grieta()
            
        invoke(destroy, self, delay=3.5)
