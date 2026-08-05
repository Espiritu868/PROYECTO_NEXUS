"""
Menú de pausa.

Aprovecha el sistema nativo de Ursina: cuando application.paused = True,
el motor deja de llamar update() en TODAS las entidades excepto las que
tengan ignore_paused=True. Como Jugador, cada enemigo (EnemigoBase y
sus hijos) y GestorArena son subclases de Entity, se congelan solos —
no hace falta tocar esos archivos para nada.

DETECCIÓN DE ESC: se revisa dentro de update() con held_keys (no con un
método input() personalizado — eso rompió el despacho global de teclado
de Ursina en pruebas anteriores). Esta entidad raíz (self) siempre está
enabled=True e ignore_paused=True, así que su update() corre SIEMPRE,
sin importar si el menú está visible o el juego está pausado. Lo visual
vive en self.contenido, un hijo separado que sí se activa/desactiva.
"""

from ursina import Entity, Button, Text, color, application, mouse, camera, window, curve, held_keys
import sys
import os
import subprocess

# Un solo color de acento (rojo, coherente con la barra de vida y el
# tono "peligro/tensión" del juego) en vez de mezclar azul + rojo.
# IMPORTANTE: color.rgba() en esta versión de Ursina NO convierte
# automáticamente de 0-255 a 0-1 — si le pasas valores >1, la GPU los
# recorta directo a 1.0 (blanco puro). Por eso todo va dividido entre 255.
COLOR_ACENTO = color.rgba(190/255, 45/255, 45/255, 1)
COLOR_PANEL = color.rgba(4/255, 6/255, 10/255, 230/255)      # Oscuro premium casi opaco
COLOR_TEXTO_SUAVE = color.rgba(150/255, 155/255, 165/255, 1)
COLOR_BOTON_NEUTRO = color.rgba(40/255, 42/255, 48/255, 1)
COLOR_BOTON_NEUTRO_HOVER = color.rgba(58/255, 61/255, 68/255, 1)
COLOR_BOTON_NEUTRO_PRESS = color.rgba(28/255, 30/255, 35/255, 1)


class MenuPausa(Entity):
    def __init__(self, **kwargs):
        # Esta entidad raíz SIEMPRE está enabled=True: es la "oreja" que
        # escucha ESC en todo momento. Nunca se desactiva.
        super().__init__(parent=camera.ui, enabled=True, ignore_paused=True, **kwargs)

        # Todo lo visual vive aquí adentro. self.contenido.enabled es lo
        # que se prende/apaga para mostrar u ocultar el menú — self (el
        # padre) se queda siempre activo para poder seguir escuchando ESC.
        self.contenido = Entity(parent=self, enabled=False, ignore_paused=True)

        # --- Velo oscuro cubriendo TODA la pantalla ---
        self.velo = Entity(
            parent=self.contenido,
            model='quad',
            color=color.rgba(0, 0, 0, 175/255),
            scale=(window.aspect_ratio * 2, 2),
            z=3,
            ignore_paused=True
        )

        # --- Panel de fondo, casi invisible: solo un tinte, no una caja ---
        self.panel = Entity(
            parent=self.contenido,
            model='quad',
            color=COLOR_PANEL,
            scale=(0.58, 0.56),
            z=2,
            ignore_paused=True
        )

        # --- ESQUINAS ESTILO HUD TÁCTICO (brackets en L) ---
        hw, hh = 0.29, 0.28
        largo, grosor = 0.05, 0.0035
        for sx, sy in [(-1, 1), (1, 1), (-1, -1), (1, -1)]:
            Entity(
                parent=self.contenido, model='quad', color=COLOR_ACENTO,
                scale=(largo, grosor),
                x=sx * (hw - largo / 2), y=sy * hh, z=1,
                ignore_paused=True
            )
            Entity(
                parent=self.contenido, model='quad', color=COLOR_ACENTO,
                scale=(grosor, largo),
                x=sx * hw, y=sy * (hh - largo / 2), z=1,
                ignore_paused=True
            )

        # --- TÍTULO ---
        self.titulo_sombra = Text(
            parent=self.contenido,
            text='P A U S A',
            origin=(0, 0),
            y=0.215, x=0.005,
            scale=3,
            color=color.black,
            ignore_paused=True
        )
        self.titulo = Text(
            parent=self.contenido,
            text='P A U S A',
            origin=(0, 0),
            y=0.22,
            scale=3,
            color=color.white,
            ignore_paused=True
        )

        self.subtitulo = Text(
            parent=self.contenido,
            text='el combate está en espera',
            origin=(0, 0),
            y=0.155,
            scale=1,
            color=COLOR_TEXTO_SUAVE,
            ignore_paused=True
        )

        self.linea_divisoria = Entity(
            parent=self.contenido,
            model='quad',
            color=COLOR_ACENTO,
            scale=(0.16, 0.0035),
            y=0.1,
            ignore_paused=True
        )

        self.boton_reanudar = Button(
            parent=self.contenido,
            text='Reanudar',
            y=0.0,
            scale=(0.32, 0.085),
            color=COLOR_BOTON_NEUTRO,
            highlight_color=COLOR_BOTON_NEUTRO_HOVER,
            pressed_color=COLOR_BOTON_NEUTRO_PRESS,
            text_color=color.white,
            ignore_paused=True
        )
        self.boton_reanudar.on_click = self.reanudar

        self.boton_reiniciar = Button(
            parent=self.contenido,
            text='Reiniciar Nivel',
            y=-0.11,
            scale=(0.32, 0.085),
            color=COLOR_BOTON_NEUTRO,
            highlight_color=COLOR_BOTON_NEUTRO_HOVER,
            pressed_color=COLOR_BOTON_NEUTRO_PRESS,
            text_color=color.white,
            ignore_paused=True
        )
        self.boton_reiniciar.on_click = self.reiniciar

        self.boton_salir = Button(
            parent=self.contenido,
            text='Volver al Menú Principal',
            y=-0.22,
            scale=(0.32, 0.085),
            color=color.rgba(110/255, 28/255, 28/255, 1),
            highlight_color=color.rgba(145/255, 40/255, 40/255, 1),
            pressed_color=color.rgba(80/255, 18/255, 18/255, 1),
            text_color=color.white,
            ignore_paused=True
        )
        self.boton_salir.on_click = self.volver_menu

        self.pie = Text(
            parent=self.contenido,
            text='ESC para reanudar',
            origin=(0, 0),
            y=-0.33,
            scale=0.75,
            color=COLOR_TEXTO_SUAVE,
            ignore_paused=True
        )

        # Se asigna desde main.py una vez que el jugador existe (el menú
        # se crea antes que el jugador, así que arranca en None).
        self.jugador = None

        # Para detectar "se acaba de presionar" y no reabrir/recerrar en
        # bucle mientras la tecla sigue físicamente presionada.
        self._esc_anterior = False

    def update(self):
        # Esta entidad tiene ignore_paused=True y enabled=True siempre,
        # así que este update() corre en TODOS los estados del juego:
        # jugando, pausado, con el menú abierto o cerrado.
        esc_actual = held_keys['escape']
        if esc_actual and not self._esc_anterior:
            self.alternar()
        self._esc_anterior = esc_actual
        
        if self.contenido.enabled:
            import math
            from ursina import time
            escala = 3.0 + math.sin(time.time() * 3) * 0.05
            self.titulo.scale = escala
            self.titulo_sombra.scale = escala

    def alternar(self):
        """Muestra u oculta el menú según su estado actual."""
        if self.contenido.enabled:
            self.reanudar()
        else:
            self.mostrar()

    def mostrar(self):
        self.contenido.enabled = True
        application.paused = True
        mouse.locked = False
        mouse.visible = True

        # Pequeña animación de entrada
        self.panel.scale = (0.52, 0.5)
        self.panel.animate_scale((0.58, 0.56), duration=0.15, curve=curve.out_expo)

        if self.jugador:
            self.jugador.mira.enabled = False
            self.jugador.barra_vida_bg.enabled = False
            self.jugador.texto_vida.enabled = False
            if hasattr(self.jugador, 'texto_monedas'):
                self.jugador.texto_monedas.enabled = False

    def reanudar(self):
        self.contenido.enabled = False
        application.paused = False
        mouse.locked = True
        mouse.visible = False
        if self.jugador:
            self.jugador.mira.enabled = True
            self.jugador.barra_vida_bg.enabled = True
            self.jugador.texto_vida.enabled = True
            if hasattr(self.jugador, 'texto_monedas'):
                self.jugador.texto_monedas.enabled = True

    def volver_menu(self):
        if hasattr(self, 'on_volver_menu') and self.on_volver_menu:
            self.on_volver_menu()
        
    def reiniciar(self):
        if hasattr(self, 'on_reiniciar') and self.on_reiniciar:
            self.on_reiniciar()

class PantallaMuerte(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True, **kwargs)

        # Fondo completamente negro semi-transparente
        self.velo = Entity(
            parent=self,
            model='quad',
            color=color.rgba(15/255, 0, 0, 230/255),  # Un tono muy oscuro rojizo
            scale=(window.aspect_ratio * 2, 2),
            z=3,
            ignore_paused=True
        )

        self.titulo_sombra = Text(
            parent=self,
            text='HAS MUERTO',
            origin=(0, 0),
            y=0.14, x=0.01,
            scale=5,
            color=color.black,
            ignore_paused=True
        )
        self.titulo = Text(
            parent=self,
            text='HAS MUERTO',
            origin=(0, 0),
            y=0.15,
            scale=5,
            color=color.red,
            ignore_paused=True
        )

        self.boton_reintentar = Button(
            parent=self,
            text='Volver a intentar',
            y=-0.1,
            scale=(0.4, 0.1),
            color=COLOR_BOTON_NEUTRO,
            highlight_color=COLOR_BOTON_NEUTRO_HOVER,
            pressed_color=COLOR_BOTON_NEUTRO_PRESS,
            text_color=color.white,
            ignore_paused=True
        )
        self.boton_reintentar.on_click = self.reiniciar

        self.boton_salir = Button(
            parent=self,
            text='Volver al Menú Principal',
            y=-0.22,
            scale=(0.4, 0.1),
            color=color.rgba(110/255, 28/255, 28/255, 1),
            highlight_color=color.rgba(145/255, 40/255, 40/255, 1),
            pressed_color=color.rgba(80/255, 18/255, 18/255, 1),
            text_color=color.white,
            ignore_paused=True
        )
        self.boton_salir.on_click = self.volver_menu
        
        self.jugador = None

    def update(self):
        if self.enabled:
            import math
            from ursina import time
            # Animación latido más fuerte para HAS MUERTO
            escala = 5.0 + math.sin(time.time() * 4) * 0.2
            self.titulo.scale = escala
            self.titulo_sombra.scale = escala

    def mostrar(self):
        self.enabled = True
        application.paused = True
        mouse.locked = False
        mouse.visible = True
        
        # Efecto de zoom out dramático
        self.titulo.scale = 8
        self.titulo_sombra.scale = 8

        if self.jugador:
            self.jugador.mira.enabled = False
            self.jugador.barra_vida_bg.enabled = False
            self.jugador.texto_vida.enabled = False
            if hasattr(self.jugador, 'texto_monedas'):
                self.jugador.texto_monedas.enabled = False

    def reiniciar(self):
        if hasattr(self, 'on_reiniciar') and self.on_reiniciar:
            self.on_reiniciar()
            
    def volver_menu(self):
        if hasattr(self, 'on_volver_menu') and self.on_volver_menu:
            self.on_volver_menu()