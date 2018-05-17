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

rfile = open("data/reincontracts.dat","r")
reincontracts = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reinoperational.dat","r")
reinop = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reincash.dat","r")
reincash = [eval(k) for k in rfile]
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

c_re = []

o_re= []

h_re = []

o_cb = []

p_e = []

for i in range(len(contracts[0])):
    cs = np.mean([item[i] for item in contracts])
    os = np.median([item[i] for item in op])
    hs = np.median([item[i] for item in cash])
    c_s.append(cs)
    o_s.append(os)
    h_s.append(hs)


    cre = np.mean([item[i] for item in reincontracts])
    ore = np.median([item[i] for item in reinop])
    hre = np.median([item[i] for item in reincash])
    c_re.append(cre)
    o_re.append(ore)
    h_re.append(hre)
    
    ocb = np.median([item[i] for item in catbop])
    o_cb.append(ocb)
    
    p_s = np.median([item[i] for item in premium])
    p_e.append(p_s)

fig = plt.figure()
ax0 = fig.add_subplot(811)
ax0.plot(range(len(c_s)), c_s,"b")
ax0.set_ylabel("Contracts")
ax1 = fig.add_subplot(812)
ax1.plot(range(len(o_s)), o_s,"b")
ax1.set_ylabel("Active firms")
ax2 = fig.add_subplot(813)
ax2.plot(range(len(h_s)), h_s,"b")
ax2.set_ylabel("Cash")
ax3 = fig.add_subplot(814)
ax3.plot(range(len(c_re)), c_re,"r")
ax3.set_ylabel("Contracts")
ax4 = fig.add_subplot(815)
ax4.plot(range(len(o_re)), o_re,"r")
ax4.set_ylabel("Active reinfirms")
ax5 = fig.add_subplot(816)
ax5.plot(range(len(h_re)), h_re,"r")
ax5.set_ylabel("Cash")
ax6 = fig.add_subplot(817)
ax6.plot(range(len(o_cb)), o_cb,"m")
ax6.set_ylabel("Active cat bonds")
ax7 = fig.add_subplot(818)
ax7.plot(range(len(p_e)), p_e,"k")
ax7.set_ylabel("Premium")
ax7.set_xlabel("Time")
plt.savefig("single_replication.pdf")
plt.show()
