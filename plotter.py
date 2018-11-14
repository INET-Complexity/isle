import matplotlib.pyplot as plt
import numpy as np

rfile = open("data/history_logs.dat","r")

data = [eval(k) for k in rfile]

contracts = data[0]['total_contracts']
op = data[0]['total_operational']
cash = data[0]['total_cash']
pl = data[0]['total_profitslosses']
reincontracts = data[0]['total_reincontracts']
reinop = data[0]['total_reinoperational']
reincash = data[0]['total_reincash']
reinpl = data[0]['total_reinprofitslosses']
premium = data[0]['market_premium']
catbop = data[0]['total_catbondsoperational']

rfile.close()

cs = contracts
pls = pl
os = op
hs = cash

cre = reincontracts
plre = reinpl
ore = reinop
hre = reincash

ocb = catbop
ps = premium

fig1 = plt.figure()
ax0 = fig1.add_subplot(511)
ax0.get_xaxis().set_visible(False)
ax0.plot(range(len(cs)), cs,"b")
ax0.set_ylabel("Contracts")
ax1 = fig1.add_subplot(512)
ax1.get_xaxis().set_visible(False)
ax1.plot(range(len(os)), os,"b")
ax1.set_ylabel("Active firms")
ax2 = fig1.add_subplot(513)
ax2.get_xaxis().set_visible(False)
ax2.plot(range(len(hs)), hs,"b")
ax2.set_ylabel("Cash")
ax3 = fig1.add_subplot(514)
ax3.get_xaxis().set_visible(False)
ax3.plot(range(len(pls)), pls,"b")
ax3.set_ylabel("Profits, Losses")
ax9 = fig1.add_subplot(515)
ax9.plot(range(len(ps)), ps,"k")
ax9.set_ylabel("Premium")
ax9.set_xlabel("Time")
plt.savefig("data/single_replication_pt1.pdf")

fig2 = plt.figure()
ax4 = fig2.add_subplot(511)
ax4.get_xaxis().set_visible(False)
ax4.plot(range(len(cre)), cre,"r")
ax4.set_ylabel("Contracts")
ax5 = fig2.add_subplot(512)
ax5.get_xaxis().set_visible(False)
ax5.plot(range(len(ore)), ore,"r")
ax5.set_ylabel("Active reinfirms")
ax6 = fig2.add_subplot(513)
ax6.get_xaxis().set_visible(False)
ax6.plot(range(len(hre)), hre,"r")
ax6.set_ylabel("Cash")
ax7 = fig2.add_subplot(514)
ax7.get_xaxis().set_visible(False)
ax7.plot(range(len(plre)), plre,"r")
ax7.set_ylabel("Profits, Losses")
ax8 = fig2.add_subplot(515)
ax8.plot(range(len(ocb)), ocb,"m")
ax8.set_ylabel("Active cat bonds")
ax8.set_xlabel("Time")

plt.savefig("data/single_replication_pt2.pdf")
plt.show()
