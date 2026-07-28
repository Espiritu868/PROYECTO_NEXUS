from ursina import Entity, color, scene, load_texture

def generar_piso(centro_x, centro_z, tamano, indice_arena=0): 
    # Fábrica (Arena 0): PISO DE CONCRETO (Textura Limpia)
    textura_concreto = load_texture('assets/texturas/pared_concreto.png')
    if textura_concreto: textura_concreto.filtering = 'mipmap'
    
    piso = Entity(
        model='cube', 
        texture=textura_concreto,
        color=color.gray, 
        position=(centro_x, -0.5, centro_z), 
        collider='box',
        scale=(tamano, 1, tamano),
        texture_scale=(tamano/30, tamano/30) 
    )

    return piso