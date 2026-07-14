from direct.showbase.ShowBase import ShowBase
import sys

app = ShowBase()
model = app.loader.loadModel("assets/modelos/villians/golem/5000_Faces/Walk Backward.fbx")
print(f"Bounds: {model.getBounds()}")
sys.exit()
