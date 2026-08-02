from ursina import *
import time

class MaquinaBebida(Entity):
    def __init__(self, tipo, modelo_path, precio, color_luz, position=(0,0,0), rotation=(0,0,0)):
        super().__init__(
            model=modelo_path,
            position=position,
            rotation=rotation,
            scale=1.5,
            collider='box'
        )
        self.tipo = tipo
        self.precio = precio
        self.comprada = False
        
        # Luz decorativa para la máquina
        PointLight(parent=self, color=color_luz, y=1.5, z=-1.0, attenuation=(0.5, 0, 0.05))
        
        # Texto UI (flotante)
        self.texto_info = Text(
            parent=camera.ui,
            text="",
            position=(0, -0.3),
            origin=(0, 0),
            scale=1.2,
            color=color_luz,
            enabled=False
        )
        
    def update(self):
        from scripts.jugador import Jugador
        jugador = getattr(Jugador, 'instancia', None)
        if not jugador or jugador.esta_muerto:
            self.texto_info.enabled = False
            return
            
        dist = distance(self.world_position, jugador.world_position)
        
        if dist < 4 and not self.comprada:
            if not self.texto_info.enabled:
                self.texto_info.enabled = True
                self.texto_info.color = color.white
            self.texto_info.text = f"Presiona [E] para comprar bebida {self.tipo.upper()} (Costo: {self.precio})"
        elif self.texto_info.enabled and not self.comprada:
            self.texto_info.enabled = False

    def input(self, key):
        if key == 'e' and not self.comprada:
            from scripts.jugador import Jugador
            jugador = getattr(Jugador, 'instancia', None)
            if not jugador or jugador.esta_muerto: return
            
            dist = distance(self.world_position, jugador.world_position)
            if dist < 4:
                if jugador.monedas >= self.precio:
                    if self.tipo not in jugador.perks_comprados:
                        jugador.ganar_monedas(-self.precio)
                        jugador.comprar_bebida(self.tipo)
                        self.comprada = True
                        
                        # Mensaje temporal
                        self.texto_info.enabled = True
                        self.texto_info.text = "¡Bebida adquirida!"
                        self.texto_info.color = color.gray
                        invoke(self.ocultar_texto, delay=2.5)
                else:
                    self.texto_info.enabled = True
                    self.texto_info.text = "¡No tienes suficientes monedas!"
                    self.texto_info.color = color.red
                    invoke(self.ocultar_texto, delay=1.5)
                    
    def ocultar_texto(self):
        if self.comprada or self.texto_info.text.startswith("¡No tienes"):
            self.texto_info.enabled = False
