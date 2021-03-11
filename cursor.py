
class Cursor:

    def __init__(self, ax):
        self.ax = ax
        self.vertical_line = ax.axvline(color='r', lw=0.8, ls='--')

    def set_cross_hair_visible(self, visible):
        need_redraw = self.vertical_line.get_visible() != visible
        self.vertical_line.set_visible(visible)
        return need_redraw

    def on_mouse_move(self, event):
        if not event.inaxes:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.draw()
        else:
            self.set_cross_hair_visible(True)
            self.vertical_line.set_xdata(event.xdata)
            self.ax.figure.canvas.draw()
