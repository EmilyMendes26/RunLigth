import numpy as np
import moderngl


class Player:

  def __init__(self, ctx):
    self.ctx = ctx

    vertices = np.array(
        [
            -0.2,
            -0.2,
            -0.2,
            0.2,
            -0.2,
            -0.2,
            0.2,
            0.2,
            -0.2,
            -0.2,
            0.2,
            -0.2,
            -0.2,
            -0.2,
            0.2,
            0.2,
            -0.2,
            0.2,
            0.2,
            0.2,
            0.2,
            -0.2,
            0.2,
            0.2,
        ],
        dtype="f4",
    )

    indices = np.array(
        [
            0,
            1,
            1,
            2,
            2,
            3,
            3,
            0,
            4,
            5,
            5,
            6,
            6,
            7,
            7,
            4,
            0,
            4,
            1,
            5,
            2,
            6,
            3,
            7,
        ],
        dtype="i4",
    )

    self.vbo = self.ctx.buffer(vertices.tobytes())
    self.ibo = self.ctx.buffer(indices.tobytes())

    vert_shader = """
            #version 330
            in vec3 in_pos;

            void main() {
                // Ajustamos levemente o X dividindo pela proporção da tela (16/9 aprox 1.77)
                // para o cubo não ficar achatado ou gigante nas bordas.
                vec3 pos = in_pos;
                pos.x = pos.x / (1280.0 / 720.0);

                gl_Position = vec4(pos, 1.0);
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

    self.vao = self.ctx.vertex_array(
        self.prog, [(self.vbo, "3f", "in_pos")], self.ibo
    )

  def instanciar(self, luz_acesa):
    if luz_acesa:
      self.prog["u_color"].value = (0, 0, 0)
    else:
      self.prog["u_color"].value = (1.0, 1.0, 1.0)
    self.vao.render(moderngl.LINES)

  def destruir(self):
    self.vao.release()
    self.vbo.release()
    self.ibo.release()
    self.prog.release()
