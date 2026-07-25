from ursina import *
app = Ursina()
window.fullscreen = False
window.size = (1920, 1200)

image_path = f"scripts/backgrounds/back1.png"
textura = load_texture(image_path)

p = Sprite(
    texture=textura,
    parent=camera.ui,
    z=-1
)
ratio = textura.width / textura.height
factor = min(window.aspect_ratio / (textura.width/100), 1 / (textura.height/100))
p.scale = (p.scale_x * factor, p.scale_y * factor)

def capture_and_quit():
    base.screenshot("debug_shot.png", defaultFilename=False)
    application.quit()

invoke(capture_and_quit, delay=1)
app.run()
