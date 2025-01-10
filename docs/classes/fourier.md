<!-- ---
title: Fourier Analysis
author: Chrystal Chern
date: Monday, April 1, 2024
... -->


## Fourier series expansion

Certain **periodic** functions can be expressed as a Fourier series expansion.  With $P$ as the period of the function,

The sine-cosine form represents $f(x)$ in the orthogonal basis $\left\{\cos{\frac{2\pi n x}{P}}, \sin{\frac{2\pi n x}{P}} ~|~ n \in \mathbb{Z}_{+} \right\}$.
$$\begin{aligned}
    f(x) &=                    \frac{a_{0}}{2} 
                              + \sum_{n=1}^{\infty}\left({
                                                a_{n}\cos{\frac{2{\pi}nx}{P}}
                                            +   b_{n}\sin{\frac{2{\pi}nx}{P}}
                                                  }\right) \\
    a_{0} &= \frac{2}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  {f(t)dt}~, \\
    a_{n} &= \frac{2}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                            {f(t) \cos{\frac{2{\pi}nt}{P}} dt}~, \text{ and} \\
    b_{n} &= \frac{2}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                            {f(t) \sin{\frac{2{\pi}nt}{P}} dt}~.
\end{aligned}$$

The exponential form represents $f(x)$ in the orthogonal basis $\left\{\exp{i \frac{2\pi n x}{P}} ~|~ n \in \mathbb{Z} \right\}$.
$$\begin{aligned}
f(x) &= \sum_{n=-\infty}^{n=\infty} {c_{n}e^{i\frac{2{\pi}n}{P}x}} \\
c_{n} &= \frac{1}{P} \int_{-\frac{P}{2}}^{\frac{P}{2}} {f(t) e^{-i\frac{2{\pi}n}{P}t} dt}
\end{aligned}$$


## Fourier transform

Plug $c_{n}$ into the exponential form:
$$\begin{aligned}
    f(x) &= \sum_{n=-\infty}^{n=\infty} {\frac{1}{P}} 
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{-i\frac{2{\pi}n}{P}t}  dt~ 
                                            e^{i\frac{2{\pi}n}{P}x} \\
        &= \sum_{n=-\infty}^{n=\infty} {\frac{1}{P}} 
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{i\frac{2{\pi}n}{P}(x-t)}  dt \\
\end{aligned}$$

To generalize to certain **non-periodic** functions, take the limit as $P \rightarrow \infty$, and change from the variable of summation $n$ to the variable of integration $\omega = \frac{2\pi{}n}{P}$ . 

$$\begin{aligned}
    f(x) &= \underset{P \rightarrow \infty}\lim{} 
                    \sum_{n=-\infty}^{n=\infty} \left( {\frac{1}{P}} 
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{i\frac{2{\pi}n}{P}(x-t)}  dt \right) \\
         &= \underset{P \rightarrow \infty}\lim{}
            \int_{n=-\infty}^{n=\infty} \left(
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{i\frac{2{\pi}n}{P}(x-t)}  dt \right) {\frac{dn}{P}} \\
         &= \int_{\omega=-\infty}^{\omega=\infty} \left(
                    \int_{-\infty}^{\infty}  
                                f(t)   e^{i\omega(x-t)}  dt \right) \frac{d\omega}{2\pi} \\
         &= \frac{1}{2\pi}\int_{-\infty}^{\infty} e^{i\omega x} \left(
                    \int_{-\infty}^{\infty}  
                                f(t)   e^{-i\omega t}  dt \right) d\omega \\
\end{aligned}$$

The Fourier transform $\mathcal{F}(f)$ is expressed as

$$\begin{aligned}
\mathcal{F}(f) &= \phi(\omega) \\
\phi(\omega) &= \int_{-\infty}^{\infty}{f(t)e^{-i\omega t} dt}
\end{aligned}$$

and exists for all $f$ that are piecewise continuous and absolutely integrable.

The inverse Fourier transform $\mathcal{F}^{-1}(\phi)$ is expressed as

$$\begin{aligned}
\mathcal{F}^{-1}(\phi) &= f(t) \\
f(t) &= \frac{1}{2\pi}\int_{-\infty}^{\infty}{\phi(\omega)e^{i\omega x} d\omega}
\end{aligned}$$


## Discrete Fourier Transform (DFT)

The Discrete Fourier Transform fits a summation approximation over $t \in \{0,1,2,\dots,n-1\}$ of the integral $\phi(\omega) = \int_{-\infty}^{\infty}{f(t)e^{-i\omega t} dt}$ over the discrete domain $\omega_{n} = e^{i\frac{2\pi}{n}}, n \in \{0,1,2,\dots,n-1\}$.

$$
\phi(n) = 
\sum_{t=0}^{t=n-1}f(t)e^{i\frac{2\pi}{n}t}~,
$$

This corresponds to frequencies $\omega \in {0, \frac{2\pi}{n}, \frac{4\pi}{n}}$

$$
\phi(\omega_{n}) = 
\sum_{t=0}^{t=n-1}f(t)\omega_{n}^{t}~,
$$

This transformation can be expressed as a Hermitian matrix multplication.


$$
    \begin{bmatrix}
    c_{0} \\
    c_{1} \\
    c_{2} \\
    \vdots \\
    c_{n-1} \\
    \end{bmatrix}
    =
    \begin{bmatrix}
    1 & 1 & 1 & \cdots & 1 \\
    1 & \omega_{n} & \omega_{n}^{2} & \cdots & \omega_{n}^{n-1} \\
    1 & \omega_{n}^{2} & \omega_{n}^{4} & \cdots & \omega_{n}^{2(n-1)} \\
    \vdots & \vdots & \vdots & \ddots & \vdots \\
    1 & \omega_{n}^{n-1} & \omega_{n}^{2(n-1)} & \cdots & \omega_{n}^{(n-1)^{2}} \\
    \end{bmatrix}
    \begin{bmatrix}
    y_{0} \\
    y_{1} \\
    y_{2} \\
    \vdots \\
    y_{n-1} \\
    \end{bmatrix}
$$



## Fast Fourier Transform (FFT)

The bare-bones (radix-2) Cooley-Tukey algorithm requires the series length to be a power of 2.

Base case: $n=1$

$$
    c_{0} 
    = F_{1}y_{0} 
    = \begin{bmatrix}
        1
    \end{bmatrix}
    y_{0}
$$

The next case: $n=2$
$$
\begin{aligned}
    \begin{bmatrix}
        c_{0} \\
        c_{1}
    \end{bmatrix}
    &= F_{2}
    \begin{bmatrix}
        y_{0}  \\
        y_{1}
    \end{bmatrix}
    = \begin{bmatrix}
        1 & 1 \\
        1 & \omega_{2}
    \end{bmatrix}
    \begin{bmatrix}
        y_{0}  \\
        y_{1}
    \end{bmatrix}
    = \begin{bmatrix}
        1 & 1 \\
        1 & -1
    \end{bmatrix}
    \begin{bmatrix}
        y_{0}  \\
        y_{1}
    \end{bmatrix} \\
    &= \begin{bmatrix}
        I_{1} &  D_{1} \\
        I_{1} & -D_{1} 
    \end{bmatrix}
    \begin{bmatrix}
        F_{1} & 0 \\
        0 & F_{1}
    \end{bmatrix}
    \begin{bmatrix}
        y_{0} \\
        y_{1}
    \end{bmatrix}
    = \begin{bmatrix}
        1 &  1 \\
        1 & -1 
    \end{bmatrix}
    \begin{bmatrix}
        1 & 0 \\
        0 & 1
    \end{bmatrix}
    \begin{bmatrix}
        y_{0} \\
        y_{1}
    \end{bmatrix}
\end{aligned}
$$

For $n = 4, 8, 16, 32, ...$

$$
    \begin{bmatrix}
        c_{0} \\
        c_{1} \\
        \vdots \\
        c_{n-1}
    \end{bmatrix}
    = F_{n}
    \begin{bmatrix}
        y_{0} \\
        y_{1} \\
        \vdots \\
        y_{n-1}
    \end{bmatrix}
    = \begin{bmatrix}
        I_{n/2} &  D_{n/2} \\
        I_{n/2} & -D_{n/2} 
    \end{bmatrix}
    \begin{bmatrix}
        F_{n/2} & 0 \\
        0 & F_{n/2}
    \end{bmatrix}
    \begin{bmatrix}
        y_{even} \\
        y_{odd}
    \end{bmatrix}
$$






<!-- 


## Sine-cosine to exponential form, algebraically

$$
f(x) =
    \frac{a_{0}}{2} 
    + \sum_{n=1}^{\infty}\left({
                    a_{n}\cos{\frac{2{\pi}nx}{P}}
                +   b_{n}\sin{\frac{2{\pi}nx}{P}}
                        }\right)
$$

where:
$$\begin{aligned}
    a_{0} &= \frac{2}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  {f(t)dt}~, \\
    a_{n} &= \frac{2}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                            {f(t) \cos{\frac{2{\pi}nt}{P}} dt}~, \text{ and} \\
    b_{n} &= \frac{2}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                            {f(t) \sin{\frac{2{\pi}nt}{P}} dt}~.
\end{aligned}$$

$$\begin{aligned}
f(x) &= \frac{1}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  {f(t)dt} \\
            &\hspace{2em}+ \sum_{n=1}^{\infty}  {\frac{2}{P}} \left[ {
                                        \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                                    {f(t) \cos{\frac{2{\pi}nt}{P}} dt}~
                                        \cos{\frac{2{\pi}nx}{P}}
                                    +   \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                                    {f(t) \sin{\frac{2{\pi}nt}{P}} dt}~
                                        \sin{\frac{2{\pi}nx}{P}}
                                               } \right]
\end{aligned}$$

$$\begin{aligned}
\text{noting that } &\cos{u} = \frac{1}{2} \left({ {\cos{u}+i\sin{u}+\cos{u}-i\sin{u}} }\right)
                                          = \frac{1}{2} \left({ {e^{iu}+e^{-iu}} }\right) \text{ and} \\
                    &\sin{u} = \frac{1}{2i}\left({ {\cos{u}-i\sin{u}-\cos{u}+i\sin{u}} }\right)
                                          = \frac{1}{2i}\left({ {e^{iu}-e^{-iu}} }\right) , 
\end{aligned}$$

$$\begin{aligned}
f(x) &= \frac{1}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  {f(t)dt} \\
            &\hspace{2em}+ \sum_{n=1}^{\infty}  {\frac{2}{P}} \left[ {
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                {f(t) \frac{1}{2} \left( 
                                    {e^{i\frac{2{\pi}nt}{P}}+e^{-i\frac{2{\pi}nt}{P}}}
                                                       \right) dt}~
                                \frac{1}{2} \left( 
                                    {e^{i\frac{2{\pi}nx}{P}}+e^{-i\frac{2{\pi}nx}{P}}}
                                            \right) 
                } \right. \\
            &\hspace{6em}  + \left. {
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                {f(t) \frac{1}{2i} \left( 
                                    {e^{i\frac{2{\pi}nt}{P}}-e^{-i\frac{2{\pi}nt}{P}}}
                                                       \right) dt}~
                                \frac{1}{2i} \left( 
                                    {e^{i\frac{2{\pi}nx}{P}}-e^{-i\frac{2{\pi}nx}{P}}}
                                            \right) 
                } \right] \\
                \\
            &= \frac{1}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  {f(t)dt} \\
            &\hspace{2em}+ \sum_{n=1}^{\infty}  {\frac{2}{P}} \left[ {
                    \frac{1}{4} \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   \left( 
                                    \cancel{e^{i\frac{2{\pi}n}{P}(x+t)}}
                                    +e^{i\frac{2{\pi}n}{P}(x-t)}
                                    +e^{i\frac{2{\pi}n}{P}(-x+t)}
                                    +\cancel{e^{i\frac{2{\pi}n}{P}(-x-t)}}
                                            \right.
                } \right. \\
            &\hspace{3.5cm}   \left. {
                                            \left. 
                                    -\cancel{e^{i\frac{2{\pi}n}{P}(x+t)}}
                                    +e^{i\frac{2{\pi}n}{P}(x-t)}
                                    +e^{i\frac{2{\pi}n}{P}(-x+t)}
                                    -\cancel{e^{i\frac{2{\pi}n}{P}(-x-t)}}
                                            \right) dt
                } \right] \\
                \\
            &= \frac{1}{P}  \int_{-\frac{P}{2}}^{\frac{P}{2}}  {f(t)dt}
            + \sum_{n=1}^{\infty}  {\frac{1}{2P}} 
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   \left( 
                                     2e^{i\frac{2{\pi}n}{P}(x-t)}
                                    +2e^{i\frac{2{\pi}n}{P}(-x+t)}
                                            \right) dt \\
                \\
            &= \frac{1}{P} \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{-i\frac{2{\pi}0}{P}t}  dt~ 
                                            e^{i\frac{2{\pi}0}{P}x} \\
            &\hspace{2em}+ \sum_{n=1}^{\infty}  {\frac{1}{P}} 
                    \left[ \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{-i\frac{2{\pi}n}{P}t}  dt~ 
                                            e^{i\frac{2{\pi}n}{P}x}
                          +\int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{-i\frac{2{\pi}(-n)}{P}t}  dt~ 
                                            e^{i\frac{2{\pi}(-n)}{P}x}
                    \right] \\
                \\
            % &=\hspace{0.5em} \sum_{n=0} {\frac{1}{P}} 
            %         \int_{-\frac{P}{2}}^{\frac{P}{2}}  
            %                     f(t)   e^{-i\frac{2{\pi}n}{P}t}  dt~ 
            %                                 e^{i\frac{2{\pi}n}{P}x} \\
            % &\hspace{0.75em}+ \sum_{n=1}^{\infty}  {\frac{1}{P}} 
            %         \int_{-\frac{P}{2}}^{\frac{P}{2}}  
            %                     f(t)   e^{-i\frac{2{\pi}n}{P}t}  dt~ 
            %                                 e^{i\frac{2{\pi}n}{P}x} \\
            % &\hspace{0.75em}+ \sum_{n=-\infty}^{-1}  {\frac{1}{P}} 
            %         \int_{-\frac{P}{2}}^{\frac{P}{2}}  
            %                     f(t)   e^{-i\frac{2{\pi}n}{P}t}  dt~ 
            %                                 e^{i\frac{2{\pi}n}{P}x} \\
            %     \\
            &=\hspace{0.5em} \sum_{n=-\infty}^{n=\infty} {\frac{1}{P}} 
                    \int_{-\frac{P}{2}}^{\frac{P}{2}}  
                                f(t)   e^{-i\frac{2{\pi}n}{P}t}  dt~ 
                                            e^{i\frac{2{\pi}n}{P}x} ~.
\end{aligned}$$



## Dirac Delta

Dirac's delta, $\delta(t)$, is a *generalized function* that has the following properties:

$$
    \int_{-\infty}^{\infty}{\delta(t)dt} = 1
$$

$$
    \int_{-\infty}^{\infty}{f(t)\delta(t-t_{o})dt} = f(t_o)
$$

A common interpretation of Dirac's delta is an instantaneous pulse.

It can be thought of as a sampler of all frequencies when used as an input. Seeing that it is equivalent to the following Fourier coefficient-like integral:

$$
    \delta(t-t_{o}) = \frac{1}{2\pi}\int_{-\infty}^{\infty}{e^{-ix(t-t_{o})}dx}
$$

The Fourier integral theorem confirms its identity.

$$
\begin{aligned}
    f(t_{o}) &= \frac{1}{2\pi}\int_{-\infty}^{\infty}{e^{ixt_{o}} \left\{ \int_{-\infty}^{\infty}{e^{-ixt}f(t)dt} \right\}  dx} \\
    f(t_{o}) &= \frac{1}{2\pi}\int_{-\infty}^{\infty}{ \int_{-\infty}^{\infty}{e^{-ix(t-t_{o})}f(t)dx}  dt} \\
    f(t_{o}) &= \frac{1}{2\pi}\int_{-\infty}^{\infty}{ \left\{ \int_{-\infty}^{\infty}{e^{-ix(t-t_{o})}dx} \right\} f(t)  dt} \\
\end{aligned}
$$ -->
