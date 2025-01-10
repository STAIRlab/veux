System Realization by Information Matrix (SRIM)
===============================================

For discrete-time systems, the correlation between inputs, outputs, and
state yield information about the system's state evolution and response.
In fact, the state equations can be estimated by manipulating
correlation matrices through the method, `System Realization by
Information Matrix <https://doi.org/10.2514/2.4068>`__ (SRIM).

Discrete-Time System Matrix Equation
------------------------------------

We begin with discrete-time state equations that correspond to the
structure's dynamics (see `Discrete LTI State-Space
Representation <https://chrystalchern.github.io/mdof/theory/statespace.html#discrete-lti-state-space-representation>`__).

.. math::


   \begin{aligned}
   \bm{x}(k+1) &= \bm{Ax}(k) + \bm{Bu}(k) \\
   \bm{y}(k) &= \bm{Cx}(k) + \bm{Du}(k)
   \end{aligned}

By noting the state evolution

.. math::


   \begin{aligned}
   \bm{x}(k+1) &= \bm{Ax}(k)+\bm{B}\bm{U}_{p}(k)\\
   \bm{x}(k+2) &= \bm{A}^2\bm{X}(k) + \bm{AB}\bm{U}_{p}(k) + \bm{Bu}(k+1)\\
   \bm{x}(k+3) &= \bm{A}^{3}\bm{X}(k) + \bm{A}^{2}\bm{Bu}(k) + \bm{ABu}(k+1) + \bm{Bu}(k+2),
   \end{aligned}

we can generalize the response for the timepoint :math:`k+p-1`:

.. math::


   \begin{aligned}
   \bm{x}(k+p) &= \bm{A}^{p}\bm{x}(k) + \sum_{i=1}^{p}\bm{A}^{p-i}\bm{Bu}(k+i-1)
   \\
   \bm{x}(k+p-1) &= \bm{A}^{p-1}\bm{x}(k) + \sum_{i=1}^{p-1}\bm{A}^{p-i-1}\bm{Bu}(k+i-1)
   \\
   \bm{y}(k+p-1) &= \bm{CA}^{p-1}\bm{x}(k) + \sum_{i=1}^{p-1}\bm{CA}^{p-i-1}\bm{Bu}(k+i-1)+\bm{Du}(k+p-1)~.
   \end{aligned}

Then, we can vertically stack :math:`p` successive time-points into a
column vector and express this vector as :math:`\bm{y}_{p}(k)`:

.. math::


   \begin{aligned}
   \bm{y}_{p}(k) &= \mathcal{O}_{p}\bm{x}(k) + \mathcal{T}_{p}\bm{u}_{p}(k) \\
   \begin{bmatrix}
   \bm{y}(k) \\
   \bm{y}(k+1) \\
   \vdots \\
   \bm{y}(k+p-1)
   \end{bmatrix}
   =&
   \begin{bmatrix}
   \bm{C} \\
   \bm{CA} \\ 
   \bm{CA}^{2} \\ 
   \vdots \\
   \bm{CA}^{p-1}
   \end{bmatrix}
   \bm{x}(k)
   ~+ \\
   &
   \begin{bmatrix}
   \bm{D} \\ 
   \bm{CB} & \bm{D} \\
   \bm{CAB} & \bm{CB} & \bm{D} \\
   \vdots & \vdots & \vdots & \ddots \\
   \bm{CA}^{p-2}\bm{B} & \bm{CA}^{p-3}\bm{B} & \bm{CA}^{p-4}\bm{B} & \cdots & \bm{D}
   \end{bmatrix}
   \begin{bmatrix}
   \bm{u}(k) \\
   \bm{u}(k+1) \\
   \vdots \\
   \bm{u}(k+p-1)
   \end{bmatrix}~.
   \end{aligned}

.. raw:: html

   <!-- $$
   \bm{y}_{p}(k) = 
   \begin{bmatrix}
   \bm{y}(k) \\
   \bm{y}(k+1) \\
   \vdots \\
   \bm{y}(k+p-1)
   \end{bmatrix}
   , \quad
   \bm{u}_{p}(k) = 
   \begin{bmatrix}
   \bm{u}(k) \\
   \bm{u}(k+1) \\
   \vdots \\
   \bm{u}(k+p-1)
   \end{bmatrix}
   $$ -->

Finally, we horizontally stack :math:`N` successive timepoints of these
column vectors in a matrix, to get the matrix equation

.. math::


   \boxed{\bm{Y}_{p}(k) = \mathcal{O}_{p}\bm{X}(k) + \mathcal{T}_{p}\bm{U}_{p}(k)} ~,

where

.. math::


   \begin{aligned}
   \bm{Y}_{p}(k) &= \begin{bmatrix} \bm{y}_{p}(k) & \bm{y}_{p}(k+1) & \cdots & \bm{y}_{p}(k+N-1) \end{bmatrix} \\
   &= \begin{bmatrix}
   \bm{y}(k)     & \bm{y}(k+1) & \cdots & \bm{y}(k+N-1)\\
   \bm{y}(k+1)   & \bm{y}(k+2) & \cdots & \bm{y}(k+N)  \\
   \vdots            & \vdots          & \ddots & \vdots \\
   \bm{y}(k+p-1) & \bm{y}(k+p) & \cdots & \bm{y}(k+N+p-2)
   \end{bmatrix}
   \end{aligned}

.. math::


   \bm{X}(k) = \begin{bmatrix} \bm{x}(k) & \bm{x}(k+1) & \cdots & \bm{x}(k+N-1) \end{bmatrix} 

.. math::


   \begin{aligned}
   \bm{U}_{p}(k) &= \begin{bmatrix} \bm{u}_{p}(k) & \bm{u}_{p}(k+1) & \cdots & \bm{u}_{p}(k+N-1) \end{bmatrix} \\
   &= \begin{bmatrix}
   \bm{u}(k)     & \bm{u}(k+1) & \cdots & \bm{u}(k+N-1)\\
   \bm{u}(k+1)   & \bm{u}(k+2) & \cdots & \bm{u}(k+N)  \\
   \vdots            & \vdots          & \ddots & \vdots \\
   \bm{u}(k+p-1) & \bm{u}(k+p) & \cdots & \bm{u}(k+N+p-2)
   \end{bmatrix}~.
   \end{aligned}

Observability Matrix from Information Matrix
--------------------------------------------

By post-multiplying the matrix equation by
:math:`\frac{1}{N}\bm{U}_{p}^{T}(k)`,
:math:`\frac{1}{N}\bm{Y}_{p}^{T}(k)` or
:math:`\frac{1}{N}\bm{X}_{p}^{T}(k)`, we obtain relationships
between correlation matrices :math:`\bm{R}_{yy}`,
:math:`\bm{R}_{yu}`, :math:`\bm{R}_{uu}`, and
:math:`\bm{R}_{xx}` (See
`Appendix <#appendix-manipulation-of-discrete-time-system-matrix-equation-into-correlation-matrix-relationships>`__).

.. math::


   \bm{R}_{yy} - \bm{R}_{yu}\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T} = \mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T} ~, 

where

.. math::

   \begin{aligned}
   \bm{R}_{yy} &= \frac{1}{N}\bm{Y}_{p}(k)\bm{Y}_{p}^{T}(k), \quad{}
   \bm{R}_{yu} = \frac{1}{N}\bm{Y}_{p}(k)\bm{U}_{p}^{T}(k) \\
   \bm{R}_{uu} &= \frac{1}{N}\bm{U}_{p}(k)\bm{U}_{p}^{T}(k) , \quad{}
   \bm{R}_{xx} = \frac{1}{N}\bm{X}(k)\bm{X}^{T}(k) ~.
   \end{aligned}

The left side of the equation is found from input and output
measurements, and is called the *information matrix* of the data. Its
singular value decomposition is computed to yield the *observability
matrix* :math:`\mathcal{O}_{p}`.

.. math::


   \bm{R}_{yy} - \bm{R}_{yu}\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T} = \bm{U} \Sigma \bm{U}^{T} = \mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T} ~. 

State Equation Matrices from Observability Matrix
-------------------------------------------------

Now, the state equation matrices :math:`\bm{A}` and
:math:`\bm{C}` can be obtained from the observability matrix
:math:`\mathcal{O}_p`.

.. math::


   \begin{aligned}
   \mathcal{O}_{p}
   =
   \begin{bmatrix}
   \bm{C} \\
   \bm{CA} \\ 
   \bm{CA}^{2} \\ 
   \vdots \\
   \bm{CA}^{p-1}
   \end{bmatrix}
   , \quad{}
   \mathcal{O}_{p}(:-1)
   =
   \begin{bmatrix}
   \bm{C} \\
   \bm{CA} \\ 
   \bm{CA}^{2} \\ 
   \vdots \\
   \bm{CA}^{p-2}
   \end{bmatrix}
   , \quad{}
   \mathcal{O}_{p}(1:)
   =
   \begin{bmatrix}
   \bm{CA} \\ 
   \bm{CA}^{2} \\ 
   \bm{CA}^{3} \\ 
   \vdots \\
   \bm{CA}^{p-1}
   \end{bmatrix}
   \end{aligned}

.. math::


   \bm{A} = \mathcal{O}_{p}(:-1)^{+}\mathcal{O}_{p}(1:)

.. math::


   \bm{C} = \mathcal{O}_{p}(0)

Appendix: Manipulation of discrete-time system matrix equation into correlation matrix relationships
----------------------------------------------------------------------------------------------------

In (`Juang 1997 <https://doi.org/10.2514/2.4068>`__), the discrete-time
system matrix equation is manipulated into a form describing the
relationship between correlation matrices :math:`\bm{R}_{yy}`,
:math:`\bm{R}_{yu}`, :math:`\bm{R}_{uu}`, and
:math:`\bm{R}_{xx}`.

Post-multiplying the `discrete-time system matrix
equation <#discrete-time-system-matrix-equation>`__ by
:math:`\frac{1}{N}\bm{U}_{p}^{T}(k)`:

.. math::

   \begin{aligned}
   \frac{1}{N}\bm{Y}_{p}(k)\bm{U}_{p}^{T}(k) &= \mathcal{O}_{p}\frac{1}{N}\bm{X}(k)\bm{U}_{p}^{T}(k) + \mathcal{T}_{p}\frac{1}{N}\bm{U}_{p}(k)\bm{U}_{p}^{T}(k) 
   \\
   \bm{R}_{yu} &= \mathcal{O}_{p}\bm{R}_{xu} + \mathcal{T}_{p}\bm{R}_{uu}
   \\
   \mathcal{T}_{p} &= \left( \bm{R}_{yu} - \mathcal{O}_{p}\bm{R}_{xu} \right)\bm{R}_{uu}^{-1}
   \end{aligned}

Post-multiplying by :math:`\frac{1}{N}\bm{Y}_{p}^{T}(k)`:

.. math::

   \begin{aligned}
   \frac{1}{N}\bm{Y}_{p}(k)\bm{Y}_{p}^{T}(k) &= \mathcal{O}_{p}\frac{1}{N}\bm{X}(k)\bm{Y}_{p}^{T}(k) + \mathcal{T}_{p}\frac{1}{N}\bm{U}_{p}(k)\bm{Y}_{p}^{T}(k)
   \\
   \bm{R}_{yy} &= \mathcal{O}_{p}\bm{R}_{yx}^{T} + \mathcal{T}_{p}\bm{R}_{yu}^{T}
   \\
   \bm{R}_{yy} &= \mathcal{O}_{p}\bm{R}_{yx}^{T} + \left( \bm{R}_{yu} - \mathcal{O}_{p}\bm{R}_{xu} \right)\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T}
   \end{aligned}

Post-multiplying by :math:`\frac{1}{N}\bm{X}_{p}^{T}(k)`:

.. math::

   \begin{aligned}
   \frac{1}{N}\bm{Y}_{p}(k)\bm{X}_{p}^{T}(k) &= \mathcal{O}_{p}\frac{1}{N}\bm{X}(k)\bm{X}_{p}^{T}(k) + \mathcal{T}_{p}\frac{1}{N}\bm{U}_{p}(k)\bm{X}_{p}^{T}(k)
   \\
   \bm{R}_{yx} &= \mathcal{O}_{p}\bm{R}_{xx} + \mathcal{T}_{p}\bm{R}_{xu}^{T}
   \\
   \bm{R}_{yx} &= \mathcal{O}_{p}\bm{R}_{xx} + \left( \bm{R}_{yu} - \mathcal{O}_{p}\bm{R}_{xu} \right)\bm{R}_{uu}^{-1}\bm{R}_{xu}^{T}
   \end{aligned}

Substituting the equation for :math:`\bm{R}_{yx}` into the equation
for :math:`\bm{R}_{yy}`:

.. math::

   \begin{aligned}
   \bm{R}_{yy} =& ~\mathcal{O}_{p}
   \left(\mathcal{O}_{p}\bm{R}_{xx} + \left( \bm{R}_{yu} - \mathcal{O}_{p}\bm{R}_{xu} \right)\bm{R}_{uu}^{-1}\bm{R}_{xu}^{T}\right)^{T} 
   \\
   &+
   \left( \bm{R}_{yu} - \mathcal{O}_{p}\bm{R}_{xu} \right)\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T}
   \\
   =& ~\mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T}
    + \mathcal{O}_{p}\bm{R}_{xu}\bm{R}_{uu}^{-1} \left( \bm{R}_{yu}^{T} - \bm{R}_{xu}^{T}\mathcal{O}_{p}^{T} \right) 
   \\
   &+
   \left( \bm{R}_{yu} - \mathcal{O}_{p}\bm{R}_{xu} \right)\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T}
   \\
   =& ~\mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T}
    + \mathcal{O}_{p}\bm{R}_{xu}\bm{R}_{uu}^{-1}  \bm{R}_{yu}^{T} - \mathcal{O}_{p}\bm{R}_{xu}\bm{R}_{uu}^{-1} \bm{R}_{xu}^{T}\mathcal{O}_{p}^{T} 
   \\
   &+
    \bm{R}_{yu}\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T} - \mathcal{O}_{p}\bm{R}_{xu} \bm{R}_{uu}^{-1}\bm{R}_{yu}^{T}
   \\
   =& ~\mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T}
    - \mathcal{O}_{p}\bm{R}_{xu}\bm{R}_{uu}^{-1} \bm{R}_{xu}^{T}\mathcal{O}_{p}^{T} +
    \bm{R}_{yu}\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T} 
   \end{aligned}

Moving all of the terms that can be composed with measured data to the
left side:

.. math::

   \begin{aligned}
   \bm{R}_{yy} - \bm{R}_{yu}\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T} 
   &= \mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T} - \mathcal{O}_{p}\bm{R}_{xu}\bm{R}_{uu}^{-1} \bm{R}_{xu}^{T}\mathcal{O}_{p}^{T} \\
   &= \mathcal{O}_{p}\left( \bm{R}_{xx} - \bm{R}_{xu}\bm{R}_{uu}^{-1} \bm{R}_{xu}^{T} \right) \mathcal{O}_{p}^{T} 
   \end{aligned}

We make the assumption that all current and future input data is
uncorrelated with the current state, which means that the average of the
products :math:`\bm{x}(k)\bm{u}(k+i), ~~ i \in [0,1,2,\dots]` is
zero. This gives:

.. math::

   \begin{aligned}
   \bm{R}_{xu} &=
   \frac{1}{N}
   \begin{bmatrix}
   \sum_{j=0}^{N-1}\bm{x}(k+j)\bm{u}(k+j) \\
   \sum_{j=0}^{N-1}\bm{x}(k+j)\bm{u}(k+j+1) \\
   \sum_{j=0}^{N-1}\bm{x}(k+j)\bm{u}(k+j+2) \\
   \vdots \\
   \sum_{j=0}^{N-1}\bm{x}(k+j)\bm{u}(k+j+p-1)
   \end{bmatrix}^{T} \\
   &=
   \bm{0}
   \end{aligned}

in order to yield:

.. math::


   \bm{R}_{yy} - \bm{R}_{yu}\bm{R}_{uu}^{-1}\bm{R}_{yu}^{T} = \mathcal{O}_{p}\bm{R}_{xx}\mathcal{O}_{p}^{T}~.

