# Modal Properties from State Space Realization

Structural system dynamics are in continuous time.  With the time-domain system identification methods in the `mdof` package such as OKID-ERA and SRIM, a structural system's discrete-time state space realization is obtained from measured data.  The following process recovers the structure's modal properties (i.e., natural frequencies, modal damping ratios, and mode shapes) from the discrete state space realization coefficients, $\mathbf{A}$ and $\mathbf{C}$.

## Eigendecompositions of $\mathbf{A}_{c}$ and $\mathbf{A}$

The relationship between the eigendecompositions of $\mathbf{A}_{c}$, the continuous-time state transition matrix, and $\mathbf{A}$, the discrete-time state transition matrix, is shown below.

$$\begin{aligned}
\mathbf{A}_{c} &= \Phi\Lambda\Phi^{-1} \\
\mathbf{A} &= \Psi\Gamma\Psi^{-1} \\
\end{aligned}$$

$$\begin{aligned}
\mathbf{A} = e^{\mathbf{A}_{c}\Delta t} = e^{\Phi\Lambda\Phi^{-1}\Delta t} = \Phi e^{\Lambda\Delta t}\Phi^{-1}
\end{aligned}$$

$$\begin{aligned}
\Psi = \Phi, \quad \Gamma = e^{\Lambda\Delta t} \\
\end{aligned}$$

where 

$$\Psi = 
\begin{bmatrix} 
\psi_{1} & \psi_{2} & \cdots & \psi_{r} 
\end{bmatrix}, \quad{} 
\Phi =
\begin{bmatrix} 
\phi_{1} & \phi_{2} & \cdots & \phi_{r} 
\end{bmatrix}
$$

$$
\Gamma = 
\begin{bmatrix}
\gamma_{1} & 0 & \cdots & 0 \\
0 & \gamma_{2} & \cdots & 0 \\
\vdots & \vdots & \ddots & \vdots \\
0 & 0 & \cdots & \gamma_{r} 
\end{bmatrix}, \quad
\Lambda = \begin{bmatrix}
\lambda_{1} & 0 & \cdots & 0 \\
0 & \lambda_{2} & \cdots & 0 \\
\vdots & \vdots & \ddots & \vdots \\
0 & 0 & \cdots & \lambda_{r} 
\end{bmatrix}$$

- $\gamma_{j}$ and $\psi_{j}$ are the eigenvalues and eigenvectors of $\mathbf{A}$,

- $\lambda_{j}$ and $\phi_{j}$ are the eigenvalues and eigenvectors of $\mathbf{A}_{c}$,

- $j \in [1,2,\dots,r]$, and $r$ is the model order.


## Natural Frequencies and Modal Damping Ratios

From the eigendecompositions of $\mathbf{A}_{c}$ and $\mathbf{A}$, we have

$$\begin{aligned}
\Gamma = e^{\Lambda\Delta t} 
\implies
\lambda_{j} = (\ln{\gamma_{j}})/\Delta t~.
\end{aligned}$$

Assuming modal damping, these eigenvalues $\lambda_{j}$ contain the damped natural frequencies and modal damping factors:

$$\begin{aligned}
\lambda_{j} &= -\zeta_{j}\omega_{j} \pm i\left(\omega_{j}\sqrt{1-\zeta_{j}^{2}}\right), \hspace{0.5cm} i=\sqrt{-1} \\ \\
\lambda_{j}\bar{\lambda}_{j} &= \zeta_{j}^{2}\omega_{j}^{2} + \omega_{j}^{2}\left(1-\zeta_{j}^{2}\right) \\
    &= \omega_{j}^{2}\left(\zeta_{j}^{2} + 1 - \zeta_{j}^{2}\right) \\
    &= \omega_{j}^{2} \\ \\
\omega_{j} &= \sqrt{\lambda_{j}\bar{\lambda}_{j}} = | \lambda_{j} |, \\
\zeta_{j} &= -\frac{\text{Re}(\lambda_{j})}{\omega_{j}},\\
\end{aligned}$$

where the overline symbol $~\overline{\cdot}~$ indicates the complex conjugate, $\text{Re}(\cdot)$ indicates the real part of the complex number, $\omega_{j}$ are the modal frequencies, and $\zeta_{j}$ are the modal damping ratios.

## Mode Shapes

The eigenvectors of the continuous state transition matrix $\mathbf{A}_{c}$ transform the modal coordinates into the state coordinates.  We define the mode shapes as the transformation from modal coordinates to the output coordinates.

$$\begin{aligned}
\mathbf{x}(t) &= \mathbf{\Phi q}(t) \\
\mathbf{y}(t) &= \mathbf{Cx}(t) + \mathbf{Du}(t) \\
\mathbf{\Phi}_{\text{modal}} &= \mathbf{C\Phi}
\end{aligned}$$

