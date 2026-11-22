import ctypes
import platform
import random
import sys
import glfw as gl
import moderngl
import numpy as np

from controles.contoles_eventos import Controles
from objetos.Player import Player
from objetos.Plataforma import Plataforma
from objetos.Fps import ContadorFPS
from objetos.Pontuacao import Pontuacao
from objetos.Arvore import CampoArvores


class _OpenGLNativo:
    """Carrega funções de Stencil e Depth Clamp do OpenGL usando apenas ctypes nativo."""

    GL_STENCIL_BUFFER_BIT = 0x00000400
    GL_STENCIL_TEST = 0x0B90
    GL_DEPTH_CLAMP = 0x864F
    GL_ALWAYS = 0x0207
    GL_NOTEQUAL = 0x0205
    GL_KEEP = 0x1E00
    GL_INCR_WRAP = 0x8507
    GL_DECR_WRAP = 0x8508

    def __init__(self):
        self._lib_gl = self._carregar_biblioteca()
        self.glEnable = self._func("glEnable", None, ctypes.c_uint)
        self.glDisable = self._func("glDisable", None, ctypes.c_uint)
        self.glClear = self._func("glClear", None, ctypes.c_uint)
        self.glStencilMask = self._func("glStencilMask", None, ctypes.c_uint)
        self.glStencilFunc = self._func(
            "glStencilFunc", None, ctypes.c_uint, ctypes.c_int, ctypes.c_uint
        )
        self.glStencilOp = self._func(
            "glStencilOp", None, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint
        )

    @staticmethod
    def _carregar_biblioteca():
        sistema = platform.system()
        if sistema == "Windows":
            return ctypes.WinDLL("opengl32")
        if sistema == "Darwin":
            return ctypes.CDLL("/System/Library/Frameworks/OpenGL.framework/OpenGL")
        for nome in ("libGL.so.1", "libGL.so", "libOpenGL.so.0"):
            try:
                return ctypes.CDLL(nome)
            except OSError:
                continue
        return None

    def _func(self, nome, restype, *argtypes):
        tipo = ctypes.CFUNCTYPE(restype, *argtypes)
        endereco = gl.get_proc_address(nome)
        if endereco:
            return tipo(endereco)
        if self._lib_gl is not None and hasattr(self._lib_gl, nome):
            fn = getattr(self._lib_gl, nome)
            fn.restype = restype
            fn.argtypes = argtypes
            return fn
        raise RuntimeError(f"Função OpenGL indisponível no driver: {nome}")


class SombraCenario:
    """
    Oclusor do cenário que projeta o Shadow Volume (Kilgard & Everist)
    sobre a plataforma e as árvores.
    """

    def __init__(self, ctx):
        self.ctx = ctx

        vertices = np.array([
            -2.5, 1.15, -0.985,
             2.5, 1.15, -0.985,
             2.5, 1.35, -0.985,
            -2.5, 1.35, -0.985,
            -2.5, 1.15,  0.50,
             2.5, 1.15,  0.50,
             2.5, 1.35,  0.50,
            -2.5, 1.35,  0.50,
        ], dtype="f4")

        indices_faces = np.array([
            0, 1, 2, 2, 3, 0,  # Frente
            5, 4, 7, 7, 6, 5,  # Trás
            0, 4, 7, 7, 3, 0,  # Esquerda
            1, 2, 6, 6, 5, 1,  # Direita
            3, 2, 6, 6, 7, 3,  # Topo
            4, 5, 1, 1, 0, 4,  # Base
        ], dtype="i4")

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo = self.ctx.buffer(indices_faces.tobytes())

        vert_vol = """
            #version 330
            in vec3 in_pos;
            out vec3 v_pos_world;

            void main() {
                v_pos_world = in_pos;
            }
        """

        geom_vol = """
            #version 330
            layout(triangles) in;
            layout(triangle_strip, max_vertices = 18) out;

            in vec3 v_pos_world[3];
            uniform vec3 u_light_pos;
            uniform float u_aspect;

            void emit_vertex(vec3 p) {
                gl_Position = vec4(p.x / u_aspect, p.y, p.z, 1.0);
                EmitVertex();
            }

            void emit_vertex_inf(vec3 p) {
                vec3 dir = p - u_light_pos;
                // Extrusão até o infinito (w = 0.0) conforme Kilgard & Everist
                gl_Position = vec4(dir.x / u_aspect, dir.y, dir.z, 0.0);
                EmitVertex();
            }

            void main() {
                vec3 v0 = v_pos_world[0];
                vec3 v1 = v_pos_world[1];
                vec3 v2 = v_pos_world[2];

                vec3 normal = cross(v2 - v0, v1 - v0);
                vec3 light_dir = u_light_pos - v0;

                if (dot(normal, light_dir) > 0.0) {
                    emit_vertex(v0);
                    emit_vertex(v1);
                    emit_vertex(v2);
                    EndPrimitive();

                    emit_vertex_inf(v0);
                    emit_vertex_inf(v2);
                    emit_vertex_inf(v1);
                    EndPrimitive();

                    emit_vertex(v0); emit_vertex(v1);
                    emit_vertex_inf(v0); emit_vertex_inf(v1);
                    EndPrimitive();

                    emit_vertex(v1); emit_vertex(v2);
                    emit_vertex_inf(v1); emit_vertex_inf(v2);
                    EndPrimitive();

                    emit_vertex(v2); emit_vertex(v0);
                    emit_vertex_inf(v2); emit_vertex_inf(v0);
                    EndPrimitive();
                }
            }
        """

        self.prog_vol = self.ctx.program(
            vertex_shader=vert_vol, geometry_shader=geom_vol
        )
        self.vao_vol = self.ctx.vertex_array(
            self.prog_vol, [(self.vbo, "3f", "in_pos")], self.ibo
        )

    def renderizar_volume(self, pos_luz, largura, altura):
        self.prog_vol["u_aspect"].value = largura / max(altura, 1)
        self.prog_vol["u_light_pos"].value = pos_luz
        self.vao_vol.render(moderngl.TRIANGLES)

    def destruir(self):
        self.vao_vol.release()
        self.vbo.release()
        self.ibo.release()
        self.prog_vol.release()


class Game:
    COR_CLARIDADE = (1.0, 1.0, 1.0)
    COR_SOMBRA = (0.68, 0.68, 0.72)

    def __init__(self, largura=1280, altura=720):
        if not gl.init():
            raise RuntimeError("Não foi possível inicializar o GLFW")

        gl.window_hint(gl.CONTEXT_VERSION_MAJOR, 3)
        gl.window_hint(gl.CONTEXT_VERSION_MINOR, 3)
        gl.window_hint(gl.OPENGL_PROFILE, gl.OPENGL_CORE_PROFILE)
        gl.window_hint(gl.OPENGL_FORWARD_COMPAT, True)
        gl.window_hint(gl.DEPTH_BITS, 24)
        gl.window_hint(gl.STENCIL_BITS, 8)

        self.window = gl.create_window(largura, altura, "RunLight", None, None)
        if not self.window:
            gl.terminate()
            raise RuntimeError("Não foi possível criar a janela")

        gl.make_context_current(self.window)
        self.ctx = moderngl.create_context()
        self.gl_nativo = _OpenGLNativo()

        self.controles = Controles(self.window)
        self.player = Player(self.ctx)
        self.plataforma = Plataforma(self.ctx, largura_pista=1.0)
        self.fps_hud = ContadorFPS(self.ctx)
        self.pontuacao = Pontuacao(self.ctx)
        self.arvores = CampoArvores(self.ctx, quantidade=16)
        self.sombra_cenario = SombraCenario(self.ctx)

        self.pos_luz = (0.0, 2.5, -0.2)

        quad_sombra = np.array(
            [-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype="f4"
        )
        self.vbo_sombra = self.ctx.buffer(quad_sombra.tobytes())
        self.prog_sombra = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_pos;
                void main() {
                    gl_Position = vec4(in_pos, 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                uniform vec3 u_shadow_color;
                out vec4 f_color;
                void main() {
                    f_color = vec4(u_shadow_color, 1.0);
                }
            """,
        )
        self.prog_sombra["u_shadow_color"].value = self.COR_SOMBRA
        self.vao_sombra = self.ctx.vertex_array(
            self.prog_sombra, [(self.vbo_sombra, "2f", "in_pos")]
        )

        self.cronometro_tela = 0.0
        self.tempo_troca_tela = random.uniform(1.5, 4.5)
        self.fps_atual = 0
        self.ultimo_tempo = gl.get_time()
        self.delta_time = 0.0
        self.contador_frames = 0
        self.acumulador_fps = 0.0

    def tratar_eventos(self):
        gl.poll_events()
        if self.controles.sair_jogo or gl.window_should_close(self.window):
            self.sair()

    def renderizar(self):
        largura, altura = gl.get_framebuffer_size(self.window)
        if altura == 0 or largura == 0:
            return

        self.ctx.viewport = (0, 0, largura, altura)

        # 1. LIMPEZA DOS BUFFERS (Cenário inicia iluminado em branco)
        self.ctx.color_mask = (True, True, True, True)
        self.ctx.depth_mask = True
        self.gl_nativo.glStencilMask(0xFF)

        self.ctx.clear(*self.COR_CLARIDADE)
        self.gl_nativo.glClear(self.gl_nativo.GL_STENCIL_BUFFER_BIT)

        # 2. PASSE DE GEOMETRIA ILUMINADA (Plataforma e Árvores)
        self.ctx.enable(moderngl.DEPTH_TEST)

        self.plataforma.instanciar(
            True, pos_y=-0.4, largura=largura, altura=altura
        )
        self.arvores.instanciar(
            True, pos_y=-0.4, largura=largura, altura=altura
        )

        # 3. SHADOW VOLUME DO CENÁRIO (KILGARD & EVERIST - Z-FAIL / CARMACK'S REVERSE)
        if not self.controles.luz_acesa_cenario:
            self.ctx.color_mask = (False, False, False, False)
            self.ctx.depth_mask = False

            self.gl_nativo.glEnable(self.gl_nativo.GL_STENCIL_TEST)
            self.gl_nativo.glEnable(self.gl_nativo.GL_DEPTH_CLAMP)
            self.gl_nativo.glStencilFunc(self.gl_nativo.GL_ALWAYS, 0, 0xFF)
            self.ctx.enable(moderngl.CULL_FACE)

            # Passo A: Back-faces incrementam Stencil no Z-Fail
            self.ctx.cull_face = "front"
            self.gl_nativo.glStencilOp(
                self.gl_nativo.GL_KEEP,
                self.gl_nativo.GL_INCR_WRAP,
                self.gl_nativo.GL_KEEP,
            )
            self.sombra_cenario.renderizar_volume(self.pos_luz, largura, altura)

            # Passo B: Front-faces decrementam Stencil no Z-Fail
            self.ctx.cull_face = "back"
            self.gl_nativo.glStencilOp(
                self.gl_nativo.GL_KEEP,
                self.gl_nativo.GL_DECR_WRAP,
                self.gl_nativo.GL_KEEP,
            )
            self.sombra_cenario.renderizar_volume(self.pos_luz, largura, altura)

            # Passo C: Aplica sombra cinza e converte contornos pretos em branco onde Stencil != 0
            # Result = 1.0 - C_dst * (1.0 - COR_SOMBRA)
            # - Fundo/faces brancas (C_dst = 1.0) -> COR_SOMBRA (cinza)
            # - Contornos pretos (C_dst = 0.0) -> (1.0, 1.0, 1.0) (branco)
            self.ctx.disable(moderngl.CULL_FACE)
            self.gl_nativo.glDisable(self.gl_nativo.GL_DEPTH_CLAMP)
            self.ctx.color_mask = (True, True, True, True)
            self.ctx.disable(moderngl.DEPTH_TEST)

            self.gl_nativo.glStencilFunc(self.gl_nativo.GL_NOTEQUAL, 0, 0xFF)
            self.gl_nativo.glStencilOp(
                self.gl_nativo.GL_KEEP,
                self.gl_nativo.GL_KEEP,
                self.gl_nativo.GL_KEEP,
            )

            self.ctx.enable(moderngl.BLEND)

            # Subpasso C1: Multiplica o framebuffer por (1.0 - COR_SOMBRA)
            self.ctx.blend_equation = moderngl.FUNC_ADD
            self.ctx.blend_func = moderngl.DST_COLOR, moderngl.ZERO
            self.prog_sombra["u_shadow_color"].value = tuple(
                1.0 - c for c in self.COR_SOMBRA
            )
            self.vao_sombra.render(moderngl.TRIANGLE_STRIP)

            # Subpasso C2: Subtrai o resultado de (1.0, 1.0, 1.0)
            self.ctx.blend_equation = moderngl.FUNC_SUBTRACT
            self.ctx.blend_func = moderngl.ONE, moderngl.ONE
            self.prog_sombra["u_shadow_color"].value = (1.0, 1.0, 1.0)
            self.vao_sombra.render(moderngl.TRIANGLE_STRIP)

            # Restaura estados padrão de Blend, Stencil e Depth
            self.ctx.blend_equation = moderngl.FUNC_ADD
            self.ctx.disable(moderngl.BLEND)
            self.gl_nativo.glDisable(self.gl_nativo.GL_STENCIL_TEST)
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.depth_mask = True

        # 4. PLAYER (sempre renderizado; alterna claro/sombreado apenas com a tecla 'I')
        self.player.instanciar(
            self.controles.luz_acesa_player,
            pos_y=-0.4,
            largura=largura,
            altura=altura,
            cor_sombra=self.COR_SOMBRA,
        )

        # 5. HUD (FPS e Pontuação sempre visíveis no topo)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.fps_hud.instanciar(
            True, pos_x=-0.95, pos_y=0.93, largura=largura, altura=altura
        )
        self.pontuacao.instanciar(
            True, pos_x=-0.95, pos_y=0.80, largura=largura, altura=altura
        )
        self.ctx.enable(moderngl.DEPTH_TEST)

        gl.swap_buffers(self.window)

    def sair(self):
        self.player.destruir()
        self.plataforma.destruir()
        self.pontuacao.destruir()
        self.fps_hud.destruir()
        self.arvores.destruir()
        self.sombra_cenario.destruir()
        self.vao_sombra.release()
        self.vbo_sombra.release()
        self.prog_sombra.release()
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
