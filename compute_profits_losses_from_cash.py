rm = ["one", "two", "three", "four"]
firmtype = ["", "rein"]

for r in rm:
    for ft in firmtype:
        filename = "data/" + r + "_" + ft + "cash.dat"
        infile = open(filename, "r")
        data = [eval(k) for k in infile]
        infile.close()
        filename = "data/" + r + "_" + ft + "profitslosses.dat"
        outfile = open(filename, "w")
        
        for series in data:
            outputdata = [series[i]-series[i-1] for i in range(1, len(series))]
            outfile.write(str(outputdata) + "\n")
        
        outfile.close()

    
