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
            4, 5, 6, 6, 7, 4,
            4, 0, 3, 3, 7, 4,
            1, 5, 6, 6, 2, 1,
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

            void main() {
                vec4 pos = u_rot * vec4(in_pos, 1.0);
                pos.x += u_pos.x;
                pos.y += u_pos.y;
                pos.x /= u_aspect;
                gl_Position = vec4(pos.xy, pos.z + u_z_bias, 1.0);
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
        self.vao_linhas = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_linhas)
        self.vao_faces = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_faces)

        angulo = math.radians(45)
        fator_z = 0.5
        matriz_obliqua = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [fator_z * math.cos(angulo), fator_z * math.sin(angulo), 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype="f4")
        self.prog["u_rot"].write(matriz_obliqua.tobytes())

        vert_sombra = """
            #version 330
            in vec3 in_pos;
            uniform mat4 u_rot;
            uniform vec2 u_pos;
            uniform float u_aspect;
            uniform vec3 u_light_pos;
            uniform float u_floor_y;

            void main() {
                vec4 p = u_rot * vec4(in_pos, 1.0);
                p.x += u_pos.x;
                p.y += u_pos.y;

                vec3 dir = p.xyz - u_light_pos;
                if (dir.y != 0.0) {
                    float t = (u_floor_y - u_light_pos.y) / dir.y;
                    p.xyz = u_light_pos + t * dir;
                }

                p.x /= u_aspect;
                gl_Position = vec4(p.xy, p.z - 0.01, 1.0);
            }
        """

        frag_sombra = """
            #version 330
            out vec4 f_color;
            void main() {
                f_color = vec4(0.08, 0.08, 0.1, 0.8);
            }
        """

        self.prog_sombra = self.ctx.program(vertex_shader=vert_sombra, fragment_shader=frag_sombra)
        self.vao_sombra = self.ctx.vertex_array(self.prog_sombra, [(self.vbo, "3f", "in_pos")], self.ibo_faces)

    def renderizar_volume(self, pos_luz, pos_x, pos_y, largura, altura):
        self.prog_sombra["u_pos"].value = (pos_x, pos_y)
        self.prog_sombra["u_aspect"].value = largura / max(altura, 1)
        self.prog_sombra["u_light_pos"].value = pos_luz
        self.prog_sombra["u_floor_y"].value = pos_y - 0.16
        self.prog_sombra["u_rot"].write(self.prog["u_rot"].read())

        self.vao_sombra.render(moderngl.TRIANGLES)

    def instanciar(self, luz_acesa, pos_x=0.0, pos_y=0.0, largura=1280, altura=720):
        self.prog["u_pos"].value = (pos_x, pos_y)
        self.prog["u_aspect"].value = largura / max(altura, 1)

        # 1. Faces sólidas (branco no modo claro, escuro no modo sombreado)
        if luz_acesa:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)
        else:
            self.prog["u_color"].value = (0.08, 0.08, 0.1)

        self.prog["u_z_bias"].value = 0.01
        self.vao_faces.render(moderngl.TRIANGLES)

        # 2. Contorno (preto no modo claro, branco no modo sombreado)
        if luz_acesa:
            self.prog["u_color"].value = (0.0, 0.0, 0.0)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)

        self.prog["u_z_bias"].value = 0.0
        self.vao_linhas.render(moderngl.LINES)

    def destruir(self):
        self.vao_linhas.release()
        self.vao_faces.release()
        self.vao_sombra.release()
        self.vbo.release()
        self.ibo_linhas.release()
        self.ibo_faces.release()
        self.prog.release()
        self.prog_sombra.release()
