import numpy as np
import moderngl

class Plataforma:
    def __init__(self, ctx, largura_pista=0.8):
        self.ctx = ctx
        meio = largura_pista / 2.0

        vertices = np.array([
            -meio, 0.0, -2.0,
            -meio, 0.0, 50.0,

             meio, 0.0, -2.0,
             meio, 0.0, 50.0,
        ], dtype="f4")

        self.vbo = self.ctx.buffer(vertices.tobytes())

        vert_shader = """
            #version 330
            in vec3 in_pos;
            uniform vec2 u_pos;
            uniform float u_aspect;

            void main() {
                vec3 pos = in_pos;
                pos.x += u_pos.x;
                pos.y += u_pos.y;

                // Mesma projeção em perspectiva usada nas árvores
                float dist = max(pos.z + 2.5, 0.2);
                float fov_scale = 1.2 / dist;

                vec2 ndc = pos.xy * fov_scale;
                ndc.x /= u_aspect;

                float depth = clamp((pos.z + 2.5) / 25.0, 0.0, 0.98) * 2.0 - 1.0;

                gl_Position = vec4(ndc, depth, 1.0);
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

    def instanciar(self, luz_acesa, pos_x=0.0, pos_y=-0.4, largura=1280, altura=720):
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
