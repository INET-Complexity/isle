import numpy as np
import csv
import os
import pdb
import scipy.stats

def allsim_filter(dirlist, series_name):
    filtered_list = []
    param_1 = []        #risk category number
    param_2 = []        #correlated probability
    param_3 = []        #risk oblivious setting
    param_4 = []        #risk category dimension number
    for dir in dirlist:
        dirpath = "result" + os.sep + dir + os.sep
        if os.path.isfile(dirpath + "description.txt"):
            simfile = open(dirpath + "description.txt","r")
            cfgdict = eval(simfile.read())
            if cfgdict.get('series') == series_name:
                filtered_list.append(dirpath)
                param_1.append(cfgdict.get("numberOfRiskCategories"))
                param_2.append(cfgdict.get("shareOfCorrelatedRisk"))
                param_3.append(cfgdict.get("numberOfRiskCategoryDimensions"))
                #if cfgdict["riskObliviousSetting"] is not None:
                param_4.append(cfgdict.get("riskObliviousSetting"))
    return [filtered_list, param_1, param_2, param_3, param_4]
    
def return_data(inputlist):
    [inputlist.append([]) for j in range(7)]
    for i in range(len(inputlist[0])):
        #rfile = open("result/abce_2017-06-15_02-50/aggregated_insurancefirm.csv","r")
        try:
            rfile = open(inputlist[0][i] + "aggregated_insurancefirm.csv","r")
        except:
            pdb.set_trace()
        csvinput = csv.reader(rfile)
        colnames = csvinput.__next__()
        rfile.close()
        #firstline = True
        #for l in csvinput:
        #    if firstline:
        aggregated_firmdata = np.genfromtxt(inputlist[0][i] + "aggregated_insurancefirm.csv", delimiter=",")[1:]
        aggregated_firmdata = aggregated_firmdata.T
        defaulted_timeseries = aggregated_firmdata[colnames.index("defaulted")]
        defaulted_final = defaulted_timeseries[-1]
        default_event_dist = [defaulted_timeseries[i] - defaulted_timeseries[i-1] for i in range(1, len(defaulted_timeseries)) if defaulted_timeseries[i] != defaulted_timeseries[i-1]]
        inputlist[5].append(defaulted_final)
        inputlist[6].append(default_event_dist)
        
        rfile = open(inputlist[0][i] + "insurancefirm.csv","r")
        csvinput = csv.reader(rfile)
        colnames = csvinput.__next__()
        rfile.close()
        firmdata = np.genfromtxt(inputlist[0][i] + "insurancefirm.csv", delimiter=",")[1:]
        firmdata = firmdata.T
        col_round = colnames.index('round')
        col_liquidity = colnames.index('money')
        col_contracts = colnames.index('num_contracts')
        col_defaulted = colnames.index('defaulted')
        last_round = max(firmdata[col_round])
        liquidity_dist = [firmdata[col_liquidity][i] for i in range(len(firmdata[col_liquidity])) if firmdata[col_round][i] == last_round]
        contracts_dist = [firmdata[col_contracts][i] for i in range(len(firmdata[col_contracts])) if firmdata[col_round][i] == last_round]
        defaulted_incid = [firmdata[col_defaulted][i] for i in range(len(firmdata[col_defaulted])) if firmdata[col_round][i] == last_round]
        liquidity_shares = np.asarray(liquidity_dist) / sum(liquidity_dist)
        contracts_shares = np.asarray(contracts_dist) / sum(contracts_dist)
        defaulted_incid = np.asarray(defaulted_incid) * (-1) + 1
        inputlist[7].append(liquidity_dist)
        inputlist[8].append(contracts_dist)
        inputlist[9].append(liquidity_shares)
        inputlist[10].append(contracts_shares)
        inputlist[11].append(defaulted_incid)
    #pdb.set_trace()
    return inputlist

def output(data):
    for i in range(len(data[0])):
        for j in range(len(data)):
            print(data[j][i])

def averaging(data):
    newdata = [[] for i in range(14)]
    for i in range(len(data[0])):
        if i == 0:
            datatype = data[3][i], data[4][i]
        else:
            try:
                assert datatype == (data[3][i], data[4][i])
            except:
                pdb.set_trace()
        candidates = [j for j in range(len(newdata[0])) if newdata[0][j]==data[1][i]]
        candidates = [j for j in candidates if newdata[1][j]==data[2][i]]
        try:
            assert len(candidates) < 2
        except:
            pdb.set_trace()
        if len(candidates) == 0:
            newdata[0].append(data[1][i])       #no risk categories
            newdata[1].append(data[2][i])       #share correlated
            newdata[2].append(data[5][i])       #no defaults
            if len(data[6][i]) > 0:
                newdata[3].append(np.mean(data[6][i]))       #avg size defaults
                newdata[13].append(1)
            else:
                newdata[3].append(-1)       #avg size defaults
                newdata[13].append(0)                
            newdata[4].append(len(data[6][i]))  #no default events
            if sum(data[11][i]) > 0:
                sizedist_liq = [data[9][i][j] for j in range(len(data[9][i])) if data[11][i][j]]
                try:
                    sizedist_con = [data[10][i][j] for j in range(len(data[10][i])) if data[11][i][j]]
                except:
                    pdb.set_trace()
                newdata[5].append(np.var(sizedist_liq)/np.mean(sizedist_liq))
                #print(newdata[5][-1])
                #pdb.set_trace()
                newdata[6].append(scipy.stats.skew(sizedist_liq))
                newdata[7].append(scipy.stats.kurtosis(sizedist_liq))
                newdata[8].append(np.var(sizedist_con)/np.mean(sizedist_con))
                newdata[9].append(scipy.stats.skew(sizedist_con))
                newdata[10].append(scipy.stats.kurtosis(sizedist_con))
                newdata[12].append(1)
            else:
                newdata[5].append(-1)
                newdata[6].append(-1)
                newdata[7].append(-1)
                newdata[8].append(-1)
                newdata[9].append(-1)
                newdata[10].append(-1)
                newdata[12].append(0)                
            newdata[11].append(1)
        else:
            idx = candidates[0]
            newdata[2][idx] = 1. / (newdata[11][idx]+1.) * (newdata[2][idx] * newdata[11][idx] + data[5][i])       #no defaults
            if len(data[6][i]) > 0:
                newdata[3][idx] = 1. / (newdata[13][idx]+1.) * (newdata[3][idx] * newdata[13][idx] + np.mean(data[6][i]))       #avg size defaults
                newdata[13][idx] += 1
            newdata[4][idx] = 1. / (newdata[11][idx]+1.) * (newdata[4][idx] * newdata[11][idx] + len(data[6][i]))  #no default events
            if sum(data[11][i]) > 0:
                sizedist_liq = [data[9][i][j] for j in range(len(data[9][i])) if data[11][i][j]]
                sizedist_con = [data[10][i][j] for j in range(len(data[10][i])) if data[11][i][j]]
                newdata[5][idx] = 1. / (newdata[12][idx]+1.) * (newdata[5][idx] * newdata[12][idx] + (np.var(sizedist_liq)/np.mean(sizedist_liq)))
                #print(newdata[5][idx])
                #pdb.set_trace()
                newdata[6][idx] = 1. / (newdata[12][idx]+1.) * (newdata[6][idx] * newdata[12][idx] + scipy.stats.skew(sizedist_liq))
                newdata[7][idx] = 1. / (newdata[12][idx]+1.) * (newdata[7][idx] * newdata[12][idx] + scipy.stats.kurtosis(sizedist_liq))
                newdata[8][idx] = 1. / (newdata[12][idx]+1.) * (newdata[8][idx] * newdata[12][idx] + (np.var(sizedist_con)/np.mean(sizedist_con)))
                newdata[9][idx] = 1. / (newdata[12][idx]+1.) * (newdata[9][idx] * newdata[12][idx] + scipy.stats.skew(sizedist_con))
                newdata[10][idx] = 1. / (newdata[12][idx]+1.) * (newdata[10][idx] * newdata[12][idx] + scipy.stats.kurtosis(sizedist_con))
                newdata[12][idx] += 1
            newdata[11][idx] += 1
    return newdata

allsims = os.listdir("result")
filtered = allsim_filter(allsims, "running002")
data = return_data(filtered)
#output(data)
plotdata = averaging(data)

for j in [2,3,4,5,6,7]:
    printv = np.zeros(12).reshape(4, 3)
    for i in range(len(plotdata[0])):
        x_dict = {.25: 0, .5: 1, .75: 2, 1.0: 3}
        y_dict = {2: 0, 5: 1, 10: 2}
        printv[x_dict[plotdata[1][i]]][y_dict[plotdata[0][i]]] = plotdata[j][i]

        #print(plotdata[0][i], plotdata[1][i], plotdata[2][i])

    print(printv)


