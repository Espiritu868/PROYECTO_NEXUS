from ursina import Entity, load_texture

class Villano(Entity):
    def __init__(self, tipo='l', **kwargs):
        super().__init__(**kwargs)
        
        # --- 1. DIBUJADO CRUDO (Ignorando rutas largas) ---
        # Al pasarle solo el nombre, Ursina lo busca en todas tus carpetas automáticamente
        self.modelo_visual = Entity(
            parent=self,
            model=f'assets/modelos/character-l.fbx', 
            scale=(0.01, 0.01, 0.01),
            rotation_y=0
        )
        
        # --- 2. EL RAYO LÁSER TEXTURIZADOR (OVERRIDE) ---
        # Hacemos lo mismo con la imagen, buscando solo el nombre del archivo
        textura_real = load_texture(f'assets/modelos/textures/texture-l.png')
        
        if textura_real:
            # Forzamos la textura para matar el material vacío (adiós al modelo blanco)
            self.modelo_visual.set_texture(textura_real._texture, 1)
        else:
            print(f"❌ Advertencia: No se encontró la textura para el villano {tipo}")
            
        # --- 3. COLISIONADOR ESTÁTICO ---
        self.collider = 'box'