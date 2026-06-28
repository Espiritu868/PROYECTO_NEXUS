from ursina import *
import random

class ServidorRoto(Entity):
    def __init__(self, position=(0,0,0)):
        esta_caido = random.random() > 0.7
        rot_z = random.uniform(-10, 10) if not esta_caido else 90
        rot_y = random.choice([0, 90, 180, 270])
        
        super().__init__(
            model='cube',
            position=position,
            scale=(1.8, 3.5, 1.8),
            color=color.hex('#222222'),
            rotation=(0, rot_y, rot_z),
            collider='box'
        )

        # ignore=True ahorra una cantidad masiva de cálculos
        self.panel = Entity(
            parent=self,
            model='cube',
            scale=(0.85, 0.9, 0.05),
            z=-0.51,
            color=color.black,
            ignore=True 
        )

        self.luces_activas = []
        for i in range(random.randint(1, 4)): # Reducimos ligeramente el máximo de luces
            color_luz = random.choice([color.red, color.hex('#444444'), color.orange])
            luz = Entity(
                parent=self.panel,
                model='cube',
                color=color_luz,
                scale=(0.15, 0.05, 1),
                x=-0.25,
                y=0.4 - (i * 0.15),
                ignore=True 
            )
            
            # Solo guardamos en memoria las luces que pueden parpadear
            if color_luz != color.hex('#444444'):
                self.luces_activas.append(luz)

        # Iniciamos el ciclo optimizado
        if self.luces_activas:
            self.parpadear()

    def parpadear(self):
        for luz in self.luces_activas:
            if random.random() > 0.6:
                luz.enabled = not luz.enabled
        
        # En lugar de un update() por frame, esto llama a la función de nuevo
        # con un retraso aleatorio. Es infinitamente más ligero para la CPU.
        invoke(self.parpadear, delay=random.uniform(0.2, 0.8))