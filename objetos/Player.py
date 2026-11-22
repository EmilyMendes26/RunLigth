import math
import moderngl
import numpy as np


class Player:
    def __init__(self, ctx):
        self.ctx = ctx

        vertices = np.array([
            -0.15, -0.15, -0.15,
             0.15, -0.15, -0.15,
             0.15,  0.15, -0.15,
            -0.15,  0.15, -0.15,
            -0.15, -0.15,  0.15,
             0.15, -0.15,  0.15,
             0.15,  0.15,  0.15,
            -0.15,  0.15,  0.15,
        ], dtype="f4")

        indices_linhas = np.array([
            0, 1, 1, 2, 2, 3, 3, 0,
            4, 5, 5, 6, 6, 7, 7, 4,
            0, 4, 1, 5, 2, 6, 3, 7,
        ], dtype="i4")

        indices_faces = np.array([
            0, 1, 2, 2, 3, 0,
            5, 4, 7, 7, 6, 5,
            0, 4, 7, 7, 3, 0,
            1, 2, 6, 6, 5, 1,
            3, 2, 6, 6, 7, 3,
            4, 5, 1, 1, 0, 4,
        ], dtype="i4")

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo_linhas = self.ctx.buffer(indices_linhas.tobytes())
        self.ibo_faces = self.ctx.buffer(indices_faces.tobytes())

        vert_shader = """
            #version 330
            in vec3 in_pos;
            uniform vec2 u_pos;
            uniform float u_aspect;
            uniform mat4 u_rot;
            uniform float u_z_bias;

            out float v_shade;

            void main() {
                if (in_pos.y > 0.0 && in_pos.z > 0.0) {
                    v_shade = 1.04;
                } else if (in_pos.z < 0.0) {
                    v_shade = 0.96;
                } else {
                    v_shade = 0.88;
                }

                vec4 pos = u_rot * vec4(in_pos, 1.0);
                pos.x += u_pos.x;
                pos.y += u_pos.y;
                pos.x /= u_aspect;

                // Posiciona o Player à frente do plano da plataforma
                float depth = -0.975 + pos.z * 0.05 + u_z_bias;
                gl_Position = vec4(pos.xy, depth, 1.0);
            }
        """

        frag_shader = """
            #version 330
            uniform vec3 u_color;
            uniform float u_use_shade;
            in float v_shade;
            out vec4 f_color;

            void main() {
                float fator = mix(1.0, v_shade, u_use_shade);
                f_color = vec4(u_color * fator, 1.0);
            }
        """

        self.prog = self.ctx.program(
            vertex_shader=vert_shader, fragment_shader=frag_shader
        )
        self.vao_linhas = self.ctx.vertex_array(
            self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_linhas
        )
        self.vao_faces = self.ctx.vertex_array(
            self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_faces
        )

        angulo = math.radians(45)
        fator_z = 0.5
        matriz_obliqua = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [fator_z * math.cos(angulo), fator_z * math.sin(angulo), 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype="f4")
        self.prog["u_rot"].write(matriz_obliqua.tobytes())

    def instanciar(
        self,
        luz_acesa,
        pos_x=0.0,
        pos_y=0.0,
        largura=1280,
        altura=720,
        cor_sombra=(0.55, 0.55, 0.58),
    ):
        self.prog["u_pos"].value = (pos_x, pos_y)
        self.prog["u_aspect"].value = largura / max(altura, 1)

        # 1. Faces do Player: branco no modo claro, cinza no modo sombreado
        if luz_acesa:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)
        else:
            self.prog["u_color"].value = cor_sombra

        self.prog["u_use_shade"].value = 1.0
        self.prog["u_z_bias"].value = 0.002
        self.vao_faces.render(moderngl.TRIANGLES)

        # 2. Contorno sempre preto
        self.prog["u_color"].value = (0.0, 0.0, 0.0)
        self.prog["u_use_shade"].value = 0.0
        self.prog["u_z_bias"].value = 0.0
        self.ctx.line_width = 3.0
        self.vao_linhas.render(moderngl.LINES)
        self.ctx.line_width = 1.0

    def destruir(self):
        self.vao_linhas.release()
        self.vao_faces.release()
        self.vbo.release()
        self.ibo_linhas.release()
        self.ibo_faces.release()
        self.prog.release()
