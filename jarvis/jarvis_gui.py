import tkinter as tk
import math

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI Interface")
        
        # Rendiamo la finestra senza bordi e sempre in primo piano
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Posizionamento al centro dello schermo
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = 400, 400
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.root.configure(bg='black')
        
        # Sfondo trasparente (solo Windows)
        self.root.attributes("-transparentcolor", "black")

        # Canvas per le animazioni
        self.canvas = tk.Canvas(root, width=400, height=400, bg='black', highlightthickness=0)
        self.canvas.pack()

        # Stati: IDLE, LISTENING, THINKING, SPEAKING
        self.state = "IDLE"
        self.angle = 0
        self.pulse = 0
        
        # Inizialmente nascosta
        self.root.withdraw()
        self.animate()

    def show(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)

    def hide(self):
        self.root.withdraw()

    def set_state(self, state):
        self.state = state

    def draw_arc_reactor(self):
        self.canvas.delete("all")
        cx, cy = 200, 200
        self.pulse += 0.1
        self.angle += 3

        if self.state == "IDLE":
            # Animazione "Breathing" (Respiro)
            r_outer = 70 + math.sin(self.pulse) * 3
            self.draw_circle(cx, cy, r_outer, "#003344", 2)
            self.draw_circle(cx, cy, 40, "#006688", 1)
            # Piccoli segmenti decorativi
            for i in range(8):
                a = math.radians(i * 45 + self.angle / 2)
                self.canvas.create_line(cx + math.cos(a)*45, cy + math.sin(a)*45,
                                        cx + math.cos(a)*55, cy + math.sin(a)*55, fill="#00ffff", width=2)

        elif self.state == "LISTENING":
            # Animazione reattiva con rotazione frenetica
            r_pulse = 85 + math.sin(self.pulse * 3) * 10
            self.draw_circle(cx, cy, r_pulse, "#0088ff", 3)
            # Archi rotanti
            self.canvas.create_arc(cx-105, cy-105, cx+105, cy+105, start=self.angle, extent=60, outline="#00ffff", style="arc", width=4)
            self.canvas.create_arc(cx-105, cy-105, cx+105, cy+105, start=self.angle+180, extent=60, outline="#00ffff", style="arc", width=4)
            # Nucleo centrale luminoso
            self.draw_circle(cx, cy, 25, "#00ccff", 0, fill="#00ccff")

        elif self.state == "THINKING":
            # Animazione di elaborazione: Esagono o forme geometriche che collassano e ruotano
            color = "#ffaa00" # Arancione/Oro tecnologico
            for i in range(6):
                a = math.radians(i * 60 + self.angle)
                dist = 60 + math.sin(self.pulse * 4) * 20
                self.canvas.create_line(cx, cy, cx + math.cos(a)*dist, cy + math.sin(a)*dist, fill=color, width=2)
            
            # Anello di "caricamento" rotante
            self.canvas.create_arc(cx-70, cy-70, cx+70, cy+70, start=-self.angle*2, extent=120, outline=color, style="arc", width=5)
            self.draw_circle(cx, cy, 30 + math.sin(self.pulse*2)*5, color, 2)

        elif self.state == "SPEAKING":
            # Onde sonore concentriche in espansione
            color = "#00ffcc"
            for i in range(3):
                # Raggio che cresce e ricomincia
                r = ((self.pulse * 50 + i * 40) % 130) + 10
                opacity_fake = max(1, int(5 * (1 - r/130)))
                self.draw_circle(cx, cy, r, color, opacity_fake)
            # Nucleo pulsante
            r_core = 20 + math.sin(self.pulse * 5) * 5
            self.draw_circle(cx, cy, r_core, "white", 0, fill=color)

    def draw_circle(self, x, y, r, color, width, fill=""):
        self.canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, width=width, fill=fill)

    def animate(self):
        self.draw_arc_reactor()
        self.root.after(20, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()