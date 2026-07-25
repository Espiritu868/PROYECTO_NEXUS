from ursina import Entity, BoxCollider, scene

def generar_decoracion(centro_x, centro_z, tamano, indice_arena=0):
    padre_decoracion = Entity()
    mitad = tamano // 2
    
    # ----------------------------------------------------
    # BIOMA MEDIEVAL (Habitación 2 / Índice 1)
    # ----------------------------------------------------
    if indice_arena == 1:
        # 1. Zonas de almacenamiento (Barriles y cajas)
        posiciones_almacen = [
            (centro_x - 70, centro_z - 70),
            (centro_x + 70, centro_z - 70),
            (centro_x - 70, centro_z + 70),
            (centro_x + 70, centro_z + 70)
        ]
        for px, pz in posiciones_almacen:
            Entity(parent=padre_decoracion, model='assets/texturas/medieval/barrels.glb', position=(px, 0, pz), scale=10, collider='box')
            Entity(parent=padre_decoracion, model='assets/texturas/medieval/detail-crate.glb', position=(px+15, 0, pz), scale=15, collider='box')
            Entity(parent=padre_decoracion, model='assets/texturas/medieval/detail-crate.glb', position=(px, 15, pz), scale=15, collider='box')
            
        # 2. Vegetación (Árboles laterales)
        # Redujimos la escala de 15 a 6 para que no se vean con baja resolución (pixelados)
        # y aumentamos la frecuencia de árboles (cada 20m en vez de 40m)
        for z in range(int(centro_z - mitad + 50), int(centro_z + mitad - 50), 20):
            t1 = Entity(parent=padre_decoracion, model='assets/texturas/medieval/tree-large.glb', position=(centro_x - (mitad - 30), 0, z), scale=6)
            # Colisionador súper delgado (20%) solo para el tronco, ignorando las ramas
            t1.collider = BoxCollider(t1, center=(0, 0.5, 0), size=(0.2, 1, 0.2))
            
            t2 = Entity(parent=padre_decoracion, model='assets/texturas/medieval/tree-large.glb', position=(centro_x + (mitad - 30), 0, z), scale=6)
            t2.collider = BoxCollider(t2, center=(0, 0.5, 0), size=(0.2, 1, 0.2))

        # 3. Columnas de madera decorativas
        posiciones_columnas = [
            (centro_x - mitad + 60, centro_z - mitad + 60),
            (centro_x + mitad - 60, centro_z - mitad + 60),
            (centro_x - mitad + 60, centro_z + mitad - 60),
            (centro_x + mitad - 60, centro_z + mitad - 60)
        ]
        for px, pz in posiciones_columnas:
            Entity(parent=padre_decoracion, model='assets/texturas/medieval/column-wood.glb', position=(px, 0, pz), scale=(10, 30, 10), collider='box')

        # Optimización extrema: Fusionar toda la geometría de árboles y cajas en 1 sola malla
        if len(padre_decoracion.children) > 0:
            hijos = list(padre_decoracion.children)
            padre_decoracion.flatten_strong()
            
            def limpiar_entidad(ent):
                if ent in scene.entities:
                    scene.entities.remove(ent)
                for c in ent.children:
                    limpiar_entidad(c)
                    
            for hijo in hijos:
                limpiar_entidad(hijo)
                
        return padre_decoracion # Finalizamos aquí para que no se generen objetos industriales

    # ----------------------------------------------------
    # BIOMA FÁBRICA INDUSTRIAL (Resto de las arenas)
    # ----------------------------------------------------
    textura_factory = 'assets/texturas/factory/Textures/colormap.png'
    
    # 1. CINTAS TRANSPORTADORAS LATERALES
    x_offset_cinta = mitad - 40 
    for z in range(int(centro_z - mitad + 50), int(centro_z + mitad - 50), 30):
        Entity(parent=padre_decoracion, model='assets/texturas/factory/conveyor-long.obj', 
               texture=textura_factory, position=(centro_x - x_offset_cinta, 0, z), 
               scale=6, collider='box')
        Entity(parent=padre_decoracion, model='assets/texturas/factory/conveyor-long.obj', 
               texture=textura_factory, position=(centro_x + x_offset_cinta, 0, z), 
               scale=6, collider='box')
               
    # 2. MAQUINARIA INDUSTRIAL (ESQUINAS)
    posiciones_maquinas = [
        (centro_x - mitad + 60, centro_z - mitad + 60),
        (centro_x + mitad - 60, centro_z - mitad + 60),
        (centro_x - mitad + 60, centro_z + mitad - 60),
        (centro_x + mitad - 60, centro_z + mitad - 60)
    ]
    for px, pz in posiciones_maquinas:
        rotacion = 45 if px < centro_x else -45
        if pz > centro_z: rotacion += 90 if px < centro_x else -90
        
        m1 = Entity(parent=padre_decoracion, model='assets/texturas/factory/machine.obj',
               texture=textura_factory, position=(px, 0, pz),
               scale=8, rotation_y=rotacion)
        # Colisionador un poco más pequeño que el modelo
        m1.collider = BoxCollider(m1, center=(0, 0.5, 0), size=(0.8, 1, 0.8))
        
        # Tubería flotante (Como está a 20m de altura, le quitamos el collider para ahorrar CPU)
        Entity(parent=padre_decoracion, model='assets/texturas/factory/pipe-large-bend.obj',
               texture=textura_factory, position=(px, 20, pz),
               scale=6, collider=None)

    # 3. ZONAS DE ALMACENAJE (COBERTURAS PARA COMBATE)
    posiciones_cajas = [
        (centro_x - 70, centro_z - 70),
        (centro_x + 70, centro_z - 70),
        (centro_x - 70, centro_z + 70),
        (centro_x + 70, centro_z + 70)
    ]
    for px, pz in posiciones_cajas:
        Entity(parent=padre_decoracion, model='assets/texturas/factory/box-large.obj', texture=textura_factory, position=(px, 0, pz), scale=5, collider='box')
        Entity(parent=padre_decoracion, model='assets/texturas/factory/box-small.obj', texture=textura_factory, position=(px+12, 0, pz), scale=5, collider='box')
        Entity(parent=padre_decoracion, model='assets/texturas/factory/box-large.obj', texture=textura_factory, position=(px, 10, pz), scale=5, collider='box')
        Entity(parent=padre_decoracion, model='assets/texturas/factory/box-small.obj', texture=textura_factory, position=(px+12, 10, pz), scale=5, collider='box')
        
    # 4. GRÚAS DE CARGA
    g1 = Entity(parent=padre_decoracion, model='assets/texturas/factory/crane.obj',
           texture=textura_factory, position=(centro_x - 120, 0, centro_z),
           scale=10, rotation_y=90)
    # Grúa tiene brazos largos, el box collider normal atraparía al jugador. Usamos uno delgado para la base.
    g1.collider = BoxCollider(g1, center=(0, 0.5, 0), size=(0.25, 1, 0.25))
    
    g2 = Entity(parent=padre_decoracion, model='assets/texturas/factory/crane.obj',
           texture=textura_factory, position=(centro_x + 120, 0, centro_z),
           scale=10, rotation_y=-90)
    g2.collider = BoxCollider(g2, center=(0, 0.5, 0), size=(0.25, 1, 0.25))

    # 5. LETREROS Y SEÑALES
    Entity(parent=padre_decoracion, model='assets/texturas/factory/warning-orange.obj',
           texture=textura_factory, position=(centro_x - 20, 0, centro_z - mitad + 20),
           scale=6, collider='box', rotation_y=180)
    Entity(parent=padre_decoracion, model='assets/texturas/factory/warning-orange.obj',
           texture=textura_factory, position=(centro_x + 20, 0, centro_z - mitad + 20),
           scale=6, collider='box', rotation_y=180)

    # Optimización extrema: Fusionar toda la geometría industrial en 1 sola malla
    if len(padre_decoracion.children) > 0:
        hijos = list(padre_decoracion.children)
        padre_decoracion.flatten_strong()
        
        def limpiar_entidad(ent):
            if ent in scene.entities:
                scene.entities.remove(ent)
            for c in ent.children:
                limpiar_entidad(c)
                
        for hijo in hijos:
            limpiar_entidad(hijo)
            
    return padre_decoracion
