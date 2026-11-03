import moderngl_window as mglw
import numpy as np

class Test(mglw.WindowConfig):
    gl_version = (3, 3)
    window_size = (1920, 1080)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 1. Defina os shaders como strings de texto (GLSL)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                out vec4 fragColor;
                void main() {
                    fragColor = vec4(1.0, 0.0, 0.0, 1.0); // Cor vermelha
                }
            """,
        )

        # 2. Dados dos vértices (um triângulo simples)
        vertices = np.array([-0.5, -0.5, 0.5, -0.5, 0.0, 0.5], dtype="f4")

        # 3. Criação do VBO e do VAO associado ao shader
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(
            self.prog, [(self.vbo, "2f", "in_vert")]
        )

        # 4. Textura
        self.texture = self.ctx.texture(self.wnd.size, 4)

    def on_render(self, time: float, frametime: float):
        self.ctx.clear(0.1, 0.1, 0.1, 1.0)  # Limpa a tela com fundo cinza escuro
        self.vao.render()


if __name__ == "__main__":
    Test.run()
