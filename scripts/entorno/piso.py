from ursina import Entity, color, scene, load_texture

def generar_piso(centro_x, centro_z, tamano, indice_arena=0): 
    mitad = tamano // 2
    
    inicio_x = centro_x - mitad
    fin_x = centro_x + mitad
    inicio_z = centro_z - mitad
    fin_z = centro_z + mitad

    padre_piso = Entity()
    
    # Fábrica (Arena 0): PISO DE CONCRETO (Textura Limpia)
    textura_concreto = load_texture('assets/texturas/pared_concreto.png')
    if textura_concreto: textura_concreto.filtering = 'mipmap'
    
    Entity(
        parent=padre_piso, 
        model='cube', 
        texture=textura_concreto,
        color=color.gray, 
        position=(centro_x, -0.5, centro_z), 
        collider='box',
        scale=(tamano, 1, tamano),
        texture_scale=(tamano/30, tamano/30) 
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