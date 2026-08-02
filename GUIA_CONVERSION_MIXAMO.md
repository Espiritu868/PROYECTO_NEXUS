# GUÍA DEFINITIVA: CONVERSIÓN DE ANIMACIONES MIXAMO A GLB PARA URSINA/PANDA3D

Esta es una bitácora técnica para que el Agente IA (o tú) recuerde exactamente cómo procesar animaciones de Mixamo (FBX) para integrarlas en el juego Nexus.

## 1. El Problema de los "Packs" de Mixamo
- **El bug:** Cuando descargas un "Pack" de animaciones en Mixamo (ej. Pro Rifle Pack), los archivos `.fbx` que vienen en el ZIP **NO contienen la malla (mesh)** del personaje, solo contienen el esqueleto (Armature) animado. 
- **La solución:** Debes descargar el personaje base desde Mixamo en pose T o Idle asegurándote de marcar la opción "Con Skin". De ese archivo base extraemos el modelo 3D estático (`sas_modelo.glb`). Las animaciones se exportarán por separado (`sas_run.glb`, `sas_walk.glb`).

## 2. Texturas y Materiales
- Si el FBX viene sin texturas integradas, Blender creará materiales vacíos o incorrectos.
- Hay que crear un script en Blender (o hacerlo manualmente) que asigne las texturas (`.png` de diffuse, normal, roughness, metallic) a los nodos `Principled BSDF` del material antes de exportar a GLB.

## 3. El Problema del "Root Motion" (El personaje no vuelve al centro)
- **El bug:** Animaciones como correr, caminar o saltar de Mixamo a menudo desplazan físicamente al esqueleto hacia adelante (Root Motion). Si las usas tal cual en Ursina, el personaje se desfasará de su "Collider" físico, y al terminar la animación se teletransportará de vuelta al origen.
- **La solución (In-Place):** Escribimos un script de Python para Blender (`make_in_place.py`).
  - Identificamos el hueso maestro: Usualmente `mixamorig:Hips`.
  - Recorremos todos los `keyframes` de la curva de animación de localización (`location`).
  - **Eje X (0) y Eje Z (2):** Sobrescribimos su valor con el valor del fotograma inicial (congelamos el movimiento horizontal y frontal).
  - **Eje Y (1):** ¡MUY IMPORTANTE! Dejamos intacto el Eje Y (arriba/abajo) para que el personaje conserve el rebote natural del cuerpo (el "bobbing") al correr o agacharse.

## 4. Ejecución Headless en Blender
- No es necesario abrir la interfaz de Blender para hacer conversiones masivas.
- Usamos el terminal para ejecutar scripts en segundo plano:
  `"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python make_in_place.py`

## 5. Exportación a GLB
- En el script, tras limpiar el Root Motion, seleccionamos el Armature y usamos:
  `bpy.ops.export_scene.gltf(filepath="sas_run.glb", export_format='GLB', export_animations=True)`
- Ursina/Panda3D carga de forma nativa los `.glb` usando `Actor()`.

## 6. Integración en Ursina (jugador.py)
- En Ursina cargamos el modelo base y le inyectamos un diccionario de animaciones independientes:
  ```python
  self.actor = Actor("sas_modelo.glb", {
      "idle": "sas_idle.glb",
      "run": "sas_run.glb",
      "jump": "sas_jump.glb"
  })
  ```
- Es importante ajustar `self.actor.setBlend(frameBlend=True)` para que las transiciones entre animaciones sean suaves.

---
**Nota para el Agente IA:** Si el usuario te pide añadir más animaciones en el futuro, lee este archivo primero. Para convertir nuevas animaciones a "In-Place", usa la lógica de congelar `fcurve.data_path == 'location'` en los array_index 0 y 2 del hueso `Hips`.
