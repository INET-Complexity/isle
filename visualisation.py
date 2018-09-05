# file to visualise all data produced from a SINGLE simulation run (plotter.py OBSOLETE)
# TODO: include support for ensemble runs

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# load in data from the history_logs dictionary
with open("data/history_logs.dat","r") as rfile:
    history_logs = eval(rfile.read())

#print(history_logs.keys())

# agent-level data


# re-load insurance firm data as numpy variables


# shape (runs, steps)

class TimeSeries(object):
    #TODO: more illuminating variable names, this is basically obsfuscated    
    #TODO: rename ax5 to something nicer, something that generalises catbonds/premiums
    def __init__(self, contracts, profitslosses, operational, cash, ax5, ax5label, title):

        self.c_s = []
        self.o_s = []
        self.h_s = []
        self.pl_s = []
        self.p_e = []

        self.ax5label = ax5label
        self.title = title
        self.timesteps = [t for t in range(len(contracts))]

        for t in self.timesteps:
            cs = np.mean([item[t] for item in contracts])
            pls = np.mean([item[t] for item in profitslosses])
            os = np.median([item[t] for item in operational])
            hs = np.median([item[t] for item in cash])
            p_s = np.median([item[t] for item in ax5])
                
            self.c_s.append(cs)
            self.pl_s.append(pls)
            self.o_s.append(os)
            self.h_s.append(hs)
            self.p_e.append(p_s)

        def plot(self):
            self.fig, self.axlist = plt.subplots(5,sharex=True)
            self.axlist[0].plot(self.timesteps), c_s, "b")
            self.axlist[0].set_ylabel("Contracts")
            self.axlist[1].plot(self.timesteps, o_s, "b")
            self.axlist[1].set_ylabel("Active firms")
            self.axlist[2].plot(self.timesteps, h_s, "b")
            self.axlist[2].set_ylabel("Cash")
            self.axlist[3].plot(self.timesteps, pl_s, "b")
            self.axlist[3].set_ylabel("Profits, Losses")
            self.axlist[4].plot(self.timesteps, p_e, "k")
            self.axlist[4].set_ylabel(ax5label)
            self.axlist[4].set_xlabel("Time")
            self.fig.savefig("{title}.pdf".format(title=self.title))
            return self.fig, self.axlist

# let's look at only the first run
first_run_insurance = insurance_firms_cash[:]
first_run_reinsurance = reinsurance_firms_cash[:]

class InsuranceFirmAnimation(object):
    '''class takes in a run of insurance data and produces animations '''
    def __init__(self, data):
        self.data = data
        self.fig, self.ax = plt.subplots()
        self.stream = self.data_stream()
        self.ani = animation.FuncAnimation(self.fig, self.update, repeat=False, interval=100,)
                                           #init_func=self.setup_plot)

    def setup_plot(self):
        """Initial drawing of the plots."""
        casharr,idarr = next(self.stream)
        self.pie = self.ax.pie(casharr, labels=idarr,autopct='%1.0f%%')
        return self.pie,

    def data_stream(self):
        for timestep in self.data:
            casharr = []
            idarr = []
            for (cash, id, operational) in timestep:
                if operational:
                    casharr.append(cash)
                    idarr.append(id)
            yield casharr,idarr

    def update(self, i):
        self.ax.clear()
        self.ax.axis('equal')
        casharr,idarr = next(self.stream)
        self.pie = self.ax.pie(casharr, labels=idarr,autopct='%1.0f%%')
        self.ax.set_title("Timestep : {:,.0f} | Total cash : {:,.0f}".format(i,sum(casharr)))
        return self.pie,

    def save(self,filename):
        self.ani.save(filename, writer='ffmpeg', dpi=80)

    def show(self):
        plt.show()

class visualisation(object):
    def __init__(self, history_logs):
        self.operational = history_logs['total_operational']
        self.contracts = history_logs['total_contracts']
        self.cash = history_logs['total_cash']
        self.excess_capital = history_logs['total_excess_capital']
        self.profitslosses = history_logs['total_profitslosses']
        self.reinoperational = history_logs['total_reinoperational']
        self.reincontracts = history_logs['total_reincontracts']
        self.reincash = history_logs['total_reincash']
        self.reinexcess_capital = history_logs['total_reinexcess_capital']
        self.reinprofitslosses = history_logs['total_reinprofitslosses']
        self.catbonds_number = history_logs['total_catbondsoperational']
        self.premium = history_logs['market_premium']
        self.diffvar = history_logs['market_diffvar']
        self.cumulative_bankruptcies = history_logs['cumulative_bankruptcies']
        self.cumulative_unrecovered_claims = history_logs['cumulative_unrecovered_claims']
        self.insurance_cash = np.array(history_logs['insurance_firms_cash'])
        self.reinsurance_cash = np.array(history_logs['reinsurance_firms_cash'])
        return

    def insurer_pie_animation(self):
        self.ins_pie_anim = InsuranceFirmAnimation(self.insurance_cash)
        return self.ins_pie_anim

    def reinsurer_pie_animation(self):
        self.reins_pie_anim = InsuranceFirmAnimation(self.reinsurance_cash)
        return self.reins_pie_anim

    def show(self):
        plt.show()
        return



#vis = visualisation(first_run_insurance,first_run_reinsurance)
#vis.insurer_pie_animation()
#vis.reinsurer_pie_animation()
#vis.show()
