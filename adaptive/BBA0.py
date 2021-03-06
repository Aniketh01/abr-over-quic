from .abr import BasicABR
import json

class BBA0(BasicABR):
    def __init__(self, manifestData):
        super(BBA0, self).__init__(manifestData)
        self.reservoir = 8
        self.cushion = 46
        self.ratePrev = 0
        # self.buffer = 0
    
    def getCurrentBuffer(self, currBuffer, step, rateMap):
        if currBuffer <= self.cushion + self.reservoir and currBuffer >= self.reservoir:
            return rateMap[round((currBuffer-self.reservoir)/step)*step + self.reservoir]
        elif currBuffer > self.cushion + self.reservoir :
            return rateMap[self.cushion + self.reservoir]
        else:
            return rateMap[self.reservoir]
    
    def NextSegmentQualityIndex(self, playerStats):
        currBuffer = 70
        #currBuffer = playerStats["currBuffer"]
        bitrates = self.getBitrateList()
        bitrates = sorted(bitrates)
        rateMap = {}

        step = self.cushion / (len(bitrates) - 1)

        for i in range(len(bitrates)):
            rateMap[self.reservoir + i * step] = bitrates[i]

        rMax = bitrates[-1]
        rMin = bitrates[0]
        ratePlus = None
        rateMinus = None

        if self.ratePrev < rMin:
            self.ratePrev = rMin
        
        if self.ratePrev == rMax:
            ratePlus = rMax
        else:
            for i in range(len(bitrates)):
                if bitrates[i] > self.ratePrev:
                    ratePlus = bitrates[i]
                    break

        if self.ratePrev == rMin:
            rateMinus = rMin
        else:
            for i in range(len(bitrates) - 1, -1, -1):
                if bitrates[i] < self.ratePrev:
                    rateMinus = bitrates[i]
                    break
        
        funCurrBuffer = self.getCurrentBuffer(currBuffer, step, rateMap)

        rateNext = None

        if currBuffer <= self.reservoir:
            rateNext = rMin
        elif currBuffer >= self.reservoir + self.cushion:
            rateNext = rMax
        elif funCurrBuffer >= ratePlus:
            for i in range(len(bitrates) - 1 , -1 , -1):
                if bitrates[i] < funCurrBuffer:
                    rateNext = bitrates[i]
                    break
        elif funCurrBuffer <= rateMinus:
            for i in range(len(bitrates)):
                if bitrates[i] >= funCurrBuffer:
                    rateNext = bitrates[i]
                    break
        else:
            rateNext = self.ratePrev
        self.ratePrev = rateNext

        return self.GetCorrespondingQualityIndex(rateNext)


# if __name__ == "__main__":
#     f = open("/home/aniketh/devel/src/abr-over-quic/src/bbb_m.json")
#     manifest = json.load(f)
#     a = BBA(manifest)
#     q = a.NextSegmentQualityIndex(60)
#     print(q)