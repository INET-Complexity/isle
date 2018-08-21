import matplotlib.pyplot as plt
import numpy as np

rfile = open("data/contracts.dat","r")
contracts = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/operational.dat","r")
op = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/cash.dat","r")
cash = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/profitslosses.dat","r")
pl = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reincontracts.dat","r")
reincontracts = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reinoperational.dat","r")
reinop = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reincash.dat","r")
reincash = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reinprofitslosses.dat","r")
reinpl = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/premium.dat","r")
premium = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/catbonds_number.dat","r")
catbop = [eval(k) for k in rfile]
rfile.close()

c_s = []

o_s = []

h_s = []

p_s = []

pl_s = []

c_re = []

o_re= []

h_re = []

pl_re = []

o_cb = []

p_e = []

for i in range(len(contracts[0])):
    cs = np.mean([item[i] for item in contracts])
    pls = np.mean([item[i] for item in pl])
    os = np.median([item[i] for item in op])
    hs = np.median([item[i] for item in cash])
    c_s.append(cs)
    pl_s.append(pls)
    o_s.append(os)
    h_s.append(hs)


    cre = np.mean([item[i] for item in reincontracts])
    plre = np.mean([item[i] for item in reinpl])
    ore = np.median([item[i] for item in reinop])
    hre = np.median([item[i] for item in reincash])
    c_re.append(cre)
    pl_re.append(plre)
    o_re.append(ore)
    h_re.append(hre)
    
    ocb = np.median([item[i] for item in catbop])
    o_cb.append(ocb)
    
    p_s = np.median([item[i] for item in premium])
    p_e.append(p_s)

fig1 = plt.figure()
ax0 = fig1.add_subplot(511)
ax0.get_xaxis().set_visible(False)
ax0.plot(range(len(c_s)), c_s,"b")
ax0.set_ylabel("Contracts")
ax1 = fig1.add_subplot(512)
ax1.get_xaxis().set_visible(False)
ax1.plot(range(len(o_s)), o_s,"b")
ax1.set_ylabel("Active firms")
ax2 = fig1.add_subplot(513)
ax2.get_xaxis().set_visible(False)
ax2.plot(range(len(h_s)), h_s,"b")
ax2.set_ylabel("Cash")
ax3 = fig1.add_subplot(514)
ax3.get_xaxis().set_visible(False)
ax3.plot(range(len(pl_s)), pl_s,"b")
ax3.set_ylabel("Profits, Losses")
ax9 = fig1.add_subplot(515)
ax9.plot(range(len(p_e)), p_e,"k")
ax9.set_ylabel("Premium")
ax9.set_xlabel("Time")
plt.savefig("data/single_replication_pt1.pdf")

fig2 = plt.figure()
ax4 = fig2.add_subplot(511)
ax4.get_xaxis().set_visible(False)
ax4.plot(range(len(c_re)), c_re,"r")
ax4.set_ylabel("Contracts")
ax5 = fig2.add_subplot(512)
ax5.get_xaxis().set_visible(False)
ax5.plot(range(len(o_re)), o_re,"r")
ax5.set_ylabel("Active reinfirms")
ax6 = fig2.add_subplot(513)
ax6.get_xaxis().set_visible(False)
ax6.plot(range(len(h_re)), h_re,"r")
ax6.set_ylabel("Cash")
ax7 = fig2.add_subplot(514)
ax7.get_xaxis().set_visible(False)
ax7.plot(range(len(pl_re)), pl_re,"r")
ax7.set_ylabel("Profits, Losses")
ax8 = fig2.add_subplot(515)
ax8.plot(range(len(o_cb)), o_cb,"m")
ax8.set_ylabel("Active cat bonds")

plt.savefig("data/single_replication_pt2.pdf")
plt.show()
