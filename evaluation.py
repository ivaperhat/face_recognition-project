from sklearn.datasets import fetch_lfw_pairs
from sklearn.metrics import classification_report
import tqdm
import matplotlib.pyplot as plt
import main as fr

lfw = fetch_lfw_pairs(subset='test', color=True, resize=1)

pairs = lfw.pairs
targets = lfw.target

predictions = []

for idx in tqdm.tqdm(range(0, pairs.shape[0])):
    pair = pairs[idx]
    img1 = pair[0]
    img2 = pair[1]

    plt.imshow(img1 / 255)
    plt.savefig('fig1.jpg')

    plt.imshow(img1 / 255)
    plt.savefig('fig2.jpg')

    actual = targets[idx]

    result = fr.face_match('fig1.jpg', 'fig2.jpg')
    prediction = 1 if result == "True" else 0

    predictions.append(prediction)

print(classification_report(targets, predictions))
