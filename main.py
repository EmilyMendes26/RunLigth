import random
import sys
import glfw as gl
import moderngl

from controles.contoles_eventos import Controles
from objetos.Player import Player
from objetos.Plataforma import Plataforma
from objetos.Fps import ContadorFPS
from objetos.Pontuacao import Pontuacao
from objetos.Arvore import CampoArvores


class Game:
    def __init__(self, largura=1280, altura=720):
        if not gl.init():
            raise RuntimeError("Não foi possível inicializar o GLFW")

        gl.window_hint(gl.CONTEXT_VERSION_MAJOR, 3)
        gl.window_hint(gl.CONTEXT_VERSION_MINOR, 3)
        gl.window_hint(gl.OPENGL_PROFILE, gl.OPENGL_CORE_PROFILE)
        gl.window_hint(gl.OPENGL_FORWARD_COMPAT, True)
        gl.window_hint(gl.DEPTH_BITS, 24)

        self.window = gl.create_window(largura, altura, "RunLight", None, None)
        if not self.window:
            gl.terminate()
            raise RuntimeError("Não foi possível criar a janela")

        gl.make_context_current(self.window)
        self.ctx = moderngl.create_context()

        self.controles = Controles(self.window)
        self.player = Player(self.ctx)
        self.plataforma = Plataforma(self.ctx, largura_pista=1.0)
        self.fps_hud = ContadorFPS(self.ctx)
        self.pontuacao = Pontuacao(self.ctx)
        self.arvores = CampoArvores(self.ctx, quantidade=16)

        self.pos_luz = (-0.7, 1.2, 0.8)

        self.cronometro_tela = 0.0
        self.tempo_troca_tela = random.uniform(1.5, 4.5)
        self.fps_atual = 0
        self.ultimo_tempo = gl.get_time()
        self.delta_time = 0.0
        self.contador_frames = 0
        self.acumulador_fps = 0.0

    def tratar_eventos(self):
        # O callback da classe Controles já alterna luz_acesa_player ao apertar 'I'
        gl.poll_events()
        if self.controles.sair_jogo or gl.window_should_close(self.window):
            self.sair()

    def renderizar(self):
        largura, altura = gl.get_framebuffer_size(self.window)
        if altura == 0 or largura == 0:
            return

        self.ctx.viewport = (0, 0, largura, altura)

        if self.controles.luz_acesa_cenario:
            self.ctx.clear(1.0, 1.0, 1.0)
        else:
            self.ctx.clear(0.08, 0.08, 0.1)

        self.ctx.color_mask = (True, True, True, True)
        self.ctx.depth_mask = True
        self.ctx.enable(moderngl.DEPTH_TEST)

        self.plataforma.instanciar(
            self.controles.luz_acesa_cenario,
            pos_y=-0.4,
            largura=largura,
            altura=altura,
        )

        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.depth_mask = False

        self.player.renderizar_volume(
            self.pos_luz,
            pos_x=0.0,
            pos_y=-0.4,
            largura=largura,
            altura=altura,
            luz_cenario=self.controles.luz_acesa_cenario
        )

        self.ctx.disable(moderngl.BLEND)
        self.ctx.depth_mask = True

        self.player.instanciar(
            self.controles.luz_acesa_player,
            pos_y=-0.4,
            largura=largura,
            altura=altura,
        )
        self.arvores.instanciar(
            self.controles.luz_acesa_cenario,
            pos_y=-0.4,
            largura=largura,
            altura=altura,
        )

        self.ctx.disable(moderngl.DEPTH_TEST)

        self.fps_hud.instanciar(
            self.controles.luz_acesa_cenario,
            pos_x=-0.95,
            pos_y=0.93,
            largura=largura,
            altura=altura,
        )
        self.pontuacao.instanciar(
            self.controles.luz_acesa_cenario,
            pos_x=-0.95,
            pos_y=0.80,
            largura=largura,
            altura=altura,
        )

        self.ctx.enable(moderngl.DEPTH_TEST)

        gl.swap_buffers(self.window)

    def sair(self):
        self.player.destruir()
        self.plataforma.destruir()
        self.pontuacao.destruir()
        self.fps_hud.destruir()
        self.arvores.destruir()
        self.ctx.release()
        gl.destroy_window(self.window)
        gl.terminate()
        sys.exit()

    def rodar(self):
        while not gl.window_should_close(self.window):
            agora = gl.get_time()
            self.delta_time = agora - self.ultimo_tempo
            self.ultimo_tempo = agora
            self.atualizar_fps()
            self.tratar_eventos()
            self.renderizar()
            self.atualizar_tela()
            self.pontuacao.atualizar(self.delta_time)
            self.arvores.atualizar(self.delta_time, velocidade=6.0)
        self.sair()

    def atualizar_tela(self):
        self.cronometro_tela += self.delta_time
        if self.cronometro_tela >= self.tempo_troca_tela:
            self.controles.luz_acesa_cenario = not self.controles.luz_acesa_cenario
            self.cronometro_tela = 0.0
            self.tempo_troca_tela = random.uniform(1.0, 4.0)

    def atualizar_fps(self):
        self.contador_frames += 1
        self.acumulador_fps += self.delta_time
        if self.acumulador_fps >= 1.0:
            self.fps_atual = round(self.contador_frames / self.acumulador_fps)
            self.fps_hud.atualizar(self.fps_atual)
            self.contador_frames = 0
            self.acumulador_fps = 0.0


if __name__ == "__main__":
    Game().rodar()
