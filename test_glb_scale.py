from direct.showbase.ShowBase import ShowBase
import sys

app = ShowBase()
model = app.loader.loadModel("assets/modelos/villians/golem/Creature Pack/cuerpo_base.glb")
print(f"Bounds: {model.getBounds()}")
sys.exit()
