mv data/one_operational.dat data/one_operational.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_contracts.dat data/one_contracts.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_cash.dat data/one_cash.dat_$(date +%Y_%h_%d_%H_%M)

for ((i=0; i<300; i++)) do
    python insurancesimulation_one.py $i
done

