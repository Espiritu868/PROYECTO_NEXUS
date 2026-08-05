"""
MenÃº de Inicio y Tutorial con Carrusel de ImÃ¡genes.

- MenuInicio: Pantalla principal tÃ¡ctica con tÃ­tulo, subtÃ­tulo, velo oscuro de fondo
  y botones [JUGAR], [TUTORIAL], [SALIR].
- CarruselTutorial: Modal interactivo con carrusel de diapositivas (imagen, tÃ­tulo,
  descripciÃ³n, navegaciÃ³n anterior/siguiente, puntos indicadores y botÃ³n de volver).
"""

from ursina import Entity, Button, Text, color, application, mouse, camera, window, curve, time
import math

COLOR_ACENTO = color.rgba(190/255, 45/255, 45/255, 1)
COLOR_PANEL = color.rgba(4/255, 6/255, 10/255, 235/255)
COLOR_TEXTO_SUAVE = color.rgba(150/255, 155/255, 165/255, 1)
COLOR_BOTON_NEUTRO = color.rgba(40/255, 42/255, 48/255, 1)
COLOR_BOTON_NEUTRO_HOVER = color.rgba(58/255, 61/255, 68/255, 1)
COLOR_BOTON_NEUTRO_PRESS = color.rgba(28/255, 30/255, 35/255, 1)

# Datos de las diapositivas del Tutorial
DIAPOSITIVAS_TUTORIAL = [
    {
        "titulo": "CONTROLES Y MOVIMIENTO",
        "imagen": "textures/tutorial_controls.jpg",
        "descripcion": (
            "â€¢ WASD: Mover al agente | MOUSE: Apuntar y Mirar alrededor\n"
            "â€¢ CLIC IZQ: Disparar arma | CLIC DER: Apuntar con precisiÃ³n\n"
            "â€¢ SHIFT: Esprintar | ESPACIO: Saltar | R: Recargar | E: Interactuar\n"
            "â€¢ 1, 2, 3: Cambiar Armas | TAB: Abrir Tienda de Armas MÃ³vil"
        )
    },
    {
        "titulo": "BEBIDAS Y POTENCIADORES (PERKS)",
        "imagen": "textures/tutorial_perks.jpg",
        "descripcion": (
            "â€¢ Encuentra las mÃ¡quinas expendedoras en la arena para comprar Perks.\n"
            "â€¢ Juggernog: Aumenta la vida mÃ¡xima del jugador.\n"
            "â€¢ Speed Cola: Recarga de municiÃ³n sÃºper rÃ¡pida.\n"
            "â€¢ Stamin-Up: Incrementa la velocidad de movimiento al esprintar."
        )
    },
    {
        "titulo": "ENEMIGOS, JEFES Y RONDAS",
        "imagen": "textures/tutorial_enemies.jpg",
        "descripcion": (
            "â€¢ Sobrevive a hordas infinitas de Zombis, Brujas y Caballeros.\n"
            "â€¢ En la ronda del GOLEM BOSS, prepÃ¡rate para un combate masivo pesadamente blindado.\n"
            "â€¢ Sella las grietas oscuras e interactÃºa con los portales para avanzar de arena."
        )
    }
]


class CarruselTutorial(Entity):
    def __init__(self, parent=camera.ui, **kwargs):
        super().__init__(parent=parent, enabled=False, ignore_paused=True, z=-10, **kwargs)

        self.index_actual = 0

        # Fondo del modal
        self.velo = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 210/255),
            scale=(window.aspect_ratio * 2, 2),
            z=5,
            ignore_paused=True
        )

        # Panel principal del tutorial
        self.panel = Entity(
            parent=self,
            model='quad',
            color=COLOR_PANEL,
            scale=(1.1, 0.85),
            z=4,
            ignore_paused=True
        )

        # Marcos tÃ¡cticos de las esquinas
        hw, hh = 0.55, 0.425
        largo, grosor = 0.06, 0.004
        for sx, sy in [(-1, 1), (1, 1), (-1, -1), (1, -1)]:
            Entity(
                parent=self, model='quad', color=COLOR_ACENTO,
                scale=(largo, grosor),
                x=sx * (hw - largo / 2), y=sy * hh, z=3,
                ignore_paused=True
            )
            Entity(
                parent=self, model='quad', color=COLOR_ACENTO,
                scale=(grosor, largo),
                x=sx * hw, y=sy * (hh - largo / 2), z=3,
                ignore_paused=True
            )

        # TÃ­tulo del Tutorial
        self.titulo_modal = Text(
            parent=self,
            text='GUÃA DE SUPERVIVENCIA - TUTORIAL',
            origin=(0, 0),
            y=0.36,
            scale=1.8,
            color=COLOR_ACENTO,
            ignore_paused=True
        )

        # Contenedor de la Imagen del Carrusel
        # Marco exterior de la imagen
        self.marco_imagen = Entity(
            parent=self,
            model='quad',
            color=COLOR_ACENTO,
            scale=(0.76, 0.43),
            y=0.08,
            z=3,
            ignore_paused=True
        )
        self.imagen_visor = Entity(
            parent=self,
            model='quad',
            texture=DIAPOSITIVAS_TUTORIAL[0]["imagen"],
            scale=(0.75, 0.42),
            y=0.08,
            z=2,
            ignore_paused=True
        )

        # TÃ­tulo de la diapositiva actual
        self.titulo_slide = Text(
            parent=self,
            text=DIAPOSITIVAS_TUTORIAL[0]["titulo"],
            origin=(0, 0),
            y=-0.16,
            scale=1.4,
            color=color.white,
            ignore_paused=True
        )

        # DescripciÃ³n de la diapositiva actual
        self.desc_slide = Text(
            parent=self,
            text=DIAPOSITIVAS_TUTORIAL[0]["descripcion"],
            origin=(0, 0),
            y=-0.25,
            scale=0.9,
            color=COLOR_TEXTO_SUAVE,
            ignore_paused=True
        )

        # Botones de navegaciÃ³n
        self.btn_anterior = Button(
            parent=self,
            text='< ANTERIOR',
            scale=(0.15, 0.06),
            x=-0.45, y=0.08,
            color=COLOR_BOTON_NEUTRO,
            highlight_color=COLOR_BOTON_NEUTRO_HOVER,
            pressed_color=COLOR_BOTON_NEUTRO_PRESS,
            text_color=color.white,
            z=1,
            ignore_paused=True
        )
        self.btn_anterior.on_click = self.anterior_slide

        self.btn_siguiente = Button(
            parent=self,
            text='SIGUIENTE >',
            scale=(0.15, 0.06),
            x=0.45, y=0.08,
            color=COLOR_BOTON_NEUTRO,
            highlight_color=COLOR_BOTON_NEUTRO_HOVER,
            pressed_color=COLOR_BOTON_NEUTRO_PRESS,
            text_color=color.white,
            z=1,
            ignore_paused=True
        )
        self.btn_siguiente.on_click = self.siguiente_slide

        # Indicador de pÃ¡gina
        self.txt_indicador = Text(
            parent=self,
            text='1 / 3',
            origin=(0, 0),
            y=-0.33,
            scale=1.0,
            color=COLOR_TEXTO_SUAVE,
            ignore_paused=True
        )

        # Puntos indicadores circulares
        self.puntos_entidades = []
        num_slides = len(DIAPOSITIVAS_TUTORIAL)
        offset_inicio = -((num_slides - 1) * 0.03) / 2
        for i in range(num_slides):
            pt = Entity(
                parent=self,
                model='circle',
                color=COLOR_ACENTO if i == 0 else COLOR_TEXTO_SUAVE,
                scale=(0.015, 0.015),
                x=offset_inicio + (i * 0.03),
                y=-0.30,
                z=2,
                ignore_paused=True
            )
            self.puntos_entidades.append(pt)

        # BotÃ³n Volver al MenÃº
        self.btn_volver = Button(
            parent=self,
            text='[ X ] VOLVER AL MENÃš',
            scale=(0.28, 0.065),
            y=-0.38,
            color=COLOR_ACENTO,
            highlight_color=color.rgba(220/255, 60/255, 60/255, 1),
            pressed_color=color.rgba(140/255, 30/255, 30/255, 1),
            text_color=color.white,
            z=1,
            ignore_paused=True
        )
        self.btn_volver.on_click = self.ocultar

    def actualizar_diapositiva(self):
        slide = DIAPOSITIVAS_TUTORIAL[self.index_actual]
        self.imagen_visor.texture = slide["imagen"]
        self.titulo_slide.text = slide["titulo"]
        self.desc_slide.text = slide["descripcion"]
        self.txt_indicador.text = f"{self.index_actual + 1} / {len(DIAPOSITIVAS_TUTORIAL)}"

        for i, pt in enumerate(self.puntos_entidades):
            if i == self.index_actual:
                pt.color = COLOR_ACENTO
                pt.scale = (0.02, 0.02)
            else:
                pt.color = COLOR_TEXTO_SUAVE
                pt.scale = (0.012, 0.012)

    def anterior_slide(self):
        self.index_actual = (self.index_actual - 1) % len(DIAPOSITIVAS_TUTORIAL)
        self.actualizar_diapositiva()

    def siguiente_slide(self):
        self.index_actual = (self.index_actual + 1) % len(DIAPOSITIVAS_TUTORIAL)
        self.actualizar_diapositiva()

    def mostrar(self):
        self.index_actual = 0
        self.actualizar_diapositiva()
        self.enabled = True

    def ocultar(self):
        self.enabled = False


class MenuInicio(Entity):
    def __init__(self, parent=camera.ui, **kwargs):
        super().__init__(parent=parent, enabled=False, ignore_paused=True, z=-5, **kwargs)

        self.on_jugar = None

        # Velo oscuro tÃ¡ctico de fondo
        self.velo = Entity(
            parent=self,
            model='quad',
            color=color.rgba(2/255, 3/255, 5/255, 235/255),
            scale=(window.aspect_ratio * 2, 2),
            z=3,
            ignore_paused=True
        )

        # Panel principal
        self.panel = Entity(
            parent=self,
            model='quad',
            color=COLOR_PANEL,
            scale=(0.65, 0.72),
            z=2,
            ignore_paused=True
        )

        # Brackets tÃ¡cticos de esquina
        hw, hh = 0.325, 0.36
        largo, grosor = 0.06, 0.004
        for sx, sy in [(-1, 1), (1, 1), (-1, -1), (1, -1)]:
            Entity(
                parent=self, model='quad', color=COLOR_ACENTO,
                scale=(largo, grosor),
                x=sx * (hw - largo / 2), y=sy * hh, z=1,
                ignore_paused=True
            )
            Entity(
                parent=self, model='quad', color=COLOR_ACENTO,
                scale=(grosor, largo),
                x=sx * hw, y=sy * (hh - largo / 2), z=3,
                ignore_paused=True
            )

        # TÃ­tulo Principal
        self.titulo_sombra = Text(
            parent=self,
            text='PROYECTO NEXO',
            origin=(0, 0),
            y=0.255, x=0.004,
            scale=3.2,
            color=color.black,
            ignore_paused=True
        )
        self.titulo = Text(
            parent=self,
            text='PROYECTO NEXO',
            origin=(0, 0),
            y=0.26,
            scale=3.2,
            color=color.white,
            ignore_paused=True
        )

        self.subtitulo = Text(
            parent=self,
            text='NIVEL 0 - SUPERVIVENCIA EN LA OSCURIDAD',
            origin=(0, 0),
            y=0.19,
            scale=0.95,
            color=COLOR_TEXTO_SUAVE,
            ignore_paused=True
        )

        self.linea_divisoria = Entity(
            parent=self,
            model='quad',
            color=COLOR_ACENTO,
            scale=(0.25, 0.004),
            y=0.14,
            ignore_paused=True
        )

        # BotÃ³n JUGAR
        self.btn_jugar = Button(
            parent=self,
            text='[ > ]  JUGAR',
            y=0.03,
            scale=(0.36, 0.09),
            color=COLOR_ACENTO,
            highlight_color=color.rgba(220/255, 60/255, 60/255, 1),
            pressed_color=color.rgba(140/255, 30/255, 30/255, 1),
            text_color=color.white,
            ignore_paused=True
        )
        self.btn_jugar.on_click = self.iniciar_juego

        # BotÃ³n TUTORIAL
        self.btn_tutorial = Button(
            parent=self,
            text='[ ? ]  TUTORIAL / GUIA',
            y=-0.09,
            scale=(0.36, 0.09),
            color=COLOR_BOTON_NEUTRO,
            highlight_color=COLOR_BOTON_NEUTRO_HOVER,
            pressed_color=COLOR_BOTON_NEUTRO_PRESS,
            text_color=color.white,
            ignore_paused=True
        )
        self.btn_tutorial.on_click = self.abrir_tutorial

        # BotÃ³n SALIR
        self.btn_salir = Button(
            parent=self,
            text='[ X ]  SALIR DEL JUEGO',
            y=-0.21,
            scale=(0.36, 0.09),
            color=color.rgba(110/255, 28/255, 28/255, 1),
            highlight_color=color.rgba(145/255, 40/255, 40/255, 1),
            pressed_color=color.rgba(80/255, 18/255, 18/255, 1),
            text_color=color.white,
            ignore_paused=True
        )
        self.btn_salir.on_click = application.quit

        # Sub-modal de tutorial
        self.carrusel_tutorial = CarruselTutorial(parent=self)

    def update(self):
        if self.enabled:
            # PulsaciÃ³n sutil en el tÃ­tulo
            escala = 3.2 + math.sin(time.time() * 2.5) * 0.04
            self.titulo.scale = escala
            self.titulo_sombra.scale = escala

    def mostrar(self):
        self.enabled = True
        application.paused = True
        mouse.locked = False
        mouse.visible = True

    def ocultar(self):
        self.enabled = False

    def iniciar_juego(self):
        self.ocultar()
        application.paused = False
        mouse.locked = True
        mouse.visible = False
        if self.on_jugar:
            self.on_jugar()

    def abrir_tutorial(self):
        self.carrusel_tutorial.mostrar()
