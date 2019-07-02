# Proof of Play mining
Proof of Play, a simple blockchain consensus based on PoW, PoS, and Proof-of-Excellence


## Background
Codes of the paper (BSCI 2019, Workshop under ASIACCS 2019):

Proof-of-Play: A Novel Consensus Model for Blockchain-based Peer-to-Peer Gaming System, 

**Ho Yin Yuen (The Hong Kong Polytechnic University, China)**; 

Feijie Wu (The Hong Kong Polytechnic University, China); 

Wei Cai (The Chinese University of Hong Kong, Shenzhen, China); 

Henry C.B. Chan (The Hong Kong Polytechnic University, China); 

Qiao Yan (Shenzhen University, China); 

Victor C.M. Leung (Shenzhen University, China)

## simulation.py

run the script in the terminal as following:

```
python simulation.py -n 100 -l 1 -p 10 -c 30 -a 10
```

where:
* ```-n``` defines the number of blocks to mine,
* ```-l``` defines the amount of logging messages in the terminal,
* ```-p``` defines the number of player (Process) to run the in mining,
* ```-c``` defines the expected confirmation time,
* ```-a``` defines the number of the history hash rate to refer to for the target calculatin

## methodology

see paper {insert paper link}
