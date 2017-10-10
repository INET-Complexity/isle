mv data/rc_event_schedule.dat data/rc_event_schedule.dat_$(date +%Y_%h_%d_%H_%M)
mv data/two_operational.dat data/two_operational.dat_$(date +%Y_%h_%d_%H_%M)
mv data/two_contracts.dat data/two_contracts.dat_$(date +%Y_%h_%d_%H_%M)
mv data/two_cash.dat data/two_cash.dat_$(date +%Y_%h_%d_%H_%M)

for ((i=0; i<300; i++)) do
    python insurancesimulation.py $i
done
