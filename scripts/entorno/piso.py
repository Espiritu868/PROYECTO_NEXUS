from ursina import Entity, color

def generar_piso(centro_x, centro_z, tamano):
    # Aumentamos el tamaño de la baldosa x10
    tamano_baldosa = 100 
    mitad = tamano // 2
    
    inicio_x = centro_x - mitad
    fin_x = centro_x + mitad
    inicio_z = centro_z - mitad
    fin_z = centro_z + mitad

    padre_piso = Entity()

    for x in range(inicio_x, fin_x, tamano_baldosa):
        for z in range(inicio_z, fin_z, tamano_baldosa):
            Entity(
                parent=padre_piso,
                model='assets/texturas/floor.glb',
                position=(x + (tamano_baldosa/2), 0, z + (tamano_baldosa/2)),
                collider='box',
                color=color.white,
                # Escala masiva para cubrir todo ese espacio extra
                scale=(100, 1, 100) 
            )