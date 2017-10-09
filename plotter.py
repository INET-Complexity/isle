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

c_s = []

o_s = []

h_s = []

c_re = []

o_re= []

h_re = []

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

fig = plt.figure()
ax0 = fig.add_subplot(611)
ax0.plot(range(len(c_s)), c_s,"b")
ax0.set_ylabel("Contracts")
ax1 = fig.add_subplot(612)
ax1.plot(range(len(o_s)), o_s,"b")
ax1.set_ylabel("Active firms (out of initially 20)")
ax0 = fig.add_subplot(613)
ax0.plot(range(len(h_s)), h_s,"b")
ax0.set_ylabel("Cash")
ax0 = fig.add_subplot(614)
ax0.plot(range(len(c_re)), c_re,"r")
ax0.set_ylabel("Contracts")
ax1 = fig.add_subplot(615)
ax1.plot(range(len(o_re)), o_re,"r")
ax1.set_ylabel("Active reinfirms (out of initially 1)")
ax0 = fig.add_subplot(616)
ax0.plot(range(len(h_re)), h_re,"r")
ax0.set_ylabel("Cash")
ax1.set_xlabel("Time")
plt.show()
