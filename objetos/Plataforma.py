import numpy as np
import moderngl
import math

class Plataforma:
    def __init__(self, ctx, largura_pista=0.8):
        self.ctx = ctx
        meio = largura_pista / 2.0

        vertices = np.array([
            -meio, -0.1, -2.0,
            -meio, -0.1, 50.0,

             meio, -0.1, -2.0,
             meio, -0.1, 50.0,
        ], dtype="f4")

        self.vbo = self.ctx.buffer(vertices.tobytes())

        vert_shader = """
            #version 330
            in vec3 in_pos;
            uniform vec2 u_pos;
            uniform float u_aspect;
            uniform mat4 u_rot;

            void main() {
                vec4 pos = u_rot * vec4(in_pos, 1.0);
                pos.x += u_pos.x;
                pos.y += u_pos.y;
                pos.x /= u_aspect;
                gl_Position = vec4(pos.xyz, 1.0);
            }
        """

        frag_shader = """
            #version 330
            uniform vec3 u_color;
            out vec4 f_color;

            void main() {
                f_color = vec4(u_color, 1.0);
            }
        """

        self.prog = self.ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)

        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")])

        angulo = math.radians(45)
        fator_z = 0.5

        matriz_obliqua = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [fator_z * math.cos(angulo), fator_z * math.sin(angulo), 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype="f4")

        self.prog["u_rot"].write(matriz_obliqua.tobytes())

    def instanciar(self, luz_acesa, pos_x=0.0, pos_y=0.0, largura=1280, altura=720):
        if luz_acesa:
            self.prog["u_color"].value = (0.0, 0.0, 0.0)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)

        self.prog["u_pos"].value = (pos_x, pos_y)
        self.prog["u_aspect"].value = largura / max(altura, 1)

        self.ctx.line_width = 3.0
        self.vao.render(moderngl.LINES)

        self.ctx.line_width = 1.0


    def destruir(self):
        self.vao.release()
        self.vbo.release()
        self.prog.release()
