from ursina import Entity

class GestorArena(Entity):
    def __init__(self, jefe_class, cantidad_enemigos, centro_x, centro_z, puertas_frente, puertas_atras, limite_z, indice_arena, **kwargs):
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
        self.completada = False
        self.jugador_dentro = False
        self.jugador = None
        
        # Variables para spawn gradual
        self.spawns_pendientes = 0
        self.tiempo_ultimo_spawn = 0

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
        
        # Si faltan por spawnear y hay menos de 5 vivos en la arena
        if self.jugador_dentro and not self.completada and self.spawns_pendientes > 0 and len(vivos) < 5:
            self.spawns_pendientes -= 1
            
            from scripts.zombie import Zombie
            from scripts.villano_l import VillanoL
            from scripts.villano_o import VillanoO
            
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
            
            while True:
                # Los primeros 5 enemigos se generan relativamente cerca del jugador
                if len(self.enemigos) <= 5: 
                    rx = random.choice([random.randint(-60, -30), random.randint(30, 60)])
                    rz = random.choice([random.randint(-60, -30), random.randint(30, 60)])
                else:
                    # Los siguientes (cuando matas a uno) se generan más lejos
                    rx = random.choice([random.randint(-150, -80), random.randint(80, 150)])
                    rz = random.choice([random.randint(-150, -80), random.randint(80, 150)])
                    
                if self.jugador:
                    # Posición relativa al centro de la arena pero basada en donde está el jugador
                    offset_x = (self.jugador.x - self.centro_x) + rx
                    offset_z = (self.jugador.z - self.centro_z) + rz
                else:
                    offset_x = rx
                    offset_z = rz
                    
                # Asegurarnos de que no spawneen fuera de los límites de la arena (-200 a 200)
                offset_x = max(-180, min(180, offset_x))
                offset_z = max(-180, min(180, offset_z))
                
                if es_posicion_valida(offset_x, offset_z):
                    break
                    
            posicion_aleatoria = (self.centro_x + offset_x, 0, self.centro_z + offset_z)
            rotacion_aleatoria = random.randint(0, 360) 

            tipo_enemigo = random.choice([VillanoL, VillanoO, Zombie])
            enemigo = tipo_enemigo(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
            self.enemigos.append(enemigo)
            
            # Reevaluar vivos inmediatamente para que spawnee los 5 en un solo frame
            vivos.append(enemigo)

        # Solo si está sellado dentro empezamos a checar la victoria
        if self.jugador_dentro and not self.completada:
            
            if len(vivos) == 0:
                if not hasattr(self, 'ronda_actual'):
                    self.ronda_actual = 1
                    
                if not hasattr(self, 'max_rondas'):
                    self.max_rondas = 3
                
                if self.ronda_actual < self.max_rondas:
                    self.ronda_actual += 1
                    # Incrementamos un poco la dificultad cada ronda sumando 2 enemigos extra
                    self.spawns_pendientes = self.cantidad_enemigos + (self.ronda_actual * 2)
                    print(f"¡Inicia Ronda {self.ronda_actual}!")
                    from ursina import Text, color, destroy
                    texto_ronda = Text(text=f"¡RONDA {self.ronda_actual}!", origin=(0, 0), scale=4, color=color.red, y=0.1)
                    texto_ronda.animate_color(color.rgba(255, 0, 0, 0), duration=2, delay=1.0)
                    texto_ronda.animate_scale(5, duration=2)
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
