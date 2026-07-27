from ursina import Entity, Text, color, held_keys, destroy, time, distance, scene, invoke, Audio
import math
import random


class Grieta(Entity):
    """
    Anomalía dimensional que el jugador debe sellar manteniendo [E]
    presionado durante 3 segundos. Se cancela si el jugador se mueve
    o recibe daño durante el proceso.
    """
    TIEMPO_SELLADO = 3.0          # segundos que hay que mantener [E]
    DISTANCIA_INTERACCION = 3.5   # qué tan cerca hay que estar
    UMBRAL_MOVIMIENTO = 0.15      # cuánto se puede mover el jugador sin cancelar

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
        jugador = next((e for e in scene.entities if isinstance(e, Jugador)), None)
        if not jugador:
            return

        dist = distance(self.position, jugador.position)

        if dist < self.DISTANCIA_INTERACCION:
            if held_keys['e']:
                if not self.sellando:
                    # Empieza el sellado: guardamos posición y vida actuales
                    self.sellando = True
                    self.progreso = 0.0
                    self._pos_inicio = jugador.position
                    
                    
                    self._vida_inicio = getattr(jugador, 'vida', None)

                # ¿Se movió demasiado? -> cancelar
                if distance(jugador.position, self._pos_inicio) > self.UMBRAL_MOVIMIENTO:
                    self._cancelar("¡Te moviste! Vuelve a intentarlo")
                    return

                # ¿Le pegaron? -> cancelar
                vida_actual = getattr(jugador, 'vida', None)
                if (self._vida_inicio is not None and vida_actual is not None
                        and vida_actual < self._vida_inicio):
                    self._cancelar("¡Te golpearon! Vuelve a intentarlo")
                    return

                # Avanza el progreso
                self.progreso += time.dt
                porcentaje = min(int((self.progreso / self.TIEMPO_SELLADO) * 100), 100)
                self._mostrar_texto(f"Sellando grieta... {porcentaje}%")

                if self.progreso >= self.TIEMPO_SELLADO:
                    self._completar()
            else:
                if self.sellando:
                    self._cancelar(None)
                self._mostrar_texto("Presiona [E] para sellar la grieta")
        else:
            if self.sellando:
                self._cancelar(None)
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
        self._vida_inicio = None
        if mensaje:
            self._mostrar_texto(mensaje)

    def _completar(self):
        self.sellada = True
        self.sellando = False
        self._mostrar_texto("¡Grieta sellada!")

        if self.sonido:
            self.sonido.stop()

        if self.gestor:
            self.gestor.sellar_grieta()

        invoke(self._ocultar_texto, delay=1.2)
        invoke(destroy, self, delay=1.2)



