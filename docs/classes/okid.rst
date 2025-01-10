
Observer Kalman Filter Identification (OKID)
---------------------------------------------

Structural dynamics are noisy, hard to measure, and lightly damped, and
ERA is intended only to characterize impulse responses rather than time
histories. However, available data from ambient or small excitations
during structure service can be de-noised and used to estimate impulse
response data. Then, ERA can be used to obtain a reduced order model
even if the available data are not a clean impulse response. This
process is called `Observer Kalman
Identification <https://doi.org/10.2514/3.21006>`__, or OKID-ERA when
combined with ERA.

When noise is incorporated into the discrete LTI state-space
representation of a structural system, it becomes a *linear Gaussian
model* of a *hidden Markov process*.

Because the data are assumed to follow a linear Gaussian model, Kalman
filtering can estimate an impulse response that is most consistent with
the input-output data. The estimated model after filtering is the same
as that of ERA:

.. math::


   \begin{aligned}
       \mathbf{x}_{k+1} &= \mathbf{Ax}_{k} + \mathbf{Bu}_{k} \\
       \mathbf{y}_{k} &= \mathbf{Cx}_{k} + \mathbf{Du}_{k} \\        
   \end{aligned}

Since the input is no longer an impulse, the state-space evolution
includes more terms than ERA.

.. math::


   \begin{aligned}
       \mathbf{u}_{0},\mathbf{u}_{1},\mathbf{u}_{2},...,\mathbf{u}_{k} :=& \text{given input} \\
       \mathbf{x}_{0},\mathbf{x}_{1},\mathbf{x}_{2},...,\mathbf{x}_{k} =&  \mathbf{0},(\mathbf{Bu}_{0}),(\mathbf{ABu}_{0}+\mathbf{Bu}_{1}),...,(\mathbf{A}^{k-1}\mathbf{Bu}_{0}+\mathbf{A}^{k-2}\mathbf{Bu}_{1}+...+\mathbf{Bu}_{k-1}) \\
       \mathbf{y}_{0},\mathbf{y}_{1},\mathbf{y}_{2},...,\mathbf{y}_{k} =&  \mathbf{Du}_0,(\mathbf{CBu}_{0}+\mathbf{Du}_{1}),(\mathbf{CABu}_{0}+\mathbf{CBu}_{1}+\mathbf{Du}_{2}),..., \\
       & (\mathbf{CA}^{k-1}\mathbf{Bu}_{0}+\mathbf{CA}^{k-2}\mathbf{Bu}_{1}+...+\mathbf{Du}_{k}).
   \end{aligned}

The output data can be expressed in terms of the Markov parameters and
an upper triangular *data matrix* :math:`\mathscr{B}` built from the
input data; however, inverting :math:`\mathscr{B}` is often
computationally expensive or ill-conditioned.

.. math::


   \underbrace{\begin{bmatrix} \mathbf{y}_{0} & \mathbf{y}_{1} & \mathbf{y}_{2} & \cdots & \mathbf{y}_{m} \end{bmatrix}}_{\mathbf{S}}
   = 
   \underbrace{\begin{bmatrix} \mathbf{y}_{0} & \mathbf{y}_{1} & \mathbf{y}_{2} & \cdots & \mathbf{y}_{m} \end{bmatrix}_{\delta}}_{\mathbf{S}_{\delta}}
   \underbrace{\begin{bmatrix}
       \mathbf{u}_{0} & \mathbf{u}_{1} & \cdots & \mathbf{u}_{m}   \\
       \mathbf{0}     & \mathbf{u}_{0} & \cdots & \mathbf{u}_{m-1} \\
       \vdots         & \vdots         & \ddots & \vdots           \\
       \mathbf{0}     & \mathbf{0}     & \cdots & \mathbf{u}_{0}   \\
   \end{bmatrix}}_{\mathscr{B}}

where the subscript :math:`\delta` indicates that the response comes
from an impulse input.

The Kalman filter is applied by augmenting the system with the outputs
:math:`\mathbf{y}_{i}` to form the *augmented data matrix*
:math:`\mathscr{V}`:

.. math::


   \mathscr{V}
   = 
   \begin{bmatrix}
       \mathbf{u}_{0} & \mathbf{u}_{1} & \cdots & \mathbf{u}_{l}   & \cdots & \mathbf{u}_{m}   \\
       \mathbf{0}     & \mathbf{v}_{0} & \cdots & \mathbf{v}_{l-1} & \cdots & \mathbf{v}_{m-1} \\
       \vdots         & \vdots         & \ddots & \vdots           & \ddots & \vdots           \\
       \mathbf{0}     & \mathbf{0}     & \cdots & \mathbf{v}_{0}   & \cdots & \mathbf{v}_{m-l} \\
   \end{bmatrix}, \hspace{1cm}
   \mathbf{v}_{i} = \begin{bmatrix} \mathbf{u}_{i} \\ \mathbf{y}_{i} \end{bmatrix}.

Then, the Markov parameters (i.e., the impulse response) can be
estimated as a function of the input and output data as follows:

.. math::  \hat{\mathbf{S}}_\delta = \mathbf{S}\mathscr{V}^{\dagger} 

where the superscript :math:`\dagger` indicates pseudo-inverse,

Extract the estimated, or *observer*, Markov parameters from the block
columns of :math:`\hat{\mathbf{S}}_\delta`:

.. math::


   \begin{aligned}
           \hat{\mathbf{S}}_{\delta 0} &\in \mathbb{R}^{p\times q} \\
           \hat{\mathbf{S}}_{\delta k} &=
           \begin{bmatrix} \hat{\mathbf{S}}_{\delta k}^{(1)} & \hat{\mathbf{S}}_{\delta k}^{(2)} \end{bmatrix} , \hspace{0.5cm} k\in[1,2,...] \\ 
       \hat{\mathbf{S}}_{\delta k}^{(1)} &\in\mathbb{R}^{p\times q}, \hspace{0.5cm} 
       \hat{\mathbf{S}}_{\delta k}^{(2)}  \in\mathbb{R}^{p\times p}
   \end{aligned}

Reconstruct the system Markov parameters:

.. math::


   \mathbf{y}_{\delta 0} = \hat{\mathbf{S}}_{\delta 0} = \mathbf{D}, \hspace{0.5cm}
   \mathbf{y}_{\delta k} = \hat{\mathbf{S}}_{\delta k}^{(1)}
   + \sum_{i=1}^{k}{\hat{\mathbf{S}}_{\delta k}^{(2)}}\mathbf{y}_{\delta (k-i)}.
