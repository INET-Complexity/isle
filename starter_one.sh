mv data/one_operational.dat data/one_operational.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_contracts.dat data/one_contracts.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_cash.dat data/one_cash.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_reinoperational.dat data/one_reinoperational.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_reincontracts.dat data/one_reincontracts.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_reincash.dat data/one_reincash.dat_$(date +%Y_%h_%d_%H_%M)
mv data/one_premium.dat data/one_premium.dat_$(date +%Y_%h_%d_%H_%M)

for ((i=0; i<300; i++)) do
    python3 start.py --replicid $i --replicating --oneriskmodel
done

