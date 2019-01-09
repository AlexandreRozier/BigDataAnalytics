import numpy as np 
import tensorflow as tf

SEQ_LEN = 50

def create_time_series():
  freq = (np.random.random()*0.5) + 0.1  # 0.1 to 0.6
  ampl = np.random.random() + 0.5  # 0.5 to 1.5
  noise = [np.random.random()*0.3 for i in range(SEQ_LEN)] # -0.3 to +0.3 uniformly distributed
  x = np.sin(np.arange(0,SEQ_LEN) * freq) * ampl + noise
  return x

def to_csv(filename, N):
  with open(filename, 'w') as ofp:
    for lineno in range(0, N):
      seq = create_time_series()
      line = ",".join(map(str, seq))
      ofp.write(line + '\n')


np.random.seed(1) # makes data generation reproducible

to_csv('dataset-eval/eval-1.csv', 1000)  # 1000 sequences
to_csv('dataset-train/train-1.csv', 250)

