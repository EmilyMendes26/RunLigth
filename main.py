import sys
# import numpy as np
import glfw as gl
import moderngl

from controles.contoles_eventos import Controles


class Game:
    def __init__(self, largura=1280, altura=720):
        gl.init()

        # Pede um contexto OpenGL 3.3 core ao GLFW
        gl.window_hint(gl.CONTEXT_VERSION_MAJOR, 3)
        gl.window_hint(gl.CONTEXT_VERSION_MINOR, 3)
        gl.window_hint(gl.OPENGL_PROFILE, gl.OPENGL_CORE_PROFILE)
        gl.window_hint(gl.OPENGL_FORWARD_COMPAT, True)
        gl.window_hint(gl.DEPTH_BITS, 24)

        # Começa em tela cheia (passa o monitor)
        monitor = gl.get_primary_monitor()
        self.janela = gl.create_window(largura, altura, "RunLight", monitor, None)
        gl.make_context_current(self.janela)

        # Contexto ModernGL (usa o contexto OpenGL que o GLFW criou)
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)  # necessário para 3D

        # Controles precisa da janela, por isso é criado aqui dentro
        self.controles = Controles(self.janela)

        self.ultimo_tempo = gl.get_time()
        self.delta_time = 0.0

        self.iniciar_cena()

    def iniciar_cena(self):
        # Shader program
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec3 in_pos;
            in vec3 in_color;
            out vec3 v_color;
            void main() {
                v_color = in_color;
                gl_Position = vec4(in_pos, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            in vec3 v_color;
            out vec4 f_color;
            void main() {
                f_color = vec4(v_color, 1.0);
            }
            """,
        )

    def tratar_eventos(self):
        # Dispara os callbacks do GLFW (teclado)
        gl.poll_events()

        if self.controles.sair_jogo or gl.window_should_close(self.janela):
            self.sair()

    def atualizar(self):
        # Aqui vai a lógica do jogo (movimento, câmera, etc.)
        pass

    def renderizar(self):
        if self.controles.luz_acesa:
            self.ctx.clear(1.0, 1.0, 1.0)
        else:
            self.ctx.clear(0.08, 0.08, 0.1)
        gl.swap_buffers(self.janela)

    def sair(self):
        gl.terminate()
        sys.exit()

    def rodar(self):
        while True:
            agora = gl.get_time()
            self.delta_time = agora - self.ultimo_tempo  # segundos
            self.ultimo_tempo = agora

            self.tratar_eventos()
            self.atualizar()
            self.renderizar()


if __name__ == "__main__":
    Game().rodar()
