import glfw as gl


class Controles:
    def __init__(self, janela):
        self.janela = janela
        self.sair_jogo = False
        self.tela_cheia = True
        self.luz_acesa = False

        # Posição e tamanho usados ao voltar para o modo janela
        self.pos_janela = (100, 100)
        self.tamanho_janela = (1280, 720)

        # Registra a função apertar para ser chamada pelo GLFW a cada tecla
        gl.set_key_callback(janela, self.apertar)

    def troca_luz(self):
        if self.luz_acesa:
            self.luz_acesa = False
        else:
            self.luz_acesa = True

    def troca_fullscreen(self):
        if self.tela_cheia:
            self.tela_cheia = False
            x, y = self.pos_janela
            largura, altura = self.tamanho_janela
            gl.set_window_monitor(self.janela, None, x, y, largura, altura, 0)
        else:
            self.tela_cheia = True
            self.pos_janela =  gl.get_window_pos(self.janela)
            self.tamanho_janela = gl.get_window_size(self.janela)
            monitor = gl.get_primary_monitor()
            modo = gl.get_video_mode(monitor)
            gl.set_window_monitor(
                self.janela, monitor, 0, 0,
                modo.size.width, modo.size.height, modo.refresh_rate,
            )

    def apertar(self, janela, tecla, scancode, acao, mods):
        if acao != gl.PRESS:
            return

        if tecla == gl.KEY_ESCAPE:
            self.sair_jogo = True
        elif tecla == gl.KEY_F11:
            self.troca_fullscreen()
        elif tecla == gl.KEY_I:
            self.troca_luz()
            print("troca de luz")
