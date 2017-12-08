import matplotlib.pyplot as plt
import numpy as np
import pdb
import os
import time
import glob

def read_data():
    # do not overwrite old pdfs
    #if os.path.exists("data/fig_one_and_two_rm_comp.pdf"):
    #    os.rename("data/fig_one_and_two_rm_comp.pdf", "data/fig_one_and_two_rm_comp_old_" + time.strftime('%Y_%b_%d_%H_%M') + ".pdf")
    #if os.path.exists("data/fig_three_and_four_rm_comp.pdf"):
    #    os.rename("data/fig_three_and_four_rm_comp.pdf", "data/fig_three_and_four_rm_comp_old_" + time.strftime('%Y_%b_%d_%H_%M') + ".pdf")

    upper_bound = 75
    lower_bound = 25

    timeseries_dict = {}
    timeseries_dict["mean"] = {}
    timeseries_dict["median"] = {}
    timeseries_dict["quantile25"] = {}
    timeseries_dict["quantile75"] = {}

    filenames_ones = glob.glob("data/one*.dat")
    filenames_twos = glob.glob("data/two*.dat")
    filenames_threes = glob.glob("data/three*.dat")
    filenames_fours = glob.glob("data/four*.dat")
    filenames_ones.sort()
    filenames_twos.sort()
    filenames_threes.sort()
    filenames_fours.sort()

    assert len(filenames_ones) == len(filenames_twos) == len(filenames_threes) == len(filenames_fours)
    all_filenames = filenames_ones + filenames_twos + filenames_threes + filenames_fours

    for filename in all_filenames:
        # read files
        rfile = open(filename, "r")
        data = [eval(k) for k in rfile]
        rfile.close()
        
        # compute data series
        data_means = []
        data_medians = []
        data_q25 = []
        data_q75 = []
        for i in range(len(data[0])):
            data_means.append(np.mean([item[i] for item in data]))
            data_q25.append(np.percentile([item[i] for item in data], lower_bound))
            data_q75.append(np.percentile([item[i] for item in data], upper_bound))
            data_medians.append(np.median([item[i] for item in data]))
        data_means = np.array(data_means)
        data_medians = np.array(data_medians)
        data_q25 = np.array(data_q25)
        data_q75 = np.array(data_q75)
        
        # record data series
        timeseries_dict["mean"][filename] = data_means
        timeseries_dict["median"][filename] = data_medians
        timeseries_dict["quantile25"][filename] = data_q25
        timeseries_dict["quantile75"][filename] = data_q75
    return timeseries_dict
        
    

def plotting(output_label, timeseries_dict, riskmodelsetting1, riskmodelsetting2, series1, series2=None, additionalriskmodelsetting3=None, additionalriskmodelsetting4=None, plottype1="mean", plottype2="mean"):
    # dictionaries
    colors = {"one": "red", "two": "blue", "three": "green", "four": "yellow"}
    labels = {"contracts": "Contracts (Insurers)", "cash": "Liquidity (Insurers)", "operational": "Active Insurers", "premium": "Premium", "reincash": "Liquidity (Reinsurers)", "reincontracts": "Contracts (Reinsurers)", "reinoperational": "Active Reinsurers"}
    
    # prepare labels, timeseries, etc.
    color1 = colors[riskmodelsetting1]
    color2 = colors[riskmodelsetting2]
    label1 = str.upper(riskmodelsetting1[0]) + riskmodelsetting1[1:] + " riskmodels"
    label2 = str.upper(riskmodelsetting2[0]) + riskmodelsetting2[1:] + " riskmodels"
    plot_1_1 = "data/" + riskmodelsetting1 + "_" + series1 + ".dat"
    plot_1_2 = "data/" + riskmodelsetting2 + "_" + series1 + ".dat"
    if series2 is not None:
        plot_2_1 = "data/" + riskmodelsetting1 + "_" + series2 + ".dat"
        plot_2_2 = "data/" + riskmodelsetting2 + "_" + series2 + ".dat"
    if additionalriskmodelsetting3 is not None:
        color3 = colors[additionalriskmodelsetting3]
        label3 = str.upper(additionalriskmodelsetting3[0]) + additionalriskmodelsetting3[1:] + " riskmodels"
        plot_1_3 = "data/" + additionalriskmodelsetting3 + "_" + series1 + ".dat"
        if series2 is not None:
            plot_2_3 = "data/" + additionalriskmodelsetting3 + "_" + series2 + ".dat"
    if additionalriskmodelsetting4 is not None:
        color4 = colors[additionalriskmodelsetting4]
        label4 = str.upper(additionalriskmodelsetting4[0]) + additionalriskmodelsetting4[1:] + " riskmodels"
        plot_1_4 = "data/" + additionalriskmodelsetting4 + "_" + series1 + ".dat"
        if series2 is not None:
            plot_2_4 = "data/" + additionalriskmodelsetting4 + "_" + series2 + ".dat"
    
    # Backup existing figures (so as not to overwrite them)
    outputfilename = "data/" + output_label + ".pdf"
    backupfilename = "data/" + output_label + "_old_" + time.strftime('%Y_%b_%d_%H_%M') + ".pdf"
    if os.path.exists(outputfilename):
        os.rename(outputfilename, backupfilename)
    
    # Plot and save
    fig = plt.figure()
    if series2 is not None:
        ax0 = fig.add_subplot(211)
    else:
        ax0 = fig.add_subplot(111)
    if additionalriskmodelsetting3 is not None:
        ax0.plot(range(len(timeseries_dict[plottype1][plot_1_3])), timeseries_dict[plottype1][plot_1_3], color=color3, label=label3)
    if additionalriskmodelsetting4 is not None:
        ax0.plot(range(len(timeseries_dict[plottype1][plot_1_4])), timeseries_dict[plottype1][plot_1_4], color=color4, label=label4)   
    ax0.plot(range(len(timeseries_dict[plottype1][plot_1_1])), timeseries_dict[plottype1][plot_1_1], color=color1, label=label1)
    ax0.plot(range(len(timeseries_dict[plottype1][plot_1_2])), timeseries_dict[plottype1][plot_1_2], color=color2, label=label2)
    ax0.fill_between(range(len(timeseries_dict["quantile25"][plot_1_1])), timeseries_dict["quantile25"][plot_1_1], timeseries_dict["quantile75"][plot_1_1], facecolor=color1, alpha=0.25)
    ax0.fill_between(range(len(timeseries_dict["quantile25"][plot_1_1])), timeseries_dict["quantile25"][plot_1_2], timeseries_dict["quantile75"][plot_1_2], facecolor=color2, alpha=0.25)
    ax0.set_ylabel(labels[series1])#"Contracts")
    ax0.legend(loc='best')
    if series2 is not None:
        ax1 = fig.add_subplot(212)
        if additionalriskmodelsetting3 is not None:
            ax1.plot(range(len(timeseries_dict[plottype2][plot_2_3])), timeseries_dict[plottype2][plot_2_3], color=color3, label=label3)
        if additionalriskmodelsetting4 is not None:
            ax1.plot(range(len(timeseries_dict[plottype2][plot_2_4])), timeseries_dict[plottype2][plot_2_4], color=color4, label=label4)   
        ax1.plot(range(len(timeseries_dict[plottype2][plot_2_1])), timeseries_dict[plottype2][plot_2_1], color=color1, label=label1)
        ax1.plot(range(len(timeseries_dict[plottype2][plot_2_2])), timeseries_dict[plottype2][plot_2_2], color=color2, label=label2)
        ax1.fill_between(range(len(timeseries_dict["quantile25"][plot_2_1])), timeseries_dict["quantile25"][plot_2_1], timeseries_dict["quantile75"][plot_2_1], facecolor=color1, alpha=0.25)
        ax1.fill_between(range(len(timeseries_dict["quantile25"][plot_2_1])), timeseries_dict["quantile25"][plot_2_2], timeseries_dict["quantile75"][plot_2_2], facecolor=color2, alpha=0.25)
        ax1.set_ylabel(labels[series2])
        ax1.set_xlabel("Time")
    plt.savefig(outputfilename)
    plt.show()

timeseries = read_data()

# for just two different riskmodel settings
plotting(output_label="fig_contracts_survival_1_2", timeseries_dict=timeseries, riskmodelsetting1="one", \
    riskmodelsetting2="two", series1="contracts", series2="operational", plottype1="mean", plottype2="median")
plotting(output_label="fig_reinsurers_contracts_survival_1_2", timeseries_dict=timeseries, riskmodelsetting1="one", \
    riskmodelsetting2="two", series1="reincontracts", series2="reinoperational", plottype1="mean", plottype2="median")
plotting(output_label="fig_premium_1_2", timeseries_dict=timeseries, riskmodelsetting1="one", riskmodelsetting2="two", \
    series1="premium", series2=None, plottype1="mean", plottype2=None)

raise SystemExit
# for four different riskmodel settings
plotting(output_label="fig_contracts_survival_1_2", timeseries_dict=timeseries, riskmodelsetting1="one", \
        riskmodelsetting2="two", series1="contracts", series2="operational", additionalriskmodelsetting3="three", \
        additionalriskmodelsetting4="four", plottype1="mean", plottype2="median")
plotting(output_label="fig_contracts_survival_3_4", timeseries_dict=timeseries, riskmodelsetting1="three", \
        riskmodelsetting2="four", series1="contracts", series2="operational",  additionalriskmodelsetting3="one", \
        additionalriskmodelsetting4="two", plottype1="mean", plottype2="median")
plotting(output_label="fig_reinsurers_contracts_survival_1_2", timeseries_dict=timeseries, riskmodelsetting1="one", \
        riskmodelsetting2="two", series1="reincontracts", series2="reinoperational", \
        additionalriskmodelsetting3="three", additionalriskmodelsetting4="four", plottype1="mean", plottype2="median")
plotting(output_label="fig_reinsurers_contracts_survival_3_4", timeseries_dict=timeseries, riskmodelsetting1="three", \
        riskmodelsetting2="four", series1="reincontracts", series2="reinoperational", \
        additionalriskmodelsetting3="one", additionalriskmodelsetting4="two", plottype1="mean", plottype2="median")
plotting(output_label="fig_premium_1_2", timeseries_dict=timeseries, riskmodelsetting1="one", riskmodelsetting2="two", \
        series1="premium", series2=None, additionalriskmodelsetting3="three", additionalriskmodelsetting4="four", \
        plottype1="mean", plottype2=None)

#pdb.set_trace()
