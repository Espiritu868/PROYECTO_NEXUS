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
        
        # --- POOL OPTIMIZADO O(1) ---
        self.enemigos_reciclables = []
        
        # --- PRE-LOAD POOL DE ENEMIGOS (Evita congelamiento mid-game) ---
        # Instanciamos 15 enemigos por arena durante la pantalla de carga para evitar lag
        import random
        from scripts.zombie import Zombie
        from scripts.villano_l import VillanoL
        from scripts.villano_o import VillanoO
        
        for _ in range(15):
            tipo_enemigo = random.choice([VillanoL, VillanoO, Zombie])
            # Se spawnean bajo tierra muy profundo para activar el culling espacial (>1000)
            enemigo = tipo_enemigo(position=(0, -2000, 0), rotation_y=0)
            enemigo.gestor_padre = self
            enemigo.listo_para_reciclar = True
            enemigo.vida = 0
            enemigo.enabled = False # Desactiva el enemigo
            if enemigo.actor:
                enemigo.actor.hide()
            else:
                enemigo.modelo_visual.enabled = False
            self.enemigos.append(enemigo)
            self.enemigos_reciclables.append(enemigo)

    def buscar_jugador(self):
        from scripts.jugador import Jugador
        return Jugador.instancia

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
                jefe.gestor_padre = self
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
            
        # Límite estricto de BO2: Máximo 24 zombies vivos en el mapa
        max_vivos = 24
        
        # Si faltan por spawnear y hay menos del límite de vivos en la arena
        if self.jugador_dentro and not getattr(self, 'modo_survival_activo', False) and self.spawns_pendientes > 0 and len(vivos) < max_vivos:
            import time
            if not hasattr(self, 'tiempo_inicio_ronda'):
                self.tiempo_inicio_ronda = time.time()
                
            # 5 segundos de preparación antes de que empiece a salir la horda
            if time.time() - self.tiempo_inicio_ronda < 5.0:
                return
                
            # Spawn Delay basado en Rondas (Estilo Black Ops 2)
            ronda = getattr(self, 'ronda_actual', 1)
            if ronda <= 15:
                delay_spawn = 3.0 # Entre 2 y 4 segundos
            elif ronda < 64:
                # Se reduce drásticamente (ej. 1s en ronda 20, 0.2s en ronda 50)
                delay_spawn = max(0.1, 2.0 - ((ronda - 15) * 0.05))
            else:
                delay_spawn = 0.0 # Ronda 64+: Instantáneo
            
            if time.time() - getattr(self, 'tiempo_ultimo_spawn', 0) < delay_spawn:
                return
                
            self.tiempo_ultimo_spawn = time.time()
            self.spawns_pendientes -= 1
            
            from scripts.zombie import Zombie
            from scripts.villano_l import VillanoL
            from scripts.villano_o import VillanoO
            
            import math
            posicion_aleatoria = None
            for _ in range(10): # Intentar hasta 10 veces encontrar posición válida
                angulo = random.uniform(0, 2 * math.pi)
                distancia = random.uniform(15, 30) # Spawnean mucho más cerca del jugador
                
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
                
                # Prevenir spawn dentro de los muros (AABB simple para los muros internos de la arena)
                rel_x = pos_x - self.centro_x
                rel_z = pos_z - self.centro_z
                
                en_muro = False
                margen = 5 # Margen de seguridad para no pegarse a los muros
                
                # Check Muros horizontales (Eje X)
                if (-200 - margen <= rel_x <= -50 + margen) or (50 - margen <= rel_x <= 200 + margen):
                    if (-100 - 1 - margen <= rel_z <= -100 + 1 + margen): en_muro = True
                    if (100 - 1 - margen <= rel_z <= 100 + 1 + margen): en_muro = True
                if (-170 - margen <= rel_x <= -50 + margen) or (50 - margen <= rel_x <= 170 + margen):
                    if (-1 - margen <= rel_z <= 1 + margen): en_muro = True
                    
                # Check Muros verticales (Eje Z)
                if (-100 - 1 - margen <= rel_x <= -100 + 1 + margen):
                    if (-150 - margen <= rel_z <= 50 + margen): en_muro = True
                if (100 - 1 - margen <= rel_x <= 100 + 1 + margen):
                    if (-50 - margen <= rel_z <= 150 + margen): en_muro = True
                    
                if not en_muro:
                    posicion_aleatoria = (pos_x, 0, pos_z)
                    break
            
            if not posicion_aleatoria:
                # Fallback al centro (el centro está vacío)
                posicion_aleatoria = (self.centro_x, 0, self.centro_z)
                
            rotacion_aleatoria = random.randint(0, 360)

            ronda_actual = getattr(self, 'ronda_actual', 1)
            
            # O(1) POOL: Intentar reciclar un enemigo existente sacándolo de la lista
            enemigo_a_reciclar = None
            if self.enemigos_reciclables:
                # Restringir la aparición de Zombies locos antes de la ronda 3
                if ronda_actual < 3:
                    for idx, e in enumerate(self.enemigos_reciclables):
                        if type(e).__name__ != 'Zombie':
                            enemigo_a_reciclar = self.enemigos_reciclables.pop(idx)
                            break
                else:
                    enemigo_a_reciclar = self.enemigos_reciclables.pop()
                
            if enemigo_a_reciclar:
                enemigo = enemigo_a_reciclar
                enemigo.listo_para_reciclar = False
                enemigo.vida = enemigo.vida_maxima if enemigo.vida_maxima else 100
                enemigo.position = posicion_aleatoria
                enemigo.rotation_y = rotacion_aleatoria
                enemigo.curando = False
                if type(enemigo).__name__ == 'VillanoL':
                    enemigo.velocidad = 5.8
                elif type(enemigo).__name__ == 'VillanoO':
                    enemigo.velocidad_normal = 3.5
                    enemigo.velocidad = 3.5
                elif type(enemigo).__name__ == 'Zombie':
                    enemigo.velocidad_normal = 9.0
                    enemigo.velocidad = 9.0
                    enemigo.frenesi = False
                
                from ursina import time
                import random
                enemigo.ultimo_ataque = time.time()
                enemigo.tiempo_ultimo_raycast = time.time() - random.uniform(0.0, 0.2)

                
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
                    
                if hasattr(enemigo, 'emerger'):
                    enemigo.emerger()
            else:
                opciones = [VillanoL, VillanoO]
                if getattr(self, 'ronda_actual', 1) >= 3:
                    opciones.append(Zombie)
                    
                tipo_enemigo = random.choice(opciones)
                enemigo = tipo_enemigo(position=posicion_aleatoria, rotation_y=rotacion_aleatoria)
                enemigo.gestor_padre = self
                self.enemigos.append(enemigo)
                
                if hasattr(enemigo, 'emerger'):
                    enemigo.emerger()

            
            # Reevaluar vivos inmediatamente para que spawnee los 5 en un solo frame
            vivos.append(enemigo)

        # Solo si está sellado dentro empezamos a checar el final de la ronda
        if self.jugador_dentro and not getattr(self, 'completada', False):
            
            if len(vivos) == 0 and self.spawns_pendientes <= 0:
                if not hasattr(self, 'ronda_actual'):
                    self.ronda_actual = 1
                    
                self.max_rondas = float('inf')
                
                self.ronda_actual += 1
                self.spawns_pendientes = self.cantidad_enemigos + (self.ronda_actual * 5)
                
                print(f"¡Inicia Ronda {self.ronda_actual}!")
                
                # --- SISTEMA DE SPAWN DE JEFES CÍCLICOS ---
                if self.ronda_actual % 5 == 0:
                    ciclo = (self.ronda_actual - 1) // 20
                    multiplicador_vida = 1.0 + (0.10 * ciclo)
                    
                    jefe_spawn = None
                    vida_base = 0
                    
                    if self.ronda_actual % 20 == 5:
                        from scripts.golem import GolemBoss
                        jefe_spawn = GolemBoss
                        vida_base = 1000
                    elif self.ronda_actual % 20 == 10:
                        # BRUJA DESACTIVADA - USANDO GOLEM TEMPORALMENTE
                        from scripts.golem import GolemBoss
                        jefe_spawn = GolemBoss
                        vida_base = 1200
                    elif self.ronda_actual % 20 == 15:
                        # KNIGHT DESACTIVADO - USANDO GOLEM TEMPORALMENTE
                        from scripts.golem import GolemBoss
                        jefe_spawn = GolemBoss
                        vida_base = 1500
                    elif self.ronda_actual % 20 == 0:
                        # DRAGON DESACTIVADO - USANDO GOLEM TEMPORALMENTE
                        from scripts.golem import GolemBoss
                        jefe_spawn = GolemBoss
                        vida_base = 2000
                        
                    if jefe_spawn:
                        pos_jefe = (self.centro_x, 0, self.centro_z)
                        vida_final = vida_base * multiplicador_vida
                        print(f"SPAWN DE JEFE: {jefe_spawn.__name__} con {vida_final} HP")
                        
                        nuevo_jefe = jefe_spawn(position=pos_jefe, vida_maxima_override=vida_final)
                        nuevo_jefe.gestor_padre = self
                        self.enemigos.append(nuevo_jefe)
                        if hasattr(nuevo_jefe, 'emerger'):
                            nuevo_jefe.emerger()
                    
                    import __main__ as main
                    if hasattr(main, 'power_up_service') and main.power_up_service:
                        main.power_up_service.iniciar_siguiente_ronda()
                        
                    import time
                    self.tiempo_inicio_ronda = time.time()
                    
                    try:
                        from ursina import Audio
                        Audio('assets/sonidos/intro de rondas.mp3', autoplay=True)
                    except:
                        pass
                        
                    from ursina import Text, color, destroy
                    texto_ronda = Text(text=f"¡Ronda {self.ronda_actual} Iniciada!\n<white>Prepárate, aquí viene la horda...", origin=(0, 0), scale=4, color=color.red, y=0.1)
                    texto_ronda.animate_color(color.rgba(255, 0, 0, 0), duration=4, delay=2.0)
                    texto_ronda.animate_scale(4.5, duration=3)
                    destroy(texto_ronda, delay=3.5)
                # Eliminamos la condición del 'else' para terminar arenas
                # Ya que las rondas son infinitas.

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
