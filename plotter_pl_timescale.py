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

#rfile = open("data/profitslosses.dat","r")
#pl = [eval(k) for k in rfile]
#rfile.close()

rfile = open("data/reincontracts.dat","r")
reincontracts = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reinoperational.dat","r")
reinop = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/reincash.dat","r")
reincash = [eval(k) for k in rfile]
rfile.close()

#rfile = open("data/reinprofitslosses.dat","r")
#reinpl = [eval(k) for k in rfile]
#rfile.close()

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

for i in range(len(contracts[0])):                              #for every time period i
    cs = np.mean([item[i] for item in contracts])
    #pls = np.mean([item[i] for item in pl])
    os = np.median([item[i] for item in op])
    hs = np.median([item[i] for item in cash])
    c_s.append(cs)
    o_s.append(os)
    h_s.append(hs)

    if i>0:
        pls = np.mean([item[i]-item[i-1] for item in cash])
        plre = np.mean([item[i]-item[i-1] for item in reincash])
        pl_s.append(pls)
        pl_re.append(plre)

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


maxlen_plots = max(len(pl_s), len(pl_re), len(o_s), len(o_re), len(p_e))
xticks =  np.arange(200, maxlen_plots, step=120)
fig0 = plt.figure()
ax3 = fig0.add_subplot(511)
ax3.plot(range(len(pl_s))[200:], pl_s[200:],"b")
ax3.set_ylabel("Profits, Losses")
ax3.set_xticks(xticks)
ax3.set_xticklabels(["${0:d}$".format(int((xtc-200)/12)) for xtc in xticks])
ax7 = fig0.add_subplot(512)
ax7.plot(range(len(pl_re))[200:], pl_re[200:],"r")
ax7.set_ylabel("Profits, Losses (Reins.)")
ax7.set_xticks(xticks)
ax7.set_xticklabels(["${0:d}$".format(int((xtc-200)/12)) for xtc in xticks])
ax1 = fig0.add_subplot(513)
ax1.plot(range(len(o_s))[200:], o_s[200:],"b")
ax1.set_ylabel("Active firms")
ax1.set_xticks(xticks)
ax1.set_xticklabels(["${0:d}$".format(int((xtc-200)/12)) for xtc in xticks])
ax5 = fig0.add_subplot(514)
ax5.plot(range(len(o_re))[200:], o_re[200:],"r")
ax5.set_ylabel("Active reins. firms")
ax5.set_xticks(xticks)
ax5.set_xticklabels(["${0:d}$".format(int((xtc-200)/12)) for xtc in xticks])
ax9 = fig0.add_subplot(515)
ax9.plot(range(len(p_e))[200:], p_e[200:],"k")
ax9.set_ylabel("Premium")
ax9.set_xlabel("Years")
ax9.set_xticks(xticks)
ax9.set_xticklabels(["${0:d}$".format(int((xtc-200)/12)) for xtc in xticks])


plt.savefig("data/single_replication_new.pdf")
plt.show()


raise SystemExit
