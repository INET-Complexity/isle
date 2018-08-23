# file to visualise agent-level data per timestep
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
# read in data for each agent for each timestep

# read in insurancefirm data
rfile = open("data/two_insurance_firms_cash.dat","r")
insurance_firms_cash = [eval(k) for k in rfile]
rfile.close()
# read in reinsurancefirm data
rfile = open("data/two_reinsurance_firms_cash.dat","r")
reinsurance_firms_cash = [eval(k) for k in rfile]
rfile.close()

insurance_firms_cash = np.array(insurance_firms_cash)
reinsurance_firms_cash = np.array(reinsurance_firms_cash)

# shape (runs, steps)
print(insurance_firms_cash.shape)
print(reinsurance_firms_cash.shape)

# let's look at only the first run
first_run_insurance = insurance_firms_cash[0][:]
first_run_reinsurance = reinsurance_firms_cash[0][:]

class InsuranceFirmAnimation(object):
    def __init__(self, data):
        self.data = data
        self.fig, self.ax = plt.subplots()
        self.stream = self.data_stream()
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=40,
                                           init_func=self.setup_plot)

    def setup_plot(self):
        """Initial drawing of the scatter plot."""
        casharr,idarr = next(self.stream)

        self.pie = self.ax.pie(casharr, labels=idarr)

        return self.pie,

    def data_stream(self):
        for timestep in self.data:
            casharr = []
            idarr = []
            for (cash, id) in timestep:
                casharr.append(cash)
                idarr.append(id)
            yield casharr,idarr

    def update(self, i):
        self.ax.clear()
        self.ax.axis('equal')
        casharr,idarr = next(self.stream)
        self.pie = self.ax.pie(casharr, labels=idarr)
        self.ax.set_title("Timestep : " + str(i))
        return self.pie,

    def save(self):
        self.ani.save('line.mp4', writer='ffmpeg', dpi=80)

    def show(self):
        plt.show()
        
anim = InsuranceFirmAnimation(first_run_reinsurance)
anim.show()
