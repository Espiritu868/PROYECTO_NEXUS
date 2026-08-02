from ursina import Entity, distance, destroy, Text, color, held_keys, time, texture

class PiezaPortal(Entity):
    def __init__(self, nombre_pieza="Pieza", modelo_path="assets/modelos/carcasa.glb", 
                 textura_path=None, position=(0,0,0), gestor=None, **kwargs):
        super().__init__(
            model=modelo_path,
            color=color.white,
            position=position,
            scale=0.1,
            collider='box',
            **kwargs
        )
        self.nombre = nombre_pieza
        self.gestor = gestor
        self.texto_info = None
        
        #  Cargar textura si se proporciona
        if textura_path:
            try:
                self.texture = texture.load(textura_path)
            except:
                print(f"No se pudo cargar textura: {textura_path}")

    def update(self):
        # Rotación continua en 3D
        self.rotation_y += 50 * time.dt

        from scripts.jugador import Jugador
        from ursina import scene
        
        jugador = Jugador.instancia
        
        if jugador:
            if distance(self.position, jugador.position) < 3:
                self.mostrar_texto(f"Presiona [E] para recoger: {self.nombre}")
                
                if held_keys['e']:
                    if self.gestor:
                        self.gestor.recolectar_pieza(self.nombre)
                    if self.texto_info:
                        destroy(self.texto_info)
                    destroy(self)
            else:
                if self.texto_info:
                    destroy(self.texto_info)
                    self.texto_info = None

    def mostrar_texto(self, msj):
        if not self.texto_info:
            self.texto_info = Text(text=msj, position=(-0.3, -0.25), scale=1.2, color=color.cyan)
        else:
            self.texto_info.text = msj