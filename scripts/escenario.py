from ursina import *
import random
from scripts.servidores import ServidorRoto # <-- NUEVA IMPORTACIÓN

def construir_piso(nivel, altura_techo=20):
    """
    Construye un piso masivo. nivel 0 = Planta baja, nivel 1 = Piso 2, etc.
    """
    y_base = nivel * altura_techo
    tamano = 150  
    
    # 1. SUELO DEL PISO
    suelo = Entity(
        model='cube', scale=(tamano, 2, tamano), position=(0, y_base, 0),
        color=color.hex('#1a1a1a'), texture='white_cube',
        texture_scale=(tamano/10, tamano/10), collider='box'
    )
    
    # 2. TECHO
    techo = Entity(
        model='cube', scale=(tamano, 2, tamano), position=(0, y_base + altura_techo, 0),
        color=color.hex('#0d0d0d'), texture='white_cube',
        texture_scale=(tamano/10, tamano/10), collider='box'
    )
    
    # 3. PAREDES PERIMETRALES
    color_pared = color.hex('#2a2a2a')
    Entity(model='cube', scale=(tamano, altura_techo, 2), position=(0, y_base + altura_techo/2, tamano/2), color=color_pared, collider='box')
    Entity(model='cube', scale=(tamano, altura_techo, 2), position=(0, y_base + altura_techo/2, -tamano/2), color=color_pared, collider='box')
    Entity(model='cube', scale=(2, altura_techo, tamano), position=(tamano/2, y_base + altura_techo/2, 0), color=color_pared, collider='box')
    Entity(model='cube', scale=(2, altura_techo, tamano), position=(-tamano/2, y_base + altura_techo/2, 0), color=color_pared, collider='box')

    # 4. ASCENSOR CENTRAL
    ascensor = Entity(
        model='cube', scale=(15, altura_techo, 15), position=(0, y_base + altura_techo/2, 0),
        color=color.orange, collider='box'
    )
    
    # 5. ZONA DE ESCALERAS
    if nivel < 3: 
        escalera_rampa = Entity(
            model='cube', scale=(10, 1, 40), position=(tamano/2 - 20, y_base + altura_techo/2, 0),
            rotation_x=-30, color=color.cyan, collider='box'
        )

    # ZONA DE SERVIDORES CATASTRÓFICOS
    for z in range(20, 60, 6):      
        for x in range(-60, -20, 4):    
            if random.random() > 0.2:
                pos_servidor = (x, y_base + 1.75, z)
                ServidorRoto(position=pos_servidor)

    # Escombros
    for _ in range(5):
        pos_azar = (random.uniform(-30, 30), y_base + 0.5, random.uniform(-30, 30))
        if abs(pos_azar[0]) > 10: 
            s = ServidorRoto(position=pos_azar)
            s.rotation_x = 90