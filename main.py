import sys
import glfw as gl
import moderngl

from controles.contoles_eventos import Controles
from objetos.Player import Player


class Game:

  def __init__(self, largura=1280, altura=720):
    gl.init()

    gl.window_hint(gl.CONTEXT_VERSION_MAJOR, 3)
    gl.window_hint(gl.CONTEXT_VERSION_MINOR, 3)
    gl.window_hint(gl.OPENGL_PROFILE, gl.OPENGL_CORE_PROFILE)
    gl.window_hint(gl.OPENGL_FORWARD_COMPAT, True)
    gl.window_hint(gl.DEPTH_BITS, 24)

    self.window = gl.create_window(largura, altura, "RunLight", None, None)
    if not self.window:
      gl.terminate()
      return

    gl.make_context_current(self.window)

    self.ctx = moderngl.create_context()
    self.ctx.enable(moderngl.DEPTH_TEST)

    self.controles = Controles(self.window)

    self.player = Player(self.ctx)

    self.ultimo_tempo = gl.get_time()
    self.delta_time = 0.0

  def tratar_eventos(self):
    gl.poll_events()

    if self.controles.sair_jogo or gl.window_should_close(self.window):
      self.sair()


  def renderizar(self):
    if self.controles.luz_acesa:
      self.ctx.clear(1.0, 1.0, 1.0)
    else:
      self.ctx.clear(0.08, 0.08, 0.1)

    self.player.instanciar(self.controles.luz_acesa)

    gl.swap_buffers(self.window)

  def sair(self):
    gl.terminate()
    sys.exit()

  def rodar(self):
    while True:
      agora = gl.get_time()
      self.delta_time = agora - self.ultimo_tempo
      self.ultimo_tempo = agora

      self.tratar_eventos()
      self.renderizar()


if __name__ == "__main__":
  Game().rodar()
