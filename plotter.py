import matplotlib.pyplot as plt
import numpy as np

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

o_one = []
o_two = []

for i in range(len(contracts_one[0])):
    c1 = np.mean([item[i] for item in contracts_one])
    c2 = np.mean([item[i] for item in contracts_two])
    #o1 = np.mean([item[i] for item in op_one])
    #o2 = np.mean([item[i] for item in op_two])
    #c1 = np.median([item[i] for item in contracts_one])
    #c2 = np.median([item[i] for item in contracts_two])
    o1 = np.median([item[i] for item in op_one])
    o2 = np.median([item[i] for item in op_two])
    c_one.append(c1)
    c_two.append(c2)
    o_one.append(o1)
    o_two.append(o2)
    
print(contracts_one)
print(contracts_two)
print(c_one)
print(c_two)

fig = plt.figure()
ax0 = fig.add_subplot(211)
ax0.plot(range(len(c_one)), c_one,"r")
ax0.plot(range(len(c_two)), c_two,"b")
ax0.set_ylabel("Contracts")
ax1 = fig.add_subplot(212)
ax1.plot(range(len(o_one)), o_one,"r")
ax1.plot(range(len(o_two)), o_two,"b")
ax1.set_ylabel("Active firms (out of initially 20)")
ax1.set_xlabel("Time")
plt.show()
