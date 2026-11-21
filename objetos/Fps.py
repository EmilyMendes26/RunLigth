import moderngl
import numpy as np


class ContadorFPS:
    SEGMENTOS = {
        "0": (0, 1, 2, 4, 5, 6),
        "1": (2, 5),
        "2": (0, 2, 3, 4, 6),
        "3": (0, 2, 3, 5, 6),
        "4": (1, 2, 3, 5),
        "5": (0, 1, 3, 5, 6),
        "6": (0, 1, 3, 4, 5, 6),
        "7": (0, 2, 5),
        "8": (0, 1, 2, 3, 4, 5, 6),
        "9": (0, 1, 2, 3, 5, 6),
        "F": (0, 1, 3, 4),
        "P": (0, 1, 2, 3, 4),
        "S": (0, 1, 3, 5, 6),
    }

    def __init__(self, ctx):
        self.ctx = ctx
        self.qtd_vertices = 0

        vert_shader = """
        #version 330
        in vec2 in_pos;
        uniform vec2 u_pos;
        uniform float u_aspect;

        void main() {
            vec2 pos = in_pos;
            pos.x /= u_aspect;
            pos += u_pos;
            gl_Position = vec4(pos, -0.99, 1.0);
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

        self.prog = self.ctx.program(
            vertex_shader=vert_shader, fragment_shader=frag_shader
        )
        self.vbo = self.ctx.buffer(reserve=4096)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f", "in_pos")])

        self.atualizar(0)

    def atualizar(self, fps):
        texto = f"FPS {int(fps)}"
        w = 0.026
        h = 0.052
        mid = -h / 2.0
        espaco = 0.015

        pontos = []
        cursor_x = 0.0

        for char in texto:
            if char in self.SEGMENTOS:
                x0 = cursor_x
                x1 = cursor_x + w
                linhas = (
                    ((x0, 0.0), (x1, 0.0)),
                    ((x0, 0.0), (x0, mid)),
                    ((x1, 0.0), (x1, mid)),
                    ((x0, mid), (x1, mid)),
                    ((x0, mid), (x0, -h)),
                    ((x1, mid), (x1, -h)),
                    ((x0, -h), (x1, -h)),
                )
                for idx in self.SEGMENTOS[char]:
                    p1, p2 = linhas[idx]
                    pontos.append(p1)
                    pontos.append(p2)

            cursor_x += w + espaco

        if pontos:
            dados = np.array(pontos, dtype="f4")
            self.vbo.write(dados.tobytes())
            self.qtd_vertices = len(dados)
        else:
            self.qtd_vertices = 0

    def instanciar(self, luz_acesa, pos_x=-0.95, pos_y=0.93, largura=1280, altura=720):
        if self.qtd_vertices == 0:
            return

        if luz_acesa:
            self.prog["u_color"].value = (0.0, 0.0, 0.0)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)

        self.prog["u_pos"].value = (pos_x, pos_y)
        self.prog["u_aspect"].value = largura / max(altura, 1)

        self.ctx.disable(moderngl.DEPTH_TEST)

        self.ctx.line_width = 2.0
        self.vao.render(moderngl.LINES, vertices=self.qtd_vertices)
        self.ctx.line_width = 1.0

        self.ctx.enable(moderngl.DEPTH_TEST)

    def destruir(self):
        self.vao.release()
        self.vbo.release()
        self.prog.release()
