from multiprocessing import Pool, Process, Manager
from statistics import mean
import random, time, queue, hashlib, math, argparse

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--loopTime", type=int, help="the number of block writing times for the experiment")
parser.add_argument("-l", "--loggingLevel", type=int, help="0 = no logging, 1 = mgr logging only, 2 = mgr & plyr logging")
parser.add_argument("-p", "--plyrNum", type=int, help="number of players")
parser.add_argument("-c", "--confTime", type=int, help="expected confirmation time")
args = parser.parse_args()
args.loggingLevel = int(args.loggingLevel)
args.loopTime = int(args.loopTime)
args.plyrNum = int(args.plyrNum)
args.confTime = int(args.confTime)

class tier:
    tierList = [5+(10*i) for i in range(0, 10)] # from 1 to 10 player tiers

class player_config:
    history_length = 10

class player:
    def __init__(self, history, threshold, index):
        self.history = history
        self.threshold = threshold
        self.index = index
        self.skill_growth = random.randrange(0,10)

    def gen_score(self):
        # offset is always an addition to a value
        if self.threshold-5 < 0: left_offset = abs(self.threshold-5)
        else: left_offset = 0
        score = random.randrange(self.threshold-5+left_offset, self.threshold+5)
        self.history.append(score)
        return score

    def trigger_skill_grow(self):
        self.threshold += self.skill_growth

class blockchain:
    def __init__(self):
        self.index = 0
        self.maxTarget = 2**256 # bitcoin is 224, PoP is same as the possible bits in SHA256 for easy difficulty
        self.target = self.maxTarget / args.plyrNum # expected to guess 10 times, since initial plyr num = args.plyrNum, then avg conf time = avg time length for one match
        self.expectedConfTime = args.confTime # unit: seconds
        self.numGuessedList = []
        self.confTimeList = []
        self.hexMsgHist = []

    def add_block(self, hexMsg, numGuessed, confTime):
        expectedNumToGuess = numGuessed / confTime * self.expectedConfTime # where hash rate = number to guess / confirmation time
        adjustedTarget = self.maxTarget / expectedNumToGuess # where expectedNumToGuess = D*(max target / 2^256), and D = max target / target
        self.target = adjustedTarget
        self.numGuessedList.append(numGuessed)
        self.confTimeList.append(confTime)
        self.hexMsgHist.append(hexMsg)
        self.index += 1
        return

def generate_history():
    myTier  = tier.tierList[random.randrange(0,args.plyrNum)]
    history = [myTier+(random.randint(0,10)-5) for _ in range(0, player_config.history_length)]
    return history

def generate_player(index):
    history = generate_history()
    threshold = int(mean(history))
    return player(history, threshold, index)

# the PoP process receive shared resource, and send to manager if target needs update
# resource to share: current block index, current target, previous target history, actual confirmation time
def PoP_reset():
    nonce, myScore, confTimeStart = 0, 0, time.time()
    return nonce, myScore, confTimeStart

def PoP(pop_args):
    (myPlyr, mySend, myRecv, args) = pop_args
    print(f"Player {myPlyr.index} started Process.")
    myBlockchain = myRecv.get()
    nonce, myScore, confTimeStart = PoP_reset()
    while True:
        # simulate a match
        time.sleep(random.randint(1, 5))
        myScore += myPlyr.gen_score()
        if myScore < myPlyr.threshold: continue

        # get latest block
        try:
            newBlockchain = myRecv.get_nowait()
            if newBlockchain is None: break
        except queue.Empty:
            newBlockchain = None

        # loop again if someone found the target
        if newBlockchain is not None:
            myBlockchain = newBlockchain
            if args.loggingLevel > 1:
                print(f"Player: {myPlyr.index}, my chain get replaced.")
            nonce, myScore, confTimeStart = PoP_reset()
            myPlyr.trigger_skill_grow()
            continue

        # hashing operation (guessing)
        msg = bytes(str(myScore)+str(nonce), encoding='utf-8')
        hashMsg = hashlib.sha256(msg).hexdigest()
        hashMsgNum = int(hashMsg, 16)
        power = math.log(hashMsgNum, 2)
        if args.loggingLevel > 1:
            print(f"Player: {myPlyr.index}, Guessed: 2^{power}, For: {nonce}, Time: {time.time()-confTimeStart}")

        if hashMsgNum < myBlockchain.target:
            myBlockchain.add_block(hashMsg, nonce+1, time.time()-confTimeStart)
            mySend.put(myBlockchain)
            if args.loggingLevel > 1:
                print(f"Player: {myPlyr.index}, Target found.")
            nonce, myScore, confTimeStart = PoP_reset()
            myPlyr.trigger_skill_grow()
        else:
            nonce += 1

# the manager receive shared resource, and send to other process to update their resource
# the manager should reject the process if their current block index is not the latest
def manager(mgrRecv, mgrSend, returnQ, args):
    print("Manager has started.")
    myBlockchain = blockchain()
    experimentTime = args.loopTime
    if args.loggingLevel > 0:
        print(f"Manager: Current Target: 2^{math.log(myBlockchain.target, 2)}")
    for send in mgrSend: send.put(myBlockchain) # signal PoP Process to start
    while myBlockchain.index != experimentTime:
        for recv in range(0, len(mgrRecv)):
            try:
                newBlockchain = mgrRecv[recv].get_nowait()
                if newBlockchain.index <= myBlockchain.index: continue
                myBlockchain = newBlockchain
                if args.loggingLevel > 0:
                    print(f"Manager: New Target. Current Target: 2^{math.log(myBlockchain.target, 2)}, Index: {myBlockchain.index}")
                for send in range(0, len(mgrSend)):
                    if recv != send: mgrSend[send].put(myBlockchain)
            except queue.Empty:
                pass
    for send in mgrSend: send.put(None)
    print("Manager: Experiment Completed.")
    returnQ.put(myBlockchain)
    return

def main():
    plyrNum = args.plyrNum
    m = Manager()
    mgrRecv = [m.Queue() for _ in range(0, plyrNum)]
    mgrSend = [m.Queue() for _ in range(0, plyrNum)]
    pop_args = [(generate_player(i), mgrRecv[i], mgrSend[i], args) for i in range(0, plyrNum)]
    # spawn a manager, and a group of PoP
    returnQ = m.Queue()
    p1 = Process(target=manager, args=(mgrRecv,mgrSend,returnQ,args))
    p1.start()
    with Pool(plyrNum) as p2:
        p2.map(PoP, pop_args)
    p1.join()
    myChain = returnQ.get()
    p1.terminate()
    print("writing blockchain to file...")
    with open(f'{int(time.time())}_confTime{args.confTime}_index{args.loopTime}.csv', 'a+') as f:
        f.write("hex,confTime,timeGuessed\n")
        for i in range(0, len(myChain.hexMsgHist)):
            f.write(f"{myChain.hexMsgHist[i]},{myChain.confTimeList[i]},{myChain.numGuessedList[i]}\n")
    print("Experiment fully completed.")

if __name__ == '__main__':
    main()