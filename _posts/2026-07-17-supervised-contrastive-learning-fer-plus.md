---
layout: post
title: "Supervised Contrastive Learning on Imbalanced Facial Expressions"
date: 2026-07-17 10:00:00-0400
description: "A reproducible FER+ case study showing why SupCon can match overall accuracy yet fail badly on rare classes."
tags: computer-vision deep-learning contrastive-learning
categories: research
published: true
toc:
  sidebar: left
---

Supervised Contrastive Learning (SupCon) produces remarkably structured representations on balanced object datasets (This case study was motivated from Supervised Contrastive Learning [paper](https://arxiv.org/abs/2004.11362)). I wanted to know whether that advantage survives in a messier setting: low-resolution facial expressions with a severe long-tail distribution.

I tested SupCon against a conventional cross-entropy classifier on **FER+**, using the same ResNet18 backbone for every experiment. The result is a useful cautionary tale: SupCon reached the best overall accuracy and produced cleaner embeddings, yet performed much worse on the rarest classes. The failure was not hidden in the model architecture. It came from how contrastive learning depends on batch composition.

The complete implementation, checkpoints, metrics, and reproduction scripts (the parent repository) are available in the [SupContrast](https://github.com/Khey17/SupContrast).

## The problem

FER+ classifies 48×48 grayscale face images into eight emotions. The low resolution is challenging, but the more important issue here is imbalance: neutral and happiness account for more than half the training set, while contempt and disgust each have fewer than 200 examples.

| Split | Neutral | Happiness | Surprise | Sadness | Anger | Disgust | Fear | Contempt |  Total |
| ----- | ------: | --------: | -------: | ------: | ----: | ------: | ---: | -------: | -----: |
| Train |  10,309 |     7,528 |    3,562 |   3,515 | 2,467 |     191 |  652 |      165 | 28,389 |
| Test  |   1,262 |       928 |      444 |     444 |   325 |      23 |   93 |       27 |  3,546 |

SupCon's headline results come from balanced datasets such as CIFAR and ImageNet, trained with batch sizes in the thousands. FER+ asks a different question: does contrastive pretraining still help when the data are small, imbalanced, and difficult?

## Why imbalance is especially difficult for SupCon

Cross entropy evaluates each image against a fixed set of class weights. Every image therefore contributes a gradient regardless of which other samples happen to be in its batch.

SupCon works differently. For each anchor, it needs another sample from the same class to form a positive pair, while all other samples act as negatives. If a class appears fewer than twice in a batch, it supplies no positive pair and therefore no useful SupCon learning signal—during that step.

For anchor \(i\), let \(P(i)\) be the same-class samples in the batch and \(A(i)\) all other samples. The supervised contrastive loss is

$$
\mathcal{L}_i =
\frac{-1}{|P(i)|}
\sum_{p \in P(i)}
\log
\frac{\exp\left(z_i \cdot z_p / \tau\right)}
{\sum_{a \in A(i)} \exp\left(z_i \cdot z_a / \tau\right)}.
$$

The dependence on \(|P(i)|\) makes batch composition part of the optimization problem.

## Experimental setup

- **Dataset:** FER+, eight emotion classes.
- **Backbone:** ResNet18 for every configuration.
- **Initialization:** either from scratch or from a ResNet18 pretrained on MS-Celeb-1M faces.
- **Cross entropy:** end-to-end classifier training.
- **SupCon:** contrastive encoder pretraining followed by a frozen-encoder linear probe.
- **Training:** batch size 256, 100 pretraining epochs, cosine schedule, crop and flip augmentation.

Using one backbone and a shared evaluation pipeline keeps the comparison focused on the learning objective rather than implementation differences.

## Results

### Overall performance

| Method                | Initialization | Test accuracy |  Macro F1 |
| --------------------- | -------------- | ------------: | --------: |
| Cross entropy         | From scratch   |         80.0% |     65.9% |
| Cross entropy         | MS-Celeb faces |         79.4% | **67.4%** |
| SupCon + linear probe | From scratch   |         78.5% |     55.8% |
| SupCon + linear probe | MS-Celeb faces |     **80.7%** |     59.0% |

SupCon with face-pretrained initialization achieved the highest accuracy, 80.7%. If accuracy were the only metric, it would appear to win, but Macro F1 gives us to look at it from another lens both SupCon configurations trail their cross-entropy counterparts because the rare classes barely benefit.

### Per-class accuracy

| Emotion   | Train samples | CE scratch | CE pretrained | SupCon scratch | SupCon pretrained |
| --------- | ------------: | ---------: | ------------: | -------------: | ----------------: |
| Happiness |         7,528 |       88.8 |          87.3 |           88.0 |              90.0 |
| Neutral   |        10,309 |       85.5 |          84.8 |           86.8 |              87.5 |
| Surprise  |         3,562 |       82.4 |          82.9 |           82.4 |              82.9 |
| Anger     |         2,467 |       73.8 |          73.5 |           74.5 |              75.4 |
| Sadness   |         3,515 |       60.1 |          60.4 |           52.5 |              59.7 |
| Fear      |           652 |       48.4 |          46.2 |           28.0 |              41.9 |
| Disgust   |           191 |       34.8 |          47.8 |            8.7 |               8.7 |
| Contempt  |           165 |       29.6 |          29.6 |            7.4 |               7.4 |

The rare-class result like `disgust` and `contempt` score exactly the same under SupCon whether the encoder starts from random weights or face-pretrained weights. If representation quality were the primary bottleneck, better initialization should have moved those numbers. It did not.

## The embeddings look better, but improvement is not justifiable

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 360px)); gap: 1rem; margin: 1.5rem 0;">
  <figure style="margin: 0;">
    <img src="{{ '/assets/img/blog/supcontrast/tsne_supcon_none.png' | relative_url }}" alt="t-SNE visualization of SupCon FER+ embeddings grouped into compact clusters">
    <figcaption style="text-align: center;">SupCon embeddings</figcaption>
  </figure>
  <figure style="margin: 0;">
    <img src="{{ '/assets/img/blog/supcontrast/tsne_ce_none.png' | relative_url }}" alt="t-SNE visualization of cross-entropy FER+ embeddings with more dispersed clusters">
    <figcaption style="text-align: center;">Cross-entropy embeddings</figcaption>
  </figure>
</div>

The t-SNE plots show SupCon doing what it was designed to do: samples from the same class form tighter, more compact clusters. Cross-entropy embeddings are comparatively dispersed.

That geometric improvement is real, but it does not guarantee balanced classification. The majority classes dominate both the embedding visualization and aggregate accuracy, while the rare-class collapse is visible only when performance is broken down by class.

## Why batch size explains the failure

The original implementation was actually done on large batch sizes (contains thousands of samples) because the idea of contrastive learning is that it pulls all the similar images together while pushing dissimilar images apart so on smaller batches, only handful of images are seen by the loss function making it harder for the model to generalize, to simply put the model lacks perspective.

Consider contempt, which represents \(p = 165 / 28{,}389 \approx 0.0058\) of the training set. If samples are drawn randomly, the number of contempt examples in a batch can be approximated by a Poisson random variable with mean

$$
\lambda = Bp,
$$

where \(B\) is the batch size. A batch supplies no positive pair when it contains zero or one contempt example:

$$
P(X < 2) = e^{-\lambda}(1 + \lambda).
$$

|       Batch size | Expected contempt samples \(\lambda\) | Batches with no positive pair |
| ---------------: | ------------------------------------: | ----------------------------: |
| 256 (this study) |                                   1.5 |                     About 56% |
|            1,024 |                                   5.9 |                      Under 2% |
|            2,048 |                                  11.9 |                   Under 0.01% |

At batch size 256, more than half the training steps provide no positive pair for contempt. At 1,024, that problem almost disappears.

Larger batches help in two ways:

1. Rare classes are much more likely to form positive pairs.
2. Every anchor sees more negatives, reducing variance in the denominator of the contrastive objective.

This explains why the original SupCon work uses batches in the thousands and suggests a concrete next experiment: larger batches or class-aware sampling should recover part of the rare-class performance.

## What I learned

1. **SupCon transfers beyond object datasets.** It matched cross entropy on overall accuracy and produced visibly cleaner embeddings on FER+.
2. **Accuracy alone hides the failure.** The 80.7% headline score obscures severe degradation on contempt and disgust; macro F1 exposes it.
3. **Initialization was not the bottleneck.** Face pretraining did not improve either rarest class under SupCon.
4. **Batch composition is part of the method.** For contrastive learning on long-tailed data, batch size and sampling strategy are not secondary implementation details.
5. **A better representation is not automatically a fairer classifier.** Compact global embeddings can coexist with poor minority-class recognition.

## Reproducing the study

The repository supports Apple Silicon MPS, CUDA, and CPU:

```bash
git clone https://github.com/Khey17/SupContrast.git
cd SupContrast

python -m venv .venv
source .venv/bin/activate
pip install torch torchvision numpy pillow scikit-learn matplotlib gdown

python datasets/build_ferplus.py
bash run_all.sh
```

The full code, detailed commands, metrics, and repository layout are documented in [Khey17/SupContrast](https://github.com/Khey17/SupContrast).

## References

- Prannay Khosla et al., _Supervised Contrastive Learning_, NeurIPS 2020.
- Emad Barsoum et al., _Training Deep Networks for Facial Expression Recognition with Crowd-Sourced Label Distribution_, ICMI 2016.
