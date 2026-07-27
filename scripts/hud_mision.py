from ursina import Entity, Text, color, camera, destroy, Mesh


def crear_octagono(ancho, alto, corte=0.03):
    """
    Crea una malla con forma de rectángulo con las 4 esquinas cortadas.
    IMPORTANTE: el punto (0,0) de esta malla es el CENTRO DEL BORDE
    SUPERIOR (no el centro del panel). Así, la 'position' que le des
    a la Entity será exactamente donde quieres que quede la parte
    de arriba del panel, sin depender de 'origin' (que no se estaba
    calculando bien con esta malla personalizada).
    """
    hw = ancho / 2
    c = min(corte, hw, alto / 2)
    y_top, y_bottom = 0, -alto  # el borde superior vive en y=0

    perimetro = [
        (-hw + c, y_top, 0),    (hw - c, y_top, 0),
        (hw, y_top - c, 0),     (hw, y_bottom + c, 0),
        (hw - c, y_bottom, 0),  (-hw + c, y_bottom, 0),
        (-hw, y_bottom + c, 0), (-hw, y_top - c, 0),
    ]
    centro_y = (y_top + y_bottom) / 2
    vertices = [(0, centro_y, 0)] + perimetro
    n = len(perimetro)
    triangles = []
    for i in range(n):
        triangles.append((0, i + 1, ((i + 1) % n) + 1))

    return Mesh(vertices=vertices, triangles=triangles, mode='triangle')


class HUDMisionPanel:
    """
    Panel táctico estilo sci-fi con esquinas cortadas, borde con glow
    y una 'píldora' superior tipo insignia. Administra varias entidades
    sueltas (no hereda de Entity).
    """
    def __init__(self, **kwargs):

        # ============ CAPA 1: Glow exterior (más grande, semi-transparente) ============
        self.panel_glow = Entity(
            parent=camera.ui,
            model=crear_octagono(0.42, 0.13, corte=0.03),
            color=color.rgba32(0, 200, 255, 70),
            position=(0, 0.46),
            z=1,
            double_sided=True,
        )

        # ============ CAPA 2: Panel principal (oscuro, un poco más chico, encima) ============
        self.panel_bg = Entity(
            parent=camera.ui,
            model=crear_octagono(0.40, 0.115, corte=0.026),
            color=color.rgba32(16, 22, 32, 235),
            position=(0, 0.452),
            z=0,
            double_sided=True,
        )

        # ============ Línea de borde fina (da el contorno cyan nítido) ============
        self.borde = Entity(
            parent=camera.ui,
            model=crear_octagono(0.402, 0.117, corte=0.027),
            color=color.rgba32(0, 220, 255, 160),
            position=(0, 0.4525),
            z=0.5,
            double_sided=True,
        )

        # ============ Píldora superior (badge "Misión táctica") ============
        self.badge_bg = Entity(
            parent=camera.ui,
            model=crear_octagono(0.19, 0.045, corte=0.018),
            color=color.rgba32(16, 22, 32, 255),
            position=(0, 0.462),
            z=-0.5,
            double_sided=True,
        )
        self.badge_borde = Entity(
            parent=camera.ui,
            model=crear_octagono(0.192, 0.047, corte=0.019),
            color=color.rgba32(0, 220, 255, 200),
            position=(0, 0.4625),
            z=-0.4,
            double_sided=True,
        )

        # Puntito cyan antes del texto de la insignia
        self.badge_punto = Entity(
            parent=camera.ui,
            model='circle',
            color=color.cyan,
            position=(-0.042, 0.4375),
            scale=0.005,
            z=-0.6,
        )

        self.badge_texto = Text(
            parent=camera.ui,
            text="Misión táctica",
            position=(-0.028, 0.438),
            origin=(-0.3, 0),
            scale=0.65,
            color=color.cyan,
            z=-0.6,
        )

        # ============ Texto de la misión (contenido principal) ============
        self.texto_mision = Text(
            parent=camera.ui,
            text="",
            position=(0, 0.395),
            origin=(0, 0),
            scale=0.75,
            color=color.white,
            z=-0.6,
        )

        # ============ Contador (0/5) ============
        self.texto_conteo = Text(
            parent=camera.ui,
            text="",
            position=(0, 0.362),
            origin=(0, 0),
            scale=0.65,
            color=color.yellow,
            z=-0.6,
        )

        self._entidades = [
            self.panel_glow, self.panel_bg, self.borde,
            self.badge_bg, self.badge_borde, self.badge_punto,
            self.badge_texto, self.texto_mision, self.texto_conteo,
        ]

    def actualizar_mision(self, texto, actual=None, total=None):
        self.texto_mision.text = texto
        if actual is not None and total is not None:
            self.texto_conteo.text = f"[{actual}/{total}]"
        else:
            self.texto_conteo.text = ""

    def mision_completada(self, mensaje):
        for e in (self.panel_glow, self.borde, self.badge_borde):
            e.color = color.rgba32(80, 255, 120, 200) if e is not self.panel_glow else color.rgba32(80, 255, 120, 90)
        self.badge_punto.color = color.lime
        self.badge_texto.color = color.lime
        self.texto_mision.color = color.lime
        self.texto_mision.text = mensaje
        self.texto_conteo.text = ""

    def enabled_setter(self, valor):
        for e in self._entidades:
            e.enabled = valor

    enabled = property(lambda self: self.panel_bg.enabled, enabled_setter)

    def destruir(self):
        for e in self._entidades:
            destroy(e)