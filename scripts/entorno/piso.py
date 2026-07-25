from ursina import Entity, color, scene

def generar_piso(centro_x, centro_z, tamano, indice_arena=0): 
    mitad = tamano // 2
    
    inicio_x = centro_x - mitad
    fin_x = centro_x + mitad
    inicio_z = centro_z - mitad
    fin_z = centro_z + mitad

    padre_piso = Entity()
    
    if indice_arena == 1:
        # Habitación medieval: USAMOS UN SOLO PLANO con textura repetida. ¡1 sola entidad en vez de 1600 para que vaya a 60FPS!
        Entity(
            parent=padre_piso,
            model='plane',
            texture='assets/texturas/medieval/Textures/planks.png',
            position=(centro_x, 0, centro_z),
            collider='box',
            scale=(tamano, 1, tamano),
            texture_scale=(tamano/10, tamano/10) # Repetimos la textura para que no se estire
        )
    else:
        # Fábrica: usamos baldosas gigantes para optimizar
        tamano_baldosa = 100
        modelo_suelo = 'assets/texturas/factory/floor-large.obj'
        textura_suelo = 'assets/texturas/factory/Textures/colormap.png'
        # El modelo mide 2x2. Para cubrir 100x100, escalamos X y Z por 50. Mantenemos Y en 1.
        escala = (50, 1, 50)

        for x in range(inicio_x, fin_x, tamano_baldosa):
            for z in range(inicio_z, fin_z, tamano_baldosa):
                Entity(
                    parent=padre_piso,
                    model=modelo_suelo,
                    texture=textura_suelo,
                    position=(x + (tamano_baldosa/2), 0, z + (tamano_baldosa/2)),
                    collider='box',
                    scale=escala 
                )

    if len(padre_piso.children) > 0:
        hijos = list(padre_piso.children)
        padre_piso.flatten_strong()
        
        def limpiar_entidad(ent):
            if ent in scene.entities:
                scene.entities.remove(ent)
            for c in ent.children:
                limpiar_entidad(c)
                
        for hijo in hijos:
            limpiar_entidad(hijo)

    return padre_piso