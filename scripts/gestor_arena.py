from ursina import Entity

class GestorArena(Entity):
    def __init__(self, enemigos, puertas_frente, puertas_atras, limite_z, indice_arena, **kwargs):
        super().__init__(**kwargs)
        self.enemigos = enemigos
        self.puertas_frente = puertas_frente
        self.puertas_atras = puertas_atras
        self.limite_z = limite_z
        self.indice_arena = indice_arena
        self.completada = False
        self.jugador_dentro = False
        self.jugador = None

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
            print("Jugador entró en la arena, cerrando puertas traseras...")
            for puerta in self.puertas_atras:
                if puerta:
                    puerta.cerrar()

        # Solo si está sellado dentro empezamos a checar la victoria
        if self.jugador_dentro and not self.completada:
            vivos = []
            for e in self.enemigos:
                if e and hasattr(e, 'vida') and e.vida > 0:
                    vivos.append(e)
            
            if len(vivos) == 0:
                self.completada = True
                print("¡Arena despejada! Abriendo puertas frontales y siguiente arena...")
                
                # --- ABRIR PUERTAS TRASERAS DE LA SIGUIENTE ARENA ---
                import main
                if hasattr(main, 'gestores_arena'):
                    if self.indice_arena + 1 < len(main.gestores_arena):
                        sig_gestor = main.gestores_arena[self.indice_arena + 1]
                        for p in sig_gestor.puertas_atras:
                            if p:
                                p.abrir()
                
                # --- UI: Texto Animado ---
                from ursina import Text, color, destroy
                texto = Text(text="¡ZONA DESPEJADA!", origin=(0, 0), scale=3, color=color.azure, y=0.1)
                texto.animate_color(color.rgba(0, 128, 255, 0), duration=3, delay=1.5)
                texto.animate_scale(4, duration=3)
                destroy(texto, delay=4.5)
                
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
                import main
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
