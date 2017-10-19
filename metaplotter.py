import matplotlib.pyplot as plt
import numpy as np
import pdb
import os
import time

# do not overwrite old pdf
if os.path.exists("data/fig_one_and_two_rm_comp.pdf"):
    os.rename("data/fig_one_and_two_rm_comp.pdf", "data/fig_one_and_two_rm_comp_old_" + time.strftime('%Y_%b_%d_%H_%M') + ".pdf")

upper_bound = 75
lower_bound = 25

rfile = open("data/one_contracts.dat","r")
contracts_one = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/two_contracts.dat","r")
contracts_two = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/one_operational.dat","r")
op_one = [eval(k) for k in rfile]
rfile.close()

rfile = open("data/two_operational.dat","r")
op_two = [eval(k) for k in rfile]
rfile.close()

c_one = []
c_two = []

c_one_lo = []
c_one_up = []
c_two_lo = []
c_two_up = []

o_one = []
o_two = []

o_one_lo = []
o_one_up = []
o_two_lo = []
o_two_up = []


for i in range(len(contracts_one[0])):
    c1 = np.mean([item[i] for item in contracts_one])
    c2 = np.mean([item[i] for item in contracts_two])
    c1_lo = np.percentile([item[i] for item in contracts_one], lower_bound)
    c1_up = np.percentile([item[i] for item in contracts_one], upper_bound)
    c2_lo = np.percentile([item[i] for item in contracts_two], lower_bound)
    c2_up = np.percentile([item[i] for item in contracts_two], upper_bound)
    #o1 = np.mean([item[i] for item in op_one])
    #o2 = np.mean([item[i] for item in op_two])
    #c1 = np.median([item[i] for item in contracts_one])
    #c2 = np.median([item[i] for item in contracts_two])
    o1 = np.median([item[i] for item in op_one])
    o2 = np.median([item[i] for item in op_two])
    o1_lo = np.percentile([item[i] for item in op_one], lower_bound)
    o1_up = np.percentile([item[i] for item in op_one], upper_bound)
    o2_lo = np.percentile([item[i] for item in op_two], lower_bound)
    o2_up = np.percentile([item[i] for item in op_two], upper_bound)
    c_one.append(c1)
    c_two.append(c2)
    c_one_up.append(c1_up)
    c_one_lo.append(c1_lo)
    c_two_up.append(c2_up)
    c_two_lo.append(c2_lo)
    o_one.append(o1)
    o_two.append(o2)
    o_one_up.append(o1_up)
    o_one_lo.append(o1_lo)
    o_two_up.append(o2_up)
    o_two_lo.append(o2_lo)
    
print(contracts_one)
print(contracts_two)
print(c_one)
print(c_two)
print(len(c_one), len(c_one_up))
#pdb.set_trace()

fig = plt.figure()
ax0 = fig.add_subplot(211)
ax0.plot(range(len(c_one)), c_one,"r", label="One riskmodel")
ax0.plot(range(len(c_two)), c_two,"b", label="Two riskmodels")
ax0.fill_between(range(len(c_one)), c_one_lo, c_one_up, facecolor='red', alpha=0.25)
ax0.fill_between(range(len(c_two)), c_two_lo, c_two_up, facecolor='blue', alpha=0.25)
ax0.set_ylabel("Contracts")
ax0.legend(loc='best')
ax1 = fig.add_subplot(212)
ax1.plot(range(len(o_one)), o_one,"r")
ax1.plot(range(len(o_two)), o_two,"b")
ax1.fill_between(range(len(o_one)), o_one_lo, o_one_up, facecolor='red', alpha=0.25)
ax1.fill_between(range(len(o_two)), o_two_lo, o_two_up, facecolor='blue', alpha=0.25)
ax1.set_ylabel("Active firms (out of initially 20)")
ax1.set_xlabel("Time")
plt.savefig("data/fig_one_and_two_rm_comp.pdf")
plt.show()
