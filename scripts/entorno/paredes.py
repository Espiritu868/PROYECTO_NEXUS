from ursina import Entity

def generar_paredes(centro_x, centro_z, tamano, indice_arena, total_arenas):
    tamano_pared = 10 
    mitad = tamano // 2
    
    inicio_x = centro_x - mitad
    fin_x = centro_x + mitad
    inicio_z = centro_z - mitad
    fin_z = centro_z + mitad

    padre_paredes = Entity()

    # Paredes Norte y Sur
    for x in range(inicio_x, fin_x, tamano_pared):
        pos_x = x + tamano_pared/2
        
        # Detectamos las dos posiciones centrales (x = -5 y x = 5)
        if pos_x == -5 or pos_x == 5:
            
            # --- PUERTA SUR (Atrás) ---
            Entity(parent=padre_paredes, model='assets/texturas/door.glb', 
                   position=(pos_x, 0, inicio_z), scale=10)
            
            # BLOQUEO INVISIBLE SUR (Campo de fuerza)
            Entity(parent=padre_paredes, position=(pos_x, 5, inicio_z), 
                   collider='box', scale=(10, 10, 2), visible=False)
            
            # --- PUERTA NORTE (Frente) ---
            Entity(parent=padre_paredes, model='assets/texturas/door.glb', 
                   position=(pos_x, 0, fin_z), rotation_y=180, scale=10)
                   
            # BLOQUEO INVISIBLE NORTE (Campo de fuerza)
            Entity(parent=padre_paredes, position=(pos_x, 5, fin_z), 
                   collider='box', scale=(10, 10, 2), visible=False)
                   
        else:
            # Muros estáticos normales a los lados de las puertas
            Entity(parent=padre_paredes, model='assets/texturas/structure-wall.glb', 
                   position=(pos_x, 0, inicio_z), collider='box', scale=10)
                   
            Entity(parent=padre_paredes, model='assets/texturas/structure-wall.glb', 
                   position=(pos_x, 0, fin_z), collider='box', rotation_y=180, scale=10)

    # Paredes Este y Oeste (Laterales completamente cerrados)
    for z in range(inicio_z, fin_z, tamano_pared):
        pos_z = z + tamano_pared/2
        Entity(parent=padre_paredes, model='assets/texturas/structure-wall.glb', 
               position=(inicio_x, 0, pos_z), collider='box', rotation_y=90, scale=10)
               
        Entity(parent=padre_paredes, model='assets/texturas/structure-wall.glb', 
               position=(fin_x, 0, pos_z), collider='box', rotation_y=-90, scale=10)