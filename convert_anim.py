import bpy
import sys

# Argumentos pasados después de "--"
argv = sys.argv
if "--" not in argv:
    argv = []
else:
    argv = argv[argv.index("--") + 1:]

if len(argv) < 2:
    print("Faltan argumentos. Uso: blender --background --python convert_anim.py -- <input.fbx> <output.glb>")
    sys.exit(1)

input_file = argv[0]
output_file = argv[1]

# Limpiar escena por defecto (cámara, cubo, luz)
bpy.ops.wm.read_factory_settings(use_empty=True)

# Importar FBX
bpy.ops.import_scene.fbx(filepath=input_file)

# Buscar armature
armature = None
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        armature = obj
        break

if not armature:
    print("No se encontró ningún armature en el FBX.")
    sys.exit(1)

# No procesamos fcurves para esta animación (es idle)

# Seleccionar el armature y exportar GLB
bpy.ops.object.select_all(action='DESELECT')
armature.select_set(True)
bpy.context.view_layer.objects.active = armature

# Ursina usa animaciones en la armature. Podemos no exportar el mesh para ahorrar espacio
bpy.ops.export_scene.gltf(
    filepath=output_file,
    export_format='GLB',
    use_selection=True,
    export_animations=True,
    export_materials='NONE'
)

print(f"Exportación exitosa: {output_file}")
