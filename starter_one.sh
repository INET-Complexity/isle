export timestamp="$(date +%Y_%h_%d_%H_%M)"  # to ensure they are identical
mv data/one_operational.dat{,_$timestamp}
mv data/one_contracts.dat{,_$timestamp}
mv data/one_cash.dat{,_$timestamp}
mv data/one_reinoperational.dat{,_$timestamp}
mv data/one_reincontracts.dat{,_$timestamp}
mv data/one_reincash.dat{,_$timestamp}
mv data/one_premium.dat{,_$timestamp}

for ((i=0; i<300; i++)) do
    python3 start.py --replicid $i --replicating --oneriskmodel
done

