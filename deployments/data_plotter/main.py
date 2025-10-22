import os
os.environ.setdefault('MPLBACKEND','Agg')
import matplotlib.pyplot as plt
import random

xs = [random.random() for _ in range(100)]
ys = [random.random() for _ in range(100)]
plt.figure()
plt.scatter(xs, ys)
plt.title('Random Scatter (100 pts)')
plt.savefig('scatter.png')
