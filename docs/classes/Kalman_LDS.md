---
title: Kalman's Mathematical Description of Linear Dynamical Systems
author: Chrystal Chern
date: Friday, December 15, 2023
...

<!-- # Kalman's Mathematical Description of Linear Dynamical Systems -->

## 0. Question and Scope

```{=tex}
\begin{centering}
```
*How much of the physical world can be determined from a given amount of experimental data?*
```{=tex}
\end{centering}
```

- Real, finite dimensional, continuous-time, linear time-invariant (LTI) dynamical systems (LTV before Section 5).
- Impulse response.

## 1. Intro and Summary

- **1&2&3**: Intro; define a dynamical system
- **4**: Present the problem of system realization from impulse response
- **5**: Present the *canonical structure theorem*: if a system realization is controllable and observable, $\implies$ it is an irreducible realization of the impulse response.
- **6&7**: Define controllability and observability and compute the canonical structure of an LTI system.
- **8**: Define MIMO state variables for LTI systems from transfer functions.
- **9**: Present common errors made by equating transfer functions and state space system realizations.


## 2. Axioms of Dynamical Systems

A dynamical system consists of the following (developed for linear time-varying (LTV) systems by Kalman, but only presented for LTI systems here):

### *state*, $\begin{bmatrix} \bm{x}(t) \\ \dot{\bm{x}}(t) \end{bmatrix} \in \Sigma = \mathbb{R}^{n}$

- Physical interpretation: instantaneous position and momentum.
- Definition: minimal information needed about the system's history which suffices to predict the effect of the past upon the future.
- Properties of state: $\begin{bmatrix} \bm{x}(t>\tau) \\ \dot{\bm{x}}(t>\tau) \end{bmatrix}$ is fully defined by $\begin{bmatrix} \bm{x}(\tau) \\ \dot{\bm{x}}(\tau) \end{bmatrix}$ and $\bm{u}(t\geq\tau)$.

### *time*, $t \in \Theta = \mathbb{R}$

### *input*, $u \in \Omega =$ piecewise continuous functions

- Physical interpretation: forcing function.

### *transition function*, $\varphi: \Omega \times \Theta \times \Theta \times \Sigma \to \Sigma$

$$
\bm{x}(t) = \varphi(\bm{u}, t; t_{o}, \bm{x}_{o})
$$

- Linear on $\Omega \times \Theta$.
- Continuous with respect to $\Sigma, \Theta, \Omega$ and their induced products.

### *output function*, $\psi: \Theta \times \Sigma \to \mathbb{R}$

- Physical interpretation: variables that are directly observed.
- Linear on $\Sigma$.
- Continuous with respect to $\Sigma, \Theta, \Omega$ and their induced products.

Every linear time-invariant ($\bm{A,B,C}$ linear in $\Sigma$ and independent of time) dynamical system is thus governed by the equations[^1]

$$
\boxed{
    \begin{aligned}
    \frac{d}{dt}\bm{x}(t) &= \bm{Ax}(t) + \bm{Bu}(t) \\
    \bm{y}(t) &= \bm{Cx}(t)
    \end{aligned}
}
$${@eq:goveqs}

The general solution to the differential equation is

$$
\begin{aligned}
\bm{x}(t) &= \Phi_{\bm{A}}(t,t_{o})\bm{x}_{o} + \int_{t_{o}}^{t}{\Phi_{\bm{A}}(t,\tau)\bm{Bu}(\tau)d\tau}
\\
\Phi_{\bm{A}}(t,\sigma) &= e^{\bm{A}(t-\sigma)}
\end{aligned}
$${#eq:gensol}

and it can be verified that $\Phi_{\bm{A}}(t,\sigma) = \Phi_{\bm{A}}(t,\tau)\Phi_{\bm{A}}(\tau,\sigma) ~~\forall{t,\tau,\sigma} \in \mathbb{R}$.

[^1]: Sometimes you'll see a system with a *feed-through* term, $\bm{D}$ in the output function, $\bm{y}(t) = \bm{Cx}(t) + \bm{Du}(t)$. This term can always be added or removed because inputs  $\bm{u}(t)$ and outputs $\bm{y}(t)$ are deterministic quantities.

## 3. Equivalent Dynamical Systems

The state vector $\bm{x}(t)$ is an abstract quantity in $\mathbb{R}^{n}$. Therefore it can be expressed in any $\mathbb{R}^{n}$ coordinates. The system with the state vector $\bar{\bm{x}}(t)$ is equivalent to the system with the state vector $\bm{x}(t)$ if there exists a nonsingular matrix $\bm{T} \in \mathbb{R}^{n\times n}$ such that

$$
\bar{\bm{x}}(t) = \bm{Tx}(t)~.
$$

The equivalent governing equations for the system are as follows:

$$
\begin{aligned}
\frac{d}{dt}\bar{\bm{x}}(t) &= \bm{TAT^{-1}\bar{x}}(t) + \bm{TBu}(t) \\
\bm{y}(t) &= \bm{CT^{-1}\bar{x}}(t)
\end{aligned}
$$

## 4. System Realization from Impulse Response

The *impulse response matrix* of a system is a time-dependent array of the output at each $\bm{y}$ coordinate in response to an pulse input, $\delta(t-t_{o})$, at each $\bm{u}$ coordinate.

That is, given the input $u_{ij}(t) = \delta_{ij}\delta(t-t_{o})$, the output is $y_{ij} = S_{ij}(t,t_{o})$, where (by plugging in (@eq:gensol),)

$$
\bm{S}(t,\tau) = \bm{C} \Phi_{\bm{A}}(t,\tau) \bm{B} ~.
$$

Given $\bm{S}(t,t_{o})$ for a dynamical system, the output can be found for any input by the convolution integral:

$$
\bm{y}(t) = \int_{t_{o}}^{t}{\bm{S}(t,\tau)\bm{u}(\tau)d\tau} ~.
$$

>The central question of this paper is,
>
>```{=tex}
>\begin{centering}
>```
>*When and how does the impulse-response matrix determine the dynamical equations of the system?*
>```{=tex}
>\end{centering}
>```

$$
\begin{aligned}
\\
\\
\end{aligned}
$$

## 5. Kalman Canonical Staircase State Space Realization (K-CSSSR)

Kalman presents his canonical form for state space system realization of a dynamical system. He proves that any system realization can be transformed into one which isolates the state vector into four parts:

- controllable and unobservable ($\bm{x}_{cuo}$)
- controllable and observable ($\bm{x}_{co}$)
- uncontrollable and unobservable ($\bm{x}_{ucuo}$)
- ucontrollable and observable ($\bm{x}_{uco}$)

The governing equations are as follows:

$$
\boxed{
    \begin{aligned}
    \frac{d}{dt}\begin{bmatrix}
    \bm{x}_{cuo}(t) \\
    \bm{x}_{co}(t) \\
    \bm{x}_{ucuo}(t) \\
    \bm{x}_{uco}(t) \\
    \end{bmatrix} &= 
    \begin{bmatrix}
    \bm{A}_{cuo} & \bm{A}_{12} & \bm{A}_{13} & \bm{A}_{14} \\
    0 & \bm{A}_{co} & 0 & \bm{A}_{24}\\
    0 & 0 & \bm{A}_{ucuo} & \bm{A}_{34} \\
    0 & 0 & 0 & \bm{A}_{uco} \\
    \end{bmatrix}
    \begin{bmatrix}
    \bm{x}_{cuo}(t) \\
    \bm{x}_{co}(t) \\
    \bm{x}_{ucuo}(t) \\
    \bm{x}_{uco}(t) \\
    \end{bmatrix} + 
    \begin{bmatrix}
    \bm{B}_{cuo}(t) \\
    \bm{B}_{co}(t) \\
    0 \\
    0 \\
    \end{bmatrix}
    \bm{u}(t) \\
    \bm{y}(t) &= 
    \begin{bmatrix}
    0 & \bm{C}_{co} & 0 & \bm{C}_{uco}
    \end{bmatrix}
    \bm{x}(t)
    \end{aligned}
}
$${#eq:canonical}

The impulse response matrix of a linear dynamical system depends only on the dynamics of the controllable and observable modes $\bm{x}_{co}(t)$.

$$
\bm{S}(t,\tau) = \bm{C}_{co}\Phi_{\bm{A}_{co}}(t,\tau)\bm{B}_{co} 
$$

Equivalently, any controllable and observable realization of an impulse response matrix is *irreducible* and equivalent to any other controllable and observable realization.

If a dynamical system is controllable and observable, it has a unique impulse response matrix.

>The answer to the central question of this paper is,
>```{=tex}
>\begin{centering}
>```
>*The impulse-response matrix fully determines the dynamical equations of a controllable and observable system.*
>```{=tex}
>\end{centering}
>```


## 6. Definition of Controllability and Observability

The following statements are equivalent:

- The system is controllable.
- The pair, $\{\bm{A},\bm{B}\}$, is controllable.
- The matrix $\bm{P} = \begin{bmatrix} \bm{B} & \bm{AB} & \cdots & \bm{A^{n-1}B} \end{bmatrix}$ has rank $n$.

The following statements are equivalent:

- The system is observable.
- The pair, $\{\bm{A},\bm{C}\}$, is observable.
- The matrix $\bm{Q} = \begin{bmatrix} \bm{C} \\ \bm{CA} \\ \cdots \\ \bm{CA^{n-1}} \end{bmatrix}$ has rank $n$.

## 7. Computing the Canonical Form (@eq:canonical)

The transformation matrix that separates us into controllable and uncontrollable modes is $\bm{M} = \begin{bmatrix} \bm{M}_{c} & \bm{M}_{uc} \end{bmatrix}$, where the columns of $\bm{M}_{c}$ are the linearly independent columns of $\bm{P}$ and the columns of $\bm{M}_{uc}$ are chosen such that $\bm{M}$ is full rank.

The transformation matrix that separates us into observable and unobservable modes is $\bm{N} = \begin{bmatrix} \bm{N}_{o} \\ \bm{N}_{uo} \end{bmatrix}$, where the rows of $\bm{N}_{o}$ are the linearly independent rows of $\bm{Q}$ and the rows of $\bm{N}_{uo}$ are chosen such that $\bm{N}$ is full rank.