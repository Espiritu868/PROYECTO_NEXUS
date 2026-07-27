from ursina import Entity, scene, color, load_texture

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
    # Fábrica (Arena 0): TECHO DE CONCRETO
    # Un solo cubo gigante mirando hacia abajo, usando la textura de concreto
    textura_concreto = load_texture('assets/texturas/pared_concreto.png')
    if textura_concreto: textura_concreto.filtering = 'mipmap'
    
    Entity(
        parent=padre_techo,
        model='cube',
        texture=textura_concreto,
        color=color.gray, 
        position=(centro_x, altura_techo, centro_z),
        rotation_x=180, 
        scale=(tamano, 1, tamano),
        texture_scale=(tamano/30, tamano/30), 
        collider=None
    )

    if len(padre_techo.children) > 0:
        hijos = list(padre_techo.children)
        padre_techo.flatten_strong()
        
        def limpiar_entidad(ent):
            if ent in scene.entities:
                scene.entities.remove(ent)
            for c in ent.children:
                limpiar_entidad(c)
                
        for hijo in hijos:
            limpiar_entidad(hijo)

    return padre_techo
