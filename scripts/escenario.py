from ursina import *
import random

# --- Nueva seccion Clase ServidorRoto
class ServidorRoto(Entity):
    def __init__(self, position=(0,0,0)):
        # Decidir si está caído o en pie
        esta_caido = random.random() > 0.7
        rot_z = random.uniform(-10, 10) if not esta_caido else 90
        rot_y = random.choice([0, 90, 180, 270])
        
        super().__init__(
            model='cube',
            position=position,
            scale=(1.8, 3.5, 1.8), # Proporción más realista para tu escala 150
            color=color.hex('#222222'),
            rotation=(0, rot_y, rot_z),
            collider='box'
        )

        # Panel frontal de luces
        self.panel = Entity(
            parent=self,
            model='cube',
            scale=(0.85, 0.9, 0.05),
            z=-0.51,
            color=color.black
        )

        # Generar luces de error
        self.luces = []
        for i in range(random.randint(2, 6)):
            luz = Entity(
                parent=self.panel,
                model='cube',
                color=random.choice([color.red, color.hex('#444444'), color.orange]),
                scale=(0.15, 0.05, 1),
                x=-0.25,
                y=0.4 - (i * 0.15)
            )
            self.luces.append(luz)

    def update(self):
        # Solo parpadean si no están "fundidas" (gris)
        for luz in self.luces:
            if luz.color != color.hex('#444444'):
                if random.random() > 0.97:
                    luz.enabled = not luz.enabled

def construir_piso(nivel, altura_techo=20):
    """
    Construye un piso masivo. 
    nivel 0 = Planta baja, nivel 1 = Piso 2, etc.
    """
    y_base = nivel * altura_techo
    tamano = 150  # Tamaño masivo para albergar NPCs y al Jefe
    
    # 1. SUELO DEL PISO
    suelo = Entity(
        model='cube',
        scale=(tamano, 2, tamano),
        position=(0, y_base, 0),
        color=color.hex('#1a1a1a'),
        texture='white_cube',
        texture_scale=(tamano/10, tamano/10),
        collider='box'
    )
    
    # 2. TECHO (El límite superior del nivel)
    techo = Entity(
        model='cube',
        scale=(tamano, 2, tamano),
        position=(0, y_base + altura_techo, 0),
        color=color.hex('#0d0d0d'),
        texture='white_cube',
        texture_scale=(tamano/10, tamano/10),
        collider='box'
    )
    
    # 3. PAREDES PERIMETRALES
    color_pared = color.hex('#2a2a2a')
    # Pared Norte
    Entity(model='cube', scale=(tamano, altura_techo, 2), position=(0, y_base + altura_techo/2, tamano/2), color=color_pared, collider='box')
    # Pared Sur
    Entity(model='cube', scale=(tamano, altura_techo, 2), position=(0, y_base + altura_techo/2, -tamano/2), color=color_pared, collider='box')
    # Pared Este
    Entity(model='cube', scale=(2, altura_techo, tamano), position=(tamano/2, y_base + altura_techo/2, 0), color=color_pared, collider='box')
    # Pared Oeste
    Entity(model='cube', scale=(2, altura_techo, tamano), position=(-tamano/2, y_base + altura_techo/2, 0), color=color_pared, collider='box')

    # 4. PLACEHOLDER: ASCENSOR CENTRAL (Color Naranja)
    # Bloque sólido temporal que luego reemplazaremos por las puertas y cabina
    ascensor = Entity(
        model='cube',
        scale=(15, altura_techo, 15),
        position=(0, y_base + altura_techo/2, 0),
        color=color.orange,
        collider='box'
    )
    
    # 5. PLACEHOLDER: ZONA DE ESCALERAS (Color Cyan)
    # Una rampa gigante temporal que conecta este piso con el siguiente
    if nivel < 3:  # El último piso (3) no necesita escaleras para subir
        escalera_rampa = Entity(
            model='cube',
            scale=(10, 1, 40),
            position=(tamano/2 - 20, y_base + altura_techo/2, 0),
            rotation_x=-30, # Inclinación de rampa
            color=color.cyan,
            collider='box'
        )

     # --- NUEVA SECCIÓN: ZONA DE SERVIDORES CATASTRÓFICOS ---
    # Crear "pasillos" de servidores en el cuadrante Norte-Oeste
    for z in range(20, 60, 6):      # Filas de servidores
        for x in range(-60, -20, 4): # Servidores por fila    
            if random.random() > 0.2:
                # Calculamos la posición: y_base + 1.75 para que estén sobre el suelo
                pos_servidor = (x, y_base + 1.75, z)
                ServidorRoto(position=pos_servidor)

    # Añadir algunos escombros (servidores tirados al azar en el centro)
    for _ in range(5):
        pos_azar = (random.uniform(-30, 30), y_base + 0.5, random.uniform(-30, 30))
        # Evitar que aparezcan dentro del ascensor (0,0,0)
        if abs(pos_azar[0]) > 10: 
            s = ServidorRoto(position=pos_azar)
            s.rotation_x = 90 # Tirado en el suelo
