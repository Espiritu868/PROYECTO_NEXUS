from ursina import Entity

class GestorArena(Entity):
    def __init__(self, jefe_class, cantidad_enemigos, centro_x, centro_z, puertas_frente, puertas_atras, limite_z, indice_arena, gestor_portal=None, **kwargs):
        super().__init__(**kwargs)
        self.jefe_class = jefe_class
        self.cantidad_enemigos = cantidad_enemigos
        self.centro_x = centro_x
        self.centro_z = centro_z
        self.enemigos = []
        self.puertas_frente = puertas_frente
        self.puertas_atras = puertas_atras
        self.limite_z = limite_z
        self.indice_arena = indice_arena
        self.gestor_portal = gestor_portal
        self.completada = False
        self.jugador_dentro = False
        self.jugador = None
        
        # Variables para spawn gradual
        self.spawns_pendientes = 0
        self.tiempo_ultimo_spawn = 0
        
        # --- PRE-LOAD POOL DE ENEMIGOS (Evita congelamiento mid-game) ---
        # Instanciamos 8 enemigos por arena durante la pantalla de carga
        import random
        from scripts.zombie import Zombie
        from scripts.villano_l import VillanoL
        from scripts.villano_o import VillanoO
        
        for _ in range(8):
            tipo_enemigo = random.choice([VillanoL, VillanoO, Zombie])
            # Se spawnean bajo tierra muy profundo para activar el culling espacial (>1000)
            enemigo = tipo_enemigo(position=(0, -2000, 0), rotation_y=0)
            enemigo.listo_para_reciclar = True
            enemigo.vida = 0
            enemigo.enabled = False # Desactiva el enemigo
            if enemigo.actor:
                enemigo.actor.hide()
            else:
                enemigo.modelo_visual.enabled = False
            self.enemigos.append(enemigo)

    def buscar_jugador(self):
        from scripts.jugador import Jugador
        from ursina import scene
        for e in scene.entities:
            if isinstance(e, Jugador):
                return e
        return None

    def update(self):
        if not self.jugador:
            self.jugador = self.buscar_jugador()
            return

        # Si el jugador avanza lo suficiente para entrar a esta arena, la sellamos
        if not self.jugador_dentro and self.jugador.z > self.limite_z + 10:
            self.jugador_dentro = True
            print("Jugador entró en la arena, cerrando puertas traseras y haciendo SPAWN...")
            for puerta in self.puertas_atras:
                if puerta:
                    puerta.cerrar()
            
            # --- SPAWN DINÁMICO ---
            import random
            from scripts.zombie import Zombie
            from scripts.villano_l import VillanoL
            from scripts.villano_o import VillanoO
            
            # 1. Spawneamos al Jefe si corresponde
            if self.jefe_class:
                # El jefe suele aparecer más al fondo (offset z = +40 o +60)
                offset_z_jefe = 60 if self.indice_arena == 3 else 40
                jefe = self.jefe_class(position=(self.centro_x, 0, self.centro_z + offset_z_jefe))
                self.enemigos.append(jefe)
                
            # 2. Activamos el contador para los enemigos normales
            self.spawns_pendientes = self.cantidad_enemigos

        # --- MANTENER HASTA 5 ENEMIGOS VIVOS (SPAWN DINÁMICO) ---
        import random
        
        # Filtramos los enemigos que siguen vivos
        vivos = [e for e in self.enemigos if e and hasattr(e, 'vida') and e.vida > 0]
        
        # Progreso de la ronda (0.0 al inicio, 1.0 al final)
        if self.cantidad_enemigos > 0:
            progreso_ronda = 1.0 - (self.spawns_pendientes / self.cantidad_enemigos)
        else:
            progreso_ronda = 1.0
            
        # Máximo de vivos permitidos (aumenta según avanza la ronda)
        # Arena 0: 2 a 6
        # Arena 1: 3 a 7
        # Arena 2: 4 a 8
        base_vivos = 2 + self.indice_arena
        max_vivos_ronda = base_vivos + int(progreso_ronda * 4) 
        
        if getattr(self, 'max_rondas', 3) == float('inf'):
            max_vivos = 15 # Survival mode post-boss
        else:
            max_vivos = max_vivos_ronda
        
        # Si faltan por spawnear y hay menos del límite de vivos en la arena
        if self.jugador_dentro and not getattr(self, 'modo_survival_activo', False) and self.spawns_pendientes > 0 and len(vivos) < max_vivos:
            import time
            if not hasattr(self, 'tiempo_inicio_ronda'):
                self.tiempo_inicio_ronda = time.time()
                
            # 5 segundos de preparación antes de que empiece a salir la horda
            if time.time() - self.tiempo_inicio_ronda < 5.0:
                return
                
            # Delay progresivo (empieza lento, se acelera hacia el final de la ronda)
            delay_base = 3.5 - self.indice_arena # Arena 0: 3.5s, Arena 1: 2.5s, Arena 2: 1.5s
            delay_spawn = max(0.5, delay_base * (1.0 - progreso_ronda))
            
            if time.time() - getattr(self, 'tiempo_ultimo_spawn', 0) < delay_spawn:
                return
                
            self.tiempo_ultimo_spawn = time.time()
            self.spawns_pendientes -= 1
            
            from scripts.zombie import Zombie
            from scripts.villano_l import VillanoL
            from scripts.villano_o import VillanoO
            
            import math
            # El Enjambre: Spawnean en un radio de 70 a 110 metros ALREDEDOR del jugador
            angulo = random.uniform(0, 2 * math.pi)
            distancia = random.uniform(70, 110)
            
            if self.jugador:
                offset_x = self.jugador.x + math.cos(angulo) * distancia
                offset_z = self.jugador.z + math.sin(angulo) * distancia
            else:
                offset_x = self.centro_x
                offset_z = self.centro_z
                
            # Limitar a los bordes de la arena para que no spawneen fuera
            min_x, max_x = self.centro_x - 180, self.centro_x + 180
            min_z, max_z = self.centro_z - 180, self.centro_z + 180
            
            pos_x = max(min_x, min(max_x, offset_x))
            pos_z = max(min_z, min(max_z, offset_z))
            
            posicion_aleatoria = (pos_x, 0, pos_z)
            rotacion_aleatoria = random.randint(0, 360)  

            # Intentar reciclar un enemigo existente antes de crear uno nuevo para evitar lag
            reciclados = [e for e in self.enemigos if getattr(e, 'listo_para_reciclar', False)]
            if reciclados:
                enemigo = random.choice(reciclados)
                enemigo.listo_para_reciclar = False
                enemigo.vida = enemigo.vida_maxima if enemigo.vida_maxima else 100
                enemigo.position = posicion_aleatoria
                enemigo.rotation_y = rotacion_aleatoria
                enemigo.curando = False
                enemigo.velocidad = 10 if type(enemigo).__name__ == 'VillanoL' else 8 if type(enemigo).__name__ == 'VillanoO' else 6
                
                from ursina import time
                enemigo.ultimo_ataque = time.time()
                enemigo.tiempo_ultimo_raycast = time.time()

                
                enemigo.enabled = True # Reactiva el enemigo completo
                
                if enemigo.actor:
                    from ursina import color
                    enemigo.actor.setColorScale(1,1,1,1)
                    enemigo.actor.show()
                    enemigo.cambiar_animacion('idle')
                else:
                    from ursina import color
                    enemigo.modelo_visual.color = color.white
                    enemigo.modelo_visual.enabled = True
            else:
                tipo_enemigo = random.choice([VillanoL, VillanoO, Zombie])
                enemigo = tipo_enemigo(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
                self.enemigos.append(enemigo)

            
            # Reevaluar vivos inmediatamente para que spawnee los 5 en un solo frame
            vivos.append(enemigo)

        # Solo si está sellado dentro empezamos a checar la victoria
        if self.jugador_dentro and not self.completada:
            
            # --- DETECCIÓN DE MUERTE DEL JEFE (MODO SUPERVIVENCIA) ---
            if self.indice_arena == 2 and self.jefe_class and not getattr(self, 'modo_survival_activo', False):
                # Buscar al jefe en la lista de enemigos
                jefe_instancia = next((e for e in self.enemigos if isinstance(e, self.jefe_class)), None)
                if jefe_instancia and hasattr(jefe_instancia, 'vida') and jefe_instancia.vida <= 0:
                    self.modo_survival_activo = True
                    self.max_rondas = float('inf')
                    if self.gestor_portal:
                        self.gestor_portal.completar_mision_jefe()
                    
                    from ursina import Text, color, destroy
                    msg = Text(text="¡VICTORIA!\n<red>MODO SUPERVIVENCIA ACTIVADO", origin=(0, 0), scale=4, y=0.2)
                    msg.animate_color(color.rgba(255, 0, 0, 0), duration=5, delay=3.0)
                    destroy(msg, delay=8.5)
            
            if len(vivos) == 0 and self.spawns_pendientes <= 0:
                if not hasattr(self, 'ronda_actual'):
                    self.ronda_actual = 1
                    
                if not hasattr(self, 'max_rondas'):
                    self.max_rondas = 3
                
                # Drop de Pieza (Misión RECOLECTAR) al superar una ronda (si no es infinita)
                if self.gestor_portal and self.gestor_portal.tipo_mision == "RECOLECTAR" and self.ronda_actual <= 5:
                    from scripts.pieza import PiezaPortal
                    modelos_piezas = [
                        ("Carcasa", "assets/modelos/carcasa_reducida.glb"),
                        ("Pinzas", "assets/modelos/pinzas.glb"),
                        ("Emisor", "assets/modelos/emisor_portal.glb"),
                        ("Base", "assets/modelos/base_trasera.glb"),
                        ("Lateral", "assets/modelos/Carcasa_lateral.glb")
                    ]
                    # Soltar una pieza diferente cada ronda cerca del jugador
                    idx = min(self.ronda_actual - 1, len(modelos_piezas)-1)
                    nombre, modelo = modelos_piezas[idx]
                    
                    # Dropear frente al jugador
                    pos_drop = self.jugador.position + self.jugador.forward * 3
                    pos_drop.y = 1
                    PiezaPortal(nombre_pieza=nombre, modelo_path=modelo, position=pos_drop, gestor=self.gestor_portal)
                    print(f"Pieza {nombre} dropeada tras superar la ronda {self.ronda_actual}")

                if self.ronda_actual < self.max_rondas:
                    self.ronda_actual += 1
                    # Incrementamos dificultad agresivamente en modo survival
                    if getattr(self, 'modo_survival_activo', False):
                        self.spawns_pendientes = self.cantidad_enemigos + (self.ronda_actual * 5)
                    else:
                        self.spawns_pendientes = self.cantidad_enemigos + (self.ronda_actual * 2)
                        
                    print(f"¡Inicia Ronda {self.ronda_actual}!")
                    import time
                    self.tiempo_inicio_ronda = time.time()
                    from ursina import Text, color, destroy
                    texto_ronda = Text(text=f"¡Ronda {self.ronda_actual} Iniciada!\n<white>Prepárate, aquí viene la horda...", origin=(0, 0), scale=4, color=color.red, y=0.1)
                    texto_ronda.animate_color(color.rgba(255, 0, 0, 0), duration=4, delay=2.0)
                    texto_ronda.animate_scale(4.5, duration=3)
                    destroy(texto_ronda, delay=3.5)
                else:
                    self.completada = True
                    print("¡Arena despejada! Abriendo puertas frontales y siguiente arena...")
                    
                    # --- ABRIR PUERTAS TRASERAS DE LA SIGUIENTE ARENA ---
                    import __main__ as main
                    if hasattr(main, 'gestores_arena'):
                        if self.indice_arena + 1 < len(main.gestores_arena):
                            sig_gestor = main.gestores_arena[self.indice_arena + 1]
                            for p in sig_gestor.puertas_atras:
                                if p:
                                    p.abrir()
                    
                    for puerta in self.puertas_frente:
                        if puerta:
                            puerta.abrir()

        # --- SELLAR ARENA AL SALIR Y ELIMINAR CADÁVERES ---
        # Si la arena fue completada, revisamos si el jugador ya salió hacia el patio.
        # La puerta frontal está en limite_z + 400. 
        if self.completada and not getattr(self, 'jugador_salio', False):
            if self.jugador.z > self.limite_z + 410:
                self.jugador_salio = True
                print(f"Jugador abandonó la arena {self.indice_arena}, sellando puertas frontales.")
                for puerta in self.puertas_frente:
                    if puerta:
                        puerta.cerrar()
                
                # --- OPTIMIZACIÓN EXTREMA Y LORE INTERDIMENSIONAL ---
                from ursina import destroy
                
                # 1. Destruimos físicamente a los enemigos muertos para liberar RAM.
                for enemigo in self.enemigos:
                    if enemigo:
                        destroy(enemigo)
                self.enemigos.clear()
                
                # 2. Destruimos físicamente la carpeta entera de la Arena (muros, pisos, árboles). 
                # Cero uso de VRAM de partes que ya no puedes ver.
                import __main__ as main
                if hasattr(main, 'coordinador'):
                    chunk = main.coordinador.chunks_arenas[self.indice_arena]
                    if chunk:
                        destroy(chunk)
                        main.coordinador.chunks_arenas[self.indice_arena] = None
                        
                # 3. Lore Animado: Hacemos creer al jugador que el mapa desapareció por razones de la historia
                from ursina import Text, color
                lore_msg = Text(text=f"<magenta>PLANTA {self.indice_arena} DEL EDIFICIO NEXUS\n<white>HA VUELTO A SU DIMENSIÓN ORIGINAL.", 
                                origin=(0, 0), scale=2.5, y=0.2)
                lore_msg.animate_color(color.rgba(255, 255, 255, 0), duration=4, delay=3)
                destroy(lore_msg, delay=8)
