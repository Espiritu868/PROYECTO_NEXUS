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
    
    # 2. Sistema de ductos de aire (ducto_amarillo.glb)
    # Creando vías de conducto en el techo
    altura_ducto = 45 # Altura para que quede suspendido
    espaciado_ducto = 30
    
    # Línea de ductos a lo largo del eje X
    for px in range(int(-mitad + 40), int(mitad - 40), espaciado_ducto):
        pos1 = (centro_x + px, altura_ducto, centro_z + 60)
        Entity(parent=padre_visual, model=ruta+'ducto_amarillo.glb', position=pos1, rotation=(0, 90, 0), scale=4)
        Entity(parent=padre_colision, model='cube', position=pos1, rotation=(0, 90, 0), scale=(4, 4, 4))
        
        pos2 = (centro_x + px, altura_ducto, centro_z - 60)
        Entity(parent=padre_visual, model=ruta+'ducto_amarillo.glb', position=pos2, rotation=(0, 90, 0), scale=4)
        Entity(parent=padre_colision, model='cube', position=pos2, rotation=(0, 90, 0), scale=(4, 4, 4))

    # Línea de ductos a lo largo del eje Z
    for pz in range(int(-mitad + 40), int(mitad - 40), espaciado_ducto):
        pos3 = (centro_x + 60, altura_ducto, centro_z + pz)
        Entity(parent=padre_visual, model=ruta+'ducto_amarillo.glb', position=pos3, rotation=(0, 0, 0), scale=4)
        Entity(parent=padre_colision, model='cube', position=pos3, rotation=(0, 0, 0), scale=(4, 4, 4))
        
        pos4 = (centro_x - 60, altura_ducto, centro_z + pz)
        Entity(parent=padre_visual, model=ruta+'ducto_amarillo.glb', position=pos4, rotation=(0, 0, 0), scale=4)
        Entity(parent=padre_colision, model='cube', position=pos4, rotation=(0, 0, 0), scale=(4, 4, 4))

    # 3. Unos cuantos servidores regados (servidor.glb)
    random.seed(indice_arena + 10)
    for _ in range(30):
        while True:
            rx = random.uniform(-mitad + 40, mitad - 40)
            rz = random.uniform(-mitad + 40, mitad - 40)
            if abs(rx) < 50 and abs(rz) > mitad - 80: continue
            if es_posicion_valida(rx, rz): break
            
        rot = random.choice([0, 90, 180, 270])
        pos_s = (centro_x + rx, 1.8, centro_z + rz)
        Entity(parent=padre_visual, model=ruta+'servidor.glb', position=pos_s, rotation=(0, rot, 0), scale=2.5)
        # Cubo para colisión
        Entity(parent=padre_colision, model='cube', position=pos_s, rotation=(0, rot, 0), scale=(2.5, 4, 2.5))
               
    # 4. Los demás objetos (barriles, cajas, máquinas transportadoras)
    # Cajas
    for _ in range(50):
        while True:
            rx = random.uniform(-mitad + 30, mitad - 30)
            rz = random.uniform(-mitad + 30, mitad - 30)
            if abs(rx) < 50 and abs(rz) > mitad - 80: continue
            if es_posicion_valida(rx, rz): break
            
        pos_c = (centro_x + rx, 0.8, centro_z + rz)
        rot_c = random.uniform(0, 360)
        Entity(parent=padre_visual, model=ruta+'caja.glb', position=pos_c, rotation=(0, rot_c, 0), scale=0.8)
        Entity(parent=padre_colision, model='cube', position=pos_c, rotation=(0, rot_c, 0), scale=(1.2, 1.2, 1.2))

    # Barriles
    for _ in range(60):
        while True:
            rx = random.uniform(-mitad + 30, mitad - 30)
            rz = random.uniform(-mitad + 30, mitad - 30)
            if abs(rx) < 50 and abs(rz) > mitad - 80: continue
            if es_posicion_valida(rx, rz): break
            
        pos_b = (centro_x + rx, 0.8, centro_z + rz)
        rot_b = random.uniform(0, 360)
        Entity(parent=padre_visual, model=ruta+'barril_toxico_red.glb', position=pos_b, rotation=(0, rot_b, 0), scale=0.8)
        Entity(parent=padre_colision, model='cube', position=pos_b, rotation=(0, rot_b, 0), scale=(0.8, 1.0, 0.8))
               
    # Máquinas transportadoras
    for _ in range(15):
        while True:
            rx = random.uniform(-mitad + 50, mitad - 50)
            rz = random.uniform(-mitad + 50, mitad - 50)
            if abs(rx) < 50 and abs(rz) > mitad - 80: continue
            if es_posicion_valida(rx, rz): break
            
        rot_m = random.choice([0, 90, 180, 270])
        pos_m = (centro_x + rx, 2, centro_z + rz)
        Entity(parent=padre_visual, model=ruta+'maquina_transportadora.glb', position=pos_m, rotation=(0, rot_m, 0), scale=4)
        Entity(parent=padre_colision, model='cube', position=pos_m, rotation=(0, rot_m, 0), scale=(4, 4, 4))

    # OPTIMIZACIÓN EXTREMA DEFINITIVA:
    # 1. Aplanamos las mallas visuales (los .glb no soportan combine() de Ursina, así que usamos flatten_strong de Panda3D)
    if len(padre_visual.children) > 0:
        padre_visual.flatten_strong()
        
    # 2. Combinamos las colisiones en UN SOLO mesh (Los cubos sí soportan combine de Ursina)
    if len(padre_colision.children) > 0:
        padre_colision.combine(auto_destroy=True)
        # Asignamos un collider de malla que envuelve los 150 objetos en uno solo
        padre_colision.collider = 'mesh'

    return padre_maestro
