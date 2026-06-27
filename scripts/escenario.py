from ursina import *

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