# System Realization by Information Matrix (SRIM)

For discrete-time systems, the correlation between inputs, outputs, and state yield information about the system's state evolution and response.  In fact, the state equations can be estimated by manipulating correlation matrices through the method, [System Realization by Information Matrix](https://doi.org/10.2514/2.4068) (SRIM).

## Discrete-Time System Matrix Equation
We begin with discrete-time state equations that correspond to the structure's dynamics (see [Discrete LTI State-Space Representation](https://chrysatlchern.github.io/mdof/theory/statespace.html#discrete-lti-state-space-representation)).

$$
\begin{aligned}
\mathbf{x}(k+1) &= \mathbf{A}\mathbf{x}(k) + \mathbf{B}\mathbf{u}(k) \\
\mathbf{y}(k) &= \mathbf{C}\mathbf{x}(k) + \mathbf{D}\mathbf{u}(k)
\end{aligned}
$$

By noting the state evolution

$$
\begin{aligned}
\mathbf{x}(k+1) &= \mathbf{Ax}(k)+\mathbf{B}\mathbf{u}(k)\\
\mathbf{x}(k+2) &= \mathbf{A}^2\mathbf{x}(k) + \mathbf{AB}\mathbf{u}(k) + \mathbf{B}\mathbf{u}(k+1)\\
\mathbf{x}(k+3) &= \mathbf{A}^{3}\mathbf{x}(k) + \mathbf{A}^{2}\mathbf{Bu}(k) + \mathbf{A}\mathbf{B}\mathbf{u}(k+1) + \mathbf{B}\mathbf{u}(k+2),
\end{aligned}
$$

we can generalize the response for the timepoint $k+p-1$:

$$
\begin{aligned}
\mathbf{x}(k+p) &= \mathbf{A}^{p}\mathbf{x}(k) + \sum_{i=1}^{p}\mathbf{A}^{p-i}\mathbf{Bu}(k+i-1)
\\
\mathbf{x}(k+p-1) &= \mathbf{A}^{p-1}\mathbf{x}(k) + \sum_{i=1}^{p-1}\mathbf{A}^{p-i-1}\mathbf{Bu}(k+i-1)
\\
\mathbf{y}(k+p-1) &= \mathbf{CA}^{p-1}\mathbf{x}(k) + \sum_{i=1}^{p-1}\mathbf{CA}^{p-i-1}\mathbf{Bu}(k+i-1)+\mathbf{Du}(k+p-1)~.
\end{aligned}
$$

Then, we can vertically stack $p$ successive time-points into a column vector and express this vector as $\mathbf{y}_{p}(k)$:

$$
\begin{aligned}
\mathbf{y}_{p}(k) &= \mathcal{O}_{p}\mathbf{x}(k) + \mathcal{T}_{p}\mathbf{u}_{p}(k) \\
\begin{bmatrix}
\mathbf{y}(k) \\
\mathbf{y}(k+1) \\
\vdots \\
\mathbf{y}(k+p-1)
\end{bmatrix}
=&
\begin{bmatrix}
\mathbf{C} \\
\mathbf{CA} \\ 
\mathbf{CA}^{2} \\ 
\vdots \\
\mathbf{CA}^{p-1}
\end{bmatrix}
\mathbf{x}(k)
~+ \\
&
\begin{bmatrix}
\mathbf{D} \\ 
\mathbf{CB} & \mathbf{D} \\
\mathbf{CAB} & \mathbf{CB} & \mathbf{D} \\
\vdots & \vdots & \vdots & \ddots \\
\mathbf{CA}^{p-2}\mathbf{B} & \mathbf{CA}^{p-3}\mathbf{B} & \mathbf{CA}^{p-4}\mathbf{B} & \cdots & \mathbf{D}
\end{bmatrix}
\begin{bmatrix}
\mathbf{u}(k) \\
\mathbf{u}(k+1) \\
\vdots \\
\mathbf{u}(k+p-1)
\end{bmatrix}~.
\end{aligned}
$$

<!-- $$
\mathbf{y}_{p}(k) = 
\begin{bmatrix}
\mathbf{y}(k) \\
\mathbf{y}(k+1) \\
\vdots \\
\mathbf{y}(k+p-1)
\end{bmatrix}
, \quad
\mathbf{u}_{p}(k) = 
\begin{bmatrix}
\mathbf{u}(k) \\
\mathbf{u}(k+1) \\
\vdots \\
\mathbf{u}(k+p-1)
\end{bmatrix}
$$ -->

Finally, we horizontally stack $N$ successive timepoints of these column vectors in a matrix, to get the matrix equation

$$
\boxed{\mathbf{Y}_{p}(k) = \mathcal{O}_{p}\mathbf{X}(k) + \mathcal{T}_{p}\mathbf{U}_{p}(k)} ~,
$$

where 
$$
\begin{aligned}
\mathbf{Y}_{p}(k) &= \begin{bmatrix} \mathbf{y}_{p}(k) & \mathbf{y}_{p}(k+1) & \cdots & \mathbf{y}_{p}(k+N-1) \end{bmatrix} \\
&= \begin{bmatrix}
\mathbf{y}(k)     & \mathbf{y}(k+1) & \cdots & \mathbf{y}(k+N-1)\\
\mathbf{y}(k+1)   & \mathbf{y}(k+2) & \cdots & \mathbf{y}(k+N)  \\
\vdots            & \vdots          & \ddots & \vdots \\
\mathbf{y}(k+p-1) & \mathbf{y}(k+p) & \cdots & \mathbf{y}(k+N+p-2)
\end{bmatrix}
\end{aligned}
$$

$$
\mathbf{X}(k) = \begin{bmatrix} \mathbf{x}(k) & \mathbf{x}(k+1) & \cdots & \mathbf{x}(k+N-1) \end{bmatrix} 
$$

$$
\begin{aligned}
\mathbf{U}_{p}(k) &= \begin{bmatrix} \mathbf{u}_{p}(k) & \mathbf{u}_{p}(k+1) & \cdots & \mathbf{u}_{p}(k+N-1) \end{bmatrix} \\
&= \begin{bmatrix}
\mathbf{u}(k)     & \mathbf{u}(k+1) & \cdots & \mathbf{u}(k+N-1)\\
\mathbf{u}(k+1)   & \mathbf{u}(k+2) & \cdots & \mathbf{u}(k+N)  \\
\vdots            & \vdots          & \ddots & \vdots \\
\mathbf{u}(k+p-1) & \mathbf{u}(k+p) & \cdots & \mathbf{u}(k+N+p-2)
\end{bmatrix}~.
\end{aligned}
$$


## Observability Matrix from Information Matrix
By post-multiplying the matrix equation by $\frac{1}{N}\mathbf{U}_{p}^{T}(k)$,  $\frac{1}{N}\mathbf{Y}_{p}^{T}(k)$ or $\frac{1}{N}\mathbf{X}_{p}^{T}(k)$, we obtain relationships between correlation matrices $\mathbf{R}_{yy}$, $\mathbf{R}_{yu}$, $\mathbf{R}_{uu}$, and $\mathbf{R}_{xx}$ (See [Appendix](#appendix-manipulation-of-discrete-time-system-matrix-equation-into-correlation-matrix-relationships)).

$$
\mathbf{R}_{yy} - \mathbf{R}_{yu}\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T} = \mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T} ~, 
$$

where

$$\begin{aligned}
\mathbf{R}_{yy} &= \frac{1}{N}\mathbf{Y}_{p}(k)\mathbf{Y}_{p}^{T}(k), \quad{}
\mathbf{R}_{yu} = \frac{1}{N}\mathbf{Y}_{p}(k)\mathbf{U}_{p}^{T}(k) \\
\mathbf{R}_{uu} &= \frac{1}{N}\mathbf{U}_{p}(k)\mathbf{U}_{p}^{T}(k) , \quad{}
\mathbf{R}_{xx} = \frac{1}{N}\mathbf{X}(k)\mathbf{X}^{T}(k) ~.
\end{aligned}$$

The left side of the equation is found from input and output measurements, and is called the *information matrix* of the data.  Its singular value decomposition is computed to yield the *observability matrix* $\mathcal{O}_{p}$.

$$
\mathbf{R}_{yy} - \mathbf{R}_{yu}\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T} = \mathbf{U} \Sigma \mathbf{U}^{T} = \mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T} ~. 
$$

## State Equation Matrices from Observability Matrix

Now, the state equation matrices $\mathbf{A}$ and $\mathbf{C}$ can be obtained from the observability matrix $\mathcal{O}_p$.

$$
\begin{aligned}
\mathcal{O}_{p}
=
\begin{bmatrix}
\mathbf{C} \\
\mathbf{CA} \\ 
\mathbf{CA}^{2} \\ 
\vdots \\
\mathbf{CA}^{p-1}
\end{bmatrix}
, \quad{}
\mathcal{O}_{p}(:-1)
=
\begin{bmatrix}
\mathbf{C} \\
\mathbf{CA} \\ 
\mathbf{CA}^{2} \\ 
\vdots \\
\mathbf{CA}^{p-2}
\end{bmatrix}
, \quad{}
\mathcal{O}_{p}(1:)
=
\begin{bmatrix}
\mathbf{CA} \\ 
\mathbf{CA}^{2} \\ 
\mathbf{CA}^{3} \\ 
\vdots \\
\mathbf{CA}^{p-1}
\end{bmatrix}
\end{aligned}
$$

$$
\mathbf{A} = \mathcal{O}_{p}(:-1)^{+}\mathcal{O}_{p}(1:)
$$

$$
\mathbf{C} = \mathcal{O}_{p}(0)
$$

## Output Error Minimization

$$
\Phi = \begin{bmatrix}
\mathbf{C} & \mathcal{U}_{p}(0) & \mathbf{0}_{p\times r} \\
\mathbf{CA} & \mathcal{U}_{p}(1) & \mathbf{C}\mathcal{U}_{r}(0) \\
\mathbf{CA^{2}} & \mathcal{U}_{p}(2) & \mathbf{CA}\mathcal{U}_{r}(0) + \mathbf{C}\mathcal{U}_{r}(1) \\
\vdots & \vdots & \vdots \\
\mathbf{CA}^{ns-1} & \mathcal{U}_{p}(ns-1) & \sum_{k=0}^{ns-2}\mathbf{CA}^{ns-k-2}\mathcal{U}_{r}(k)
\end{bmatrix} \in \mathbb{R}^{(ns*p) \times (pr+pq+rq)}
$$



## Appendix: Manipulation of discrete-time system matrix equation into correlation matrix relationships

In ([Juang 1997](https://doi.org/10.2514/2.4068)), the discrete-time system matrix equation is manipulated into a form describing the relationship between correlation matrices $\mathbf{R}_{yy}$, $\mathbf{R}_{yu}$, $\mathbf{R}_{uu}$, and $\mathbf{R}_{xx}$.

Post-multiplying the [discrete-time system matrix equation](#discrete-time-system-matrix-equation) by $\frac{1}{N}\mathbf{U}_{p}^{T}(k)$:

$$\begin{aligned}
\frac{1}{N}\mathbf{Y}_{p}(k)\mathbf{U}_{p}^{T}(k) &= \mathcal{O}_{p}\frac{1}{N}\mathbf{X}(k)\mathbf{U}_{p}^{T}(k) + \mathcal{T}_{p}\frac{1}{N}\mathbf{U}_{p}(k)\mathbf{U}_{p}^{T}(k) 
\\
\mathbf{R}_{yu} &= \mathcal{O}_{p}\mathbf{R}_{xu} + \mathcal{T}_{p}\mathbf{R}_{uu}
\\
\mathcal{T}_{p} &= \left( \mathbf{R}_{yu} - \mathcal{O}_{p}\mathbf{R}_{xu} \right)\mathbf{R}_{uu}^{-1}
\end{aligned}$$

Post-multiplying by $\frac{1}{N}\mathbf{Y}_{p}^{T}(k)$:

$$\begin{aligned}
\frac{1}{N}\mathbf{Y}_{p}(k)\mathbf{Y}_{p}^{T}(k) &= \mathcal{O}_{p}\frac{1}{N}\mathbf{X}(k)\mathbf{Y}_{p}^{T}(k) + \mathcal{T}_{p}\frac{1}{N}\mathbf{U}_{p}(k)\mathbf{Y}_{p}^{T}(k)
\\
\mathbf{R}_{yy} &= \mathcal{O}_{p}\mathbf{R}_{yx}^{T} + \mathcal{T}_{p}\mathbf{R}_{yu}^{T}
\\
\mathbf{R}_{yy} &= \mathcal{O}_{p}\mathbf{R}_{yx}^{T} + \left( \mathbf{R}_{yu} - \mathcal{O}_{p}\mathbf{R}_{xu} \right)\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T}
\end{aligned}$$

Post-multiplying by $\frac{1}{N}\mathbf{X}_{p}^{T}(k)$:

$$\begin{aligned}
\frac{1}{N}\mathbf{Y}_{p}(k)\mathbf{X}_{p}^{T}(k) &= \mathcal{O}_{p}\frac{1}{N}\mathbf{X}(k)\mathbf{X}_{p}^{T}(k) + \mathcal{T}_{p}\frac{1}{N}\mathbf{U}_{p}(k)\mathbf{X}_{p}^{T}(k)
\\
\mathbf{R}_{yx} &= \mathcal{O}_{p}\mathbf{R}_{xx} + \mathcal{T}_{p}\mathbf{R}_{xu}^{T}
\\
\mathbf{R}_{yx} &= \mathcal{O}_{p}\mathbf{R}_{xx} + \left( \mathbf{R}_{yu} - \mathcal{O}_{p}\mathbf{R}_{xu} \right)\mathbf{R}_{uu}^{-1}\mathbf{R}_{xu}^{T}
\end{aligned}$$

Substituting the equation for $\mathbf{R}_{yx}$ into the equation for $\mathbf{R}_{yy}$:

$$\begin{aligned}
\mathbf{R}_{yy} =& ~\mathcal{O}_{p}
\left(\mathcal{O}_{p}\mathbf{R}_{xx} + \left( \mathbf{R}_{yu} - \mathcal{O}_{p}\mathbf{R}_{xu} \right)\mathbf{R}_{uu}^{-1}\mathbf{R}_{xu}^{T}\right)^{T} 
\\
&+
\left( \mathbf{R}_{yu} - \mathcal{O}_{p}\mathbf{R}_{xu} \right)\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T}
\\
=& ~\mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T}
 + \mathcal{O}_{p}\mathbf{R}_{xu}\mathbf{R}_{uu}^{-1} \left( \mathbf{R}_{yu}^{T} - \mathbf{R}_{xu}^{T}\mathcal{O}_{p}^{T} \right) 
\\
&+
\left( \mathbf{R}_{yu} - \mathcal{O}_{p}\mathbf{R}_{xu} \right)\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T}
\\
=& ~\mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T}
 + \mathcal{O}_{p}\mathbf{R}_{xu}\mathbf{R}_{uu}^{-1}  \mathbf{R}_{yu}^{T} - \mathcal{O}_{p}\mathbf{R}_{xu}\mathbf{R}_{uu}^{-1} \mathbf{R}_{xu}^{T}\mathcal{O}_{p}^{T} 
\\
&+
 \mathbf{R}_{yu}\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T} - \mathcal{O}_{p}\mathbf{R}_{xu} \mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T}
\\
=& ~\mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T}
 - \mathcal{O}_{p}\mathbf{R}_{xu}\mathbf{R}_{uu}^{-1} \mathbf{R}_{xu}^{T}\mathcal{O}_{p}^{T} +
 \mathbf{R}_{yu}\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T} 
\end{aligned}$$

Moving all of the terms that can be composed with measured data to the left side:

$$\begin{aligned}
\mathbf{R}_{yy} - \mathbf{R}_{yu}\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T} 
&= \mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T} - \mathcal{O}_{p}\mathbf{R}_{xu}\mathbf{R}_{uu}^{-1} \mathbf{R}_{xu}^{T}\mathcal{O}_{p}^{T} \\
&= \mathcal{O}_{p}\left( \mathbf{R}_{xx} - \mathbf{R}_{xu}\mathbf{R}_{uu}^{-1} \mathbf{R}_{xu}^{T} \right) \mathcal{O}_{p}^{T} 
\end{aligned}$$

We make the assumption that all current and future input data is uncorrelated with the current state, which means that the average of the products $\mathbf{x}(k)\mathbf{u}(k+i), ~~ i \in [0,1,2,\dots]$ is zero.  This gives:

$$\begin{aligned}
\mathbf{R}_{xu} &=
\frac{1}{N}
\begin{bmatrix}
\sum_{j=0}^{N-1}\mathbf{x}(k+j)\mathbf{u}(k+j) \\
\sum_{j=0}^{N-1}\mathbf{x}(k+j)\mathbf{u}(k+j+1) \\
\sum_{j=0}^{N-1}\mathbf{x}(k+j)\mathbf{u}(k+j+2) \\
\vdots \\
\sum_{j=0}^{N-1}\mathbf{x}(k+j)\mathbf{u}(k+j+p-1)
\end{bmatrix}^{T} \\
&=
\mathbf{0}
\end{aligned}$$

in order to yield:

$$
\mathbf{R}_{yy} - \mathbf{R}_{yu}\mathbf{R}_{uu}^{-1}\mathbf{R}_{yu}^{T} = \mathcal{O}_{p}\mathbf{R}_{xx}\mathcal{O}_{p}^{T}~.
$$