from ursina import Entity, color, BoxCollider, scene
import random
import time

def generar_patio_global(num_arenas, offset_z, tamano_arena):
    padre_patio = Entity()
    
    # Dimensiones del patio masivo
    ancho_patio = tamano_arena + 400 # 800 de ancho (va de x=-400 a x=400)
    z_inicio = -300
    z_fin = ((num_arenas - 1) * offset_z) + 300
    
    textura_patio = 'assets/texturas/out/Textures/colormap.png'
    
    # Aumentamos el tamaño de baldosa para menos entidades
    tamano_baldosa = 40 
    
    print("Generando patio masivo optimizado...")
    tiempo_inicio = time.time()
    
    modelos_piso = ['assets/texturas/out/floor-detail.obj', 'assets/texturas/out/dirt.obj']
    
    # 0. PISO INVISIBLE MASIVO (1 solo colisionador para TODO el mapa = 60+ FPS)
    largo_total = z_fin - z_inicio
    centro_z = (z_inicio + z_fin) / 2
    Entity(parent=padre_patio, model='cube', position=(0, -0.5, centro_z), scale=(ancho_patio, 1, largo_total), collider='box', visible=False)
    
    import __main__ as main
    if not hasattr(main, 'patio_chunks'):
        main.patio_chunks = []
        
    # 1. Generar el suelo visual en Chunks y fusionarlos en C++
    longitud_chunk = 400
    for z_chunk_start in range(int(z_inicio), int(z_fin), longitud_chunk):
        # Creamos la entidad base del chunk y la posicionamos en su centro
        z_centro_chunk = z_chunk_start + (longitud_chunk / 2)
        chunk = Entity(parent=padre_patio, z=z_centro_chunk)
        main.patio_chunks.append(chunk)
        
        for x in range(int(-ancho_patio/2), int(ancho_patio/2), tamano_baldosa):
            for z_local in range(0, longitud_chunk, tamano_baldosa):
                z_global = z_chunk_start + z_local
                z_relativo = z_global - z_centro_chunk
                
                modelo = random.choices(modelos_piso, weights=[0.8, 0.2])[0]
                
                Entity(
                    parent=chunk,
                    model=modelo,
                    texture=textura_patio,
                    position=(x + tamano_baldosa/2, -0.5, z_relativo + tamano_baldosa/2),
                    scale=(tamano_baldosa, 1, tamano_baldosa), 
                    collider=None 
                )
                
        # Fusionamos usando flatten_strong de Panda3D para asegurar limpieza de memoria
        if len(chunk.children) > 0:
            hijos_chunk = list(chunk.children)
            chunk.flatten_strong()
            
            def limpiar_entidad(ent):
                if ent in scene.entities:
                    scene.entities.remove(ent)
                for c in ent.children:
                    limpiar_entidad(c)
                    
            for hijo in hijos_chunk:
                limpiar_entidad(hijo)
                
        # RE-APLICAMOS LA TEXTURA AL CHUNK COMBINADO PARA EVITAR QUE SE VEA BLANCO
        chunk.texture = textura_patio

    # 2. Muros invisibles en los bordes del mundo
    altura_muro = 50
    Entity(parent=padre_patio, model='cube', position=(-ancho_patio/2, altura_muro/2, (z_inicio+z_fin)/2), scale=(2, altura_muro, z_fin-z_inicio), collider='box', visible=False)
    Entity(parent=padre_patio, model='cube', position=(ancho_patio/2, altura_muro/2, (z_inicio+z_fin)/2), scale=(2, altura_muro, z_fin-z_inicio), collider='box', visible=False)
    Entity(parent=padre_patio, model='cube', position=(0, altura_muro/2, z_inicio), scale=(ancho_patio, altura_muro, 2), collider='box', visible=False)
    Entity(parent=padre_patio, model='cube', position=(0, altura_muro/2, z_fin), scale=(ancho_patio, altura_muro, 2), collider='box', visible=False)

    # 3. Decoraciones (Sin combine, ya que necesitan colisiones individuales)
    modelos_decoracion = [
        'assets/texturas/out/rocks.obj',
        'assets/texturas/out/stones.obj',
        'assets/texturas/out/column.obj',
        'assets/texturas/out/wood-structure.obj',
        'assets/texturas/out/dirt.obj'
    ]
    
    cantidad_decoraciones = 400
    padre_decoraciones_patio = Entity(parent=padre_patio)
    
    for _ in range(cantidad_decoraciones):
        dx = random.uniform(-ancho_patio/2 + 20, ancho_patio/2 - 20)
        dz = random.uniform(z_inicio + 20, z_fin - 20)
        
        # Evitar el interior de las habitaciones
        dentro_habitacion = False
        for i in range(num_arenas):
            centro_z = i * offset_z
            if (-200 <= dx <= 200) and (centro_z - 200 <= dz <= centro_z + 200):
                dentro_habitacion = True
                break
                
        if not dentro_habitacion:
            modelo = random.choice(modelos_decoracion)
            escala = random.uniform(4, 9) 
            e = Entity(
                parent=padre_decoraciones_patio,
                model=modelo,
                texture=textura_patio,
                position=(dx, -0.5, dz),
                rotation_y=random.uniform(0, 360),
                scale=escala,
                collider=None
            )
            if 'dirt' not in modelo:
                # Cajas de colisión un 50% más delgadas para no atorar al jugador
                e.collider = BoxCollider(e, center=(0, 0.5, 0), size=(0.5, 1, 0.5))
                
    # Optimizamos las 400 decoraciones fusionando su geometría
    if len(padre_decoraciones_patio.children) > 0:
        hijos_dec = list(padre_decoraciones_patio.children)
        padre_decoraciones_patio.flatten_strong()
        
        def limpiar_entidad(ent):
            if ent in scene.entities:
                scene.entities.remove(ent)
            for c in ent.children:
                limpiar_entidad(c)
                
        for hijo in hijos_dec:
            limpiar_entidad(hijo)
            
    print(f"Patio generado en {round(time.time() - tiempo_inicio, 2)} segundos.")
    return padre_patio
