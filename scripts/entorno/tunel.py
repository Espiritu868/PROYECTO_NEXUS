from ursina import Entity, color

def generar_tunel(z_inicio, z_fin):
    padre_tunel = Entity()
    
    # La longitud de cada sección del tubo asumiendo un tamaño nativo de 2 unidades y escala 10
    longitud_segmento = 20
    
    # Empezamos ligeramente adelantados para que encaje bien en la pared
    z_actual = z_inicio + (longitud_segmento / 2)
    
    while z_actual < z_fin:
        # Generar el tubo visual
        Entity(
            parent=padre_tunel,
            model='assets/texturas/factory/pipe-glass-large-long.obj',
            texture='assets/texturas/factory/Textures/colormap.png',
            position=(0, 0, z_actual), # y=0 porque el origen del modelo está en su base
            rotation_y=90, 
            # scale=(X_local, Y_local, Z_local)
            # Al girar 90: X es longitud, Y es altura, Z es anchura
            scale=(10, 10, 25), # Z=25 para hacerlo muy ancho y que encaje con el pasillo
            double_sided=True
        )
        z_actual += longitud_segmento
        
    # --- COLISIONES INVISIBLES ---
    longitud_total = z_fin - z_inicio
    z_centro = z_inicio + (longitud_total / 2)
    
    # Piso invisible (transparente, para dar vértigo)
    # y = -0.5 para que esté ligeramente bajo el nivel visual de los pies y parezca que pisan el cristal
    Entity(
        parent=padre_tunel,
        model='cube',
        position=(0, -0.5, z_centro),
        scale=(10, 1, longitud_total),
        collider='box',
        visible=False
    )
    
    # Paredes invisibles para evitar que el jugador atraviese el cristal curvo
    Entity(
        parent=padre_tunel,
        model='cube',
        position=(-10, 5, z_centro), # Ensanchadas a -10
        scale=(1, 15, longitud_total),
        collider='box',
        visible=False
    )
    Entity(
        parent=padre_tunel,
        model='cube',
        position=(10, 5, z_centro), # Ensanchadas a 10
        scale=(1, 15, longitud_total),
        collider='box',
        visible=False
    )
    
    # Techo invisible
    Entity(
        parent=padre_tunel,
        model='cube',
        position=(0, 10, z_centro),
        scale=(10, 1, longitud_total),
        collider='box',
        visible=False
    )
