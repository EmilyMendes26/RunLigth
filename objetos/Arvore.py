import random
import moderngl
import numpy as np

class CampoArvores:
    def __init__(self, ctx, quantidade=16):
        self.ctx = ctx
        self.quantidade = quantidade

        vert_shader = """
        #version 330
        in vec3 in_pos;

        uniform vec3 u_offset;
        uniform vec3 u_scale;
        uniform float u_aspect;
        uniform float u_pos_y;

        void main() {
            vec3 pos = in_pos * u_scale + u_offset;
            pos.y += u_pos_y;

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

        vertices = self._gerar_malha_arvore()
        self.vbo_pos = self.ctx.buffer(vertices.tobytes())
        self.qtd_vertices = len(vertices)

        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo_pos, "3f", "in_pos")],
        )

        self.arvores = []
        self._inicializar_arvores()

    def _gerar_malha_arvore(self):
        linhas_pos = []

        def add_line(p0, p1):
            linhas_pos.extend([p0, p1])

        def add_quad(p0, p1, p2, p3):
            add_line(p0, p1)
            add_line(p1, p2)
            add_line(p2, p3)
            add_line(p3, p0)

        def add_tri(p0, p1, p2):
            add_line(p0, p1)
            add_line(p1, p2)
            add_line(p2, p0)

        # --- Tronco ---
        tw = 0.08
        th = 0.45
        td = 0.08
        add_quad((-tw, 0.0, td), (tw, 0.0, td), (tw, th, td), (-tw, th, td))
        add_quad((tw, 0.0, -td), (-tw, 0.0, -td), (-tw, th, -td), (tw, th, -td))
        add_quad((-tw, 0.0, -td), (-tw, 0.0, td), (-tw, th, td), (-tw, th, -td))
        add_quad((tw, 0.0, td), (tw, 0.0, -td), (tw, th, -td), (tw, th, td))
        add_quad((-tw, th, td), (tw, th, td), (tw, th, -td), (-tw, th, -td))

        # --- Copa ---
        cw = 0.36
        cd = 0.36
        base_y = th
        topo = (0.0, 1.35, 0.0)

        b0 = (-cw, base_y, cd)
        b1 = (cw, base_y, cd)
        b2 = (cw, base_y, -cd)
        b3 = (-cw, base_y, -cd)

        add_tri(b0, b1, topo)
        add_tri(b1, b2, topo)
        add_tri(b2, b3, topo)
        add_tri(b3, b0, topo)
        add_quad(b3, b2, b1, b0)

        return np.array(linhas_pos, dtype="f4")

    def _sortear_x_lateral(self):
        lado = random.choice([-1.0, 1.0])
        distancia_lateral = random.uniform(1.1, 3.2)
        return lado * distancia_lateral

    def _inicializar_arvores(self):
        z_inicio = 1.0
        z_fim = 16.0
        passo_z = (z_fim - z_inicio) / max(self.quantidade, 1)

        for i in range(self.quantidade):
            z = z_inicio + i * passo_z + random.uniform(-0.3, 0.3)
            self.arvores.append(
                {
                    "x": self._sortear_x_lateral(),
                    "y": 0.0,
                    "z": z,
                    "escala": random.uniform(0.75, 1.35),
                }
            )

    def atualizar(self, delta_time, velocidade=6.0, z_limite_frente=-1.8, z_reset=16.0):
        for arvore in self.arvores:
            arvore["z"] -= velocidade * delta_time
            if arvore["z"] < z_limite_frente:
                arvore["z"] = z_reset + random.uniform(0.0, 2.0)
                arvore["x"] = self._sortear_x_lateral()
                arvore["escala"] = random.uniform(0.75, 1.35)

    def instanciar(self, luz_acesa, pos_y=-0.4, largura=1280, altura=720):
        aspect = largura / max(altura, 1)
        self.prog["u_aspect"].value = aspect
        self.prog["u_pos_y"].value = pos_y

        if luz_acesa:
            self.prog["u_color"].value = (0.0, 0.0, 0.0)
        else:
            self.prog["u_color"].value = (1.0, 1.0, 1.0)

        self.ctx.line_width = 3.0

        for arvore in self.arvores:
            s = arvore["escala"]
            self.prog["u_offset"].value = (arvore["x"], arvore["y"], arvore["z"])
            self.prog["u_scale"].value = (s, s, s)
            self.vao.render(moderngl.LINES, vertices=self.qtd_vertices)

        self.ctx.line_width = 1.0

    def destruir(self):
        self.vao.release()
        self.vbo_pos.release()
        self.prog.release()
