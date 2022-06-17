# PressureDependMultiYield-Example 9

<table>
<tbody>
<tr class="odd">
<td><p>&lt;center&gt;<strong>Plastic Pressure Dependent Wet Level
Pushover</strong>&lt;/center&gt;</p></td>
</tr>
</tbody>
</table>
<h2 id="input_file">Input File</h2>

```tcl

# Created by Zhaohui Yang (zhyang@ucsd.edu)
# 
<li>plane strain, single element, # push over analysis (Applied load
linearly increases with time)</li>
# SI units (m, s, KN, ton)
# 
# 4 3
<li>------- --&gt; F (loads applied to node 3)</li>
<li>| |</li>
<li>| |</li>
<li>| |</li>
# 1-------2 (nodes 1 and 2 fixed)
# ^ ^

wipe

# 
# some user defined variables
# 

<p>set massDen 2.00 ;# solid mass density set fluidDen 1.0 ;# fluid mass
density set massProportionalDamping 0.0 ; set
stiffnessProportionalDamping 0.001 ;
set fangle 31.40 ;#friction angle
set ptangle 26.50 ;#phase transformation angle set E 90000.0 ;#shear
modulus set poisson 0.40 ;
set G [expr $E/(2*(1+$poisson))] ;
set B [expr $E/(3*(1-2*$poisson))] ;
set press 0.0 ;# isotropic consolidation
pressure on quad element(s) set deltaT 0.010 ;# time step for analysis
set numSteps 2000 ;# Number of analysis steps set gamma 0.500 ;# Newmark
integration parameter set period 1 ;# Period of applied sinusoidal
load</p>
<p>set pi 3.1415926535 ;
set inclination 0 ;
set unitWeightX [expr ($massDen-$fluidDen)*9.81*sin($inclination/180.0*$pi)] ;# unit weight in
X direction set unitWeightY [expr -($massDen-$fluidDen)*9.81*cos($inclination/180.0*$pi)] ;# unit weight
in Y direction</p>
set loadIncr 1 ;# Static shear load

<li><ol>
# 
</ol></li>


# create the ModelBuilder

model basic -ndm 2 -ndf 2

# define material and properties

<p>nDMaterial PressureDependMultiYield 2 2 $massDen $G $B $fangle .1 80
0.5 \ $ptangle 0.17 0.4 10 00 0.015 1.0 nDMaterial FluidSolidPorous 1 2
2 2.2e6</p>

# define the nodes

node 1 0.0 0.0
node 2 1.0 0.0
node 3 1.0 1.0
node 4 0.0 1.0

# define the element thick material maTag press density gravity

<p>element quad 1 1 2 3 4 1.0 "PlaneStrain" 1 $press 0.0 $unitWeightX
$unitWeightY</p>
updateMaterialStage -material 2 -stage 0

# fix the base in vertical direction

fix 1 1 1
fix 2 1 1 equalDOF 3 4 1 2 ;#tie nodes 3 and 4

<li><ol>
# 
</ol></li>
# GRAVITY APPLICATION (elastic behavior)
<li>create the SOE, ConstraintHandler, Integrator, Algorithm and
Numberer</li>

<p>system ProfileSPD 
test NormDispIncr 1.e-12 25 0
constraints Transformation
 integrator LoadControl 1 1 1 1 algorithm Newton numberer
RCM</p>

# create the Analysis

analysis Static

# analyze

analyze 2

# switch the material to plastic

<p>updateMaterialStage -material 1 -stage 1 updateMaterialStage
-material 2 -stage 1 updateMaterials -material 2 bulkModulus [expr $G*2/3.];</p>

# analyze

analyze 1

<li><ol>
# 
</ol></li>
# NOW APPLY LOADING SEQUENCE AND ANALYZE (plastic)


# rezero time

setTime 0.0

# loadConst -time 0.0

wipeAnalysis

# create a LoadPattern with a Linear time series

<p>pattern Plain 1 Linear { load 3 $loadIncr 0.0 ;#load applied in x
direction }</p>
<p>recorder Node -file disp.out -time -node 1 2 3 4 -dof 1 2 -dT 0.01
disp recorder Node -file acce.out -time -node 1 2 3 4 -dof 1 2 -dT 0.01
accel recorder Element -ele 1 -time -file stress1.out -dT 0.01 material
1 stress recorder Element -ele 1 -time -file strain1.out -dT 0.01
material 1 strain recorder Element -ele 1 -time -file stress3.out -dT
0.01 material 3 stress recorder Element -ele 1 -time -file strain3.out
-dT 0.01 material 3 strain recorder Element -ele 1 -time -file
press1.out -dT 0.01 material 1 pressure recorder Element -ele 1 -time
-file press3.out -dT 0.01 material 3 pressure</p>

# create the Analysis

<p>constraints Transformation; # Penalty 1.0e18 1.0e18 ;# test
NormDispIncr 1.e-12 25 0 algorithm Newton numberer RCM system ProfileSPD
rayleigh $massProportionalDamping 0.0 $stiffnessProportionalDamping 0.
integrator Newmark $gamma [expr pow($gamma+0.5, 2)/4] analysis
VariableTransient</p>

# analyze

<p>set startT [clock seconds] analyze $numSteps $deltaT [expr $deltaT/100] $deltaT 10 set endT [clock seconds] puts "Execution time: [expr $endT-$startT] seconds."</p>
wipe #flush ouput stream
<p>
```

<h2 id="matlab_plotting_file">MATLAB Plotting File</h2>

```matlab
 clear all;</p>
<p>a1=load('acce.out'); d1=load('disp.out'); s1=load('stress1.out');
e1=load('strain1.out'); s5=load('stress3.out'); e5=load('strain3.out');
p1=load('press1.out'); p3=load('press3.out');</p>
<p>fs=[0., 0.2, 4, 6];</p>
<p>%integration point 1 p-q po=(s1(:,2)+s1(:,3)+s1(:,4))/3; for
i=1:size(s1,1) qo(i)=(s1(i,2)-s1(i,3))^2 + (s1(i,3)-s1(i,4))^2
+(s1(i,2)-s1(i,4))^2 + 6.0* s1(i,5)^2;
qo(i)=sign(s1(i,5))*1/3.0*qo(i)^0.5; end figure(1); clf; %integration
point 1 stress-strain subplot(2,1,1), plot(e1(:,4),s1(:,5),'r'); title
('Integration point 1 shear stress \tau_x_y VS. shear strain
\epsilon_x_y'); xLabel('Shear strain \epsilon_x_y'); yLabel('Shear
stress \tau_x_y (kPa)');</p>
<p>subplot(2,1,2), plot(-po,qo,'r'); title ('Integration point 1
confinement p VS. deviatoric q relation'); xLabel('confinement p
(kPa)'); yLabel('q (kPa)'); set(gcf,'paperposition',fs);
saveas(gcf,'SS_PQ1','jpg');</p>
<p>%integration point 3 p-q po=(s5(:,2)+s5(:,3)+s5(:,4))/3; for
i=1:size(s5,1) qo(i)=(s5(i,2)-s5(i,3))^2 + (s5(i,3)-s5(i,4))^2
+(s5(i,2)-s5(i,4))^2 + 6.0* s5(i,5)^2;
qo(i)=sign(s5(i,5))*1/3.0*qo(i)^0.5; end</p>
<p>figure(4); clf; %integration point 3 stress-strain subplot(2,1,1),
plot(e5(:,4),s5(:,5),'r'); title ('Integration point 3 shear stress
\tau_x_y VS. shear strain \epsilon_x_y'); xLabel('Shear strain
\epsilon_x_y'); yLabel('Shear stress \tau_x_y (kPa)');</p>
<p>subplot(2,1,2), plot(-po,qo,'r'); title ('Integration point 3
confinement p VS. deviatoric q relation'); xLabel('confinement p
(kPa)'); yLabel('q (kPa)'); set(gcf,'paperposition',fs);
saveas(gcf,'SS_PQ5','jpg');</p>
<p>figure(2); clf; %node 3 displacement relative to node 1
subplot(2,1,1),plot(d1(:,1),d1(:,6)*100,'r'); title ('Lateral
displacement at element top'); xLabel('Time (s)'); yLabel('Displacement
(cm)'); set(gcf,'paperposition',fs); saveas(gcf,'D','jpg');</p>
<p>figure(5); clf; %integration point 1 excess pore water pressure
subplot(2,1,1),plot(p1(:,1),-p1(:,2),'r'); title ('Integration point 1
excess pore pressure'); xLabel('Time (s)'); yLabel('Excess pore pressure
(kPa)');</p>
<p>subplot(2,1,2),plot(p1(:,1),p1(:,3),'r'); title ('Integration point 1
excess pore pressure ratio'); xLabel('Time (s)'); yLabel('Excess pore
pressure ratio'); set(gcf,'paperposition',fs); saveas(gcf,'EPWP','jpg');

```

<h2 id="displacement_output_file">Displacement Output File</h2>
<figure>
<img src="/OpenSeesRT/contrib/static/PD_Ex16Disp.png" title="PD_Ex16Disp.png"
alt="PD_Ex16Disp.png" />
<figcaption aria-hidden="true">PD_Ex16Disp.png</figcaption>
</figure>
<h2 id="stress_strain_output_file_integration_point_1">Stress-Strain
Output File (Integration Point 1)</h2>
<figure>
<img src="/OpenSeesRT/contrib/static/PD_Ex16SS_PQ13.png" title="PD_Ex16SS_PQ13.png"
alt="PD_Ex16SS_PQ13.png" />
<figcaption aria-hidden="true">PD_Ex16SS_PQ13.png</figcaption>
</figure>
<h2 id="excess_pore_pressure_output_file">Excess Pore Pressure Output
File</h2>
<figure>
<img src="/OpenSeesRT/contrib/static/PD_Ex16EPP.png" title="PD_Ex16EPP.png" alt="PD_Ex16EPP.png" />
<figcaption aria-hidden="true">PD_Ex16EPP.png</figcaption>
</figure>
<hr />
Return to: 