from ursina import Entity

def generar_techo(centro_x, centro_z, tamano, indice_arena=0):
    # Usamos baldosas gigantes para evitar miles de objetos (optimización de FPS)
    # Al escalar un modelo con UVs sólidos (como los de Kenney), no hay estiramiento visible. 
    mitad = tamano // 2
    altura_techo = 30 
    
    inicio_x = int(centro_x - mitad)
    fin_x = int(centro_x + mitad)
    inicio_z = int(centro_z - mitad)
    fin_z = int(centro_z + mitad)
    
    padre_techo = Entity()
    
    # Configuramos el modelo y textura del techo
    if indice_arena == 1:
        # Habitación medieval: USAMOS UN SOLO PLANO para 60FPS
        Entity(
            parent=padre_techo,
            model='plane',
            texture='assets/texturas/medieval/Textures/planks.png',
            position=(centro_x, altura_techo, centro_z),
            rotation_x=180, # Invertido para mirar abajo
            scale=(tamano, 1, tamano),
            texture_scale=(tamano/10, tamano/10),
            collider=None
        )
    else:
        # Fábrica: optimizado
        tamano_baldosa = 100
        modelo_techo = 'assets/texturas/factory/top-large.obj'
        textura_techo = 'assets/texturas/factory/Textures/colormap.png'
        # El modelo mide 2x2. Para cubrir 100x100, escalamos X y Z por 50. Mantenemos Y en 1.
        escala_techo = (50, 1, 50)

        for x in range(inicio_x, fin_x, tamano_baldosa):
            for z in range(inicio_z, fin_z, tamano_baldosa):
                Entity(
                    parent=padre_techo,
                    model=modelo_techo,
                    texture=textura_techo,
                    position=(x + (tamano_baldosa/2), altura_techo, z + (tamano_baldosa/2)),
                    rotation_x=180, 
                    scale=escala_techo, 
                    collider=None
                )

    return padre_techo
