mv data/three_operational.dat data/three_operational.dat_$(date +%Y_%h_%d_%H_%M)
mv data/three_contracts.dat data/three_contracts.dat_$(date +%Y_%h_%d_%H_%M)
mv data/three_cash.dat data/three_cash.dat_$(date +%Y_%h_%d_%H_%M)
mv data/three_reinoperational.dat data/three_reinoperational.dat_$(date +%Y_%h_%d_%H_%M)
mv data/three_reincontracts.dat data/three_reincontracts.dat_$(date +%Y_%h_%d_%H_%M)
mv data/three_reincash.dat data/three_reincash.dat_$(date +%Y_%h_%d_%H_%M)

for ((i=0; i<3; i++)) do
    #python insurancesimulation_one.py $i
    python start.py --abce 0 --replicid $i --replicating --riskmodels 3
done
