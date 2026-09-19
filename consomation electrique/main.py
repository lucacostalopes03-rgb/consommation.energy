import time
import tkinter as tk
from tkinter import ttk
 
try:
    import psutil
except ImportError:
    raise SystemExit("Installe psutil d'abord :  pip install psutil")
 
INTERVALLE_MS = 1000  # mise à jour toutes les secondes
 
 
class App:
    def __init__(self, root):
        self.root = root
        root.title("Consommation électrique en temps réel")
        root.resizable(False, False)
 
        frm = ttk.Frame(root, padding=14)
        frm.grid()
 
        # --- Réglages ---
        self.e_repos = self.champ(frm, 0, "Puissance PC au repos (W) :", 40)
        self.e_max = self.champ(frm, 1, "Puissance PC à 100 % CPU (W) :", 120)
        self.e_prix = self.champ(frm, 2, "Prix du kWh (CHF) :", 0.27)
        self.e_seuil = self.champ(frm, 3, "Seuil « repos » (% CPU) :", 10)
 
        ttk.Separator(frm).grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
 
        # --- Affichage ---
        self.v = {}
        for i, (cle, texte) in enumerate([
            ("cpu", "Charge CPU"),
            ("watts", "Puissance estimée"),
            ("duree", "Durée de mesure"),
            ("kwh", "Énergie consommée"),
            ("cout", "Coût"),
            ("gaspi", "Gaspillé au repos"),
            ("gaspi_cout", "Coût du gaspillage"),
            ("annee", "Projection sur 1 an"),
        ]):
            ttk.Label(frm, text=texte + " :").grid(row=5 + i, column=0, sticky="w", pady=2)
            self.v[cle] = tk.StringVar(value="—")
            ttk.Label(frm, textvariable=self.v[cle], font=("Segoe UI", 10, "bold")).grid(
                row=5 + i, column=1, sticky="e", pady=2)
 
        btns = ttk.Frame(frm)
        btns.grid(row=14, column=0, columnspan=2, pady=10)
        self.btn = ttk.Button(btns, text="Pause", command=self.toggle)
        self.btn.grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Réinitialiser", command=self.reset).grid(row=0, column=1, padx=4)
 
        ttk.Label(
            frm, wraplength=340, foreground="gray",
            text="Estimation basée sur la charge CPU. Pour une valeur exacte, "
                 "mesure avec un wattmètre de prise et ajuste les deux puissances."
        ).grid(row=15, column=0, columnspan=2)
 
        self.reset()
        psutil.cpu_percent(None)  # amorce la mesure
        self.tick()
 
    @staticmethod
    def champ(frm, ligne, texte, defaut):
        ttk.Label(frm, text=texte).grid(row=ligne, column=0, sticky="w", pady=3)
        e = ttk.Entry(frm, width=10, justify="right")
        e.insert(0, str(defaut))
        e.grid(row=ligne, column=1, pady=3, sticky="e")
        return e
 
    def reset(self):
        self.running = True
        self.duree = 0.0        # secondes
        self.wh_total = 0.0
        self.wh_gaspi = 0.0
        self.dernier = time.monotonic()
        if hasattr(self, "btn"):
            self.btn.config(text="Pause")
 
    def toggle(self):
        self.running = not self.running
        self.dernier = time.monotonic()
        self.btn.config(text="Pause" if self.running else "Reprendre")
 
    @staticmethod
    def nombre(entry, defaut):
        try:
            return max(0.0, float(entry.get().strip().replace(",", ".")))
        except ValueError:
            return defaut
 
    def tick(self):
        maintenant = time.monotonic()
        dt = maintenant - self.dernier
        self.dernier = maintenant
 
        w_repos = self.nombre(self.e_repos, 40)
        w_max = max(self.nombre(self.e_max, 120), w_repos)
        prix = self.nombre(self.e_prix, 0.27)
        seuil = self.nombre(self.e_seuil, 10)
 
        cpu = psutil.cpu_percent(None)
        watts = w_repos + (w_max - w_repos) * cpu / 100
 
        if self.running:
            self.duree += dt
            wh = watts * dt / 3600
            self.wh_total += wh
            if cpu < seuil:  # PC allumé mais quasi inactif = gaspillage
                self.wh_gaspi += wh
 
        kwh = self.wh_total / 1000
        kwh_gaspi = self.wh_gaspi / 1000
        h = self.duree / 3600
 
        self.v["cpu"].set(f"{cpu:.0f} %")
        self.v["watts"].set(f"{watts:.1f} W")
        self.v["duree"].set(time.strftime("%H:%M:%S", time.gmtime(self.duree)))
        self.v["kwh"].set(f"{kwh:.4f} kWh")
        self.v["cout"].set(f"{kwh * prix:.4f} CHF")
        self.v["gaspi"].set(f"{kwh_gaspi:.4f} kWh")
        self.v["gaspi_cout"].set(f"{kwh_gaspi * prix:.4f} CHF")
        if h > 0.0014:  # ~5 s de mesure minimum
            self.v["annee"].set(f"{kwh / h * 8760 * prix:.0f} CHF")
 
        self.root.after(INTERVALLE_MS, self.tick)
 
 
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
 