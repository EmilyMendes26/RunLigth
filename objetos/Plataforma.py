import moderngl
import numpy as np


class Plataforma:
    def __init__(self, ctx, largura_pista=0.8):
        self.ctx = ctx
        meio = largura_pista / 2.0

        vertices = np.array([
            -meio, 0.0, -2.0,
             meio, 0.0, -2.0,
            -meio, 0.0, 50.0,
             meio, 0.0, 50.0,
        ], dtype="f4")

        indices_faces = np.array([0, 1, 2, 1, 3, 2], dtype="i4")
        indices_linhas = np.array([0, 1, 1, 3, 3, 2, 2, 0], dtype="i4")

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo_faces = self.ctx.buffer(indices_faces.tobytes())
        self.ibo_linhas = self.ctx.buffer(indices_linhas.tobytes())

        vert_shader = """
            #version 330
            in vec3 in_pos;
            uniform vec2 u_pos;
            uniform float u_aspect;
            uniform float u_z_bias;

            void main() {
                vec3 pos = in_pos;
                pos.x += u_pos.x;
                pos.y += u_pos.y;

                float dist = max(pos.z + 2.5, 0.2);
                float fov_scale = 1.2 / dist;

                vec2 ndc = pos.xy * fov_scale;
                ndc.x /= u_aspect;
                float depth = clamp((pos.z + 2.5) / 25.0, 0.0, 0.98) * 2.0 - 1.0;

                gl_Position = vec4(ndc, depth + u_z_bias, 1.0);
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
        self.vao_faces = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_faces)
        self.vao_linhas = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_linhas)

    def instanciar(self, luz_acesa, pos_x=0.0, pos_y=-0.4, largura=1280, altura=720):
        self.prog["u_pos"].value = (pos_x, pos_y)
        self.prog["u_aspect"].value = largura / max(altura, 1)

        # 1. Superfície sólida acompanhando o estado do cenário
        if luz_acesa:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)
        else:
            self.prog["u_color"].value = (0.08, 0.08, 0.1)

        self.prog["u_z_bias"].value = 0.01
        self.vao_faces.render(moderngl.TRIANGLES)

        # 2. Linhas de contorno acompanhando o estado do cenário
        if luz_acesa:
            self.prog["u_color"].value = (0.0, 0.0, 0.0)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)

        self.prog["u_z_bias"].value = 0.0
        self.ctx.line_width = 3.0
        self.vao_linhas.render(moderngl.LINES)
        self.ctx.line_width = 1.0

    def destruir(self):
        self.vao_faces.release()
        self.vao_linhas.release()
        self.vbo.release()
        self.ibo_faces.release()
        self.ibo_linhas.release()
        self.prog.release()
