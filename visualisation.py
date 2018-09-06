# file to visualise all data produced from a SINGLE simulation run
# TODO: include support for ensemble runs

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# load in data from the history_logs dictionary
with open("data/history_logs.dat","r") as rfile:
    history_logs = eval(rfile.read())

class TimeSeries(object):
    #TODO: more illuminating variable names, this is basically obsfuscated    
    #TODO: rename ax5 to something nicer, something that generalises catbonds/premiums
    def __init__(self, contracts, profitslosses, operational, cash, ax5, ax5label, title):

        self.contracts = contracts
        self.profitslosses = profitslosses
        self.cash = cash
        self.operational = operational
        self.ax5 = ax5
        self.ax5label = ax5label
        self.title = title
        self.timesteps = [t for t in range(len(contracts))]
        self.plot() # we create the object when we want the plot so call plot() in the constructor

    def plot(self):
        #TODO: Add nicely formatted strings for axes labels (LaTeX markup?)
        self.fig, self.axlist = plt.subplots(5,sharex=True)
        self.axlist[0].plot(self.timesteps, self.contracts, "b")
        self.axlist[0].set_ylabel("Contracts")
        self.axlist[1].plot(self.timesteps, self.operational, "b")
        self.axlist[1].set_ylabel("Active firms")
        self.axlist[2].plot(self.timesteps, self.cash, "b")
        self.axlist[2].set_ylabel("Cash")
        self.axlist[3].plot(self.timesteps, self.profitslosses, "b")
        self.axlist[3].set_ylabel("Profits, Losses")
        self.axlist[4].plot(self.timesteps, self.ax5, "k")
        self.axlist[4].set_ylabel(self.ax5label)
        self.axlist[4].set_xlabel("Time")
        
        self.fig.suptitle(self.title)
        return self.fig, self.axlist

    def save(self, filename):
        self.fig.savefig("{filename}".format(filename=filename))
        return

class InsuranceFirmAnimation(object):
    '''class takes in a run of insurance data and produces animations '''
    def __init__(self, data):
        self.data = data
        self.fig, self.ax = plt.subplots()
        self.stream = self.data_stream()
        self.ani = animation.FuncAnimation(self.fig, self.update, repeat=False, interval=100,)
                                           #init_func=self.setup_plot)

    def setup_plot(self):
        # initial drawing of the plot
        casharr,idarr = next(self.stream)
        self.pie = self.ax.pie(casharr, labels=idarr,autopct='%1.0f%%')
        return self.pie,

    def data_stream(self):
        # unpack data in a format ready for update()
        for timestep in self.data:
            casharr = []
            idarr = []
            for (cash, id, operational) in timestep:
                if operational:
                    casharr.append(cash)
                    idarr.append(id)
            yield casharr,idarr

    def update(self, i):
        # clear plot and redraw
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
        # unpack history_logs
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

    def insurer_time_series(self):
        self.ins_time_series = TimeSeries(self.contracts, self.profitslosses, self.operational, self.cash, self.premium, "Premium", "Insurer")
        return self.ins_time_series

    def reinsurer_time_series(self):
        self.reins_time_series = TimeSeries(self.reincontracts, self.reinprofitslosses, self.reinoperational, self.reincash, self.catbonds_number, "Active Cat Bonds", "Reinsurer")
        return self.ins_time_series

    def show(self):
        plt.show()
        return


# first create visualisation object, then create graph/animation objects as necessary
vis = visualisation(history_logs)
#vis.insurer_pie_animation()
#vis.reinsurer_pie_animation()
vis.insurer_time_series().save("insurer_time_series.pdf")
vis.reinsurer_time_series().save("reinsurer_time_series.pdf")
vis.show()
