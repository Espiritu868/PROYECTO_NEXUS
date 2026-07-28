from ursina import Entity, scene, color, load_texture

def generar_techo(centro_x, centro_z, tamano, indice_arena=0):
    # Usamos baldosas gigantes para evitar miles de objetos (optimización de FPS)
    altura_techo = 15 
    
    textura_concreto = load_texture('assets/texturas/pared_concreto.png')
    if textura_concreto: textura_concreto.filtering = 'mipmap'
    
    techo = Entity(
        model='cube',
        texture=textura_concreto,
        color=color.gray, 
        position=(centro_x, altura_techo, centro_z),
        rotation_x=180, 
        scale=(tamano, 1, tamano),
        texture_scale=(tamano/30, tamano/30), 
        collider=None
    )

    return techo
