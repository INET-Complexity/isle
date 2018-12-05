export timestamp="$(date +%Y_%h_%d_%H_%M)"  # to ensure they are identical
mv data/replication_rc_event_schedule.dat{,_$timestamp}
mv data/replication_randomseed.dat{,_$timestamp}
mv data/two_operational.dat{,_$timestamp}
mv data/two_contracts.dat{,_$timestamp}
mv data/two_cash.dat{,_$timestamp}
mv data/two_reinoperational.dat{,_$timestamp}
mv data/two_reincontracts.dat{,_$timestamp}
mv data/two_reincash.dat{,_$timestamp}
mv data/two_premium.dat{,_$timestamp}

for ((i=0; i<300; i++)) do
    python3 start.py --replicid $i 
done
