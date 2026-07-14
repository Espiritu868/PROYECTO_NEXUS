from direct.showbase.ShowBase import ShowBase
import sys

app = ShowBase()
model = app.loader.loadModel("assets/modelos/villians/golem/Creature Pack/mutant idle.glb")
print(f"Bounds: {model.getBounds()}")
print(f"Scale: {model.getScale()}")
print(f"Scale: {model.getScale()}")
sys.exit()
