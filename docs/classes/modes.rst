Modal Properties from State Space Realization
=============================================

Structural system dynamics are in continuous time. With the time-domain
system identification methods in the ``mdof`` package such as OKID-ERA
and SRIM, a structural system’s discrete-time state space realization is
obtained from measured data. The following process recovers the
structure’s modal properties (i.e., natural frequencies, modal damping
ratios, and mode shapes) from the discrete state space realization
coefficients, :math:`\mathbf{A}` and :math:`\mathbf{C}`.

Eigendecompositions of :math:`\mathbf{A}_{c}` and :math:`\mathbf{A}`
--------------------------------------------------------------------

The relationship between the eigendecompositions of
:math:`\mathbf{A}_{c}`, the continuous-time state transition matrix, and
:math:`\mathbf{A}`, the discrete-time state transition matrix, is shown
below.

.. math::

   \begin{aligned}
   \mathbf{A}_{c} &= \Phi\Lambda\Phi^{-1} \\
   \mathbf{A} &= \Psi\Gamma\Psi^{-1} \\
   \end{aligned}

.. math::

   \begin{aligned}
   \mathbf{A} = e^{\mathbf{A}_{c}\Delta t} = e^{\Phi\Lambda\Phi^{-1}\Delta t} = \Phi e^{\Lambda\Delta t}\Phi^{-1}
   \end{aligned}

.. math::

   \begin{aligned}
   \Psi = \Phi, \quad \Gamma = e^{\Lambda\Delta t} \\
   \end{aligned}

where

.. math::

   \Psi = 
   \begin{bmatrix} 
   \psi_{1} & \psi_{2} & \cdots & \psi_{r} 
   \end{bmatrix}, \quad{} 
   \Phi =
   \begin{bmatrix} 
   \phi_{1} & \phi_{2} & \cdots & \phi_{r} 
   \end{bmatrix}

.. math::


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
   \end{bmatrix}

-  :math:`\gamma_{j}` and :math:`\psi_{j}` are the eigenvalues and
   eigenvectors of :math:`\mathbf{A}`,

-  :math:`\lambda_{j}` and :math:`\phi_{j}` are the eigenvalues and
   eigenvectors of :math:`\mathbf{A}_{c}`,

-  :math:`j \in [1,2,\dots,r]`, and :math:`r` is the model order.

Natural Frequencies and Modal Damping Ratios
--------------------------------------------

From the eigendecompositions of :math:`\mathbf{A}_{c}` and
:math:`\mathbf{A}`, we have

.. math::

   \begin{aligned}
   \Gamma = e^{\Lambda\Delta t} 
   \implies
   \lambda_{j} = (\ln{\gamma_{j}})/\Delta t~.
   \end{aligned}

Assuming modal damping, these eigenvalues :math:`\lambda_{j}` contain
the damped natural frequencies and modal damping factors:

.. math::

   \begin{aligned}
   \lambda_{j} &= -\zeta_{j}\omega_{j} \pm i\left(\omega_{j}\sqrt{1-\zeta_{j}^{2}}\right), \hspace{0.5cm} i=\sqrt{-1} \\ \\
   \lambda_{j}\bar{\lambda}_{j} &= \zeta_{j}^{2}\omega_{j}^{2} + \omega_{j}^{2}\left(1-\zeta_{j}^{2}\right) \\
       &= \omega_{j}^{2}\left(\zeta_{j}^{2} + 1 - \zeta_{j}^{2}\right) \\
       &= \omega_{j}^{2} \\ \\
   \omega_{j} &= \sqrt{\lambda_{j}\bar{\lambda}_{j}} = | \lambda_{j} |, \\
   \zeta_{j} &= -\frac{\text{Re}(\lambda_{j})}{\omega_{j}},\\
   \end{aligned}

where the overline symbol :math:`~\overline{\cdot}~` indicates the
complex conjugate, :math:`\text{Re}(\cdot)` indicates the real part of
the complex number, :math:`\omega_{j}` are the modal frequencies, and
:math:`\zeta_{j}` are the modal damping ratios.

Mode Shapes
-----------

The eigenvectors of the continuous state transition matrix
:math:`\mathbf{A}_{c}` transform the modal coordinates into the state
coordinates. We define the mode shapes as the transformation from modal
coordinates to the output coordinates.

.. math::

   \begin{aligned}
   \mathbf{x}(t) &= \mathbf{\Phi q}(t) \\
   \mathbf{y}(t) &= \mathbf{Cx}(t) + \mathbf{Du}(t) \\
   \mathbf{\Phi}_{\text{modal}} &= \mathbf{C\Phi}
   \end{aligned}
