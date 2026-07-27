from ursina import Entity, Button, Text, color, mouse, camera, held_keys, Vec3, BoxCollider, invoke, destroy, time

import os

class ObjetoEditor(Entity):
    def __init__(self, modelo_path, **kwargs):
        super().__init__(model=modelo_path, collider='box', **kwargs)
        self.modelo_path = modelo_path
        self.es_seleccionado = False
        self.color_original = color.white

    def on_click(self):
        # Cuando el usuario hace click en un objeto colocado, se selecciona
        if hasattr(self.parent_editor, 'seleccionar_objeto'):
            self.parent_editor.seleccionar_objeto(self)

class EditorNivel(Entity):
    def __init__(self, jugador):
        super().__init__(ignore_paused=True) # El editor debe funcionar incluso si pausamos
        self.jugador = jugador
        self.activo = False
        
        self.objeto_fantasma = None
        self.modelo_actual_path = None
        
        self.objeto_seleccionado = None
        self.objetos_colocados = []
        
        self.ruta_modelos = 'assets/modelos/objetos_con_meshy'
        self.modelos = []
        if os.path.exists(self.ruta_modelos):
            self.modelos = [f for f in os.listdir(self.ruta_modelos) if f.endswith('.glb') or f.endswith('.obj')]
        self.indice_modelo = 0
        
        self.crear_interfaz()
        self.ui_padre.enabled = False

    def crear_interfaz(self):
        self.ui_padre = Entity(parent=camera.ui, z=-1)
        
        Text(parent=self.ui_padre, text="MODO EDITOR DE NIVELES", position=(-0.82, 0.45), scale=1.5, color=color.cyan)
        
        # Texto para mostrar el modelo actual
        self.texto_modelo = Text(parent=self.ui_padre, text="Modelo: Ninguno", position=(-0.82, 0.35), scale=1.3, color=color.green)
        
        # --- INSTRUCCIONES EN PANTALLA ---
        texto_instrucciones = """
CONTROLES DEL EDITOR:
[F4] - Abrir/Cerrar Editor
[Flecha Izq / Der] - Cambiar Objeto
[Click Izq] - Colocar objeto
[Click Der] - Cancelar / Deseleccionar
[R / F] - Rotar (Eje Y)
[Y / H] - Rotar (Eje X)
[U / J] - Rotar (Eje Z)
[T / G] - Escalar objeto
[Suprimir] - Eliminar objeto apuntado/seleccionado
[C] - Copiar objeto apuntado/seleccionado
[Enter] - Exportar Mapa
        """
        Text(parent=self.ui_padre, text=texto_instrucciones, position=(0.3, 0.45), scale=1.2, color=color.yellow)

    def seleccionar_modelo(self, nombre_archivo):
        # Si ya teníamos un fantasma, lo borramos
        if self.objeto_fantasma:
            destroy(self.objeto_fantasma)
            
        self.modelo_actual_path = f"{self.ruta_modelos}/{nombre_archivo}"
        self.texto_modelo.text = f"Modelo:\\n{nombre_archivo}"
        
        # Crear objeto fantasma anclado a la cámara (estático en la vista)
        self.objeto_fantasma = Entity(
            model=self.modelo_actual_path, 
            color=color.rgba(100, 255, 100, 150), 
            collider=None,
            parent=camera,
            position=(0, 0, 10) # 10 unidades frente a la cámara
        )
        
    def seleccionar_objeto(self, obj):
        if not self.activo: return
        self.deseleccionar_todo()
        self.objeto_seleccionado = obj
        obj.es_seleccionado = True
        obj.color = color.cyan

    def deseleccionar_todo(self):
        if self.objeto_seleccionado:
            self.objeto_seleccionado.color = self.objeto_seleccionado.color_original
            self.objeto_seleccionado.es_seleccionado = False
            self.objeto_seleccionado = None

    def update(self):
        if not self.activo:
            return
            
        # El objeto fantasma ya sigue a la cámara automáticamente porque parent=camera.
        # Solo aplicamos rotación o escala si existe.
        if self.objeto_fantasma:
            self.aplicar_transformaciones(self.objeto_fantasma)
            
        # Aplicar transformaciones al objeto seleccionado
        elif self.objeto_seleccionado:
            self.aplicar_transformaciones(self.objeto_seleccionado)

    def aplicar_transformaciones(self, obj):
        # Rotación Y (Izquierda / Derecha)
        if held_keys['r']:
            obj.rotation_y += 100 * time.dt
        if held_keys['f']:
            obj.rotation_y -= 100 * time.dt
            
        # Rotación X (Frente / Atrás)
        if held_keys['y']:
            obj.rotation_x += 100 * time.dt
        if held_keys['h']:
            obj.rotation_x -= 100 * time.dt
            
        # Rotación Z (Inclinación Lateral)
        if held_keys['u']:
            obj.rotation_z += 100 * time.dt
        if held_keys['j']:
            obj.rotation_z -= 100 * time.dt
            
        # Escala
        if held_keys['t']:
            obj.scale += Vec3(1, 1, 1) * 2 * time.dt
        if held_keys['g']:
            obj.scale -= Vec3(1, 1, 1) * 2 * time.dt
            # Evitar escalas negativas
            if obj.scale_x < 0.1: obj.scale = Vec3(0.1, 0.1, 0.1)

    def input(self, key):
        if key == 'f4':
            self.toggle_editor()
            return
            
        if not self.activo:
            return
            
        # Cambiar de objeto con flechas
        if key == 'right arrow' and self.modelos:
            self.indice_modelo = (self.indice_modelo + 1) % len(self.modelos)
            self.seleccionar_modelo(self.modelos[self.indice_modelo])
            
        if key == 'left arrow' and self.modelos:
            self.indice_modelo = (self.indice_modelo - 1) % len(self.modelos)
            self.seleccionar_modelo(self.modelos[self.indice_modelo])
            
        # Exportar mapa
        if key == 'enter':
            self.exportar_mapa()
            
        # Colocar objeto
        if key == 'left mouse down' and self.objeto_fantasma:
            # Crear el objeto real en la posición mundial del fantasma
            nuevo_obj = ObjetoEditor(
                modelo_path=self.modelo_actual_path, 
                position=self.objeto_fantasma.world_position,
                rotation=self.objeto_fantasma.world_rotation,
                scale=self.objeto_fantasma.world_scale
            )
            nuevo_obj.parent_editor = self
            self.objetos_colocados.append(nuevo_obj)
            
            # NOTA: Ya no destruimos el fantasma para que puedas seguir colocando más copias del mismo modelo.
            # (El click derecho sigue sirviendo para cancelar/limpiar la selección).
            
        # Cancelar / Deseleccionar
        if key == 'right mouse down':
            if self.objeto_fantasma:
                destroy(self.objeto_fantasma)
                self.objeto_fantasma = None
                self.modelo_actual_path = None
                self.texto_modelo.text = "Modelo: Ninguno"
            elif self.objeto_seleccionado:
                self.deseleccionar_todo()
                
        # Eliminar
        if key == 'delete' or key == 'backspace':
            if self.objeto_seleccionado:
                if self.objeto_seleccionado in self.objetos_colocados:
                    self.objetos_colocados.remove(self.objeto_seleccionado)
                destroy(self.objeto_seleccionado)
                self.objeto_seleccionado = None
            elif isinstance(mouse.hovered_entity, ObjetoEditor):
                if mouse.hovered_entity in self.objetos_colocados:
                    self.objetos_colocados.remove(mouse.hovered_entity)
                destroy(mouse.hovered_entity)
            
        # Copiar
        if key == 'c' and self.objeto_seleccionado:
            self.modelo_actual_path = self.objeto_seleccionado.modelo_path
            self.texto_modelo.text = f"Modelo (Copiado):\\n{self.modelo_actual_path.split('/')[-1]}"
            self.objeto_fantasma = Entity(
                model=self.modelo_actual_path, 
                color=color.rgba(100, 255, 100, 150), 
                collider=None,
                parent=camera,
                position=(0, 0, 10),
                rotation=self.objeto_seleccionado.rotation,
                scale=self.objeto_seleccionado.scale
            )
            self.deseleccionar_todo()

    def toggle_editor(self):
        self.activo = not self.activo
        self.ui_padre.enabled = self.activo
        
        if self.activo:
            # Ya no liberamos el mouse, lo mantenemos bloqueado para poder mirar
            if self.modelos:
                self.seleccionar_modelo(self.modelos[self.indice_modelo])
        else:
            self.deseleccionar_todo()
            if self.objeto_fantasma:
                destroy(self.objeto_fantasma)
                self.objeto_fantasma = None
                self.modelo_actual_path = None
                self.texto_modelo.text = "Modelo: Ninguno"

    def exportar_mapa(self):
        print("\n--- EXPORTANDO MAPA ---")
        codigo_exportado = "# COPIA ESTE CÓDIGO Y PÁSALO AL ASISTENTE\\n"
        for obj in self.objetos_colocados:
            p = obj.position
            r = obj.rotation
            s = obj.scale
            
            # Redondear para limpiar código
            pos = f"({p.x:.2f}, {p.y:.2f}, {p.z:.2f})"
            rot = f"({r.x:.2f}, {r.y:.2f}, {r.z:.2f})"
            scl = f"({s.x:.2f}, {s.y:.2f}, {s.z:.2f})"
            
            linea = f"Entity(parent=padre_decoracion, model='{obj.modelo_path}', position={pos}, rotation={rot}, scale={scl}, collider='box')"
            codigo_exportado += linea + "\\n"
            
        with open('layout_exportado.txt', 'w') as f:
            f.write(codigo_exportado)
            
        print("¡Mapa exportado a layout_exportado.txt!")
        # Notificación en pantalla
        notif = Text(text="¡Exportado con éxito a layout_exportado.txt!", origin=(0,0), scale=2, color=color.green, y=0.3)
        invoke(destroy, notif, delay=3)
