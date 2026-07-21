---
layout: post
title: "Notes on the Hierarchical Poincaré–Steklov Method"
date: 2026-07-20 20:00:00-0400
description: "Working notes on HPS for linear elliptic PDEs: leaf operators, merging boxes, and how the tree scales."
tags: scientific-computing pde hierarchical-methods
categories: research
published: true
related_posts: false
thumbnail: assets/img/blog/hps/cover.png
toc:
  sidebar: left
---

These are my working notes on the Hierarchical Poincaré–Steklov (HPS) method for linear elliptic PDEs. The implementation follows Chapters 25 and 26 of Per-Gunnar Martinsson's [textbook](https://epubs.siam.org/doi/book/10.1137/1.9781611976045). The code lives in a private repo for now, so this post is the public version of the notes.

The BVP I care about is

$$
\begin{cases}
[Au](x) = 0, & x \in \Omega, \\
u(x) = f(x), & x \in \Gamma.
\end{cases}
$$

Here \(\Omega\) is the domain and \(\Gamma = \partial\Omega\) is its boundary. HPS solves this by chopping \(\Omega\) into leaf boxes, building local Dirichlet to Neumann maps, and then merging those maps up a tree with Schur complements.

## Trivial case

Start with the smallest picture that still has the whole idea in it. Break the domain into panels and put a \(p \times p\) Chebyshev mesh (tensor product) on each panel. Take \(n_1 = n_2 = 1\), so there are just two leaf boxes: \(\alpha\) on the left and \(\beta\) on the right. The outer boundary \(\Gamma\) sits on the outer edges of the pair. The shared vertical cut between \(\alpha\) and \(\beta\) is the interface.

<figure style="margin: 1.5rem 0;">
  <img src="{{ '/assets/img/blog/hps/trivial_case.png' | relative_url }}" alt="Two leaf boxes alpha and beta sharing a red interface, with blue outer boundary Gamma" style="display: block; width: 100%; max-width: 100%; height: auto;">
  <figcaption style="text-align: center;">Trivial case: two leaves with a \(p\times p\) Chebyshev grid on each panel, shared interface (red), outer boundary \(\Gamma\) (blue).</figcaption>
</figure>

For any box \(\tau\), the vector \(I_b^\tau\) lists all indices on \(\partial\Omega_\tau\). For a leaf box \(\tau\), the vector \(I_i^\tau\) lists all indices strictly interior to \(\Omega_\tau\). Write

$$
u_i^\tau = u(I_i^\tau)
\quad\text{(interior potential of leaf \(\tau\))}
$$

$$
u_b^\tau = u(I_b^\tau)
\quad\text{(boundary potential on the leaf boundary)}.
$$

## Solution operator

We want a map from boundary values to the solution inside the leaf:

$$
u_i^\tau = S^\tau \, u_b^\tau.
$$

So \(S^\tau\) is the solution operator:

$$
S^\tau : u_b^\tau \mapsto u_i^\tau.
$$

## Flux / DtN operator

Along with the potential we also map flux. DtN means Dirichlet to Neumann. The matrix \(T^\tau\) sends boundary data \(u_b^\tau\) to a vector \(v^\tau\) of boundary fluxes:

$$
v^\tau = T^\tau \, u_b^\tau.
$$

In 2D you can read the entries as normal derivatives on each side:

$$
v^\tau(i) \cong \frac{\partial u}{\partial x_1}(x_i)
\quad\text{on a vertical edge,}
$$

$$
v^\tau(j) \cong \frac{\partial u}{\partial x_2}(x_j)
\quad\text{on a horizontal edge.}
$$

## Leaf computation

For one leaf box the local equilibrium equation is

$$
A_{i,i} \, u_i + A_{i,b} \, u_b = 0.
$$

Solve for the interior potential:

$$
A_{i,i} \, u_i = - A_{i,b} \, u_b,
\qquad
u_i = - \bigl( A_{i,i}^{-1} A_{i,b} \bigr) u_b.
$$

So the solution operator is

$$
S^\tau = - A_{i,i}^{-1} A_{i,b}.
$$

Boundary fluxes come from the potentials \((u_b, u_i)\) through spectral differentiation. Let \(N\) be the matrix that maps local grid values to the four side fluxes. Then

$$
v^\tau
= N
\begin{bmatrix}
u_b \\
u_i
\end{bmatrix}.
$$

Substitute \(u_i = S^\tau u_b\):

$$
v^\tau
= N
\begin{bmatrix}
I \\
S^\tau
\end{bmatrix}
u_b,
\qquad
T^\tau
= N
\begin{bmatrix}
I \\
S^\tau
\end{bmatrix}.
$$

On a \(p \times p\) grid, \(N\) is roughly size \(4(p-2) \times p^2\) after dropping corners. As \(p\) grows, building \(T\) and \(S\) gets more expensive, which is expected.

## Merging boxes (leaves)

Now merge two leaves into a parent. Let \(\Omega_\alpha\) be the left child and \(\Omega_\beta\) the right child, with

$$
\Omega_\tau = \Omega_\alpha \cup \Omega_\beta.
$$

Partition the points on \(\partial\Omega_\alpha\) and \(\partial\Omega_\beta\) into three sets:

- \(J_1\): boundary indices of \(\Omega_\alpha\) that are not on \(\Omega_\beta\) (outer edge of \(\alpha\))
- \(J_2\): boundary indices of \(\Omega_\beta\) that are not on \(\Omega_\alpha\) (outer edge of \(\beta\))
- \(J_3\): boundary indices of both \(\Omega_\alpha\) and \(\Omega_\beta\) that are **not** on \(\partial\Omega_\tau\) (the shared interface)

<figure style="margin: 1.5rem 0;">
  <img src="{{ '/assets/img/blog/hps/merging_boxes.png' | relative_url }}" alt="Two boxes Omega alpha and Omega beta with outer boundaries J1 and J2 and shared red interface J3" style="display: block; width: 100%; max-width: 100%; height: auto;">
  <figcaption style="text-align: center;">Merging leaves: outer edges \(J_1\), \(J_2\), and shared interface \(J_3\).</figcaption>
</figure>

HPS says the values on \(J_3\) have to agree. Two conditions:

1. Continuity of the solution: \(u\) on the interface is the same from both sides (one shared \(u_3\)).
2. Net flux at the interface is zero: the flux \(v_3\) from \(\alpha\) matches the flux \(v_3\) from \(\beta\).

### Partition the child DtN maps

For \(\Omega_\alpha\):

$$
\begin{bmatrix}
v_1 \\
v_3
\end{bmatrix}
=
\begin{bmatrix}
T^\alpha_{11} & T^\alpha_{13} \\
T^\alpha_{31} & T^\alpha_{33}
\end{bmatrix}
\begin{bmatrix}
u_1 \\
u_3
\end{bmatrix}.
$$

For \(\Omega_\beta\):

$$
\begin{bmatrix}
v_2 \\
v_3
\end{bmatrix}
=
\begin{bmatrix}
T^\beta_{22} & T^\beta_{23} \\
T^\beta_{32} & T^\beta_{33}
\end{bmatrix}
\begin{bmatrix}
u_2 \\
u_3
\end{bmatrix}.
$$

### Solve for the interface potential \(u_3\)

Write the two expressions for \(v_3\):

$$
v_3 = T^\alpha_{31} u_1 + T^\alpha_{33} u_3,
\qquad
v_3 = T^\beta_{32} u_2 + T^\beta_{33} u_3.
$$

Set them equal (flux matching):

$$
T^\alpha_{31} u_1 + T^\alpha_{33} u_3
= T^\beta_{32} u_2 + T^\beta_{33} u_3.
$$

Move every term with \(u_3\) to the left:

$$
\bigl( T^\alpha_{33} - T^\beta_{33} \bigr) u_3
= - T^\alpha_{31} u_1 + T^\beta_{32} u_2.
$$

Invert the interface block:

$$
u_3
= \bigl( T^\alpha_{33} - T^\beta_{33} \bigr)^{-1}
\bigl( - T^\alpha_{31} u_1 + T^\beta_{32} u_2 \bigr).
$$

In block form,

$$
u_3
= S^\tau
\begin{bmatrix}
u_1 \\
u_2
\end{bmatrix},
\qquad
S^\tau
= \bigl( T^\alpha_{33} - T^\beta_{33} \bigr)^{-1}
\begin{bmatrix}
-T^\alpha_{31} & T^\beta_{32}
\end{bmatrix}.
$$

So \(S^\tau\) maps the outer potentials \((u_1, u_2)\) to the interface potential \(u_3\).

### Parent DtN \(T^\tau\)

Plug that expression for \(u_3\) back into the equations for \(v_1\) and \(v_2\), then stack:

$$
\begin{bmatrix}
v_1 \\
v_2
\end{bmatrix}
= T^\tau
\begin{bmatrix}
u_1 \\
u_2
\end{bmatrix},
$$

with

$$
T^\tau
=
\begin{bmatrix}
T^\alpha_{11} & 0 \\
0 & T^\beta_{22}
\end{bmatrix}
+
\begin{bmatrix}
T^\alpha_{13} \\
T^\beta_{23}
\end{bmatrix}
S^\tau.
$$

Writing \(S^\tau\) out fully,

$$
T^\tau
=
\begin{bmatrix}
T^\alpha_{11} & 0 \\
0 & T^\beta_{22}
\end{bmatrix}
+
\begin{bmatrix}
T^\alpha_{13} \\
T^\beta_{23}
\end{bmatrix}
\bigl( T^\alpha_{33} - T^\beta_{33} \bigr)^{-1}
\begin{bmatrix}
-T^\alpha_{31} & T^\beta_{32}
\end{bmatrix}.
$$

We eliminated \(u_3\) and factorized the interface block. That merge is a Schur complement. After the leaves are solved, parent operators at every level are built the same way: continuity plus flux matching. That was the trivial case.

## Deeper tree

Scale the same idea past one parent and two children. Imagine 4 leaves, then 8, 16, 32, 64, and so on. The hard global problem becomes a stack of Schur complements on a tree.

<figure style="margin: 1.5rem 0;">
  <img src="{{ '/assets/img/blog/hps/hierarchical_tree.png' | relative_url }}" alt="Square domain on [0,2]x[0,2] partitioned hierarchically into finer leaves" style="display: block; width: 100%; max-width: 100%; height: auto;">
  <figcaption style="text-align: center;">How the partition looks when you keep splitting: white, then red, then orange/green levels.</figcaption>
</figure>

On a \([0,2]\times[0,2]\) box, leaf size \([0.25, 0.5]\) gives an \(8\times 4\) panel grid (32 leaves). Leaf size \([0.25, 0.25]\) gives \(8\times 8\) (64 leaves). Same merge rule, just more levels.

## What a solved example looks like

Here are a few verified runs from the example gallery. Each figure is exact solution, numerical solution, and pointwise error.

<div style="display: grid; grid-template-columns: minmax(0, 1fr); gap: 1rem; width: 100%; max-width: 100%; margin: 1.5rem 0;">
  <figure style="min-width: 0; margin: 0;">
    <img src="{{ '/assets/img/blog/hps/2d_homogeneous_flag1.png' | relative_url }}" alt="2D homogeneous HPS solution triptych with max absolute error about 8.5e-12" style="display: block; width: 100%; max-width: 100%; height: auto;">
    <figcaption style="text-align: center;">2D homogeneous example. Max absolute error on the order of \(10^{-12}\).</figcaption>
  </figure>
  <figure style="min-width: 0; margin: 0;">
    <img src="{{ '/assets/img/blog/hps/2d_body_flag1.png' | relative_url }}" alt="2D body load HPS solution triptych" style="display: block; width: 100%; max-width: 100%; height: auto;">
    <figcaption style="text-align: center;">2D body load example from the same gallery.</figcaption>
  </figure>
  <figure style="min-width: 0; margin: 0;">
    <img src="{{ '/assets/img/blog/hps/1d_homogeneous_flag1.png' | relative_url }}" alt="1D homogeneous HPS solution and error" style="display: block; width: 100%; max-width: 100%; height: auto;">
    <figcaption style="text-align: center;">1D homogeneous check, same leaf and merge idea in one dimension.</figcaption>
  </figure>
</div>

## What I take from this

1. **Leaves own the PDE.** On each panel you build \(S^\tau\) and \(T^\tau\) from the local spectral discretization.
2. **Parents only talk about boundaries.** Merging never revisits interiors. Continuity of \(u\) and matching of flux on \(J_3\) are enough.
3. **The merge is a Schur complement.** That block formula for \(T^\tau\) is the whole hierarchical step.
4. **Scaling is mechanical.** Deeper trees are the same merge repeated, which is why the partition drawing matters as much as the algebra.

When the repo is public I will add a projects card and a proper reproduction path. For now these notes are the readable version of the method as I understand it.
