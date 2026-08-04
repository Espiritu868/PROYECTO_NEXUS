from ursina import Entity, color
import random

def generar_decoracion(centro_x, centro_z, tamano, indice_arena=0):
    padre_maestro = Entity()
    padre_visual = Entity(parent=padre_maestro)
    padre_colision = Entity(parent=padre_maestro, visible=False)
    
    mitad = tamano // 2
    
    def es_posicion_valida(rx, rz):
        margen = 3.5
        if -100 - margen < rz < -100 + margen:
            if -200 - margen < rx < -50 + margen or 50 - margen < rx < 200 + margen: return False
        if -margen < rz < margen:
            if -170 - margen < rx < -50 + margen or 50 - margen < rx < 170 + margen: return False
        if 100 - margen < rz < 100 + margen:
            if -200 - margen < rx < -50 + margen or 50 - margen < rx < 200 + margen: return False
        if -100 - margen < rx < -100 + margen:
            if -150 - margen < rz < 50 + margen: return False
        if 100 - margen < rx < 100 + margen:
            if -50 - margen < rz < 150 + margen: return False
        return True
        
    ruta = 'assets/modelos/objetos_con_meshy/'
    
    # 1. Una sola mesa de crafteo en una esquina
    pos_mesa = (centro_x - mitad + 30, 0.75, centro_z - mitad + 30)
    mesa = Entity(parent=padre_visual, model=ruta+'mesa_trabajo.glb', 
           position=pos_mesa, rotation=(0, 45, 0), scale=1.5, color=color.yellow) 
    Entity(parent=padre_colision, model='cube', position=pos_mesa, rotation=(0, 45, 0), scale=(1.5, 1.5, 1.5))
           
    import __main__ as main
    main.mesa_trabajo = mesa
    
    # Eliminada la decoración innecesaria (ductos, servidores, cajas, barriles) para optimizar rendimiento y limpieza visual

    # --- 5. CAJA MISTERIOSA (Mystery Box) ---
    from scripts.caja_armas import CajaMisteriosa
    
    # 4 posiciones en las esquinas de la arena (dependiendo del tamaño, usando 'mitad')
    margen_caja = 25
    posiciones_caja = [
        (centro_x - mitad + margen_caja, 0.5, centro_z + mitad - margen_caja), # Noroeste
        (centro_x + mitad - margen_caja, 0.5, centro_z + mitad - margen_caja), # Noreste
        (centro_x - mitad + margen_caja, 0.5, centro_z - mitad + margen_caja), # Suroeste
        (centro_x + mitad - margen_caja, 0.5, centro_z - mitad + margen_caja)  # Sureste
    ]
    
    # Creamos UNA sola caja que se moverá entre esas 4 posiciones.
    # No la hacemos hija de padre_visual porque padre_visual se aplana (flatten_strong).
    caja_misteriosa = CajaMisteriosa(posiciones_spawn=posiciones_caja, parent_visual=padre_maestro)
    import __main__ as main
    main.caja_misteriosa = caja_misteriosa

    # --- 6. MÁQUINAS DE BEBIDAS (PERKS) ---
    from scripts.bebidas import MaquinaBebida
    
    # Generar 3 posiciones aleatorias y válidas
    posiciones_bebidas = []
    for _ in range(3):
        while True:
            rx = random.uniform(-mitad + 40, mitad - 40)
            rz = random.uniform(-mitad + 40, mitad - 40)
            if abs(rx) < 50 and abs(rz) > mitad - 80: continue # Evitar pasillos centrales
            if es_posicion_valida(rx, rz):
                pos_valida = (centro_x + rx, 1.8, centro_z + rz) # Subimos el y=1.8 para que no queden enterradas
                posiciones_bebidas.append(pos_valida)
                break
                
    if len(posiciones_bebidas) >= 3:
        MaquinaBebida(tipo='azul', modelo_path='assets/modelos/objetos_con_meshy/bebidas/bebida_azul.glb', precio=500, color_luz=color.cyan, position=posiciones_bebidas[0], rotation=(0, random.uniform(0,360), 0))
        MaquinaBebida(tipo='roja', modelo_path='assets/modelos/objetos_con_meshy/bebidas/bebida_red.glb', precio=2500, color_luz=color.red, position=posiciones_bebidas[1], rotation=(0, random.uniform(0,360), 0))
        MaquinaBebida(tipo='verde', modelo_path='assets/modelos/objetos_con_meshy/bebidas/bebida_verde.glb', precio=4000, color_luz=color.green, position=posiciones_bebidas[2], rotation=(0, random.uniform(0,360), 0))

    return padre_maestro
