# simple-PoW-based-consensus
Proof of Play, a simple blockchain consensus based on PoW

## simulation.py

run the script in the terminal as following:

```
python simulation.py -n 1000 -l 2 -p 10 -c 5 -t 254
```

where:
* ```-n``` defines the number of blocks to mine,
* ```-l``` defines the amount of logging messages in the terminal,
* ```-p``` defines the number of player (Process) to run the in mining,
* ```-c``` defines the expected confirmation time,
* ```-t``` defines the base-2-power of the target value of the PoW mining (Bitcoin is 2^224, so the base-2-power is 224)