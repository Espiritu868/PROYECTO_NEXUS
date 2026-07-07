from ursina import Entity, curve

class Puerta(Entity):
    def __init__(self, position, rotation_y=0, **kwargs):
        super().__init__(
            model='assets/texturas/factory/door-wide-closed.obj',
            texture='assets/texturas/factory/Textures/colormap.png',
            position=position,
            rotation_y=rotation_y,
            scale=(10, 10, 1.5), # Z más delgado para que no sobresalga del muro
            double_sided=True, # Hace que la puerta sea visible desde atrás
            **kwargs
        )
        
        # El muro invisible que impide cruzar mientras esté cerrada
        self.bloqueo = Entity(
            parent=self,
            collider='box',
            scale=(2.2, 2, 0.5), # Más ancho, más alto y más grueso para evitar glitches
            position=(0, 1, 0),
            visible=False
        )
        self.abierta = False

    def abrir(self):
        if not self.abierta:
            self.abierta = True
            self.bloqueo.collider = None # Desactiva el choque
            
            # Animación cinemática: la puerta se levanta hacia el techo
            self.animate_y(self.y + 15, duration=2, curve=curve.in_out_quad)
            
    def cerrar(self):
        if self.abierta:
            self.abierta = False
            self.bloqueo.collider = 'box' # Reactiva el choque
            
            # La puerta vuelve a bajar al suelo
            self.animate_y(self.y - 15, duration=0.5, curve=curve.linear)
